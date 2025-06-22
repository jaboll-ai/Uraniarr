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
    series: dict[str, Edition] = {}
    for book_edition_id in author_data.get("_books", []): 
        eds, series_title = scrape_book_editions(book_edition_id)
        _ed = min(eds, key=lambda x: medium_priority.get(x["medium"], 10))
        book = Book(autor_key=author.key)
        book.name, book.bild = _ed["titel"], _ed["bild"]
        if series_title and not series.get(series_title):
            series[series_title] = _ed
        editions = [Edition(**i) for i in eds]
        book.editions = editions
        author.books.append(book)
    session.add(author)
    session.flush()
    for name in series:
        ser: dict[int, list[str]] = scrape_book_series(series[name]["key"])
        # if (cname:=clean_series_title(name)) in [i.name for i in author.reihen]: #TODO technically using series name as key
        #     reihe = session.exec(select(Reihe).where(Reihe.name == cname)).one()
        #     print("series already exists")
        # else:
        reihe = Reihe(name=clean_series_title(name), autor_key=author.key)
        for pos in ser:
            for i, ed_id in enumerate(ser[pos]):
                edition = session.get(Edition, ed_id)
                if not edition: #TODO revisit for multi autor series, if its not there the autor is not there thus, series contains book of diffrent author
                    continue
                book = edition.book
                print(book.name)
                if pos is not None:
                    if i != 0:
                        book.reihe_position =f"{pos+(i)/len(ser[pos]):.1f}"
                    else: book.reihe_position = f"{pos:.0f}"
                else: book.reihe_position = None
                book.name = clean_title(book.name, reihe.name, book.reihe_position)
                book.reihe_key = reihe.key
        author.reihen.append(reihe)
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
def unify_books_of_author(author_id: str, session: Session = Depends(get_session)):
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
app.include_router(api)

