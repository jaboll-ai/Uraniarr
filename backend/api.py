from fastapi import FastAPI, HTTPException, Depends, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, create_engine, select
from backend.datamodels import *
from backend.scrape import *
from backend.nzbapi import *
from backend.config import ConfigManager
from itertools import combinations
from rapidfuzz import fuzz
from uuid import uuid4

base="***REMOVED***"
book="/shop/home/artikeldetails/"
series="/api/serienslider/v2/"

app = FastAPI()
tapi = APIRouter(prefix="/tapi", tags=["scraped"])
mapi = APIRouter(prefix="/mapi", tags=["middleware (very I/O heavy, careful!)"])
api = APIRouter(prefix="/api", tags=["database"])
nzbapi = APIRouter(prefix="/nzbapi", tags=["NZB Handling"])
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
def get_cfg_manager():
    return ConfigManager()

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
                    b.reihe_position = round(0.1*idx + int(book.reihe_position), 1) # maybe check date before??
        editions = [Edition(**i) for i in eds]
        book.editions = editions
        author.books.append(book)
        author.reihen = list(reihen.values())
    session.add(author)
    session.flush()
    for reihe in author.reihen: #really inefficient needs revisit #TODO
        for book, book2 in combinations(reihe.books, 2):
            if fuzz.ratio(book.name, book2.name) > 90 and round(float(book.reihe_position)) == round(float(book2.reihe_position)): # we basically have the same book twice
                for edition in book2.editions:
                    book.editions.append(edition)
                author.books.remove(book2)
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

@api.get("/settings")
def get_settings(cfg: ConfigManager = Depends(get_cfg_manager)):
    """Retrieve all configuration settings."""
    return cfg.get()

@api.patch("/settings")
def update_settings(settings: dict, cfg: ConfigManager = Depends(get_cfg_manager)):
    """Update all configuration settings in one call using attribute access."""
    for key in settings:
        setattr(cfg, key, settings[key])
    return cfg.get()

@nzbapi.post("/book/{book_id}")
def download_book(book_id: str, session: Session = Depends(get_session), cfg: ConfigManager = Depends(get_cfg_manager)):
    book = session.get(Book, book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    data = indexer_search(f"{book.autor.name} {book.name}", cfg=cfg)
    query = data["channel"]
    if (total:=query["response"]["@attributes"]["total"]) == "0": raise HTTPException(status_code=404, detail="Book not found")
    else: #maybe do fuzzy ratio?
        item = query["item"] if total == "1" else query["item"][0] 
        guid=item["attr"][2]["@attributes"]["value"]
        nzb = indexer_nzb(guid, cfg=cfg)
        download(nzb, nzbname=book.key, cfg=cfg)
    return


# Includings
app.include_router(tapi)
app.include_router(mapi)
app.include_router(nzbapi)
app.include_router(api)

