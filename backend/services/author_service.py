import asyncio
from itertools import combinations
from rapidfuzz import fuzz
from sqlmodel import Session, select
from backend.datamodels import *
from backend.exceptions import AuthorError
from backend.services.scrape_service import clean_title

def save_author_to_db(author_id: str, session: Session, scraped: dict, override: bool = False):
    author_data = scraped["author_data"]
    books_data = scraped["books"]
    if (author:=session.get(Author, author_id)):
        if not override:
            raise AuthorError(detail=f"Author {author_id} already exists", status_code=403)
        else: session.delete(author)
    author = Author(**author_data)
    resp = add_books_to_author(author, session, books_data)
    return resp

def add_books_to_author(author: Author, session : Session, books_data: list):
    reihen: dict[str, Reihe] = {}
    sanity_dedub = set() # see A1040945738 for funky shit
    in_db = set(session.exec(select(Edition.key)).all())
    for eds, series_title in books_data:
        eds = sorted(eds, key=lambda x: medium_priority.get(x["medium"], 10))
        for ed in eds:
            if ed["key"] in in_db: continue
            break
        else: continue
        book = Book(autor_key=author.key)
        book.name, book.bild, book.reihe_position = eds[0].get("titel"), eds[0].get("bild"), eds[0].get("_pos")
        if series_title:
            ctitles = [clean_title(ed.get("titel"), series_title, ed.get("_pos")) for ed in eds]
            book.name = sorted(ctitles, key=lambda x: len(x))[0]
            reihe = reihen.setdefault(series_title, Reihe(name=series_title, autor_key=author.key))
            reihe.books.append(book)
            # if book.reihe_position and (bs:=[b for b in reihe.books if b.reihe_position and int(b.reihe_position) == int(book.reihe_position)]):
            #     for idx, b in enumerate(bs):
            #         b.reihe_position = round(0.1*idx + int(book.reihe_position), 1) # maybe check date before??
        editions = []
        for i in eds:
            if i["key"] in sanity_dedub or i["key"] in in_db:
                continue
            editions.append(Edition(**i))
            sanity_dedub.add(i["key"])
        book.editions = editions
        author.books.append(book)
    session.add(author)
    session.flush()
    auto_union_series(author.reihen, session)
    for reihe in author.reihen: #really inefficient needs revisit #TODO
        clean_series_duplicates(reihe, session)
    session.commit()
    return author.key

def auto_union_series(reihen: list[Reihe], session: Session):
    for r1, r2 in combinations(reihen, 2):
        if len(r1.name) > 5 and fuzz.token_set_ratio(r1.name.replace("-", " "), r2.name.replace("-", " ")) > 80:
            if len(r1.name) > len(r2.name): r1, r2 = r2, r1
            for book in r2.books:
                book.name = clean_title(book.name, r1.name, book.reihe_position)
            r1.books.extend(r2.books)
            session.delete(r2)

def clean_series_duplicates(reihe: Reihe, session: Session):
    for book, book2 in combinations(reihe.books, 2):
        if not book.reihe_position or not book2.reihe_position: continue
        if fuzz.ratio(book.name, book2.name) > 80 and float(book.reihe_position) == float(book2.reihe_position): # we basically have the same book twice
            book.editions.extend(book2.editions)
            session.delete(book2)

def complete_series_in_db(series_id: str, session: Session, scraped: dict):
    reihe = session.get(Reihe, series_id)
    if not reihe:
        raise AuthorError(status_code=404, detail="Series not found")
    for book_data in scraped:
        if session.get(Edition, book_data.get("key")): continue
        book = Book(autor_key=reihe.autor_key, name=book_data.get("titel"), bild=book_data.get("bild"), reihe_position=book_data.get("_pos"))
        book.editions.append(Edition(**book_data))
        reihe.books.append(book)
    session.commit()
    resp = [b["key"] for b in scraped]
    return resp

def make_author_from_series(name:str, session: Session, scraped: dict):
    author = Author(key=id_generator(), name=name, is_series=True)
    reihe = Reihe(name=name)
    in_db = set(session.exec(select(Edition.key)).all())
    for book_data in scraped:
        if book_data.get("key") in in_db: 
            raise AuthorError(status_code=409, detail="Book already exists for diffrent author")
        book = Book(autor_key=author.key, name=book_data.get("titel"), bild=book_data.get("bild"), reihe_position=book_data.get("_pos"))
        book.editions.append(Edition(**book_data))
        reihe.books.append(book)
    author.reihen = [reihe]
    session.add(author)
    session.commit()
    return author.key

def union_series(series_id: str, series_ids: list[str], session: Session):
    reihe = session.get(Reihe, series_id)
    if not reihe:
        raise AuthorError(status_code=404, detail="Series not found")
    for id in series_ids:
        reihe2 = session.get(Reihe, id)
        if not reihe2:
            raise AuthorError(status_code=404, detail="Series not found")
        for book in reihe2.books:
            book.name = clean_title(book.name, reihe.name, book.reihe_position)
        reihe.books.extend(reihe2.books)
        session.delete(reihe2)
    clean_series_duplicates(reihe)
    session.commit()
    return id