
from contextlib import suppress
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
import asyncio
from backend.config import ConfigManager

from backend.dependencies import get_session
from backend.services.indexer import BaseIndexer
from backend.services.downloader import BaseDownloader
from backend.datamodels import Book, Author, Series, Activity, ActivityStatus
from backend.payloads import ManualGUIDDownload
router = APIRouter(prefix="/dapi", tags=["NZB"])


@router.post("/book/{book_id}")
async def download_book(request: Request, book_id: str,  audio: bool = True, session: AsyncSession = Depends(get_session)):
    cfg = request.app.state.cfg_manager
    indexers: list[BaseIndexer] = request.app.state.indexers[audio]
    downloaders: list[BaseDownloader] = request.app.state.downloaders[audio]
    book = await session.get(Book, book_id, options=[selectinload(Book.series), selectinload(Book.author)])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    for indexer in indexers:
        name, guid, download = await indexer.query_book(book, cfg=cfg, audio=audio)
        if not download:
            continue
        nzb = await indexer.grab(download, cfg=cfg)
        break
    else:
        raise HTTPException(status_code=404, detail=f"Book {book.name} not found")
    activity = await schedule_download(guid, name, nzb, book=book, downloaders=downloaders, cfg=cfg, audio=audio)
    if isinstance(activity, Activity):
        session.add(activity)
        await session.commit()
    else:
        raise HTTPException(status_code=activity["code"], detail=activity["error"])
    return book_id

@router.post("/guid")
async def download_guid(request: Request, data: ManualGUIDDownload, audio: bool = True, session: AsyncSession = Depends(get_session)):
    cfg = request.app.state.cfg_manager
    indexers: list[BaseIndexer] = request.app.state.indexers[audio]
    downloaders: list[BaseDownloader] = request.app.state.downloaders[audio]
    book = await session.get(Book, data.book_key)
    nzb = await indexers[data.i_idx].grab(data.download, cfg=cfg)
    activity=await schedule_download(data.guid, data.name, nzb, book=book, downloaders=downloaders, cfg=cfg, audio=audio)
    if isinstance(activity, Activity):
        session.add(activity)
        await session.commit()
    else:
        raise HTTPException(status_code=activity["code"], detail=activity["error"])
    return data.guid

@router.get("/manual/{book_id}")
async def search_manual(request: Request, book_id: str, page:int = 0, audio: bool = True, session: AsyncSession = Depends(get_session)):
    cfg = request.app.state.cfg_manager
    indexers: list[BaseIndexer] = request.app.state.indexers[audio]
    book = await session.get(Book, book_id, options=[selectinload(Book.series), selectinload(Book.author)])
    data = None
    nzbs = []
    for indexer in indexers:
        data = await indexer.query_manual(book, page, cfg=cfg, audio=audio)
        if not data:
            continue
        nzbs.extend(data["nzbs"])
    return { **data, "nzbs": nzbs }

@router.post("/author/{author_id}")
async def download_author(request: Request, author_id: str, audio: bool = True, session: AsyncSession = Depends(get_session)):
    cfg = request.app.state.cfg_manager
    indexers: list[BaseIndexer] = request.app.state.indexers[audio]
    downloaders: list[BaseDownloader] = request.app.state.downloaders[audio]
    author = await session.get(Author, author_id, options=[selectinload(Author.books).selectinload(Book.series), selectinload(Author.books).selectinload(Book.author)])
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    not_found = []
    errors = []
    coros = []
    for book in author.books:
        if (audio and book.a_dl_loc) or (not audio and book.b_dl_loc) or book.blocked: continue
        for indexer in indexers:
            with suppress(Exception):
                name, guid, download = await indexer.query_book(book, cfg=cfg, audio=audio)
                if not guid:
                    continue
                nzb = await indexer.grab(download, cfg=cfg)
                break
        else:
            not_found.append(book.key)
            continue
        coros.append(schedule_download(guid, name, nzb, book=book, downloaders=downloaders, cfg=cfg, audio=audio))
    activities = await asyncio.gather(*coros)
    for activity in activities:
        if isinstance(activity, Activity):
            session.add(activity)
        else:
            errors.append(activity)
    await session.commit()
    if not_found or errors:
        return {"partial_success": author_id, "not_found": not_found, "errors": errors}
    return {"success": author_id}

@router.post("/series/{series_id}")
async def download_series(request: Request, series_id: str, audio: bool = True, session: AsyncSession = Depends(get_session)):
    cfg = request.app.state.cfg_manager
    indexers: list[BaseIndexer] = request.app.state.indexers[audio]
    downloaders: list[BaseDownloader] = request.app.state.downloaders[audio]
    series = await session.get(Series, series_id, options=[selectinload(Series.books).selectinload(Book.series), selectinload(Series.books).selectinload(Book.author)])
    if not series:
        raise HTTPException(status_code=404, detail="Author not found")
    not_found = []
    errors = []
    coros = []
    for book in series.books:
        if (audio and book.a_dl_loc) or (not audio and book.b_dl_loc) or book.blocked: continue
        for indexer in indexers:
            with suppress(Exception):
                name, guid, download = await indexer.query_book(book, cfg=cfg, audio=audio)
                if not guid:
                    continue
                nzb = await indexer.grab(download, cfg=cfg)
                break
        else:
            not_found.append(book.key)
            continue
        coros.append(schedule_download(guid, name, nzb, book=book, downloaders=downloaders, cfg=cfg, audio=audio))
    activities = await asyncio.gather(*coros)
    for activity in activities:
        if isinstance(activity, Activity):
            session.add(activity)
        else:
            errors.append(activity)
    await session.commit()
    if not_found or errors:
        return {"partial_success": series_id, "not_found": not_found, "errors": errors}
    return series_id

@router.delete("/book/{book_id}")
async def delete_book_from_history(request: Request, book_id: str, audio: bool = True):
    downloaders: list[BaseDownloader] = request.app.state.downloaders[audio]
    cfg = request.app.state.cfg_manager
    coros = [downloader.remove_from_queue(cfg, book_id) for downloader in downloaders]
    r = await asyncio.gather(*coros, return_exceptions=True)
    return any([not isinstance(x, Exception) for x in r])

@router.get("/activities")
async def get_activities(request: Request, session: AsyncSession = Depends(get_session)): #TODO shift logic to downloader
    downloaders: list[BaseDownloader] = request.app.state.downloaders[True] + request.app.state.downloaders[False]
    cfg = request.app.state.cfg_manager
    result = {}
    for downloader in downloaders:
        queue, history = await asyncio.gather(downloader.get_queue(cfg=cfg), downloader.get_history(cfg=cfg))
        combine = queue | history
        result = result | combine
    query = await session.exec(select(Activity).where(Activity.nzo_id.in_(result.keys())).options(selectinload(Activity.book)))
    nzbs = query.all()
    resp =  [{
        "id": activity.nzo_id,
        "percentage": result[activity.nzo_id]["percentage"],
        "filename": result[activity.nzo_id]["name"],
        "book_key": activity.book_key,
        "book_name": activity.book.name,
        "status": "Failed to import" if activity.status == ActivityStatus.failed else result[activity.nzo_id]["status"]
    } for activity in nzbs]
    return sorted(resp, key=lambda x: int(x["percentage"]), reverse=True)

@router.delete("/activity/{activity_id}")
async def delete_activity(request: Request, activity_id: str, session: AsyncSession = Depends(get_session)):
    downloaders: list[BaseDownloader] = request.app.state.downloaders[True] + request.app.state.downloaders[False]
    cfg = request.app.state.cfg_manager
    coros = [downloader.remove_from_queue(cfg, activity_id) for downloader in downloaders]
    r = await asyncio.gather(*coros, return_exceptions=True)
    for resp in r:
        if isinstance(resp, Exception): continue
        activity = await session.get(Activity, activity_id)
        if activity:
            activity.status = ActivityStatus.canceled
            await session.commit()
            break
    return activity_id

async def schedule_download(guid: str, release_title: str, nzb : bytes, downloaders: list[BaseDownloader], cfg: ConfigManager, book: Book, audio: bool):
    for downloader in downloaders:
        data = await downloader.download(nzb, nzbname=release_title, cfg=cfg)
    if not data:

        return {"book": book, "error": "Download failed", "code": 500}
    try:
        activity = Activity(nzo_id=data[0], book=book, release_title=release_title, audio=audio, guid=guid)
    except:
        return {"book": book, "error": "Could not queue item for SABnzbd. Internal Error. SAB gave the following data back: " + str(data), "code": 500}
    return activity
