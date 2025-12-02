import httpx
from backend.dependencies import get_logger, get_scorer
from backend.services.indexer.base_indexer import BaseIndexer
from backend.exceptions import IndexerError

class ProwlarrService(BaseIndexer):
    async def search(self, q, cfg, audio):
        params = {
            "query": q,
            "categories": self.audio_categories if audio else self.book_categories,
            "type": "search",
            "apikey": self.apikey,
            "limit": 100,
            "offset": 0
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.url+"/v1/search", params=params)
        except httpx.ConnectError as e:
            raise IndexerError(status_code=404, detail="Could not connect to indexer", exception=e)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail="Could not connect to prowlarr", exception=response.text)
        response.encoding = 'utf-8'
        if "error" in response.text: raise IndexerError(status_code=403, detail="Could not connect to prowlarr", exception=response.text)
        data = response.json()
        return data

    async def grab(self, download, cfg):
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(download, follow_redirects=True)
        except httpx.ConnectError as e:
            raise IndexerError(status_code=404, detail="Could not connect to indexer", exception=e)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code,detail="Could not connect to prowlarr", exception=response.text)
        response.encoding = 'utf-8'
        if "error" in response.text: raise IndexerError(status_code=403, detail="Could not connect to prowlarr", exception=response.text)
        return response.content


    async def query_manual(self, book, page, cfg, audio):
        base_queries = self.build_queries(book)
        data = await self.search(base_queries[page], cfg=cfg, audio=audio)
        try:
            response = [{
                "name": item["title"],
                "guid": item["guid"].split("/")[-1],
                "size": item["size"],
                "download": item["downloadUrl"],
                "i_idx": self.i_idx
            } for item in data]
        except KeyError as e:
            raise IndexerError(status_code=500, detail="Ran into a key error. Are we pointing to prowlarr or newznab?", exception=e)
        return { "query": base_queries[page], "nzbs": response , "pages": len(base_queries) }


    async def query_book(self, book, cfg, audio):
        try:
            base_queries = self.build_queries(book)
            for q in base_queries: #TODO
                data = await self.search(q, cfg=cfg, audio=audio)
                if len(data) == 0: continue
                for item in data:
                    ratio = get_scorer()(book.name, item["title"])
                    get_logger().log(5, f"Testing {item['title']} == {book.name}. {ratio=}")
                    if ratio > cfg.name_ratio: break
                else:
                    continue
                break
            else:
                get_logger().info(f"Could not find a match for {book.name}, try raising your name ratio in the settings.")
                return None, None, None
            name = item["title"]
            guid = item["guid"]
            download = item["downloadUrl"]
        except KeyError as e:
            raise IndexerError(status_code=500, detail="Ran into a key error. Are we pointing to prowlarr or newznab?", exception=e)
        return name, guid, download

