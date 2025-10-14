from fastapi import APIRouter, Depends
from backend.datamodels import Edition
from backend.dependencies import get_cfg_manager
from backend.services.scrape_service import (
    scrape_book_editions,
    scrape_author_data,
    scrape_search,
)


router = APIRouter(prefix="/tapi", tags=["scraped"])

@router.get("/books/editions/{book_id}")
async def fetch_book_editions(book_id: str, cfg = Depends(get_cfg_manager)):
    editions, series = await scrape_book_editions(book_id, cfg)
    return {
        "editions": [Edition(**i) for i in editions],
        "series": series,
    }

@router.get("/author/{author_id}")
async def fetch_author_data(author_id: str, cfg = Depends(get_cfg_manager)):
    data = await scrape_author_data(author_id, cfg)
    return data

@router.get("/search")
async def search(q: str, cfg = Depends(get_cfg_manager)):
    data = await scrape_search(q, cfg)
    return data
