from backend.exceptions import NzbsError
import requests
from uuid import uuid4
from backend.config import ConfigManager


def indexer_search(q: str, cfg: ConfigManager):
    search = {
        "t": "search",
        "cat":3000,
        "o" : "json",
        "q": q,
        "apikey": cfg.indexer_apikey
    }
    response = requests.get(cfg.indexer_url, params=search)
    if response.status_code != 200: raise NzbsError(status_code=response.status_code, detail=response.text)
    response.encoding = 'utf-8'
    if "error" in response.text: raise NzbsError(status_code=403, detail=response.text)
    data = response.json()
    return data

def indexer_nzb(guid: str, cfg: ConfigManager):
    get = {
        "t": "get",
        "id": guid,
        "o" : "json",
        "apikey": cfg.indexer_apikey
    }
    response = requests.get(cfg.indexer_url, params=get)
    if response.status_code != 200: raise NzbsError(status_code=response.status_code, detail=response.text)
    response.encoding = 'utf-8'
    if "error" in response.text: raise NzbsError(status_code=403, detail=response.text)
    return response.content

def download(nzb : bytes, cfg: ConfigManager, nzbname: str = str(uuid4())):
    resp=requests.post(cfg.downloader_url, params={"apikey": cfg.downloader_apikey}, data={"mode": "addfile", "nzbname": nzbname, "cat": cfg.downloader_category or ""}, files={"nzbfile": nzb})
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)

def get_config(cfg: ConfigManager, section: str, keyword: str = None) -> dict:
    resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"get_config","section":section,"output":"json"})
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    parsed = resp.json()
    if keyword:
        return parsed["config"][section][keyword]
    return parsed["config"][section]