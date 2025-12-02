from io import BytesIO
from urllib.parse import urlencode
from backend.dependencies import get_logger, get_scorer
from backend.exceptions import IndexerError
from backend.services.indexer.base_indexer import BaseIndexer
import xml.etree.ElementTree as ET
import httpx
from time import time
import asyncio

class NewznabService(BaseIndexer):
    async def search(self, q, cfg, audio):
        if (timeout:=time() - self.last_hit) < cfg.indexer_timeout:
            get_logger().log(5, f"Sleeping {cfg.indexer_timeout - timeout} seconds")
            await asyncio.sleep(cfg.indexer_timeout - timeout)
        self.last_hit = time()
        search = {
            "t": "search",
            "cat": self.audio_categories if audio else self.book_categories,
            "q": q,
            "apikey": self.apikey
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.url, params=search)
        except httpx.ConnectError as e:
            raise IndexerError(status_code=404, detail="Could not connect to indexer", exception=e)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail="Could not connect to indexer", exception=response.text)
        if "error" in response.text: raise IndexerError(status_code=403, detail="Could not connect to indexer", exception=response.text)
        data = response.content
        return data

    async def grab(self, download, cfg):
        if (timeout:=time() - self.last_hit) < cfg.indexer_timeout:
            await asyncio.sleep(cfg.indexer_timeout - timeout)
        self.last_hit = time()
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(download, follow_redirects=True)
        except Exception as e:
            raise IndexerError(status_code=404, detail="Could not connect to indexer", exception=e)
        if response.status_code != 200: raise IndexerError(status_code=response.status_code, detail="Could not connect to indexer", exception=response.text)
        if "error" in response.text: raise IndexerError(status_code=403, detail="Could not connect to indexer", exception=response.text)
        return response.content

    async def query_manual(self, book, page, cfg, audio):
        try:
            base_queries = self.build_queries(book)
            data = await self.search(base_queries[page], cfg=cfg, audio=audio)
            ns = {}
            for event, (prefix, uri) in ET.iterparse(BytesIO(data), events=("start-ns",)):
                ns[prefix] = uri
            data = ET.parse(BytesIO(data))
            if (resp:=data.find(".//newznab:response", ns)) is None or resp.attrib["total"] == "0":
                return { "query": base_queries[page], "nzbs": [], "pages": len(base_queries)}
            response = []
            for item in data.findall(".//item"):
                i = {"name": item.find("title").text, "i_idx": self.i_idx, "download": item.find("link").text}
                for attribute in item.findall("newznab:attr", ns):
                    if attribute.attrib["name"] == "guid":
                        i["guid"] = attribute.attrib["value"]
                    elif attribute.attrib["name"] == "size":
                        i["size"] = attribute.attrib["value"]
                response.append(i)
        except KeyError as e:
            raise IndexerError(status_code=500, detail="Ran into a key error. Are we pointing to prowlarr or newznab?", exception=e)
        return { "query": base_queries[page], "nzbs": response , "pages": len(base_queries) }

    async def query_book(self, book, cfg, audio):
        try:
            base_queries = self.build_queries(book)
            for q in base_queries: #TODO
                data = await self.search(q, cfg=cfg, audio=audio)
                ns = {}
                for event, (prefix, uri) in ET.iterparse(BytesIO(data), events=("start-ns",)):
                    ns[prefix] = uri
                data = ET.parse(BytesIO(data))
                if (resp:=data.find(".//newznab:response", ns)) is None or resp.attrib["total"] == "0":
                    continue
                items = data.findall(".//item")
                for item in items:
                    ratio = get_scorer()(book.name, item.find("title").text)
                    get_logger().log(5, f"Testing {item.find('title').text} == {book.name}. {ratio=}")
                    if ratio > cfg.name_ratio: break
                else:
                    continue
                break
            else:
                get_logger().info(f"Could not find a match for {book.name}, try raising your name ratio in the settings.")
                return None, None, None
            name = item.find("title").text
            guid = None
            download = item.find("link").text
            for attribute in item.findall("newznab:attr", ns):
                if attribute.attrib["name"] == "guid":
                    guid = attribute.attrib["value"]
                    break
        except KeyError as e:
            raise IndexerError(status_code=500, detail=f"Ran into a key error. Are we pointing to prowlarr or newznab?", exception=e)
        get_logger().log(5, f"Found release {name} for {book.name}")
        return name, guid, download

