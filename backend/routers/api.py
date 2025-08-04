from fastapi import HTTPException, Depends, APIRouter
from backend.dependencies import get_session, get_cfg_manager
from sqlmodel import Session, select
from backend.datamodels import *
from backend.config import ConfigManager
from backend.services.scrape_service import scrape_all_author_data, scrape_book_series, clean_title
from backend.services.author_service import save_author_to_db, complete_series_in_db
from backend.services.filehelper import delete_audio_reihe, delete_audio_book, delete_audio_author
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
    data = await scrape_all_author_data(author_id)
    resp = await asyncio.to_thread(save_author_to_db, author_id, session, data, override)
    return resp

@router.post("/series/complete/{series_id}")
async def complete_series_of_author(series_id: str, session: Session = Depends(get_session)):
    reihe = session.get(Reihe, series_id)
    ed_id = min(reihe.books, key=lambda b: (b.reihe_position or 999)).editions[0].key
    data = await scrape_book_series(ed_id)
    resp = await asyncio.to_thread(complete_series_in_db, series_id, session, data)
    return resp

@router.delete("/series/{series_id}")
def delete_series(series_id: str, session: Session = Depends(get_session), files: bool = False):
    if files:
        delete_audio_reihe(series_id, session)
    session.delete(session.get(Reihe, series_id))
    session.commit()
    return {"deleted": series_id}

@router.delete("/series/{series_id}/files")
def delete_series_files(series_id: str, session: Session = Depends(get_session)):
    delete_audio_reihe(series_id, session)
    return {"deleted files": series_id}

@router.delete("/book/{book_id}")
def delete_book(book_id: str, session: Session = Depends(get_session), files: bool = False):
    if files:
        delete_audio_book(book_id, session)
    session.delete(session.get(Book, book_id))
    session.commit()
    return {"deleted": book_id}

@router.delete("/book/{book_id}/files")
def delete_book_files(book_id: str, session: Session = Depends(get_session)):
    delete_audio_book(book_id, session)
    return {"deleted files": book_id}

@router.delete("/author/{author_id}")
def delete_author(author_id: str, session: Session = Depends(get_session), files: bool = False):
    if files:
        delete_audio_author(author_id, session)
    session.delete(session.get(Author, author_id))
    session.commit()
    return {"deleted": author_id}

@router.delete("/author/{author_id}/files")
def delete_author_files(author_id: str, session: Session = Depends(get_session)):
    delete_audio_author(author_id, session)
    return {"deleted files": author_id}

@router.patch("/book/{book_id}")
async def update_book(book_id: str, data: dict, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    for field, value in data.items():
        if hasattr(book, field):
            setattr(book, field, value)
    session.commit()
    return book

@router.post("/series/cleanup/{series_id}")
async def cleanup_series(series_id: str, name: str, session: Session = Depends(get_session)):
    reihe = session.get(Reihe, series_id)
    if not reihe: raise HTTPException(status_code=404, detail="Series not found")
    updates = 0
    for book in reihe.books:
        ctitle = clean_title(book.name, name, book.reihe_position)
        if ctitle != book.name:
            book.name = ctitle
            updates += 1
    session.commit()
    return {"updated": updates}
