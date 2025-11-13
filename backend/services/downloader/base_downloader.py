from abc import ABC, abstractmethod
from backend.config import ConfigManager

class BaseDownloader(ABC):

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