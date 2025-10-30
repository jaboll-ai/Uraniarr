
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from uuid import uuid4
from backend.config import ConfigManager

from backend.dependencies import get_session, get_cfg_manager
from backend.services.downloader_service import download, get_config, remove_from_history, remove_from_queue, get_queue, get_history
from backend.services.indexer_service import grab_nzb, query_book, query_manual

from backend.datamodels import Book, Author, Reihe, Activity, ActivityStatus
from backend.payloads import ManualGUIDDownload
router = APIRouter(prefix="/dapi", tags=["NZB"])


@router.post("/book/{book_id}")
def download_book(book_id: str, audio: bool = True, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    name, guid = query_book(book, cfg=cfg, audio=audio)
    if not guid:
        raise HTTPException(status_code=404, detail=f"Book {book.name} not found")
    nzb = grab_nzb(guid, cfg=cfg)
    schedule_download(name, nzb, book=book, cfg=cfg, session=session, audio=audio)
    return book_id

@router.post("/guid")
def download_guid(data: ManualGUIDDownload, audio: bool = True, cfg: ConfigManager = Depends(get_cfg_manager), session: Session = Depends(get_session)):
    book=session.get(Book, data.book_key)
    nzb = grab_nzb(data.guid, cfg=cfg)
    schedule_download(data.name, nzb, book=book, cfg=cfg, session=session, audio=audio)
    return data.guid

@router.get("/manual/{book_id}")
def search_manual(book_id: str, page:int = 0, audio: bool = True, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    data = query_manual(book, page, cfg=cfg, audio=audio)
    if not data:
        raise HTTPException(status_code=404, detail=f"Book {book.name} not found")
    return data

@router.post("/author/{author_id}")
def download_author(author_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    author = session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    not_found = []
    for book in author.books:
        if book.a_dl_loc or book.blocked: continue
        name, guid = query_book(book, cfg=cfg, audio=True)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = grab_nzb(guid, cfg=cfg)
        schedule_download(name, nzb, book=book, cfg=cfg, session=session, audio=True)
    for book in author.books:
        if book.b_dl_loc or book.blocked: continue
        name, guid = query_book(book, cfg=cfg, audio=False)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = grab_nzb(guid, cfg=cfg)
        schedule_download(name, nzb, book=book, cfg=cfg, session=session, audio=False)
    if not_found:
        return {"partial_success": author_id, "not_found": not_found}
    return {"success": author_id}

@router.post("/series/{reihe_id}")
def download_reihe(reihe_id: str, audio: bool = True, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    reihe = session.get(Reihe, reihe_id)
    if not reihe:
        raise HTTPException(status_code=404, detail="Author not found")
    not_found = []
    for book in reihe.books:
        if (audio and book.a_dl_loc) or (not audio and book.b_dl_loc) or book.blocked: continue
        name, guid = query_book(book, cfg=cfg, audio=audio)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = grab_nzb(guid, cfg=cfg)
        schedule_download(name, nzb, book=book, cfg=cfg, session=session, audio=audio)
    if not_found:
        return {"partial_success": reihe_id, "not_found": not_found}
    return reihe_id

@router.get("/config")
def get_sab_config(section: str, keyword: str = None, cfg = Depends(get_cfg_manager)):
    return get_config(cfg, section, keyword)

@router.delete("/book/{book_id}")
def delete_book_from_history(book_id: str, cfg: ConfigManager = Depends(get_cfg_manager)):
    return remove_from_history(cfg, book_id)

@router.get("/activities")
def get_activities(session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    queue = get_queue(cfg=cfg)
    history = get_history(cfg=cfg)
    resp = []
    for item in queue:
        activity = session.get(Activity, item["nzo_id"])
        if not activity: continue
        resp.append({
            "id": item["nzo_id"],
            "percentage": item["percentage"],
            "filename": item["filename"],
            "book_key": activity.book_key,
            "book_name": activity.book.name,
            "status": item["status"]
        })
    for item in history:
        activity = session.get(Activity, item["nzo_id"])
        if not activity: continue
        resp.append({
            "id": item["nzo_id"],
            "percentage": 100,
            "filename": item["name"],
            "book_key": activity.book_key,
            "book_name": activity.book.name,
            "status": "Failed to import" if activity.status == ActivityStatus.failed else item["status"]
        })
    return resp
    
@router.delete("/activity/{activity_id}")
def delete_activity(activity_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    resp = remove_from_queue(cfg, activity_id)
    if resp:
        activity = session.get(Activity, activity_id)
        if activity:
            activity.status = ActivityStatus.canceled
            session.commit()
    return activity_id

def schedule_download(release_title: str, nzb : bytes, cfg: ConfigManager, session: Session, book: Book, audio: bool):
    data = download(nzb, nzbname=release_title, cfg=cfg)
    if not data: 
        raise HTTPException(status_code=500, detail="Download failed")
    try:
        activity = Activity(nzo_id=data["nzo_ids"][0], book=book, release_title=release_title, audio=audio)
    except:
        raise HTTPException(status_code=500, detail="Could not queue item for SABnzbd. Internal Error. SAB gave the following data back: " + str(data))
    session.add(activity)
    session.commit()
