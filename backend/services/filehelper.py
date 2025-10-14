import asyncio
from pathlib import Path
import shutil
from sqlmodel import Session
from backend.db import engine
from backend.config import ConfigManager
from backend.services.downloader_service import get_config, remove_from_history
from backend.datamodels import Book, Reihe, Author
from backend.exceptions import FileError
import os

def move_file(src: Path):
    cfg = ConfigManager()
    # source is in the SAB “complete” directory for this category
    book_id = src.name
    try:
        with Session(engine) as session:
            book = session.get(Book, book_id)
            if not book:
                print(f"Book '{book_id}' not found. Cannot import.")
                return #TODO better logging

            dst_base = Path(cfg.data_path)
            dst_dir = dst_base / book.autor.name
            if not book.autor.a_dl_loc: book.autor.a_dl_loc = str(dst_dir)
            if book.reihe_key: #TODO custom patterns
                dst_dir = dst_dir / book.reihe.name
                if not book.reihe.a_dl_loc: book.reihe.a_dl_loc = str(dst_dir) # TODO revisit for book
                if book.reihe_position:
                    dst_dir = dst_dir / f"{book.reihe_position} - {book.name}" 
                else:
                    dst_dir = dst_dir / book.name
            else:
                dst_dir = dst_dir / book.name / book.name

            dst_dir.mkdir(parents=True, exist_ok=True)
            counts = {}
            for file in Path(src).iterdir():
                if file.is_file():
                    ext = file.suffix.lower()
                    if not ext: continue
                    counts[ext] = counts.get(ext, 0) + 1
            exts = sorted(counts, key=counts.get)
            
            for ext in exts[::-1]:
                if ext not in cfg.unwanted_extensions.split(","):
                    wanted_ext = ext
                    break
            else: wanted_ext = ""
            for file in Path(src).iterdir():
                if file.is_file():
                    if file.suffix.lower() == wanted_ext:
                        shutil.move(str(file), str(dst_dir)) #TODO pattern
            shutil.rmtree(src)
            remove_from_history(cfg, book_id)
            book.a_dl_loc = str(dst_dir) #TODO revisit for Books
    except Exception as e:
        print(e) #TODO LOGGGG and FIX


def scan_and_move_all_files():
    cfg = ConfigManager()
    complete_base = Path(get_config(cfg, "misc", "complete_dir"))
    cats = get_config(cfg, "categories")
    entry = next((c for c in cats if c["name"] == cfg.downloader_category), None) #TIL lol
    if not entry:
        return  # unknown category TODO LOGGG
    subdir = entry.get("dir", "")
    category_dir: Path = complete_base / subdir
    if os.getenv("DEV", "0") == "1":
        category_dir = Path(".local") / str(category_dir)[1:] # DEV
    if not category_dir.is_dir():
        return  # TODO LOGGG
    for book_entry in category_dir.iterdir():
        if not book_entry.is_dir():
            print(f"Skipping {book_entry}. Not a file.")
            continue  # TODO LOGGG
        move_file(book_entry)

def delete_audio_book(book_id: str, session: Session):
    book = session.get(Book, book_id)
    if not book or not book.a_dl_loc:
        raise FileError(status_code=404, detail=f"Book '{book_id}' not found or not downloaded")
    shutil.rmtree(book.a_dl_loc)
    book.a_dl_loc = None
    session.commit()

def delete_audio_reihe(reihe_id: str, session: Session):
    reihe = session.get(Reihe, reihe_id)
    if not reihe or not reihe.a_dl_loc:
        raise FileError(status_code=404, detail=f"Reihe '{reihe_id}' not found or not downloaded")
    shutil.rmtree(reihe.a_dl_loc)
    reihe.a_dl_loc = None
    session.commit()

def delete_audio_author(author_id: str, session: Session):
    author = session.get(Author, author_id)
    if not author or not author.a_dl_loc:
        raise FileError(status_code=404, detail=f"Author '{author_id}' not found or not downloaded")
    shutil.rmtree(author.a_dl_loc)
    author.a_dl_loc = None
    session.commit()

async def poll_folder(interval: int = 60):
    """
    Every `interval` seconds, offload scan_and_move_all_files() to a thread,
    log errors, and repeat indefinitely.
    """
    while True:
        try:
            await asyncio.to_thread(scan_and_move_all_files)
        except Exception:
            pass #TODO LOGGG
        await asyncio.sleep(interval)
