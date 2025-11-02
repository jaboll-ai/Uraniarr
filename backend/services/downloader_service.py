from backend.exceptions import NzbsError
import httpx
from backend.config import ConfigManager

async def download(nzb : bytes, cfg: ConfigManager, nzbname: str):
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
        async with httpx.AsyncClient() as client:
            resp = await client.post(cfg.downloader_url, params=params, data=data, files=files)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not queue item for SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    try:
        return resp.json()["nzo_ids"]
    except Exception as e:
        print(e, resp.text)
        raise NzbsError(status_code=500, detail="Could not queue item for SABnzbd. Internal Error") 

async def get_config(cfg: ConfigManager, section: str, keyword: str = None) -> dict:
    try:
        get_cfg ={
            "apikey": cfg.downloader_apikey,
            "mode": "get_config",
            "section": section,
            "output": "json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(cfg.downloader_url, params=get_cfg, timeout=10.0)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get config from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    parsed = resp.json()
    if keyword:
        return parsed["config"][section][keyword]
    return parsed["config"][section]

async def get_history(cfg: ConfigManager):
    try:
        get_hst = {
            "apikey": cfg.downloader_apikey,
            "mode":"history",
            "output":"json"
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(cfg.downloader_url, params=get_hst)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    data = resp.json()
    r = {item["nzo_id"] : {
        "percentage": 100,
        "name": item["name"],
        "status": item["status"],
        "storage": item["storage"]
    } for item in data["history"]["slots"]}
    return r

async def remove_from_history(cfg: ConfigManager, nzo_id: str):
    try:
        rm_hst = {
            "apikey": cfg.downloader_apikey,
            "mode": "history",
            "name": "delete",
            "value": ",".join([nzo_id] if isinstance(nzo_id, str) else nzo_id),
            "output": "json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(cfg.downloader_url, params=rm_hst)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return nzo_id


async def remove_from_queue(cfg: ConfigManager, nzo_id: str):
    try:
        rm_q = {
            "apikey": cfg.downloader_apikey,
            "mode": "queue",
            "name": "delete",
            "value": ",".join([nzo_id] if isinstance(nzo_id, str) else nzo_id),
            "output": "json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(cfg.downloader_url, params=rm_q)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not queue item from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    return nzo_id


async def get_queue(cfg: ConfigManager):
    try:
        get_q = {
            "apikey": cfg.downloader_apikey,
            "mode": "queue",
            "output": "json",
        }
        async with httpx.AsyncClient() as client:
            resp = await client.get(cfg.downloader_url, params=get_q)
    except Exception as e:
        raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?")
    if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail=resp.text)
    data = resp.json()
    r = {item["nzo_id"] : {
        "percentage": item["percentage"],
        "name": item["filename"],
        "status": item["status"]
    } for item in data["queue"]["slots"]}
    return r
