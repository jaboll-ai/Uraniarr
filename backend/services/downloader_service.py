from backend.exceptions import NzbsError
import requests
from backend.config import ConfigManager

def download(nzb : bytes, cfg: ConfigManager, nzbname: str):
    resp=requests.post(cfg.downloader_url, params={"apikey": cfg.downloader_apikey}, data={"mode": "addfile", "nzbname": nzbname, "cat": cfg.downloader_category or ""}, files={"nzbfile": nzb})
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_config(cfg: ConfigManager, section: str, keyword: str = None) -> dict:
    resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"get_config","section":section,"output":"json"}, timeout=10)
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    parsed = resp.json()
    if keyword:
        return parsed["config"][section][keyword]
    return parsed["config"][section]

def get_history(cfg: ConfigManager):
    resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"history","output":"json"})
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return data["history"]["slots"]

def remove_from_history(cfg: ConfigManager, nzo_id: str):
    try:
        resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"history", "name":"delete", "value":",".join(nzo_id)})
    except KeyError as e:
        raise NzbsError(status_code=resp.status_code, detail=e)
    return nzo_id

def get_queue(cfg: ConfigManager):
    resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"queue","output":"json"})
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return data["queue"]["slots"]