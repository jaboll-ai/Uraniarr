import asyncio
import logging
from pathlib import Path
import re
import shutil
from sqlmodel import func, select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.config import ConfigManager
from backend.datamodels import Book, Series, Author, Activity, ActivityStatus
from backend.exceptions import FileError
from backend.services.downloader import BaseDownloader
from backend.services.scrape import strip_pos
from backend.dependencies import get_error_logger, get_logger, get_scorer
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

def compute_template(book: Book, template: str):
    attrs_used = set()
    response = list(template)
    pattern = re.compile(r"{[^{}]*?{([^{}]*?)}[^{}]*?}")
    if book.series_key:
        max_pos = max(b.position or 0 for b in book.series.books)
        padding = len(str(int(max_pos)))
    parts = template.split("/")
    domain = {"author": len(parts)-1, "series": len(parts)-1}
    for idx, s in list(enumerate(parts))[::-1]:
        if "author." not in s and idx >= domain["author"]: domain["author"] -= 1
        if "series." not in s and idx >= domain["series"]: domain["series"] -= 1
    for p in pattern.finditer(template):
        length = p.end() - p.start() -1
        alternatives = p.group(1).replace(" ", "").split("??")
        trees = [alt.split(".") for alt in alternatives]
        for tree in trees:
            if len(tree) > 3 or len(tree) < 1: raise FileError(f"Too few/many levels in template: {p.group(1)} ({len(tree)})")
            if len(tree) == 1 or tree[0] == "book":
                obj = book
            elif hasattr(book, tree[0]):
                obj = getattr(book, tree[0])
            else:
                get_logger().error(f"Template error: {tree[0]} is not a known namespace")
                obj = object()
            if obj is None or hasattr(obj, tree[-1]) and getattr(obj, tree[-1]) is None:
                sl = ""
            elif tree[0] == "series" and book.author.is_series:
                sl = ""
            elif hasattr(obj, tree[-1]):
                if getattr(obj, tree[-1]) is not None:
                    value = str(getattr(obj, tree[-1]))
                    if tree[-1] == "position" and isinstance(obj, Book):
                        if book.position % 1 != 0:
                            value = f"{str(int(book.position)).zfill(padding)}.{str(book.position).split('.')[-1]}"
                        else:
                            value=f"{str(int(book.position)).zfill(padding)}"
                sl = p.group(0)[1:-1].replace("{"+f"{p.group(1)}"+"}", value)
                attrs_used.add(tree[0])
            else:
                get_logger().debug(f"Unknown attribute: {tree[-1]}")
                sl = re.sub(r"[{}]", "", p.group(0))
            if sl: continue
        response[p.start():p.end()] = [sl] + [""] * length
    response = "".join(response)
    resp = {
        attr: "/".join(response.split("/")[:domain[attr]+1]) if attr in domain else response
        for attr in attrs_used
    }
    return Path(response), resp


def get_destination_dir(book: Book, audio: bool, cfg) -> tuple[str, Optional[str], Path]:
    template = cfg.audiobook_template if audio else cfg.book_template
    path_str = cfg.audio_path if audio else cfg.book_path
    if not path_str: raise FileError(status_code=404, detail=f"{'Audio' if audio else 'Book'} path not configured but tried to import.")
    dst_base = Path(cfg.audio_path if audio else cfg.book_path)
    author_dir, series_dir, book_dst = None, None, None
    if template:
        book_dst, attrs = compute_template(book, template)
        if attrs.get("author"):
            author_dir = str(dst_base/attrs.get("author"))
        if attrs.get("series"):
            series_dir = str(dst_base/attrs.get("series"))
        if book_dst:
            return author_dir, series_dir, dst_base/book_dst

    dst_dir = dst_base / book.author.name
    author_dir = str(dst_dir)

    if book.series_key:
        dst_dir = dst_dir / book.series.name
        series_dir = str(dst_dir)
        if book.position is not None:
            max_pos = max(b.position or 0 for b in book.series.books)
            padding = len(str(int(max_pos)))
            if book.position % 1 != 0:
                dst_dir = dst_dir / f"{str(int(book.position)).zfill(padding)}.{str(book.position).split('.')[-1]} - {book.name}"
            else:
                dst_dir = dst_dir / f"{str(int(book.position)).zfill(padding)} - {book.name}"
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
    get_logger().log(5, f"Cleanup called for {src}")
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


def import_book_from_acitivity(activity: Optional[Activity], book: Book, audio: bool, src: Path, cat_dir: Path, cfg: ConfigManager, overwrite: bool = False):
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
            book.a_dl_loc = str(dst_dir)
            if not overwrite:
                return activity.nzo_id if activity else "retag"
            book.author.a_dl_loc = autor_dir
            book.series.a_dl_loc = series_dir
        else:
            book.b_dl_loc = str(dst_dir)
            if not overwrite:
                return activity.nzo_id if activity else "retag"
            book.author.b_dl_loc = autor_dir
            book.series.b_dl_loc = series_dir
        return activity.nzo_id if activity else "retag"
    except Exception as e:
        get_error_logger().exception(e)
        get_logger().error(f"Error importing {src}: {e}")
        if activity is not None:
            activity.status = ActivityStatus.failed
        restore_backup(bak_dir, dst_dir, overwritten_act)
        return None
    finally:
        cleanup_backup(bak_dir, dst_dir)

def preview_retag(book: Book, cfg: ConfigManager):
    prv = {
        "book": book.key,
        "name": book.name,
        "retag": {
            "old_audio": None,
            "old_book": None,
            "new_audio": None,
            "new_book": None
        }
    }
    if book.a_dl_loc:
        prv["retag"]["old_audio"] = book.a_dl_loc
        old = Path(book.a_dl_loc).resolve()
        author_dir, series_dir, book_dir = get_destination_dir(book, True, cfg)
        new = book_dir.resolve()
        get_logger().log(5, f"{old} == {new}: {old == new}")
        if old == new:
            get_logger().debug(f"RETAG Nothing to do for {book.name}")
        else:
            prv["retag"]["new_audio"] = book_dir
    if book.b_dl_loc:
        prv["retag"]["old_book"] = book.b_dl_loc
        old = Path(book.b_dl_loc).resolve()
        author_dir, series_dir, book_dir = get_destination_dir(book, False, cfg)
        get_logger().debug(f"Calculated {author_dir=}, {series_dir=}")
        new = book_dir.resolve()
        get_logger().log(5, f"{old} == {new}: {old == new}")
        if old == new:
            get_logger().debug(f"RETAG Nothing to do for {book.name}")
        else:
            prv["retag"]["new_book"] = book_dir
    return prv


async def retag_book(book: Book, cfg: ConfigManager, overwrite: bool = False):
    moved = []
    prv = preview_retag(book, cfg)
    if book.a_dl_loc and prv["retag"]["new_audio"]:
        a = Path(book.a_dl_loc)
        moved.append(asyncio.to_thread(import_book_from_acitivity, None, book, True, Path(book.a_dl_loc), cat_dir=a.parent, cfg=cfg, overwrite=overwrite))
    if book.b_dl_loc and prv["retag"]["new_book"]:
        b = Path(book.b_dl_loc)
        moved.append(asyncio.to_thread(import_book_from_acitivity, None, book, False, Path(book.b_dl_loc), cat_dir=b.parent, cfg=cfg, overwrite=overwrite))
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
    await session.commit()

async def delete_audio_series(series_id: str, session: AsyncSession):
    series = await session.get(Series, series_id)
    if not series or not series.a_dl_loc:
        raise FileError(status_code=404, detail=f"Series '{series_id}' not found or not downloaded")
    await asyncio.to_thread(shutil.rmtree, series.a_dl_loc)
    series.a_dl_loc = None
    await session.commit()

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
        raise FileError(status_code=404, detail=f"Error while getting files of book '{book.name}'", exception=e)
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
    paths = [p for p in base_paths if p is not None]
    get_logger().log(5, f"Trying reimport with: {paths}")
    for base_path in map(Path, paths):
        if not base_path.exists():
            continue
        for root, dirs, files in os.walk(base_path):
            # normalize extensions for comparison
            if any(Path(f).suffix.lower() in exts for f in files):
                audio_dirs.add(Path(root))
    return audio_dirs

async def scan_and_move_all_files(state):
    cfg = state.cfg_manager
    downloaders: list[BaseDownloader] = state.downloaders[True] + state.downloaders[False]
    async with AsyncSession(state.engine) as session:
        for downloader in downloaders:
            hist, cat_dir = await asyncio.gather(
                downloader.get_history(cfg),
                downloader.get_cat_dir(cfg)
            )
            moved = []
            for key, slot in hist.items():
                activity = await session.get(Activity, key, options=[
                    selectinload(Activity.book).selectinload(Book.author),
                    selectinload(Activity.book).selectinload(Book.series).selectinload(Series.books),
                    selectinload(Activity.book).selectinload(Book.activities)
                ])
                if not activity:
                    get_logger().debug(f"Activity {key} of our category not found in db")
                    continue
                if not slot["status"] == "Completed": continue
                src = Path(slot["storage"])
                if os.getenv("DEV"):
                    src = Path(os.getenv("DEV")) / str(slot["storage"])[1:] # DEV
                moved.append(asyncio.to_thread(import_book_from_acitivity, activity, activity.book, activity.audio, src, cat_dir=Path(cat_dir), cfg=cfg))
            await downloader.remove_from_history(cfg, [nzo_id for nzo_id in await asyncio.gather(*moved) if nzo_id is not None])
        await session.commit()

async def rescan_files(state):
    async with AsyncSession(state.engine) as session:
        targets = [
            (Book, ["a_dl_loc", "b_dl_loc"]),
            (Author, ["a_dl_loc", "b_dl_loc"]),
            (Series, ["a_dl_loc", "b_dl_loc"]),
        ]
        for model, fields in targets:
            result = await session.exec(select(model))
            instances = result.all()
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
        for a in query.all():
            a.status = ActivityStatus.deleted
        await session.commit()

async def reimport_files(state):
    cfg = state.cfg_manager
    downloaders: list[BaseDownloader]= state.downloaders[True] + state.downloaders[False]
    async with AsyncSession(state.engine) as session:
        query = await session.exec(select(Book).options(
            selectinload(Book.author),
            selectinload(Book.series).selectinload(Series.books),
            selectinload(Book.activities)
        ).order_by(func.length(Book.name).desc()))
        books: list[Book] = query.all()
        if len(books) == 0: return
        cat_dirs = []
        if cfg.import_unfinished:
            coros = [downloader.get_cat_dir(cfg) for downloader in downloaders]
            for d in await asyncio.gather(*coros, return_exceptions=True):
                if isinstance(d, Exception):
                    get_logger().debug(f"Failed to get category dir of a downloader")
                else:
                    if os.getenv("DEV") and d is not None:
                        d = Path(os.getenv("DEV")) / d[1:] # DEV
                    cat_dirs.append(d)
        get_logger().log(5, f"Also checking reimport with: {cat_dirs}")
        a_paths, b_paths = await asyncio.gather(
            asyncio.to_thread(get_dirs_of_ext, [cfg.audio_path, *cat_dirs], cfg.audio_extensions_rating), # add cat dir?
            asyncio.to_thread(get_dirs_of_ext, [cfg.book_path, *cat_dirs], cfg.book_extensions),
        )

        book_names = [b.name for b in books]
        ai_idx, bi_idx = [], []
        a_fuzz_coros = [asyncio.to_thread(process.extractOne, p.name, book_names, scorer=get_scorer()) for p in a_paths]
        b_fuzz_coros = [asyncio.to_thread(process.extractOne, p.name, book_names, scorer=get_scorer()) for p in b_paths]
        a_results, b_results = await asyncio.gather(
            asyncio.gather(*a_fuzz_coros),
            asyncio.gather(*b_fuzz_coros)
        )
        ai_idx = [(p, index, score) for p, (name, score, index) in zip(a_paths, a_results) if score > 80]
        bi_idx = [(p, index, score) for p, (name, score, index) in zip(b_paths, b_results) if score > 80]
        # moved = []
        for p, idx, score in ai_idx:
            if Path(books[idx].a_dl_loc or "").resolve() == p.resolve(): continue
            get_logger().info(f"Found {books[idx].name} at {p} with {score=}")
            mark_overwritten_activity(books[idx], True)
            activity = Activity(release_title=f"_local_unknown_{books[idx].name}", book=books[idx], audio=True, status=ActivityStatus.imported)
            session.add(activity)
            # moved.append(asyncio.to_thread(move_file, activity, activity.book, activity.audio, p, cat_dir=cat_dir, cfg=cfg))
            books[idx].a_dl_loc = str(p)
        for p, idx, score in bi_idx:
            if Path(books[idx].b_dl_loc or "").resolve() == p.resolve(): continue
            get_logger().info(f"Found {books[idx].name} at {p} with {score=}")
            mark_overwritten_activity(books[idx], False)
            activity = Activity(release_title=f"_local_unknown_{books[idx].name}", book=books[idx], audio=False, status=ActivityStatus.imported)
            session.add(activity)
            # moved.append(asyncio.to_thread(move_file, activity, activity.book, activity.audio, p, cat_dir=cat_dir, cfg=cfg))
            books[idx].b_dl_loc = str(p)
        # await asyncio.gather(*moved) #TODO log
        await session.commit()






