from pickle import dump, load
from time import time
from urllib.parse import urlencode
from backend.config import ConfigManager
import asyncio


cache_dir = ConfigManager.config_dir / "cache"
scraper = None

try: _cache = load(cache_dir.open("rb"))
except FileNotFoundError: _cache = {}


def set_scraper(s):
    global scraper
    scraper = s

async def fetch(url: str, params: dict = {}) -> dict:
    cfg = ConfigManager()
    target = f"{url}?{urlencode(params)}" if params else url
    if cfg.playwright:
        page = await scraper.new_page()
        await page.goto(target)
        data = await page.body()
        await page.close()
    else:
        response = await asyncio.to_thread(scraper.get, target)
        data = response.content
    return data

async def fetch_or_cached(url: str, params: dict = {}):
    cfg = ConfigManager()
    key = (url, tuple(sorted(params.items())))
    now = time()
    if not cfg.skip_cache and key in _cache and now - _cache[key]["time"] < 5*24*3600:
        data = _cache[key]["data"]
    else:
        data = await fetch(url, params)
        _cache[key] = {"time": now, "data": data}
        dump(_cache, cache_dir.open("wb"))
    return data