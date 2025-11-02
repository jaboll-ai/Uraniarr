
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
import asyncio
from backend.config import ConfigManager

from backend.dependencies import get_session, get_cfg_manager
from backend.services.downloader_service import download, get_config, remove_from_history, remove_from_queue, get_queue, get_history
from backend.services.indexer_service import grab_nzb, query_book, query_manual

from backend.datamodels import Book, Author, Reihe, Activity, ActivityStatus
from backend.payloads import ManualGUIDDownload
router = APIRouter(prefix="/dapi", tags=["NZB"])


@router.post("/book/{book_id}")
async def download_book(book_id: str, audio: bool = True, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = await session.get(Book, book_id, options=[selectinload(Book.reihe), selectinload(Book.autor)])
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    name, guid = await query_book(book, cfg=cfg, audio=audio)
    if not guid:
        raise HTTPException(status_code=404, detail=f"Book {book.name} not found")
    nzb = await grab_nzb(guid, cfg=cfg)
    await schedule_download(guid, name, nzb, book=book, cfg=cfg, session=session, audio=audio)
    return book_id

@router.post("/guid")
async def download_guid(data: ManualGUIDDownload, audio: bool = True, cfg: ConfigManager = Depends(get_cfg_manager), session: AsyncSession = Depends(get_session)):
    book = await session.get(Book, data.book_key)
    nzb = await grab_nzb(data.guid, cfg=cfg)
    await schedule_download(data.guid, data.name, nzb, book=book, cfg=cfg, session=session, audio=audio)
    return data.guid

@router.get("/manual/{book_id}")
async def search_manual(book_id: str, page:int = 0, audio: bool = True, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = await session.get(Book, book_id, options=[selectinload(Book.reihe), selectinload(Book.autor)])
    data = await query_manual(book, page, cfg=cfg, audio=audio)
    if not data:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return data

@router.post("/author/{author_id}")
async def download_author(author_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    author = await session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    not_found = []
    for book in author.books: #TODO Make use of parallelism TODO
        if book.a_dl_loc or book.blocked: continue
        name, guid = await query_book(book, session=session, cfg=cfg, audio=True)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = await grab_nzb(guid, cfg=cfg)
        await schedule_download(guid, name, nzb, book=book, cfg=cfg, session=session, audio=True)
    for book in author.books:
        if book.b_dl_loc or book.blocked: continue
        name, guid = await query_book(book, cfg=cfg, audio=False)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = await grab_nzb(guid, cfg=cfg)
        await schedule_download(guid, name, nzb, book=book, cfg=cfg, session=session, audio=False)
    if not_found:
        return {"partial_success": author_id, "not_found": not_found}
    return {"success": author_id}

@router.post("/series/{reihe_id}")
async def download_reihe(reihe_id: str, audio: bool = True, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    reihe = await session.get(Reihe, reihe_id)
    if not reihe:
        raise HTTPException(status_code=404, detail="Author not found")
    not_found = []
    for book in reihe.books:
        if (audio and book.a_dl_loc) or (not audio and book.b_dl_loc) or book.blocked: continue
        name, guid = await query_book(book, cfg=cfg, audio=audio)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = await grab_nzb(guid, cfg=cfg)
        await schedule_download(guid, name, nzb, book=book, cfg=cfg, session=session, audio=audio)
    if not_found:
        return {"partial_success": reihe_id, "not_found": not_found}
    return reihe_id

@router.get("/config")
async def get_sab_config(section: str, keyword: str = None, cfg = Depends(get_cfg_manager)):
    return await get_config(cfg, section, keyword)

@router.delete("/book/{book_id}")
async def delete_book_from_history(book_id: str, cfg: ConfigManager = Depends(get_cfg_manager)):
    return await remove_from_history(cfg, book_id)

@router.get("/activities")
async def get_activities(session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)): #TODO shift logic to downloader
    queue, history = await asyncio.gather(get_queue(cfg=cfg), get_history(cfg=cfg))
    result = queue | history
    result = await session.exec(select(Activity).where(Activity.nzo_id.in_(result.keys())).options(selectinload(Activity.book)))
    nzbs = result.scalars().all()
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
async def delete_activity(activity_id: str, session: AsyncSession = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    resp = await remove_from_queue(cfg, activity_id)
    if resp:
        activity = session.get(Activity, activity_id)
        if activity:
            activity.status = ActivityStatus.canceled
            session.commit()
    return activity_id

async def schedule_download(guid: str, release_title: str, nzb : bytes, cfg: ConfigManager, session: AsyncSession, book: Book, audio: bool):
    data = await download(nzb, nzbname=release_title, cfg=cfg)
    if not data: 
        raise HTTPException(status_code=500, detail="Download failed")
    try:
        activity = Activity(nzo_id=data[0], book=book, release_title=release_title, audio=audio, guid=guid)
    except:
        raise HTTPException(status_code=500, detail="Could not queue item for SABnzbd. Internal Error. SAB gave the following data back: " + str(data))
    session.add(activity)
    await session.commit()
