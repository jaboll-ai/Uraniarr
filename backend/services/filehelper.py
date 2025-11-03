import asyncio
from pathlib import Path
import shutil
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.db import engine
from backend.config import ConfigManager
from backend.datamodels import Book, Reihe, Author, Activity, ActivityStatus
from backend.exceptions import FileError
from backend.services.downloader import BaseDownloader
import os

def move_file(activity: Activity, src: Path, cfg: ConfigManager):
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
                if book.reihe_position % 1 != 0:
                    dst_dir = dst_dir / f"{str(int(book.reihe_position)).zfill(3)}{str(book.reihe_position%1)[1:]} - {book.name}" 
                else:
                    dst_dir = dst_dir / f"{str(int(book.reihe_position)).zfill(3)} - {book.name}"
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
            for file in src.iterdir():
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
            for file in src.iterdir():
                if file.is_file():
                    if file.suffix.lower() == wanted_ext:
                        shutil.move(str(file), str(dst_dir)) #TODO pattern
        else:
            for file in src.iterdir():
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
        # remove_from_history(cfg, activity.nzo_id)
        return activity.nzo_id
    except Exception as e:
        activity.status = ActivityStatus.failed
        print(e) #TODO LOGGGG and FIX
        return None


async def scan_and_move_all_files(state):
    cfg = state.cfg_manager
    downloader: BaseDownloader = state.downloader
    hist = await downloader.get_history(cfg)
    async with AsyncSession(engine) as session:
        moved = []
        for key, slot in hist.items():
            activity = await session.get(Activity, key, options=[
                selectinload(Activity.book).selectinload(Book.autor), 
                selectinload(Activity.book).selectinload(Book.reihe),
                selectinload(Activity.book).selectinload(Book.activities)
            ])
            if not activity: continue
            if not slot["status"] == "Completed": continue
            src = Path(slot["storage"])
            if os.getenv("DEV") == "1":
                src = Path(".local") / str(slot["storage"])[1:] # DEV
            moved.append(asyncio.to_thread(move_file, activity, src, cfg))
        coros = [downloader.remove_from_history(cfg, nzo_id) for nzo_id in await asyncio.gather(*moved) if nzo_id is not None]
        await asyncio.gather(*coros)
        await session.commit()

async def delete_audio_book(book_id: str, session: AsyncSession):
    book = await session.get(Book, book_id)
    if not book or not book.a_dl_loc:
        raise FileError(status_code=404, detail=f"Book '{book_id}' not found or not downloaded")
    await asyncio.to_thread(shutil.rmtree, book.a_dl_loc)
    book.a_dl_loc = None
    session.commit()

async def delete_audio_reihe(reihe_id: str, session: AsyncSession):
    reihe = await session.get(Reihe, reihe_id)
    if not reihe or not reihe.a_dl_loc:
        raise FileError(status_code=404, detail=f"Reihe '{reihe_id}' not found or not downloaded")
    await asyncio.to_thread(shutil.rmtree, reihe.a_dl_loc)
    reihe.a_dl_loc = None
    session.commit()

async def delete_audio_author(author_id: str, session: AsyncSession):
    author = await session.get(Author, author_id)
    if not author or not author.a_dl_loc:
        raise FileError(status_code=404, detail=f"Author '{author_id}' not found or not downloaded")
    await asyncio.to_thread(shutil.rmtree, author.a_dl_loc)
    author.a_dl_loc = None
    await session.commit()

async def get_files_of_book(book: Book):
    p_a = await asyncio.to_thread(get_files_from_disk, book.a_dl_loc)
    p_b = await asyncio.to_thread(get_files_from_disk, book.b_dl_loc)
    try:
        a, b = await asyncio.gather(get_file_stats(p_a), get_file_stats(p_b))
    except Exception as e:
        raise FileError(status_code=404, detail=f"{e}: Error while getting files of book '{book.name}'")
    return {
        "audio": a,
        "book": b
    }

def get_files_from_disk(path: str | None):
    if path is None: return []
    path = Path(path)
    try: 
        return sorted([p for p in path.iterdir() if p.is_file()], key=lambda x: str(x))
    except Exception as e:
        return None

async def get_file_stats(paths: list[Path] | None):
    if paths is None: return
    coros = [asyncio.to_thread(lambda p: {"path": str(p), "size": p.stat().st_size}, p) for p in paths]
    return await asyncio.gather(*coros)

def check_missing_paths(model_instance, fields: list[str]):
    missing = []
    for field in fields:
        path_str = getattr(model_instance, field, None)
        if not path_str:
            continue
        try:
            if not Path(path_str).exists():
                missing.append(field)
        except Exception:
            missing.append(field)
    return missing

async def poll_folder(state):
    """
    Every `interval` seconds, offload scan_and_move_all_files() to a thread,
    log errors, and repeat indefinitely.
    """
    while True:
        try:
            await scan_and_move_all_files(state)
        except Exception as e:
            print("Polling Error", e) #TODO LOGGG
            await asyncio.sleep(state.cfg_manager.import_poll_interval)

async def rescan_files(state):
    """Background task to clear missing file paths in Book entries."""
    while True:
        async with AsyncSession(engine) as session:
            targets = [
                (Book, ["a_dl_loc", "b_dl_loc"]),
                (Author, ["a_dl_loc", "b_dl_loc"]),
                (Reihe, ["a_dl_loc", "b_dl_loc"]),
            ]
            for model, fields in targets:
                result = await session.exec(select(model))
                instances = result.scalars().all()
                coros = [asyncio.to_thread(check_missing_paths, instance, fields) for instance in instances]
                missing_results = await asyncio.gather(*coros)

                for instance, missing_fields in zip(instances, missing_results):
                    if missing_fields:
                        for f in missing_fields:
                            setattr(instance, f, None)
                        if type(instance) == Book:
                            query = await session.exec(select(Activity).where(Activity.book_key == instance.key))
                            for a in query.scalars().all():
                                if a.status == ActivityStatus.imported:
                                    a.status = ActivityStatus.deleted
                                    break
                        # session.add(instance)
            await session.commit()
        await asyncio.sleep(state.cfg_manager.rescan_interval)
            

