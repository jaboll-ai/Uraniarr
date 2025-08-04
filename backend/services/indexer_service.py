from backend.config import ConfigManager
from backend.exceptions import IndexerError
import requests
from backend.services.scrape_service import fix_umlaut
from backend.datamodels import Book
def indexer_search(q: str, cfg: ConfigManager):
    search = {
        "t": "search",
        "cat":3000,
        "o" : "json",
        "q": q,
        "apikey": cfg.indexer_apikey
    }
    response = requests.get(cfg.indexer_url, params=search)
    if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail=response.text)
    response.encoding = 'utf-8'
    if "error" in response.text: raise IndexerError(status_code=403, detail=response.text)
    data = response.json()
    return data

def grab_nzb(guid: str, cfg: ConfigManager):
    get = {
        "t": "get",
        "id": guid,
        "o" : "json",
        "apikey": cfg.indexer_apikey
    }
    response = requests.get(cfg.indexer_url, params=get)
    if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail=response.text)
    response.encoding = 'utf-8'
    if "error" in response.text: raise IndexerError(status_code=403, detail=response.text)
    return response.content

def query_book(book: Book, cfg: ConfigManager):
    base_queries = [
        (book.autor.name, book.name),
        (fix_umlaut(book.autor.name), fix_umlaut(book.name)),
        (fix_umlaut(book.autor.name), book.name),
        (book.autor.name, fix_umlaut(book.name)),
    ]
    if book.reihe_key:
        base_queries.extend([(fix_umlaut(book.autor.name), f"{book.reihe.name} {book.reihe_position}"),
            (book.autor.name, f"{book.reihe.name} {book.reihe_position}"),
            (fix_umlaut(book.autor.name), f"{book.reihe.name} {round(book.reihe_position or 0)}"),
            (book.autor.name, f"{book.reihe.name} {round(book.reihe_position or 0)}"),
            (book.reihe.name, book.name),
            (fix_umlaut(book.reihe.name), fix_umlaut(book.name))])
    for autor, name in base_queries:
        data = indexer_search(f"{autor} {name}", cfg=cfg)
        query = data["channel"]
        if (total:=query["response"]["@attributes"]["total"]) != "0":
            break
    else: return None
    item = query["item"] if total == "1" else query["item"][0] 
    guid=item["attr"][2]["@attributes"]["value"]
    return guid