from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, case
from datetime import date
from pydantic import BaseModel
from uuid import uuid4

def id_generator():
    return uuid4().hex[:12].upper()

medium_priority = {20: 0, 42: 1, 18: 2, 1: 3}

class Reihe(SQLModel, table=True):
    key: str = Field(primary_key=True, default_factory=id_generator)
    name: str
    autor_key: str = Field(foreign_key="author.key")
    a_dl_loc: Optional[str] = None
    b_dl_loc: Optional[str] = None

    autor: "Author" = Relationship(back_populates="reihen")
    books: List["Book"] = Relationship(back_populates="reihe", sa_relationship_kwargs={"order_by": "Book.reihe_position", "cascade": "all, delete-orphan"})

class Edition(SQLModel, table=True):
    key: str = Field(primary_key=True)
    book_key: str = Field(foreign_key="book.key")
    titel: str
    bild: str
    einband: Optional[str] = None
    altersempfehlung: Optional[str] = None
    erscheinungsdatum: Optional[str] = None
    herausgeber: Optional[str] = None
    verlag: Optional[str] = None 
    auflage: Optional[str] = None
    übersetzt_von: Optional[str] = None
    sprache: Optional[str] = None
    isbn: Optional[str] = None
    ean: Optional[str] = None
    medium: Optional[int] = None
    
    book: "Book" = Relationship(back_populates="editions")
 
class Book(SQLModel, table=True):
    key: str = Field(primary_key=True, default_factory=id_generator)
    name: str
    autor_key: str = Field(foreign_key="author.key")
    bild: Optional[str] = None
    reihe_key: Optional[str] = Field(default=None, foreign_key="reihe.key")
    reihe_position: Optional[float] = None
    a_dl_loc: Optional[str] = None
    b_dl_loc: Optional[str] = None
    
    autor: "Author" = Relationship(back_populates="books")
    reihe: Optional["Reihe"] = Relationship(back_populates="books")
    editions: List["Edition"] = Relationship(back_populates="book", sa_relationship_kwargs={"order_by": case(medium_priority, value=Edition.medium, else_=10), "cascade": "all, delete-orphan"})
    

class Author(SQLModel, table=True):
    key: str = Field(primary_key=True)
    name: str
    bild: Optional[str] = None
    bio: Optional[str] = None
    a_dl_loc: Optional[str] = None
    b_dl_loc: Optional[str] = None
    
    books: List["Book"] = Relationship(back_populates="autor", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    reihen: List["Reihe"] = Relationship(back_populates="autor", sa_relationship_kwargs={"cascade": "all, delete-orphan"})
    