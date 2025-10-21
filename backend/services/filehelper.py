import asyncio
from pathlib import Path
import shutil
from sqlmodel import Session
from backend.db import engine
from backend.config import ConfigManager
from backend.services.downloader_service import get_config, remove_from_history, get_history
from backend.datamodels import Book, Reihe, Author, Activity, ActivityStatus
from backend.exceptions import FileError
import os

def move_file(activity: Activity, src: Path, cfg: ConfigManager):
    with open("/config/debug.log", "a") as f:
        f.write(f"Moving {src}\n")
        f.write(f"Audio: {activity.audio}\n")
        f.write(src.is_file(),"\n")
        f.write("TEstttt","\n")
        
    src = src.parent if src.is_file() else src
    cfg = ConfigManager()
    book = activity.book
    # source is in the SAB “complete” directory for this category
    try:
        if not book:
            print(f"No book for {src.name} found")
            return #TODO better logging
        dst_base = Path(cfg.audio_path if activity.audio else cfg.book_path)
        dst_dir = dst_base / book.autor.name
        var_name = "a_dl_loc" if activity.audio else "b_dl_loc"
        if not getattr(book.autor, var_name): setattr(book.autor, var_name, str(dst_dir))
        if book.reihe_key: #TODO custom patterns
            dst_dir = dst_dir / book.reihe.name
            if not getattr(book.reihe, var_name): setattr(book.reihe, var_name, str(dst_dir))
            if book.reihe_position is not None:
                dst_dir = dst_dir / f"{book.reihe_position} - {book.name}" 
            else:
                dst_dir = dst_dir / book.name
        else:
            dst_dir = dst_dir / book.name #TODO revisit? same depth vs clearer structure
        if dst_dir.exists():
            print(f"Directory {dst_dir} already exists. Will replace.")
            shutil.rmtree(dst_dir)
        dst_dir.mkdir(parents=True)
        counts = {}
        if activity.audio:
            for file in Path(src).iterdir():
                if file.is_file():
                    ext = file.suffix.lower()
                    if not ext: continue
                    counts[ext] = counts.get(ext, 0) + 1
            exts = sorted(counts, key=counts.get, reverse=True)
            
            for ext in cfg.audio_extensions_rating.split(","):
                if ext in exts:
                    wanted_ext = ext
                    break
            else: wanted_ext = exts[0]
            for file in Path(src).iterdir():
                if file.is_file():
                    if file.suffix.lower() == wanted_ext:
                        shutil.move(str(file), str(dst_dir)) #TODO pattern
        else:
            for file in Path(src).iterdir():
                if file.is_file():
                    if file.suffix.lower() in cfg.book_extensions.split(","):
                        shutil.move(str(file), str(dst_dir))
        for act in book.activities:
            if act.audio != activity.audio: continue
            match act.status:
                case ActivityStatus.imported:
                    act.status = ActivityStatus.overwritten
                case _:
                    continue
        activity.status = ActivityStatus.imported
        shutil.rmtree(src)
        setattr(book, var_name, str(dst_dir)) #TODO revisit for Books
        remove_from_history(cfg, activity.nzo_id)
    except Exception as e:
        activity.status = ActivityStatus.failed
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
    if os.getenv("DEV") == "1":
        category_dir = Path(".local") / str(category_dir)[1:] # DEV
    if not category_dir.is_dir():
        return  # TODO LOGGG
    slots = get_history(cfg)
    with Session(engine) as session:
        for slot in slots:
            activity = session.get(Activity, slot["nzo_id"])
            if not activity: continue
            if not slot["status"] == "Completed": continue
            if os.getenv("DEV") == "1":
                slot["storage"] = Path(".local") / str(slot["storage"])[1:] # DEV
            move_file(activity, slot["storage"], cfg)
            session.commit()

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
