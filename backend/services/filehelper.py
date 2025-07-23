import asyncio
from pathlib import Path
import shutil
from sqlmodel import Session
from backend.db import engine
from backend.config import ConfigManager
from backend.services.sabnzbd_service import get_config
from backend.datamodels import Book
from backend.exceptions import FileError

def move_file(src: Path):
    cfg = ConfigManager()
    # source is in the SAB “complete” directory for this category
    book_id = src.name
    try:
        with Session(engine) as session:
            book = session.get(Book, book_id)
            if not book:
                raise FileError(status_code=404, detail=f"Book '{book_id}' not found")

            dst_base = Path(cfg.data_path)
            dst_dir = dst_base / book.autor.name
            if book.reihe_key: #TODO custom patterns
                dst_dir = dst_dir / book.reihe.name
                if book.reihe_position:
                    dst_dir = dst_dir / f"{book.reihe_position} - {book.name}" 
            else:
                dst_dir = dst_dir / book.name / book.name

        dst_dir.mkdir(parents=True, exist_ok=True)
        counts = {}
        for file in Path(src).iterdir():
            if file.is_file():
                ext = file.suffix.lower()
                if not ext: continue
                counts[ext] = counts.get(ext, 0) + 1
        wanted_ext = max(counts, key=counts.get)
        for file in Path(src).iterdir():
            if file.is_file():
                if file.suffix.lower() == wanted_ext:
                    shutil.move(str(file), str(dst_dir)) #TODO pattern
        shutil.rmtree(src)
    except Exception as e:
        print(e) #TODO LOGGGG


def scan_and_move_all_files():
    cfg = ConfigManager()
    complete_base = Path(get_config(cfg, "misc", "complete_dir"))
    cats = get_config(cfg, "categories")  # this returns your list of dicts
    entry = next((c for c in cats if c["name"] == cfg.downloader_category), None) #TIL lol
    if not entry:
        return  # unknown category TODO LOGGG
    subdir = entry.get("dir") or ""
    category_dir = complete_base / subdir

    if not category_dir.is_dir():
        return  # TODO LOGGG
    for book_entry in category_dir.iterdir():
        if not book_entry.is_dir():
            continue  # TODO LOGGG
        move_file(book_entry)

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
