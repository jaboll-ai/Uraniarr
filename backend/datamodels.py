from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import date
import pydantic
from uuid import uuid4

def id_generator():
    return uuid4().hex[:12].upper()

class Reihe(SQLModel, table=True):
    key: str = Field(primary_key=True, default_factory=id_generator)
    name: str
    
    books: List["Book"] = Relationship(back_populates="serie")
    
class Book(SQLModel, table=True):
    key: str = Field(primary_key=True, default_factory=id_generator)
    titel: str
    autor: str
    sprache: str
    erscheinungsdatum: str
    hörbuch: str = Field(default=None, unique=True)
    bild_hörbuch: str = Field(default=None)
    taschenbuch: str = Field(default=None, unique=True)
    bild_taschenbuch: str = Field(default=None)
    hardcover: str = Field(default=None, unique=True)
    bild_hardcover: str = Field(default=None)
    ebook: str = Field(default=None, unique=True)
    bild_ebook: str = Field(default=None)
    serie_key: str = Field(default=None, foreign_key="reihe.key")
    
    serie: Optional["Reihe"] = Relationship(back_populates="books")
    

class SearchResult(pydantic.BaseModel):
    query: str
    books: list
    autors: list