import asyncio
from backend.exceptions import NzbsError
import httpx
from backend.services.downloader.base_downloader import BaseDownloader
from pathlib import Path
from backend.dependencies import get_logger

class SABDownloader(BaseDownloader):
    async def download(self, nzb, cfg, nzbname):
        try:
            files = {
                "nzbfile": (f"{nzbname}.nzb", nzb, "application/x-nzb")
            }
            data = {
                "mode": "addfile",
                "nzbname": nzbname,
                "cat": cfg.downloader_category or "*",
            }
            params = {"apikey": cfg.downloader_apikey}
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.normalize(cfg.downloader_url), params=params, data=data, files=files)
        except Exception:
            raise NzbsError(status_code=404, detail="Could not queue item for SABnzbd. Is the service running?")
        if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail="Error from SABnzbd", exception=resp.text)
        try:
            return resp.json()["nzo_ids"]
        except Exception as e:
            get_logger().error(f"{e} {resp.text}")
            raise NzbsError(status_code=500, detail="Could not queue item for SABnzbd. Internal Error", exception=e)

    async def get_history(self, cfg):
        try:
            get_hst = {
                "apikey": cfg.downloader_apikey,
                "mode":"history",
                "output":"json"
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.normalize(cfg.downloader_url), params=get_hst)
        except Exception as e:
            raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?", exception=e)
        data = resp.json()
        r = {item["nzo_id"] : {
            "percentage": 100,
            "name": item["name"],
            "status": item["status"],
            "storage": item["storage"]
        } for item in data["history"]["slots"]}
        return r

    async def remove_from_history(self, cfg, nzo_id):
        try:
            rm_hst = {
                "apikey": cfg.downloader_apikey,
                "mode": "history",
                "name": "delete",
                "value": ",".join([nzo_id] if isinstance(nzo_id, str) else nzo_id),
                "output": "json",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.normalize(cfg.downloader_url), params=rm_hst)
        except Exception as e:
            raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?", exception=e)
        if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail="Error from SABnzbd", exception=resp.text)
        return nzo_id

    async def remove_from_queue(self, cfg, nzo_id):
        try:
            rm_q = {
                "apikey": cfg.downloader_apikey,
                "mode": "queue",
                "name": "delete",
                "value": ",".join([nzo_id] if isinstance(nzo_id, str) else nzo_id),
                "output": "json",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.normalize(cfg.downloader_url), params=rm_q)
        except Exception as e:
            raise NzbsError(status_code=404, detail="Could not queue item from SABnzbd. Is the service running?", exception=e)
        if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail="Error from SABnzbd", exception=resp.text)
        return nzo_id

    async def get_queue(self, cfg):
        try:
            get_q = {
                "apikey": cfg.downloader_apikey,
                "mode": "queue",
                "output": "json",
            }
            async with httpx.AsyncClient() as client:
                resp = await client.get(self.normalize(cfg.downloader_url), params=get_q)
        except Exception as e:
            raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?", exception=e)
        if resp.status_code != 200: raise NzbsError(status_code=resp.status_code, detail="Error from SABnzbd", exception=resp.text)
        data = resp.json()
        r = {item["nzo_id"] : {
            "percentage": item["percentage"],
            "name": item["filename"],
            "status": item["status"]
        } for item in data["queue"]["slots"]}
        return r

    async def get_cat_dir(self, cfg):
        p = {
            "apikey": cfg.downloader_apikey,
            "mode": "get_config",
        }
        try:
            async with httpx.AsyncClient() as client:
                coros = [client.get(self.normalize(cfg.downloader_url), params={**p, "section": s}) for s in ["misc", "categories"]]
                misc, categories = await asyncio.gather(*coros)
        except Exception as e:
            get_logger().debug(e)
            raise NzbsError(status_code=404, detail="Could not get history from SABnzbd. Is the service running?", exception=e)
        if misc.status_code != 200: raise NzbsError(status_code=misc.status_code, detail="Error from SABnzbd", exception=misc.text)
        if categories.status_code != 200: raise NzbsError(status_code=categories.status_code, detail="Error from SABnzbd", exception=categories.text)
        cat_folder = None
        base_folder = None
        try:
            for c in categories.json()["config"]["categories"]:
                if c["name"] == cfg.downloader_category:
                    cat_folder = c["dir"]
            base_folder = Path(misc.json()["config"]["misc"]["complete_dir"])
        except Exception as e:
            get_logger().debug(e)
            raise NzbsError(status_code=500, detail=f"Unexpected response from SABnzbd", exception=e)
        if base_folder is None or cat_folder is None: raise NzbsError(status_code=500, detail="Could not get SABnzbd category directory")
        return str(base_folder / cat_folder)

