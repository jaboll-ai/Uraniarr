from backend.config import ConfigManager
from backend.exceptions import IndexerError
import requests
from backend.services.scrape_service import fix_umlaut, has_umlaut
from backend.datamodels import Book
def indexer_search(q: str, cfg: ConfigManager, audio: bool):
    search = {
        "t": "search",
        "cat":cfg.indexer_audio_category if audio else cfg.indexer_book_category,
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

def query_manual(book: Book, page: int, cfg: ConfigManager, audio: bool):
    base_queries = build_queries(book)
    data = indexer_search(base_queries[page], cfg=cfg, audio=audio)
    query = data["channel"]
    if (total:=query["response"]["@attributes"]["total"]) == "0":
        return { "query": base_queries[page], "nzbs": [], "pages": len(base_queries)}
    items = [query["item"]] if total == "1" else query["item"]
    response = []
    for item in items:
        i = {"name": item["title"]}
        for attribute in item["attr"]:
            if attribute["@attributes"]["name"] == "guid":
                i["guid"] = attribute["@attributes"]["value"]
            elif attribute["@attributes"]["name"] == "size":
                i["size"] = attribute["@attributes"]["value"]
        response.append(i)
    return { "query": base_queries[page], "nzbs": response , "pages": len(base_queries) }
    # for autor, name in base_queries:
    #     used_term = f"{autor} {name}"
    #     data = indexer_search(used_term, cfg=cfg)
    #     query = data["channel"]
    #     if (total:=query["response"]["@attributes"]["total"]) != "0":
    #         break
    # else: return { "query": used_term, "nzbs": [] }

def query_book(book: Book, cfg: ConfigManager, audio: bool):
    base_queries = build_queries(book)
    for q in base_queries: #TODO
        data = indexer_search(q, cfg=cfg, audio=audio)
        query = data["channel"]
        if (total:=query["response"]["@attributes"]["total"]) != "0":
            break
    else: return None, None
    item = query["item"] if total == "1" else query["item"][0]
    name = item["title"]
    for attribute in item["attr"]:
        if attribute["@attributes"]["name"] == "guid":
            guid = attribute["@attributes"]["value"]
    return name, guid

def build_queries(book: Book): #TODO revisit
    base_queries = [f"{book.autor.name} {book.name}"]
    base_queries.append(book.name)
    if has_umlaut(book.autor.name) or has_umlaut(book.name):
        base_queries.append(f"{fix_umlaut(book.autor.name)} {fix_umlaut(book.name)}")
    if has_umlaut(book.name):
        base_queries.append(f"{fix_umlaut(book.name)}")

    if book.reihe_key and book.reihe_position:
        if book.reihe_position % 1 != 0:
            base_queries.append(f"{book.reihe.name} {book.reihe_position}")
        else:
            base_queries.append(f"{book.reihe.name} {round(book.reihe_position)}")
        if has_umlaut(book.reihe.name):
            if book.reihe_position % 1 != 0:
                base_queries.append(f"{fix_umlaut(book.reihe.name)} {book.reihe_position}")
            else:
                base_queries.append(f"{fix_umlaut(book.reihe.name)} {round(book.reihe_position)}")

    return base_queries