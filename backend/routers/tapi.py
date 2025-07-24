from fastapi import APIRouter
from backend.datamodels import Edition
from backend.services.scrape_service import (
    scrape_book_editions,
    scrape_author_data,
    scrape_search,
)

router = APIRouter(prefix="/tapi", tags=["scraped"])

@router.get("/books/editions/{book_id}")
async def fetch_book_editions(book_id: str):
    editions, series = await scrape_book_editions(book_id)
    return {
        "editions": [Edition(**i) for i in editions],
        "series": series,
    }

@router.get("/author/{author_id}")
async def fetch_author_data(author_id: str):
    return await scrape_author_data(author_id)

@router.get("/search")
async def search(q: str):
    return await scrape_search(q)
