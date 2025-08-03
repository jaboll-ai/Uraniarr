from pickle import dump, load
from time import time
from urllib.parse import urlencode
from backend.config import ConfigManager
import asyncio
from backend.exceptions import ScrapeError


cache_dir = ConfigManager.config_dir / "cache"
scraper = None

try: _cache = load(cache_dir.open("rb"))
except FileNotFoundError: _cache = {}


def set_scraper(s):
    global scraper
    scraper = s

async def fetch(url: str, params: dict, xhr: bool) -> dict:
    cfg = ConfigManager()
    target = f"{url}?{urlencode(params)}" if params else url
    if cfg.playwright:
        page = await scraper.new_page()
        if xhr: xhrPromise = page.wait_for_response(target)
        await page.goto(target)
        if xhr: 
            data = await xhrPromise
        else:
            data = await page.content()
        await page.close()
    else:
        response = await asyncio.to_thread(scraper.get, target)
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