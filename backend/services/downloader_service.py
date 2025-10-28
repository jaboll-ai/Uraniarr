from backend.exceptions import NzbsError
import requests
from backend.config import ConfigManager
from sqlmodel import Session

def download(nzb : bytes, cfg: ConfigManager, nzbname: str):
    try:
        resp=requests.post(cfg.downloader_url, params={"apikey": cfg.downloader_apikey}, data={"mode": "addfile", "nzbname": nzbname, "cat": cfg.downloader_category or ""}, files={"nzbfile": nzb})
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not queue item for SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return resp.json()

def get_config(cfg: ConfigManager, section: str, keyword: str = None) -> dict:
    try:
        resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"get_config","section":section,"output":"json"}, timeout=10)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get config from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    parsed = resp.json()
    if keyword:
        return parsed["config"][section][keyword]
    return parsed["config"][section]

def get_history(cfg: ConfigManager):
    try:
        resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"history","output":"json"})
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    data = resp.json()
    return data["history"]["slots"]

def remove_from_history(cfg: ConfigManager, nzo_id: str):
    try:
        resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"history", "name":"delete", "value":",".join([nzo_id] if type(nzo_id) == str else nzo_id), "output":"json"})
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return nzo_id

def remove_from_queue(cfg: ConfigManager, nzo_id: str):
    try:
        resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"queue", "name":"delete", "value":",".join([nzo_id] if type(nzo_id) == str else nzo_id), "output":"json"})
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not queue item from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return nzo_id

def get_queue(cfg: ConfigManager):
    try:
        resp = requests.get(cfg.downloader_url, params={"apikey":cfg.downloader_apikey,"mode":"queue","output":"json"})
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return data["queue"]["slots"]