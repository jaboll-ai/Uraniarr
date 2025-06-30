from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, create_engine, select
from backend.datamodels import Book, Reihe, Edition, Author, medium_priority
from backend.scrape import *
from datetime import datetime
from rapidfuzz import fuzz

base="***REMOVED***"
book="/shop/home/artikeldetails/"
series="/api/serienslider/v2/"

app = FastAPI()
tapi = APIRouter(prefix="/tapi", tags=["scraped"])
mapi = APIRouter(prefix="/mapi", tags=["middleware (very I/O heavy, careful!)"])
api = APIRouter(prefix="/api", tags=["database"])
uapi = APIRouter(prefix="/uapi", tags=["usenet"])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Might make docker env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine("sqlite:///data/database.db")
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

@tapi.get("/books/editions/{book_id}")
def fetch_book_editions(book_id: str):
    editions, _ = scrape_book_editions(book_id)
    return [Edition(**i) for i in editions]

@tapi.get("/author/{author_id}")
def fetch_author_data(author_id: str):
    return scrape_author_data(author_id)

@tapi.get("/search")
def search(q: str):
    return scrape_search(q)

@mapi.post("/author/{author_id}")
def import_author(author_id: str, override: bool = False, session: Session = Depends(get_session)):
    if (author:=session.get(Author, author_id)):
        if not override:
            raise HTTPException(status_code=403, detail="Author already exists")
        else: session.delete(author)
    author_data = scrape_author_data(author_id)
    author = Author(**author_data)
    reihen: dict[str, Reihe] = {}
    for book_edition_id in author_data.get("_books", []):
        eds, series_title = scrape_book_editions(book_edition_id)
        eds = sorted(eds, key=lambda x: medium_priority.get(x["medium"], 10))
        book = Book(autor_key=author.key)
        book.name, book.bild, book.reihe_position = eds[0].get("titel"), eds[0].get("bild"), eds[0].get("_pos")
        if series_title:
            ctitle = clean_title(book.name, series_title, book.reihe_position)
            if book.name == ctitle:
                for ed in eds:
                    ctitle = clean_title(ed.get("titel"), series_title, ed.get("_pos")) # if fallback was used e.g. Title of Edition was only Series Name + Series Pos we check if there is a better title
                    if book.name != ctitle:
                        break
            book.name = ctitle
            reihe = reihen.setdefault(series_title, Reihe(name=series_title, autor_key=author.key))
            reihe.books.append(book)
            if book.reihe_position and (bs:=[b for b in reihe.books if b.reihe_position and int(b.reihe_position) == int(book.reihe_position)]):
                for idx, b in enumerate(bs):
                    b.reihe_position = round(0.1*idx + int(book.reihe_position), 1)
        editions = [Edition(**i) for i in eds]
        book.editions = editions
        author.books.append(book)
        author.reihen = list(reihen.values())
    session.add(author)
    session.flush()
    ### black magic to join series that got detected as 2 separate ###
    for reihe1 in author.reihen:
        rp1 = { b.reihe_position for b in reihe1.books }
        for reihe2 in author.reihen:
            if reihe1.key == reihe2.key: continue
            rp2 = { b.reihe_position for b in reihe2.books }
            if fuzz.ratio(reihe1.name, reihe2.name) > 45 and not rp1.intersection(rp2):
                if len(reihe1.name) > len(reihe2.name): reihe1, reihe2 = reihe2, reihe1
                while reihe2.books:
                    b = reihe2.books.pop(0)
                    reihe1.books.append(b)
                author.reihen.remove(reihe2)
    session.commit()
    return author.key

@api.get("/author/{author_id}/series")
def get_author_series(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author.reihen
    raise HTTPException(status_code=404, detail="Author not found")

@api.get("/author/{author_id}/books")
def get_author_books(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author.books
    raise HTTPException(status_code=404, detail="Author not found")

@api.get("/author/{author_id}")
def get_author_info(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author
    raise HTTPException(status_code=404, detail="Author not found")

@api.get("/book/{book_id}")
def get_book(book_id: str, session: Session = Depends(get_session)):
    if book := session.get(Book, book_id):
        return book
    raise HTTPException(status_code=404, detail="Book not found")

@api.get("/authors")
def get_authors(session: Session = Depends(get_session)):
    return session.scalars(select(Author)).all()

@api.get("/series/{series_id}/books")
def get_books_of_series(series_id: str, session: Session = Depends(get_session)):
    if reihe := session.get(Reihe, series_id):
        return reihe.books
    raise HTTPException(status_code=404, detail="Series not found") 

@api.post("/author/{author_id}/unify")
def unify_series_of_author(author_id: str, session: Session = Depends(get_session)):
    books = session.get(Author, author_id).books
    grouped = {}
    for book in books:
        key = (book.name, book.autor_key, book.reihe_position, book.reihe_key)
        grouped.setdefault(key, []).append(book)

    for group in grouped.values():
        if len(group) <= 1: continue 
        main_book = group[0]
        for book in group[1:]:
            for edition in book.editions:
                main_book.editions.append(edition)
            session.delete(book)
            if book.reihe_key:
                main_book.reihe_key = book.reihe_key # TODO
    session.commit()

    return {"merged_into": main_book.key}

@api.delete("/author/{author_id}")
def delete_author(author_id: str, session: Session = Depends(get_session)):
    session.delete(session.get(Author, author_id))
    session.commit()
    return {"deleted": author_id}

# Includings
app.include_router(tapi)
app.include_router(mapi)
app.include_router(uapi)
app.include_router(api)

