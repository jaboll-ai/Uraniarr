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
from backend.services.scrape_service import strip_pos
from backend.dependencies import get_logger
import os
from rapidfuzz import process

import shutil
from pathlib import Path
from typing import Optional
import asyncio

def ensure_backup(dst_dir: Path) -> Optional[Path]:
    bak_dir = dst_dir.with_name(f".{dst_dir.name}.bak")
    if bak_dir.exists():
        shutil.rmtree(bak_dir)
    shutil.move(dst_dir, bak_dir)
    get_logger().info(f"Directory {dst_dir} already exists. Will replace.")
    return bak_dir


def get_destination_dir(book: Book, audio: bool, cfg) -> Path:
    dst_base = Path(cfg.audio_path if audio else cfg.book_path)
    dst_dir = dst_base / book.autor.name

    author_dir = str(dst_dir)

    if book.reihe_key:
        dst_dir = dst_dir / book.reihe.name
        series_dir = str(dst_dir)
        if book.reihe_position is not None:
            max_pos = max(b.reihe_position or 0 for b in book.reihe.books)
            padding = len(str(int(max_pos)))
            if book.reihe_position % 1 != 0:
                dst_dir = dst_dir / f"{str(int(book.reihe_position)).zfill(padding)}{str(book.reihe_position%1)[1:]} - {book.name}"
            else:
                dst_dir = dst_dir / f"{str(int(book.reihe_position)).zfill(padding)} - {book.name}"
        else:
            dst_dir = dst_dir / book.name
    else:
        dst_dir = dst_dir / book.name

    return author_dir, series_dir, dst_dir


def mark_overwritten_activity(book, audio: bool):
    for act in book.activities:
        if act.audio != audio:
            continue
        if act.status == ActivityStatus.imported:
            act.status = ActivityStatus.overwritten
            return act
    return None


def select_wanted_ext(src: Path, cfg) -> str:
    counts = {}
    for file in src.rglob("*"):
        if file.is_file():
            ext = file.suffix.lower()
            if ext:
                counts[ext] = counts.get(ext, 0) + 1
    exts = sorted(counts, key=counts.get, reverse=True)
    for ext in cfg.audio_extensions_rating.split(","):
        if ext in exts:
            return ext
    return exts[0] if exts else ""


def move_files(src: Path, dst_dir: Path, audio: bool, cfg):
    dst_dir.mkdir(parents=True)
    if audio:
        wanted_ext = select_wanted_ext(src, cfg)
        for file in src.rglob("*"):
            if file.is_file() and file.suffix.lower() == wanted_ext:
                shutil.move(str(file), str(dst_dir))
    else:
        for file in src.rglob("*"):
            if file.is_file() and file.suffix.lower() in cfg.book_extensions.split(","):
                shutil.move(str(file), str(dst_dir))


def cleanup_source(src: Path, cat_dir: Path, safe_delete: bool, cfg):
    if src.resolve() == cat_dir.resolve():
        get_logger().info(f"The source directory is the same as the category directory. Will not delete. This cannot be overwritten by ignore_safe_delete. {src}")
        return

    if safe_delete or cfg.ignore_safe_delete:
        if not safe_delete:
            get_logger().info(f"Cannot safely delete source directory, but ignore_safe_delete is set by user. Deleting {src} ...")
        shutil.rmtree(src)


def restore_backup(bak_dir: Optional[Path], dst_dir: Optional[Path], overwritten_act):
    try:
        if bak_dir and dst_dir:
            if dst_dir.exists():
                shutil.rmtree(dst_dir)
            shutil.move(bak_dir, dst_dir)
        if overwritten_act:
            overwritten_act.status = ActivityStatus.imported
    except Exception as e:
        get_logger().error(f"Tried restoring {dst_dir} but failed with: {e}")


def cleanup_backup(bak_dir: Optional[Path], dst_dir: Optional[Path]):
    try:
        if bak_dir and dst_dir:
            if dst_dir.exists() and bak_dir.exists():
                shutil.rmtree(bak_dir)
    except Exception as e:
        get_logger().error(f"Final cleanup of {bak_dir} failed with: {e}")


def import_book_from_acitivity(activity: Optional[Activity], book: Book, audio: bool, src: Path, cat_dir: Path, cfg: ConfigManager):
    safe_delete = True
    if src.is_file():
        src = src.parent
        safe_delete = False

    bak_dir = None
    overwritten_act = None
    try:
        if not book:
            get_logger().info(f"No book for {src.name} found")
            return
        autor_dir, series_dir, dst_dir = get_destination_dir(book, audio, cfg)
        if src.resolve() == dst_dir.resolve():
            raise Exception(f"Source and destination are the same: {src}")
        if dst_dir.exists():
            bak_dir = ensure_backup(dst_dir)
        if activity is not None:
            overwritten_act = mark_overwritten_activity(book, audio)
        move_files(src, dst_dir, audio, cfg)
        cleanup_source(src, cat_dir, safe_delete, cfg)
        if activity is not None:
            activity.status = ActivityStatus.imported
        if audio:
            book.autor.a_dl_loc = autor_dir
            book.reihe.a_dl_loc = series_dir
            book.a_dl_loc = str(dst_dir) 
        else:
            book.autor.b_dl_loc = autor_dir
            book.reihe.b_dl_loc = series_dir
            book.b_dl_loc = str(dst_dir)
        return activity.nzo_id if activity else "retag"
    except Exception as e:
        get_logger().error(f"Error importing {src} to {dst_dir}: {e}")
        if activity is not None:
            activity.status = ActivityStatus.failed
        restore_backup(bak_dir, dst_dir, overwritten_act)
        return None
    finally:
        cleanup_backup(bak_dir, dst_dir)


async def retag_book(book: Book, cfg: ConfigManager):
    moved = []
    if book.a_dl_loc:
        a = Path(book.a_dl_loc)
        moved.append(asyncio.to_thread(import_book_from_acitivity, None, book, True, Path(book.a_dl_loc), cat_dir=a.parent, cfg=cfg))
    if book.b_dl_loc:
        b = Path(book.b_dl_loc)
        moved.append(asyncio.to_thread(import_book_from_acitivity, None, book, False, Path(book.b_dl_loc), cat_dir=b.parent, cfg=cfg))
    r = await asyncio.gather(*moved)
    if len(r) == 0: return None, None
    if len(r) == 1: 
        if book.a_dl_loc:
            return r[0], None
        if book.b_dl_loc:
            return None, r[0]
    return r

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
        return sorted([p for p in path.iterdir() if p.is_file()])
    except Exception as e:
        return None

async def get_file_stats(paths: list[Path] | None):
    if paths is None: return
    coros = [asyncio.to_thread(lambda p: {"path": p, "size": p.stat().st_size}, p) for p in paths]
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

def get_dirs_of_ext(base_paths, exts):
    audio_dirs = set()
    for base_path in map(Path, base_paths):
        if not base_path.exists():
            continue
        for root, dirs, files in os.walk(base_path):
            # normalize extensions for comparison
            if any(Path(f).suffix.lower() in exts for f in files):
                audio_dirs.add(Path(root))
    return audio_dirs

async def periodic_task(interval_attr: str, task_coro, state, name: Optional[str]):
    while True:
        if getattr(state.cfg_manager, interval_attr) <= 0:
            get_logger().info((f"Disabling {name or task_coro.__name__}"))
            break
        try:
            get_logger().debug(f"Running {name or task_coro.__name__} ...")
            await task_coro(state)
        except Exception as e:
            get_logger().error(f"{name or task_coro.__name__} failed: {e}")
        await asyncio.sleep(getattr(state.cfg_manager, interval_attr))

async def scan_and_move_all_files(state):
    cfg = state.cfg_manager
    downloader: BaseDownloader = state.downloader
    hist, cat_dir = await asyncio.gather(
        downloader.get_history(cfg),
        downloader.get_cat_dir(cfg)
    )
    async with AsyncSession(engine) as session:
        moved = []
        for key, slot in hist.items():
            activity = await session.get(Activity, key, options=[
                selectinload(Activity.book).selectinload(Book.autor), 
                selectinload(Activity.book).selectinload(Book.reihe).selectinload(Reihe.books),
                selectinload(Activity.book).selectinload(Book.activities)
            ])
            if not activity: continue
            if not slot["status"] == "Completed": continue
            src = Path(slot["storage"])
            if os.getenv("DEV"):
                src = Path(os.getenv("DEV")) / str(slot["storage"])[1:] # DEV
            moved.append(asyncio.to_thread(import_book_from_acitivity, activity, activity.book, activity.audio, src, cat_dir=Path(cat_dir), cfg=cfg))
        await downloader.remove_from_history(cfg, [nzo_id for nzo_id in await asyncio.gather(*moved) if nzo_id is not None])
        await session.commit()

async def rescan_files(state):
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

        query = await session.exec(select(Activity).join(Activity.book).where(Activity.status == ActivityStatus.imported, (
            (Activity.audio.is_(True) & Book.a_dl_loc.is_(None)) |
            (Activity.audio.is_(False) & Book.b_dl_loc.is_(None))
        )))
        for a in query.scalars().all():
            a.status = ActivityStatus.deleted
        await session.commit()

async def reimport_files(state):
    cfg = state.cfg_manager
    downloader: BaseDownloader = state.downloader
    async with AsyncSession(engine) as session:
        query = await session.exec(select(Book).options(
            selectinload(Book.autor), 
            selectinload(Book.reihe).selectinload(Reihe.books),
            selectinload(Book.activities)
        ))
        books: list[Book] = query.scalars().all()
        if len(books) == 0: return
        cat_dir = await downloader.get_cat_dir(cfg)
        if os.getenv("DEV") and cat_dir is not None:
            cat_dir = Path(os.getenv("DEV")) / cat_dir[1:] # DEV
        a_paths, b_paths = await asyncio.gather(
            asyncio.to_thread(get_dirs_of_ext, [cfg.audio_path], cfg.audio_extensions_rating), # add cat dir?
            asyncio.to_thread(get_dirs_of_ext, [cfg.book_path], cfg.book_extensions),
        )

        book_names = [b.name.lower().replace("-", " ") for b in books]
        a_idx, b_idx = [], []
        a_fuzz_coros = [asyncio.to_thread(process.extractOne, strip_pos(p.name.lower().replace("-", " ")), book_names) for p in a_paths]
        b_fuzz_coros = [asyncio.to_thread(process.extractOne, strip_pos(p.name.lower().replace("-", " ")), book_names) for p in b_paths]
        a_results, b_results = await asyncio.gather(
            asyncio.gather(*a_fuzz_coros),
            asyncio.gather(*b_fuzz_coros)
        )
        a_idx = [(p, index) for p, (name, score, index) in zip(a_paths, a_results) if score > 70]
        b_idx = [(p, index) for p, (name, score, index) in zip(b_paths, b_results) if score > 70]
        # moved = []
        for p, idx in a_idx:
            if Path(books[idx].a_dl_loc or "").resolve() == p.resolve(): continue
            get_logger().info(f"Found {books[idx].name} at {p}")
            mark_overwritten_activity(books[idx], True)
            activity = Activity(release_title=f"_local_unknown_{books[idx].name}", book=books[idx], audio=True, status=ActivityStatus.imported)
            session.add(activity)
            # moved.append(asyncio.to_thread(move_file, activity, activity.book, activity.audio, p, cat_dir=cat_dir, cfg=cfg))
            books[idx].a_dl_loc = str(p)
        for p, idx in b_idx:
            if Path(books[idx].b_dl_loc or "").resolve() == p.resolve(): continue
            get_logger().info(f"Found {books[idx].name} at {p}")
            mark_overwritten_activity(books[idx], False)
            activity = Activity(release_title=f"_local_unknown_{books[idx].name}", book=books[idx], audio=False, status=ActivityStatus.imported)
            session.add(activity)
            # moved.append(asyncio.to_thread(move_file, activity, activity.book, activity.audio, p, cat_dir=cat_dir, cfg=cfg))
            books[idx].b_dl_loc = str(p)
        # await asyncio.gather(*moved) #TODO log
        await session.commit()

            


            

