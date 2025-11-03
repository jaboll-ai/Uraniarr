from pickle import dump, load
from time import time
import os
from urllib.parse import urlencode
from backend.config import ConfigManager
import asyncio
from backend.exceptions import ScrapeError
from contextlib import suppress
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from cloudscraper import create_scraper

cache_dir = ConfigManager.config_dir / "cache"
scraper = None

try: _cache = load(cache_dir.open("rb"))
except FileNotFoundError: _cache = {}


async def reload_scraper(state):
    global scraper
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

    
async def fetch(url: str, params: dict, xhr: bool) -> dict:
    cfg = ConfigManager()
    target = f"{url}?{urlencode(params)}" if params else url
    if cfg.playwright:
        page = await scraper.new_page()
        if xhr:
            async with page.expect_response(target) as response_info:
                await page.goto(target)
            response = await response_info.value
            if response.status != 200:
                raise ScrapeError(status_code=response.status, detail=response.text)
            data = await response.body()
        else:
            await page.goto(target)
            data = await page.content()
        await page.close()
    else:
        response = await asyncio.to_thread(scraper.get, target)
        if response.status_code != 200:
                raise ScrapeError(status_code=response.status_code, detail=response.text)
        data = response.content
    if not data:
        raise ScrapeError(status_code=response.status_code, detail=response.text)
    return data

async def fetch_or_cached(url: str, params: dict = {}, xhr: bool = True):
    cfg = ConfigManager()
    key = (url, tuple(sorted(params.items())))
    now = time()
    if not cfg.skip_cache and key in _cache and now - _cache[key]["time"] < 5*24*3600:
        data = _cache[key]["data"]
    else:
        data = await fetch(url, params, xhr)
        _cache[key] = {"time": now, "data": data}
        dump(_cache, cache_dir.open("wb"))
    return data