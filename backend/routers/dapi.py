
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from backend.config import ConfigManager

from backend.dependencies import get_session, get_cfg_manager
from backend.services.downloader_service import download, get_config, remove_from_history
from backend.services.indexer_service import grab_nzb, query_book, query_manual

from backend.datamodels import Book, Author, Reihe
from backend.payloads import ManualGUIDDownload

router = APIRouter(prefix="/dapi", tags=["NZB"])


@router.post("/book/{book_id}")
def download_book(book_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    guid = query_book(book, cfg=cfg)
    if not guid:
        raise HTTPException(status_code=404, detail=f"Book {book.name} not found")
    nzb = grab_nzb(guid, cfg=cfg)
    download(nzb, nzbname=book.key, cfg=cfg)
    return book_id

@router.post("/guid")
def download_guid(data: ManualGUIDDownload, cfg: ConfigManager = Depends(get_cfg_manager)):
    nzb = grab_nzb(data.guid, cfg=cfg)
    download(nzb, nzbname=data.guid, cfg=cfg)
    return data.guid

@router.get("/manual/{book_id}")
def search_manual(book_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    data = query_manual(book, cfg=cfg)
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
        if book.a_dl_loc: continue #TODO revisit for Books
        guid = query_book(book, cfg=cfg)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = grab_nzb(guid, cfg=cfg)
        download(nzb, nzbname=book.key, cfg=cfg)
    if not_found:
        return {"partial_success": author_id, "not_found": not_found}
    return {"success": author_id}

@router.post("/series/{reihe_id}")
def download_reihe(reihe_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    reihe = session.get(Reihe, reihe_id)
    if not reihe:
        raise HTTPException(status_code=404, detail="Author not found")
    not_found = []
    for book in reihe.books:
        if book.a_dl_loc: continue #TODO revisit for Books
        guid = query_book(book, cfg=cfg)
        if not guid:
            not_found.append(book.key)
            continue
        nzb = grab_nzb(guid, cfg=cfg)
        download(nzb, nzbname=book.key, cfg=cfg)
    if not_found:
        return {"partial_success": reihe_id, "not_found": not_found}
    return reihe_id

@router.get("/config")
def get_sab_config(section: str, keyword: str = None, cfg = Depends(get_cfg_manager)):
    return get_config(cfg, section, keyword)

@router.delete("/book/{book_id}")
def delete_book_from_history(book_id: str, cfg: ConfigManager = Depends(get_cfg_manager)):
    return remove_from_history(cfg, book_id)

