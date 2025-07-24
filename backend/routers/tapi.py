from fastapi import APIRouter
from backend.datamodels import Edition
from backend.services.scrape_service import (
    scrape_book_editions,
    scrape_author_data,
    scrape_search,
)
from playwright_stealth import Stealth
from playwright.async_api import async_playwright

router = APIRouter(prefix="/tapi", tags=["scraped"])

@router.get("/books/editions/{book_id}")
async def fetch_book_editions(book_id: str):
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        editions, series = await scrape_book_editions(browser,book_id)
    return {
        "editions": [Edition(**i) for i in editions],
        "series": series,
    }

@router.get("/author/{author_id}")
async def fetch_author_data(author_id: str):
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        data = await scrape_author_data(browser, author_id)
    return data

@router.get("/search")
async def search(q: str):
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        data = await scrape_search(browser, q)
    return data
