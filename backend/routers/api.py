from fastapi import HTTPException, Depends, APIRouter
from backend.dependencies import get_session, get_cfg_manager
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.datamodels import *
from backend.payloads import *
from backend.config import ConfigManager
from backend.services.scrape_service import scrape_all_author_data, scrape_book_series, clean_title
from backend.services.author_service import save_author_to_db, complete_series_in_db, add_books_to_author, make_author_from_series, union_series
from backend.services.filehelper import delete_audio_reihe, delete_audio_book, delete_audio_author, get_files_of_book
import asyncio

router = APIRouter(prefix="/api", tags=["database"])

@router.get("/authors")
async def get_authors(session: AsyncSession = Depends(get_session)):
    scalar = await session.scalars(select(Author))
    return scalar.all()

@router.get("/author/{author_id}")
async def get_author_info(author_id: str, session: AsyncSession = Depends(get_session)):
    if author := await session.get(Author, author_id):
        return author
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/author/{author_id}/series")
async def get_author_series(author_id: str, session: AsyncSession = Depends(get_session)):
    if author := await session.get(Author, author_id, options=[selectinload(Author.reihen)]):
        return author.reihen
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/author/{author_id}/books")
async def get_author_books(author_id: str, session: AsyncSession = Depends(get_session)):
    if author := await session.get(Author, author_id, options=[selectinload(Author.books).selectinload(Book.activities)]):
        books = []
        for book in author.books:
            if book.blocked: continue
            resp = book.model_dump()
            resp["activities"] = book.activities
            books.append(resp)
        return books
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/series/{series_id}/books")
async def get_books_of_series(series_id: str, session: AsyncSession = Depends(get_session)):
    if reihe := await session.get(Reihe, series_id, options=[selectinload(Reihe.books).selectinload(Book.activities)]):
        books = []
        for book in reihe.books:
            if book.blocked: continue
            resp = book.model_dump()
            resp["activities"] = book.activities
            books.append(resp)
        return books
    raise HTTPException(status_code=404, detail="Series not found") 

@router.get("/book/{book_id}")
async def get_book(book_id: str, session: AsyncSession = Depends(get_session)):
    if book := await session.get(Book, book_id, options=[selectinload(Book.activities)]):
        resp = book.model_dump()
        resp["activities"] = book.activities
        return resp
    raise HTTPException(status_code=404, detail="Book not found")

@router.get("/book/titles/{book_id}")
async def get_alternative_titles(book_id: str, session: AsyncSession = Depends(get_session)):
    book = await session.get(Book, book_id, options=[selectinload(Book.editions), selectinload(Book.reihe)])
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    return [clean_title(ed.titel, book.reihe.name if book.reihe_key else None, book.reihe_position) for ed in book.editions]

@router.get("/book/files/{book_id}")
async def get_book_files(book_id: str, session: AsyncSession = Depends(get_session)):
    book = await session.get(Book, book_id)
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    data = await get_files_of_book(book)
    return data

@router.get("/settings")
async def get_settings(cfg: ConfigManager = Depends(get_cfg_manager)):
    return cfg.get()

@router.post("/author/{author_id}")
async def add_author(author_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager), override: bool = False, name: str = ""):
    data = await scrape_all_author_data(author_id, cfg, name)
    resp = await save_author_to_db(author_id, session, data, override)
    return resp

@router.post("/author/complete/{author_id}")
async def complete_author(author_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    author = await session.get(Author, author_id, options=[selectinload(Author.reihen).selectinload(Reihe.books), selectinload(Author.books)])
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    data = await scrape_all_author_data(author.key, cfg, author.name)
    resp = await add_books_to_author(author, session, data["books"])
    return resp

@router.post("/fakeauthor")
async def fake_author(seriesAuthor: SeriesAuthor, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    data = await scrape_book_series(seriesAuthor.entry_id, cfg)
    resp = await make_author_from_series(seriesAuthor.name, session, data)
    return resp

@router.post("/series/complete/{series_id}")
async def complete_series_of_author(series_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    reihe = await session.get(Reihe, series_id, options=[selectinload(Reihe.books).selectinload(Book.editions)])
    ed_id = min(reihe.books, key=lambda b: (b.reihe_position or 999)).editions[0].key
    data = await scrape_book_series(ed_id, cfg)
    resp = await complete_series_in_db(series_id, session, data)
    return resp

@router.post("/series/cleanup/{series_id}")
async def cleanup_series(series_id: str, name: str, session: AsyncSession = Depends(get_session)):
    reihe = await session.get(Reihe, series_id)
    if not reihe: raise HTTPException(status_code=404, detail="Series not found")
    updates = 0
    for book in reihe.books:
        ctitle = clean_title(book.name, name, book.reihe_position)
        if ctitle != book.name:
            book.name = ctitle
            updates += 1
    await session.commit()
    return {"updated": updates}

@router.post("/misc/union/")
async def unite_series(data: UnionSeries, session: AsyncSession = Depends(get_session)):
    resp = await union_series(data.series_id, data.series_ids, session)
    return resp

@router.patch("/book/{book_id}")
async def update_book(book_id: str, data: dict, session: AsyncSession = Depends(get_session)):
    book = await session.get(Book, book_id)
    for field, value in data.items():
        if hasattr(book, field):
            setattr(book, field, value)
    await session.commit()
    return book

@router.patch("/settings")
async def update_settings(settings: dict, cfg: ConfigManager = Depends(get_cfg_manager)):
    for key in settings:
        setattr(cfg, key, settings[key])
    return cfg.get()

@router.delete("/author/{author_id}")
async def delete_author(author_id: str, session: AsyncSession = Depends(get_session), files: bool = False):
    if files:
        await delete_audio_author(author_id, session)
    if author := await session.get(Author, author_id):
        await session.delete(author)
        await session.commit()
        return {"deleted": author_id}
    raise HTTPException(status_code=404, detail="Author not found")

@router.delete("/author/{author_id}/files")
async def delete_author_files(author_id: str, session: AsyncSession = Depends(get_session)):
    await delete_audio_author(author_id, session)
    return {"deleted files": author_id}

@router.delete("/series/{series_id}")
async def delete_series(series_id: str, session: AsyncSession = Depends(get_session), files: bool = False):
    if files:
        await delete_audio_reihe(series_id, session)
    if series := await session.get(Reihe, series_id):
        await session.delete(series)
        await session.commit()
        return {"deleted": series_id}
    raise HTTPException(status_code=404, detail="Series not found")

@router.delete("/series/{series_id}/files")
async def delete_series_files(series_id: str, session: AsyncSession = Depends(get_session)):
    await delete_audio_reihe(series_id, session)
    return {"deleted files": series_id}

@router.delete("/book/{book_id}")
async def delete_book(book_id: str, session: AsyncSession = Depends(get_session), files: bool = False, block: bool = False):
    if files:
        await delete_audio_book(book_id, session)
    book = await session.get(Book, book_id, options=[selectinload(Book.reihe).selectinload(Reihe.books)])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    reihe = book.reihe
    if not reihe:
        if block:
            book.blocked = True
            await session.commit()
            return {"blocked": book_id}
        await session.delete(book)
        await session.commit()
        return {"deleted": book_id}
    if block:
        book.blocked = True
        book.reihe_key = None
        if len(reihe.books) == 0:
            session.delete(reihe)
        await session.commit()
        return {"blocked": book_id}
    if len(reihe.books) == 1:
        await session.delete(reihe)
    await session.delete(book)
    await session.commit()
    return {"deleted": book_id}

@router.delete("/book/{book_id}/files")
async def delete_book_files(book_id: str, session: AsyncSession = Depends(get_session)):
    await delete_audio_book(book_id, session)
    return {"deleted files": book_id}
