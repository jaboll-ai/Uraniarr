import asyncio
from itertools import combinations
from rapidfuzz import fuzz
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.datamodels import *
from backend.dependencies import get_logger, get_scorer
from backend.exceptions import AuthorError
from backend.services.scrape import clean_title

async def save_author_to_db(author_id: str, session: AsyncSession, scraped: dict, override: bool = False):
    author_data = scraped["author_data"]
    books_data = scraped["books"]
    if author := await session.get(Author, author_id):
        if not override:
            raise AuthorError(detail=f"Author {author_id} already exists", status_code=403)
        else: await session.delete(author)
    author = Author(**author_data)
    resp = await add_books_to_author(author, session, books_data)
    return resp

async def add_books_to_author(author: Author, session: AsyncSession, books_data: list):
    found_series: dict[str, Series] = {}
    sanity_dedub = set() # see A1040945738 for funky shit
    result = await session.exec(select(Edition.key))
    in_db = set(result.scalars().all())
    for eds, series_title in books_data:
        if not eds:
            get_logger().debug(f"Skipping book because it has no editions")
            continue
        eds = sorted(eds, key=lambda x: medium_priority.get(x["medium"], 10))
        if any([ed["key"] in in_db for ed in eds]):
            get_logger().warning(f"Skipping {eds[0]['key']} because it already exists")
        book = Book(autor_key=author.key)
        book.name, book.bild, book.position = clean_title(eds[0].get("titel")), eds[0].get("bild"), eds[0].get("_pos")
        if series_title:
            ctitles = [clean_title(ed.get("titel"), series_title, ed.get("_pos")) for ed in eds]
            book.name = sorted(ctitles, key=lambda x: len(x))[0]
            series = found_series.setdefault(series_title, Series(name=series_title, autor_key=author.key))
            series.books.append(book)
            # if book.position and (bs:=[b for b in series.books if b.position and int(b.position) == int(book.position)]):
            #     for idx, b in enumerate(bs):
            #         b.position = round(0.1*idx + int(book.position), 1) # maybe check date before??
        editions = []
        for i in eds:
            if i["key"] in sanity_dedub or i["key"] in in_db:
                continue
            editions.append(Edition(**i))
            sanity_dedub.add(i["key"])
        book.editions = editions
        author.books.append(book)
    session.add(author)
    await session.flush()
    await session.refresh(author, attribute_names=["series"])
    await auto_union_series(author.series, session)
    coros = [clean_series_duplicates(series, session) for series in author.series]
    await asyncio.gather(*coros)
    resp = author.key
    await session.commit()
    return resp

async def auto_union_series(series: list[Series], session: AsyncSession):
    for r1, r2 in combinations(series, 2):
        if get_scorer()(r1.name, r2.name) > 80:
            if len(r1.name) > len(r2.name): r1, r2 = r2, r1
            for book in r2.books:
                book.name = clean_title(book.name, r1.name, book.position)
            r1.books.extend(r2.books)
            await session.delete(r2)

async def clean_series_duplicates(series: Series, session: AsyncSession):
    for book, book2 in combinations(series.books, 2):
        if not book.position or not book2.position: continue
        if float(book.position) == float(book2.position) and (
            (_b1:=clean_title(book.name, series.name, book.position, can_be_empty=True)=="") or # one of our books is just Series Name - Series Position like "Skulduggery Pleasant - 17"
            clean_title(book2.name, series.name, book2.position, can_be_empty=True)=="" or
            get_scorer()(book.name, book2.name) > 80): # we basically have the same book twice
            if _b1: book, book2 = book2, book
            book.editions.extend(book2.editions)
            await session.delete(book2)

async def complete_series_in_db(series_id: str, session: AsyncSession, scraped: dict):
    series = await session.get(Series, series_id)
    if not series:
        raise AuthorError(status_code=404, detail="Series not found")
    for book_data in scraped:
        if await session.get(Edition, book_data.get("key")): continue
        book = Book(autor_key=series.autor_key, name=book_data.get("titel"), bild=book_data.get("bild"), position=book_data.get("_pos"))
        book.editions.append(Edition(**book_data))
        series.books.append(book)
    await session.commit()
    resp = [b["key"] for b in scraped]
    return resp

async def make_author_from_series(name:str, session: AsyncSession, scraped: dict):
    author = Author(key=id_generator(), name=name, is_series=True)
    series = Series(name=name)
    result = await session.exec(select(Edition.key))
    in_db = set(result.scalars().all())
    for book_data in scraped:
        if book_data.get("key") in in_db:
            raise AuthorError(status_code=409, detail="Book already exists for diffrent author")
        book = Book(autor_key=author.key, name=book_data.get("titel"), bild=book_data.get("bild"), position=book_data.get("_pos"))
        book.editions.append(Edition(**book_data))
        series.books.append(book)
    author.series = [series]
    session.add(author)
    resp = author.key
    await session.commit()
    return resp

async def union_series(series_id: str, series_ids: list[str], session: AsyncSession):
    series = await session.get(Series, series_id, options=[selectinload(Series.books)])
    if not series:
        raise AuthorError(status_code=404, detail="Series not found")
    r2s = await session.exec(select(Series).where(Series.key.in_(series_ids)).options(selectinload(Series.books)))
    series = r2s.scalars().all()
    # if len(r2s) != len(series_ids):
    #     raise AuthorError(status_code=404, detail="Series not found")
    for series2 in series:
        for book in series2.books:
            book.name = clean_title(book.name, series.name, book.position)
        series.books.extend(series2.books)
        await session.delete(series2)
    await clean_series_duplicates(series, session)
    await session.commit()
    return series_ids