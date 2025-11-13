from typing import Optional, List, Literal
from sqlmodel import SQLModel, Field, Relationship, case
from time import time
from enum import Enum
from uuid import uuid4

def id_generator(prefix: str = ""):
    return prefix + uuid4().hex[:11].upper()

medium_priority = {20: 0, 42: 1, 18: 2, 1: 3}

class Series(SQLModel, table=True):
    key: str = Field(primary_key=True, default_factory=lambda: id_generator("S"))
    name: str
    autor_key: str = Field(foreign_key="author.key")
    a_dl_loc: Optional[str] = None
    b_dl_loc: Optional[str] = None

    author: "Author" = Relationship(back_populates="series")
    books: List["Book"] = Relationship(back_populates="series", sa_relationship_kwargs={"order_by": "Book.position", "cascade": "all, delete-orphan"})

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
    key: str = Field(primary_key=True, default_factory=lambda: id_generator("B"))
    name: str
    autor_key: str = Field(foreign_key="author.key")
    bild: Optional[str] = None
    series_key: Optional[str] = Field(default=None, foreign_key="series.key")
    position: Optional[float] = None
    a_dl_loc: Optional[str] = None
    b_dl_loc: Optional[str] = None
    blocked: bool = False
    foreign: bool = False

    # Change in api.py lin 143
    author: "Author" = Relationship(back_populates="books")
    series: Optional["Series"] = Relationship(back_populates="books")
    editions: List["Edition"] = Relationship(back_populates="book", sa_relationship_kwargs={"order_by": case(medium_priority, value=Edition.medium, else_=10), "cascade": "all, delete-orphan"})
    activities: Optional[List["Activity"]] = Relationship(back_populates="book", sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "-Activity.created"})


class Author(SQLModel, table=True):
    key: str = Field(primary_key=True)
    name: str
    bild: Optional[str] = None
    bio: Optional[str] = None
    a_dl_loc: Optional[str] = None
    b_dl_loc: Optional[str] = None
    is_series: bool = False

    books: List["Book"] = Relationship(back_populates="author", sa_relationship_kwargs={"order_by": (Book.series_key, Book.position), "cascade": "all, delete-orphan"})
    series: List["Series"] = Relationship(back_populates="author", sa_relationship_kwargs={"cascade": "all, delete-orphan"})

class ActivityStatus(str, Enum):
    imported = "imported"
    download = "download"
    canceled = "canceled"
    failed = "failed"
    overwritten = "overwritten"
    deleted = "deleted"

class Activity(SQLModel, table=True):
    nzo_id: str = Field(primary_key=True, default_factory=lambda: id_generator("A"))
    created: float = Field(default_factory=time)
    release_title: str
    book_key: str = Field(foreign_key="book.key")
    status: ActivityStatus = ActivityStatus.download
    audio: bool
    guid: Optional[str] = None

    book: "Book" = Relationship(back_populates="activities")

class BlocklistNZB(SQLModel, table=True):
    guid: str = Field(primary_key=True)
    created: float = Field(default_factory=time)