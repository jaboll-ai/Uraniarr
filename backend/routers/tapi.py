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
    data = await scrape_author_data(author_id)
    return data

@router.get("/search")
async def search(q: str):
    data = await scrape_search(q)
    return data
