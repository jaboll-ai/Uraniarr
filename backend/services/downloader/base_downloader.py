from abc import ABC, abstractmethod
from backend.config import ConfigManager

class BaseDownloader(ABC):

    def __init__(self, dwn_cfg: dict, downloaderi_idx: int):
        self.last_hit = 0
        self.url = self.normalize(dwn_cfg["url"])
        self.apikey = dwn_cfg["apikey"].strip()
        self.download_category = dwn_cfg["download_categories"]
        self.i_idx = downloaderi_idx

    @abstractmethod
    async def download(self, nzb : bytes, cfg: ConfigManager, nzbname: str):
        pass

    @abstractmethod
    async def get_history(self, cfg: ConfigManager):
        pass

    @abstractmethod
    async def remove_from_history(self, cfg: ConfigManager, nzo_id: str|list[str]):
        pass

    @abstractmethod
    async def remove_from_queue(self, cfg: ConfigManager, nzo_id: str):
        pass

    @abstractmethod
    async def get_queue(self, cfg: ConfigManager):
        pass

    @abstractmethod
    async def get_cat_dir(self, cfg: ConfigManager):
        pass

    def normalize(self, url: str) -> str:
        url=url.rstrip("/")
        url=url.rstrip("/api") + "/api"
        return url