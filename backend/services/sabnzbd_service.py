from backend.exceptions import NzbsError
import requests
from uuid import uuid4
from backend.config import ConfigManager

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