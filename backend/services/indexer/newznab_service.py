from backend.exceptions import IndexerError
from backend.services.indexer.base_indexer import BaseIndexer
import httpx
from time import time
import asyncio

class NewznabService(BaseIndexer):
    async def search(self, q, cfg, audio):
        if (timeout:=time() - self.last_hit) < cfg.indexer_timeout:
            await asyncio.sleep(cfg.indexer_timeout - timeout)
        self.last_hit = time()
        search = {
            "t": "search",
            "cat":cfg.indexer_audio_category if audio else cfg.indexer_book_category,
            "o" : "json",
            "q": q,
            "apikey": cfg.indexer_apikey
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(cfg.indexer_url, params=search)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail=response.text)
        response.encoding = 'utf-8'
        if "error" in response.text: raise IndexerError(status_code=403, detail=response.text)
        data = response.json()
        return data
    
    async def grab(self, download, cfg):
        if (timeout:=time() - self.last_hit) < cfg.indexer_timeout: 
            await asyncio.sleep(cfg.indexer_timeout - timeout)
        self.last_hit = time()
        get = {
            "t": "get",
            "id": download,
            "o" : "json",
            "apikey": cfg.indexer_apikey
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(cfg.indexer_url, params=get, follow_redirects=True)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail=response.text)
        response.encoding = 'utf-8'
        if "error" in response.text: raise IndexerError(status_code=403, detail=response.text)
        return response.content

    async def query_manual(self, book, page, cfg, audio):
        try:
            base_queries = self.build_queries(book)
            data = await self.search(base_queries[page], cfg=cfg, audio=audio)
            query = data["channel"]
            if (total:=query["response"]["@attributes"]["total"]) == "0":
                return { "query": base_queries[page], "nzbs": [], "pages": len(base_queries)}
            items = [query["item"]] if total == "1" else query["item"]
            response = []
            for item in items:
                i = {"name": item["title"]}
                for attribute in item["attr"]:
                    if attribute["@attributes"]["name"] == "guid":
                        i["guid"] = attribute["@attributes"]["value"]
                        i["download"] = i["guid"]
                    elif attribute["@attributes"]["name"] == "size":
                        i["size"] = attribute["@attributes"]["value"]
                response.append(i)
        except KeyError as e:
            raise IndexerError(status_code=500, detail=f"Ran into a key error. Are we pointing to prowlarr or newznab\n Further info: {e}")
        return { "query": base_queries[page], "nzbs": response , "pages": len(base_queries) }
        # for autor, name in base_queries:
        #     used_term = f"{autor} {name}"
        #     data = indexer_search(used_term, cfg=cfg)
        #     query = data["channel"]
        #     if (total:=query["response"]["@attributes"]["total"]) != "0":
        #         break
        # else: return { "query": used_term, "nzbs": [] }

    async def query_book(self, book, cfg, audio):
        try:
            base_queries = await self.build_queries(book)
            for q in base_queries: #TODO
                data = await self.search(q, cfg=cfg, audio=audio)
                query = data["channel"]
                if (total:=query["response"]["@attributes"]["total"]) != "0":
                    break
            else: return None, None
            item = query["item"] if total == "1" else query["item"][0]
            name = item["title"]
            for attribute in item["attr"]:
                if attribute["@attributes"]["name"] == "guid":
                    guid = attribute["@attributes"]["value"]
        except KeyError as e:
            raise IndexerError(status_code=500, detail=f"Ran into a key error. Are we pointing to prowlarr or newznab?\nFurther info: {e}")
        return name, guid, guid

