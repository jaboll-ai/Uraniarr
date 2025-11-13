import logging
from pathlib import Path
from pickle import dump, load
from time import time
import os
from urllib.parse import urlencode
from backend.config import ConfigManager
import asyncio
from backend.dependencies import get_error_logger, get_logger
from backend.exceptions import ScrapeError
from contextlib import suppress
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from cloudscraper import create_scraper

try:
    cache_dir = Path(os.getenv("CONFIG_DIR", "./config")) / "cache"
except Exception as exc:
    get_logger().error(f"Failed to get cache directory")
    get_error_logger().exception(exc)
scraper = None

try: _cache = load(cache_dir.open("rb"))
except FileNotFoundError: _cache = {}
except Exception as e: get_logger().error(f"Failed to load cache: {e}")


async def reload_scraper(state):
    global scraper
    get_logger().debug("Reloading scraper...")
    with suppress(Exception):
        await state.browser.close()
    with suppress(Exception):
        await state.playwright.stop()
    if state.cfg_manager.playwright:
        if os.name == "nt":
            state.cfg_manager.playwright = False
            raise ScrapeError(status_code=500, detail="Playwright is not supported on Windows")
        state.playwright = await Stealth().use_async(async_playwright()).__aenter__()
        state.browser = await state.playwright.chromium.launch(headless=True)
    else:
        state.browser = create_scraper()
    scraper = state.browser


async def fetch(cfg: ConfigManager, url: str, params: dict, xhr: bool) -> dict:
    target = f"{url}?{urlencode(params)}" if params else url
    if cfg.playwright:
        page = await scraper.new_page()
        if xhr:
            get_logger().log(5, f"Using playwright#expect_response to GET {target}")
            async with page.expect_response(target) as response_info:
                await page.goto(target)
            response = await response_info.value
            if response.status != 200:
                raise ScrapeError(status_code=response.status, detail=response.text)
            data = await response.body()
        else:
            get_logger().log(5, f"Using playwright#goto to GET {target}")
            await page.goto(target)
            data = await page.content()
        await page.close()
    else:
        get_logger().log(5, f"Using cloudscraper to GET {target}")
        response = await asyncio.to_thread(scraper.get, target)
        if response.status_code != 200:
                raise ScrapeError(status_code=response.status_code, detail=response.text)
        data = response.content
    if not data:
        raise ScrapeError(status_code=response.status_code, detail=response.text)
    return data

async def fetch_or_cached(cfg: ConfigManager, url: str, params: dict = {}, xhr: bool = True):
    key = (url, tuple(sorted(params.items())))
    now = time()
    if not cfg.skip_cache and key in _cache and now - _cache[key]["time"] < 5*24*3600:
        get_logger().log(5, f"Using cache for {url}")
        data = _cache[key]["data"]
    else:
        data = await fetch(cfg, url, params, xhr)
        _cache[key] = {"time": now, "data": data}
        dump(_cache, cache_dir.open("wb"))
    return data