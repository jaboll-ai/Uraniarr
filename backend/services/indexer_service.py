from backend.config import ConfigManager
from backend.exceptions import IndexerError
import requests

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