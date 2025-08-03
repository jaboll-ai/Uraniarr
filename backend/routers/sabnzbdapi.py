
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from backend.config import ConfigManager
from backend.services.scrape_service import fix_umlaut

from backend.dependencies import get_session, get_cfg_manager
from backend.services.sabnzbd_service import download, get_config
from backend.services.indexer_service import grab_nzb, indexer_search

from backend.datamodels import Book

router = APIRouter(prefix="/sabnzbdapi", tags=["NZB"])

@router.post("/book/{book_id}")
def download_book(book_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    base_queries = [
        (book.autor.name, book.name),
        (fix_umlaut(book.autor.name), fix_umlaut(book.name)),
        (fix_umlaut(book.autor.name), book.name),
        (book.autor.name, fix_umlaut(book.name)),
    ]
    if book.reihe_key:
        base_queries.extend([(fix_umlaut(book.autor.name), f"{book.reihe.name} {book.reihe_position}"),
            (book.autor.name, f"{book.reihe.name} {book.reihe_position}"),
            (fix_umlaut(book.autor.name), f"{book.reihe.name} {round(book.reihe_position or 0)}"),
            (book.autor.name, f"{book.reihe.name} {round(book.reihe_position or 0)}")])
    for autor, name in base_queries:
        data = indexer_search(f"{autor} {name}", cfg=cfg)
        query = data["channel"]
        if (total:=query["response"]["@attributes"]["total"]) != "0":
            break
    else: raise HTTPException(status_code=404, detail="No books for query found")
    item = query["item"] if total == "1" else query["item"][0] 
    guid=item["attr"][2]["@attributes"]["value"]
    nzb = grab_nzb(guid, cfg=cfg)
    download(nzb, nzbname=book.key, cfg=cfg)
    return

@router.get("/config")
def get_sab_config(section: str, keyword: str = None, cfg = Depends(get_cfg_manager)):
    return get_config(cfg, section, keyword)