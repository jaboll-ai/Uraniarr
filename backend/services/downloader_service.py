from backend.exceptions import NzbsError
import httpx
from backend.config import ConfigManager
from sqlmodel import Session

def download(nzb : bytes, cfg: ConfigManager, nzbname: str):
    try:
        files = {
            "nzbfile": (f"{nzbname}.nzb", nzb, "application/x-nzb")
        }
        data = {
            "mode": "addfile",
            "nzbname": nzbname,
            "cat": cfg.downloader_category or "",
        }
        params = {"apikey": cfg.downloader_apikey}
        resp = httpx.post(cfg.downloader_url, params=params, data=data, files=files)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not queue item for SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    try:
        return resp.json()
    except Exception as e:
        print(e, resp.text)
        raise NzbsError(status_code=500, detail="Could not queue item for SABnzbd. Internal Error") 

def get_config(cfg: ConfigManager, section: str, keyword: str = None) -> dict:
    try:
        get_cfg ={
            "apikey": cfg.downloader_apikey,
            "mode": "get_config",
            "section": section,
            "output": "json",
        }
        resp = httpx.get(cfg.downloader_url, params=get_cfg, timeout=10.0)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get config from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    parsed = resp.json()
    if keyword:
        return parsed["config"][section][keyword]
    return parsed["config"][section]

def get_history(cfg: ConfigManager):
    try:
        get_hst = {
            "apikey": cfg.downloader_apikey,
            "mode":"history",
            "output":"json"
        }
        print(f"httpx.get({cfg.downloader_url}, params={get_hst})")
        resp = httpx.get(cfg.downloader_url, params=get_hst)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    data = resp.json()
    return data["history"]["slots"]

def remove_from_history(cfg: ConfigManager, nzo_id: str):
    try:
        rm_hst = {
            "apikey": cfg.downloader_apikey,
            "mode": "history",
            "name": "delete",
            "value": ",".join([nzo_id] if isinstance(nzo_id, str) else nzo_id),
            "output": "json",
        }
        resp = httpx.get(cfg.downloader_url, params=rm_hst)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return nzo_id


def remove_from_queue(cfg: ConfigManager, nzo_id: str):
    try:
        rm_q = {
            "apikey": cfg.downloader_apikey,
            "mode": "queue",
            "name": "delete",
            "value": ",".join([nzo_id] if isinstance(nzo_id, str) else nzo_id),
            "output": "json",
        }
        resp = httpx.get(cfg.downloader_url, params=rm_q)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not queue item from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return nzo_id


def get_queue(cfg: ConfigManager):
    try:
        get_q = {
            "apikey": cfg.downloader_apikey,
            "mode": "queue",
            "output": "json",
        }
        resp = httpx.get(cfg.downloader_url, params=get_q)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    return data["queue"]["slots"]
