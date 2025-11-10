from abc import ABC, abstractmethod
from backend.config import ConfigManager
from backend.datamodels import Book
from backend.services.scrape import fix_umlaut, has_umlaut
from backend.exceptions import IndexerError
import httpx
import asyncio
from time import time

class BaseIndexer(ABC):
    def __init__(self):
        self.last_hit = 0

    @abstractmethod
    async def search(self, q: str, cfg: ConfigManager, audio: bool):
        pass

    @abstractmethod
    async def query_manual(self, book: Book, page: int, cfg: ConfigManager, audio: bool):
        pass

    @abstractmethod
    async def query_book(self, book: Book, cfg: ConfigManager, audio: bool):
        pass

    @abstractmethod
    async def grab(self, download: str, cfg: ConfigManager):
        pass
    
    def build_queries(self, book: Book): #TODO revisit
        base_queries = [f"{book.author.name} {book.name}"]
        base_queries.append(book.name)
        if has_umlaut(book.author.name) or has_umlaut(book.name):
            base_queries.append(f"{fix_umlaut(book.author.name)} {fix_umlaut(book.name)}")
        if has_umlaut(book.name):
            base_queries.append(f"{fix_umlaut(book.name)}")

        if book.series_key and book.position:
            if book.position % 1 != 0:
                base_queries.append(f"{book.series.name} {book.position}")
            else:
                base_queries.append(f"{book.series.name} {int(book.position)}")
            if has_umlaut(book.series.name):
                if book.position % 1 != 0:
                    base_queries.append(f"{fix_umlaut(book.series.name)} {book.position}")
                else:
                    base_queries.append(f"{fix_umlaut(book.series.name)} {int(book.position)}")

        return base_queries
    
    def normalize(self, url: str) -> str:
        url=url.rstrip("/")
        url=url.rstrip("/api") + "/api"
        return url
