from fastapi import HTTPException, Depends, APIRouter
from backend.dependencies import get_session, get_cfg_manager
from sqlmodel import Session, select
from backend.datamodels import *
from backend.config import ConfigManager
from backend.services.scrape_service import scrape_all_author_data
from backend.services.author_service import save_author_to_db
from playwright_stealth import Stealth
from playwright.async_api import async_playwright
import asyncio

router = APIRouter(prefix="/api", tags=["database"])

@router.get("/author/{author_id}/series")
def get_author_series(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author.reihen
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/author/{author_id}/books")
def get_author_books(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author.books
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/author/{author_id}")
def get_author_info(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/book/{book_id}")
def get_book(book_id: str, session: Session = Depends(get_session)):
    if book := session.get(Book, book_id):
        return book
    raise HTTPException(status_code=404, detail="Book not found")

@router.get("/authors")
def get_authors(session: Session = Depends(get_session)):
    return session.scalars(select(Author)).all()

@router.get("/series/{series_id}/books")
def get_books_of_series(series_id: str, session: Session = Depends(get_session)):
    if reihe := session.get(Reihe, series_id):
        return reihe.books
    raise HTTPException(status_code=404, detail="Series not found") 

@router.delete("/author/{author_id}")
def delete_author(author_id: str, session: Session = Depends(get_session)):
    session.delete(session.get(Author, author_id))
    session.commit()
    return {"deleted": author_id}

@router.get("/settings")
def get_settings(cfg: ConfigManager = Depends(get_cfg_manager)):
    """Retrieve all configuration settings."""
    return cfg.get()

@router.patch("/settings")
def update_settings(settings: dict, cfg: ConfigManager = Depends(get_cfg_manager)):
    """Update all configuration settings in one call using attribute access."""
    for key in settings:
        setattr(cfg, key, settings[key])
    return cfg.get()

@router.post("/author/{author_id}")
async def add_author(author_id: str, session: Session = Depends(get_session), override: bool = False):
    async with Stealth().use_async(async_playwright()) as p:
        browser = await p.chromium.launch(headless=True)
        data = await scrape_all_author_data(browser, author_id)
    resp = await asyncio.to_thread(save_author_to_db, author_id, session, data, override)
    return resp
