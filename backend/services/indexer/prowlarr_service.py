import httpx
from backend.services.indexer.base_indexer import BaseIndexer
from backend.exceptions import IndexerError

class ProwlarrService(BaseIndexer):
    async def search(self, q, cfg, audio):
        params = {
            "query": q,
            "categories": cfg.indexer_audio_category if audio else cfg.indexer_book_category,
            "type": "search",
            "apikey": cfg.indexer_apikey,
            "limit": 100,
            "offset": 0
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(cfg.indexer_url.rstrip("/")+"/v1/search", params=params)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail=response.text)
        response.encoding = 'utf-8'
        if "error" in response.text: raise IndexerError(status_code=403, detail=response.text)
        data = response.json()
        return data
    
    async def grab(self, download, cfg):
        async with httpx.AsyncClient() as client:
            response = await client.get(download, follow_redirects=True)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail=response.text)
        response.encoding = 'utf-8'
        if "error" in response.text: raise IndexerError(status_code=403, detail=response.text)
        return response.content
    

    async def query_manual(self, book, page, cfg, audio):
        base_queries = self.build_queries(book)
        data = await self.search(base_queries[page], cfg=cfg, audio=audio)
        try:
            response = [{
                "name": item["title"],
                "guid": item["guid"].split("/")[-1],
                "size": item["size"],
                "download": item["downloadUrl"]
            } for item in data]
        except KeyError as e:
            raise IndexerError(status_code=500, detail=f"Ran into a key error. Are we pointing to prowlarr or newznab?\nFurther info: {e}")
        return { "query": base_queries[page], "nzbs": response , "pages": len(base_queries) }


    async def query_book(self, book, cfg, audio):
        try:
            base_queries = self.build_queries(book)
            for q in base_queries: #TODO
                data = await self.search(q, cfg=cfg, audio=audio)
                if len(data) != 0: break
            else: return None, None
            item = data[0]
            name = item["title"]
            guid = item["guid"]
            download = item["downloadUrl"]
        except KeyError as e:
            raise IndexerError(status_code=500, detail=f"Ran into a key error. Are we pointing to prowlarr or newznab?\nFurther info: {e}")
        return name, guid, download

