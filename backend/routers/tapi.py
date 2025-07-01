from fastapi import APIRouter
from backend.datamodels import Edition
from backend.services.scrape_service import (
    scrape_book_editions,
    scrape_author_data,
    scrape_search,
)

router = APIRouter(prefix="/tapi", tags=["scraped"])

@router.get("/books/editions/{book_id}")
def fetch_book_editions(book_id: str):
    editions, series = scrape_book_editions(book_id)
    return {
        "editions": [Edition(**i) for i in editions],
        "series": series,
    }

@router.get("/author/{author_id}")
def fetch_author_data(author_id: str):
    return scrape_author_data(author_id)

@router.get("/search")
def search(q: str):
    return scrape_search(q)
