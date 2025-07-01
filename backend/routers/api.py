from fastapi import HTTPException, Depends, APIRouter
from backend.dependencies import get_session, get_cfg_manager
from sqlmodel import Session, select
from backend.datamodels import *
from backend.config import ConfigManager

router = APIRouter(prefix="/api", tags=["database"])

@router.get("/author/{author_id}/series")
def get_author_series(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author.reihen
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/author/{author_id}/books")
def get_author_books(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author.books
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/author/{author_id}")
def get_author_info(author_id: str, session: Session = Depends(get_session)):
    if author := session.get(Author, author_id):
        return author
    raise HTTPException(status_code=404, detail="Author not found")

@router.get("/book/{book_id}")
def get_book(book_id: str, session: Session = Depends(get_session)):
    if book := session.get(Book, book_id):
        return book
    raise HTTPException(status_code=404, detail="Book not found")

@router.get("/authors")
def get_authors(session: Session = Depends(get_session)):
    return session.scalars(select(Author)).all()

@router.get("/series/{series_id}/books")
def get_books_of_series(series_id: str, session: Session = Depends(get_session)):
    if reihe := session.get(Reihe, series_id):
        return reihe.books
    raise HTTPException(status_code=404, detail="Series not found") 

@router.delete("/author/{author_id}")
def delete_author(author_id: str, session: Session = Depends(get_session)):
    session.delete(session.get(Author, author_id))
    session.commit()
    return {"deleted": author_id}

@router.get("/settings")
def get_settings(cfg: ConfigManager = Depends(get_cfg_manager)):
    """Retrieve all configuration settings."""
    return cfg.get()

@router.patch("/settings")
def update_settings(settings: dict, cfg: ConfigManager = Depends(get_cfg_manager)):
    """Update all configuration settings in one call using attribute access."""
    for key in settings:
        setattr(cfg, key, settings[key])
    return cfg.get()


