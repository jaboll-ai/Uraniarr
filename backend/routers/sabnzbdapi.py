
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from backend.config import ConfigManager

from backend.dependencies import get_session, get_cfg_manager
from backend.services.nzb_service import indexer_search, indexer_nzb, download

from backend.datamodels import Book

router = APIRouter(prefix="/nzbapi", tags=["NZB"])

@router.post("/book/{book_id}")
def download_book(book_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    data = indexer_search(f"{book.autor.name} {book.name}", cfg=cfg)
    query = data["channel"]
    if (total:=query["response"]["@attributes"]["total"]) == "0": raise HTTPException(status_code=404, detail="No books for query found")
    else: #maybe do fuzzy ratio?
        item = query["item"] if total == "1" else query["item"][0] 
        guid=item["attr"][2]["@attributes"]["value"]
        nzb = indexer_nzb(guid, cfg=cfg)
        download(nzb, nzbname=book.key, cfg=cfg)
    return