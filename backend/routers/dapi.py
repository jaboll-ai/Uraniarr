
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from backend.config import ConfigManager

from backend.dependencies import get_session, get_cfg_manager
from backend.services.downloader_service import download, get_config, remove_from_history
from backend.services.indexer_service import grab_nzb, query_book

from backend.datamodels import Book, Author, Reihe

router = APIRouter(prefix="/dapi", tags=["NZB"])


@router.post("/book/{book_id}")
def download_book(book_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    guid = query_book(book, cfg=cfg)
    nzb = grab_nzb(guid, cfg=cfg)
    download(nzb, nzbname=book.key, cfg=cfg)
    return book_id

@router.post("/author/{author_id}")
def download_author(author_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    author = session.get(Author, author_id)
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    for book in author.books:
        if book.a_dl_loc: continue #TODO revisit for Books
        guid = query_book(book, cfg=cfg)
        nzb = grab_nzb(guid, cfg=cfg)
        download(nzb, nzbname=book.key, cfg=cfg)
    return author_id

@router.post("/reihe/{reihe_id}")
def download_reihe(reihe_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    reihe = session.get(Reihe, reihe_id)
    if not reihe:
        raise HTTPException(status_code=404, detail="Author not found")
    for book in reihe.books:
        if book.a_dl_loc: continue #TODO revisit for Books
        guid = query_book(book, cfg=cfg)
        nzb = grab_nzb(guid, cfg=cfg)
        download(nzb, nzbname=book.key, cfg=cfg)
    return reihe_id

@router.get("/config")
def get_sab_config(section: str, keyword: str = None, cfg = Depends(get_cfg_manager)):
    return get_config(cfg, section, keyword)

@router.delete("/book/{book_id}")
def delete_book_from_history(book_id: str, cfg: ConfigManager = Depends(get_cfg_manager)):
    return remove_from_history(cfg, book_id)

