from fastapi import HTTPException, Depends, APIRouter
from backend.dependencies import get_session, get_cfg_manager
from sqlmodel import Session, select
from backend.datamodels import *
from backend.payloads import *
from backend.config import ConfigManager
from backend.services.scrape_service import scrape_all_author_data, scrape_book_series, clean_title
from backend.services.author_service import save_author_to_db, complete_series_in_db, make_author_from_series, union_series
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
        books = []
        for book in author.books:
            resp = book.model_dump()
            resp["activities"] = book.activities
            books.append(resp)
        return resp
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/author/{author_id}")
def get_author_info(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/book/{book_id}")
def get_book(book_id: str, session: Session = Depends(get_session)):
    if book := session.get(Book, book_id):
        resp = book.model_dump()
        resp["activities"] = book.activities
        return resp
    raise HTTPException(status_code=404, detail="Book not found")

@router.get("/authors")
def get_authors(session: Session = Depends(get_session)):
    return session.scalars(select(Author)).all()

@router.get("/series/{series_id}/books")
def get_books_of_series(series_id: str, session: Session = Depends(get_session)):
    if reihe := session.get(Reihe, series_id):
        books = []
        for book in reihe.books:
            resp = book.model_dump()
            resp["activities"] = book.activities
            books.append(resp)
        return books
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
async def add_author(author_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager), override: bool = False, name: str = ""):
    data = await scrape_all_author_data(author_id, cfg, name)
    resp = await asyncio.to_thread(save_author_to_db, author_id, session, data, override)
    return resp

@router.post("/series/complete/{series_id}")
async def complete_series_of_author(series_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    reihe = session.get(Reihe, series_id)
    ed_id = min(reihe.books, key=lambda b: (b.reihe_position or 999)).editions[0].key
    data = await scrape_book_series(ed_id, cfg)
    resp = await asyncio.to_thread(complete_series_in_db, series_id, session, data)
    return resp

@router.delete("/series/{series_id}")
def delete_series(series_id: str, session: Session = Depends(get_session), files: bool = False):
    if files:
        delete_audio_reihe(series_id, session)
    if series := session.get(Reihe, series_id):
        session.delete(series)
        session.commit()
        return {"deleted": series_id}
    raise HTTPException(status_code=404, detail="Series not found")

@router.delete("/series/{series_id}/files")
def delete_series_files(series_id: str, session: Session = Depends(get_session)):
    delete_audio_reihe(series_id, session)
    return {"deleted files": series_id}

@router.delete("/book/{book_id}")
def delete_book(book_id: str, session: Session = Depends(get_session), files: bool = False):
    if files:
        delete_audio_book(book_id, session)
    if book := session.get(Book, book_id):
        if len(book.reihe.books) == 1:
            session.delete(book.reihe)
        session.delete(book)
        session.commit()
        return {"deleted": book_id}
    raise HTTPException(status_code=404, detail="Book not found")

@router.delete("/book/{book_id}/files")
def delete_book_files(book_id: str, session: Session = Depends(get_session)):
    delete_audio_book(book_id, session)
    return {"deleted files": book_id}

@router.delete("/author/{author_id}")
def delete_author(author_id: str, session: Session = Depends(get_session), files: bool = False):
    if files:
        delete_audio_author(author_id, session)
    if author := session.get(Author, author_id):
        session.delete(author)
        session.commit()
        return {"deleted": author_id}
    raise HTTPException(status_code=404, detail="Author not found")

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

@router.post("/fakeauthor")
async def fake_author(seriesAuthor: SeriesAuthor, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    data = await scrape_book_series(seriesAuthor.entry_id, cfg)
    resp = await asyncio.to_thread(make_author_from_series, seriesAuthor.name, session, data)
    return resp

@router.post("/misc/union/")
async def unite_series(data: UnionSeries, session: Session = Depends(get_session)):
    resp = union_series(data.series_id, data.series_ids, session)
    return resp

@router.get("/book/titles/{book_id}")
async def get_alternative_titles(book_id: str, session: Session = Depends(get_session)):
    book = session.get(Book, book_id)
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    return [clean_title(ed.titel, book.reihe.name if book.reihe_key else None, book.reihe_position) for ed in book.editions]
    