import asyncio
from typing import Any
from fastapi import HTTPException, Depends, APIRouter, Request
from backend.dependencies import get_logger, get_session, get_cfg_manager
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.datamodels import *
from backend.payloads import *
from backend.config import ConfigManager
from backend.services.jobs import get_job_by_interval, restart_job
from backend.services.scrape import scrape_all_author_data, scrape_book_series, clean_title
from backend.services.request import reload_scraper
from backend.services.author_service import save_author_to_db, complete_series_in_db, add_books_to_author, make_author_from_series, union_series
from backend.services.filehelper import delete_audio_series, delete_audio_book, delete_audio_author, ensure_backup, get_files_of_book, preview_retag, retag_book
from backend.services.indexer import *
from backend.services.downloader import *

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
    if author := await session.get(Author, author_id, options=[selectinload(Author.series)]):
        return author.series
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
    if series := await session.get(Series, series_id, options=[selectinload(Series.books).selectinload(Book.activities)]):
        books = []
        for book in series.books:
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
    book = await session.get(Book, book_id, options=[selectinload(Book.editions)])
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    return [ed.titel for ed in book.editions]

@router.get("/book/files/{book_id}")
async def get_book_files(book_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = await session.get(Book, book_id, options=[selectinload(Book.author)])
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    data = await get_files_of_book(book)
    if data["audio"] is None:
        book.a_dl_loc = None
        data["audio"] = []
    if data["book"] is None:
        book.b_dl_loc = None
        data["book"] = []
    await session.commit()
    a = [{ "path": i["path"].relative_to(cfg.audio_path) if i["path"].is_relative_to(cfg.audio_path) else i["path"], "size": i["size"]} for i in data["audio"]]
    b = [{ "path": i["path"].relative_to(cfg.book_path) if i["path"].is_relative_to(cfg.book_path) else i["path"], "size": i["size"]} for i in data["book"]]
    return {
        "audio": a,
        "book": b
    }

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
    author = await session.get(Author, author_id, options=[selectinload(Author.series).selectinload(Series.books).selectinload(Book.editions), selectinload(Author.books).selectinload(Book.editions)])
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    if author.is_series:
        ed_id = min(author.series[0].books, key=lambda b: (b.position or 999)).editions[0].key
        data = await scrape_book_series(ed_id, cfg)
        resp = await complete_series_in_db(author.series[0].key, session, data)
        return resp
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
    series = await session.get(Series, series_id, options=[selectinload(Series.books).selectinload(Book.editions)])
    if not series: raise HTTPException(status_code=404, detail="Series not found")
    ed_id = min(series.books, key=lambda b: (b.position or 999)).editions[0].key
    data = await scrape_book_series(ed_id, cfg)
    resp = await complete_series_in_db(series_id, session, data)
    return resp

@router.post("/series/cleanup/{series_id}")
async def cleanup_series(series_id: str, name: str, session: AsyncSession = Depends(get_session)):
    series = await session.get(Series, series_id)
    if not series: raise HTTPException(status_code=404, detail="Series not found")
    updates = 0
    for book in series.books:
        ctitle = clean_title(book.name, name, book.position)
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
async def update_book(book_id: str, data: dict, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = await session.get(Book, book_id, options=[
        selectinload(Book.author),
        selectinload(Book.series).selectinload(Series.books),
        selectinload(Book.activities)
    ])
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    errors = []
    for field, value in data.items():
        if field in ["author", "series", "editions", "activities", "a_dl_loc", "b_dl_loc", "key"]:
            errors.append(field)
        elif hasattr(book, field):
            setattr(book, field, value if value != "" else None)
    await session.commit()
    if errors:
        raise HTTPException(status_code=403, detail=f"Tried to update immutable fields: {', '.join(errors)}")
    return book_id

@router.get("/retag/author/{author_id}")
async def get_preview_retag_author(author_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    author = await session.get(Author, author_id, options=[
        selectinload(Author.books).selectinload(Book.author),
        selectinload(Author.books).selectinload(Book.series).selectinload(Series.books),
        selectinload(Author.books).selectinload(Book.activities)
    ])
    if not author: raise HTTPException(status_code=404, detail="Author not found")
    retags = [preview_retag(book, cfg) for book in author.books]
    resp = {
        "name": author.name,
        "key": author.key,
        "retags": [r for r in retags if r["retag"]["new_audio"] or r["retag"]["new_book"]]
    }
    return resp

@router.get("/retag/book/{book_id}")
async def get_preview_retag(book_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = await session.get(Book, book_id, options=[
        selectinload(Book.author),
        selectinload(Book.series).selectinload(Series.books),
        selectinload(Book.activities)
    ])
    if not book: raise HTTPException(status_code=404, detail="Book not found")
    if not book.a_dl_loc and not book.b_dl_loc: raise HTTPException(status_code=404, detail=f"{book.name} is not downloaded, cant retag")
    resp=preview_retag(book, cfg)
    return resp

@router.post("/retag/books")
async def do_retag_books(data: list[str], session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    query = await session.exec(select(Book).where(Book.key.in_(data)).options(
        selectinload(Book.author),
        selectinload(Book.series).selectinload(Series.books),
        selectinload(Book.activities)
    ))
    downloaded = await session.exec(select(Book).where(Book.a_dl_loc.isnot(None) | Book.b_dl_loc.isnot(None)))
    count = len(downloaded.all())
    books: list[Book] = list(query.scalars().all())
    missing = set(b.key for b in books).difference(set(data))
    if missing: raise HTTPException(status_code=404, detail=f"Books dont exist: {', '.join(missing)}")
    retags = []
    overwrite = len(books)==count
    get_logger().debug(f"Retagging with overwrite: {overwrite}")
    # if overwrite:
    #     # BACKUP HERE
    #     raise NotImplementedError
    for book in books:
        if not book.a_dl_loc and not book.b_dl_loc: raise HTTPException(status_code=404, detail=f"{book.name} is not downloaded, cant retag")
        retags.append(retag_book(book, cfg, overwrite=overwrite))
    rs = await asyncio.gather(*retags)
    resp = [
        {book.key: {
            "audio": r[0] is not None,
            "book": r[1] is not None
        }} for r, book in zip(rs, books)
    ]
    await session.commit()
    return resp

@router.patch("/settings")
async def update_settings(settings: dict[str, Any], request: Request):
    state = request.app.state
    cfg = state.cfg_manager
    for key in settings:
        setattr(cfg, key, settings[key])
        if key == "playwright":
            await reload_scraper(state)
        elif key == "indexer_prowlarr":
            state.indexer = ProwlarrService() if settings[key] else NewznabService()
        elif key == "downloader_type":
            if cfg.downloader_type == "sab":
                state.downloader = SABDownloader()
            else:
                cfg.downloader_type = "sab" #TODO other downloaders
                state.downloader = SABDownloader()
                raise HTTPException(status_code=500, detail="Only SABDownloader supported currently")
        elif key.endswith("_interval"):
            await restart_job(state, get_job_by_interval(key))
    return state.cfg_manager.get()

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
        await delete_audio_series(series_id, session)
    if series := await session.get(Series, series_id):
        await session.delete(series)
        await session.commit()
        return {"deleted": series_id}
    raise HTTPException(status_code=404, detail="Series not found")

@router.delete("/series/{series_id}/files")
async def delete_series_files(series_id: str, session: AsyncSession = Depends(get_session)):
    await delete_audio_series(series_id, session)
    return {"deleted files": series_id}

@router.delete("/book/{book_id}")
async def delete_book(book_id: str, session: AsyncSession = Depends(get_session), files: bool = False, block: bool = False):
    if files:
        await delete_audio_book(book_id, session)
    book = await session.get(Book, book_id, options=[selectinload(Book.series).selectinload(Series.books)])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    series = book.series
    if not series:
        if block:
            book.blocked = True
            await session.commit()
            return {"blocked": book_id}
        await session.delete(book)
        await session.commit()
        return {"deleted": book_id}
    if block:
        book.blocked = True
        book.series_key = None
    else:
        await session.delete(book)

    _s = series.key
    await session.commit() #DONT flush. We need to commit for async to work
    series = await session.get(Series, _s, options=[selectinload(Series.books)])
    if len(series.books) == 0:
        await session.delete(series)
    await session.commit()
    return {"blocked" if block else "deleted": book_id}

@router.delete("/book/{book_id}/files")
async def delete_book_files(book_id: str, session: AsyncSession = Depends(get_session)):
    await delete_audio_book(book_id, session)
    return {"deleted files": book_id}
