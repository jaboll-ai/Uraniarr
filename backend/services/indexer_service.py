from backend.config import ConfigManager
from backend.exceptions import IndexerError
import requests
from backend.services.scrape_service import fix_umlaut, has_umlaut
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

def query_manual(book: Book, page: int, cfg: ConfigManager):
    base_queries = build_queries(book)
    data = indexer_search(base_queries[page], cfg=cfg)
    query = data["channel"]
    if (total:=query["response"]["@attributes"]["total"]) == "0":
        return { "query": base_queries[page], "nzbs": [], "pages": len(base_queries)}
    items = [query["item"]] if total == "1" else query["item"]
    reponse = [{"name": item["title"],
                "guid": item["attr"][2]["@attributes"]["value"],
                "size": item["attr"][1]["@attributes"]["value"] } for item in items ]
    return { "query": base_queries[page], "nzbs": reponse , "pages": len(base_queries) }
    # for autor, name in base_queries:
    #     used_term = f"{autor} {name}"
    #     data = indexer_search(used_term, cfg=cfg)
    #     query = data["channel"]
    #     if (total:=query["response"]["@attributes"]["total"]) != "0":
    #         break
    # else: return { "query": used_term, "nzbs": [] }

def query_book(book: Book, cfg: ConfigManager):
    base_queries = build_queries(book)
    for q in base_queries: #TODO
        data = indexer_search(q, cfg=cfg)
        query = data["channel"]
        if (total:=query["response"]["@attributes"]["total"]) != "0":
            break
    else: return None
    item = query["item"] if total == "1" else query["item"][0] 
    guid=item["attr"][2]["@attributes"]["value"]
    name=item["title"] 
    return name, guid

def build_queries(book: Book): #TODO revisit
    base_queries = [f"{book.autor.name} {book.name}"]
    author_fix = fix_umlaut(book.autor.name)
    book_fix = fix_umlaut(book.name)
    base_queries.append(f"{author_fix} {book_fix}")
    if book.reihe_key and book.reihe_position is not None:
        series_fix = fix_umlaut(book.reihe.name)
        base_queries.append(f"{book.reihe.name} {round(book.reihe_position)}")
        if book.reihe_position % 1 != 0:
            base_queries.append(f"{book.reihe.name} {book.reihe_position}")
        if has_umlaut(series_fix):
            base_queries.append(f"{series_fix} {round(book.reihe_position)}")
            if book.reihe_position % 1 != 0:
                base_queries.append(f"{series_fix} {book.reihe_position}")
        for entry in list(base_queries)[:2]:
            base_queries.append(f"{entry} {round(book.reihe_position)}")
            if book.reihe_position % 1 != 0:
                base_queries.append(f"{entry} {book.reihe_position}")
    return base_queries