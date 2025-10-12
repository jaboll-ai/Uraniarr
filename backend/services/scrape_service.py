import re
import asyncio
from backend.services.request_service import fetch_or_cached
from bs4 import BeautifulSoup
from io import BytesIO
import json
from backend.config import ConfigManager

base="***REMOVED***"
book="/api/2003/artikel/v4/"
series="/api/2003/serienartikel/v4/"
author="/autor/-"
suche = "/api/rest/suche/v5"

async def scrape_search(q: str, page: int = 1):
    params = {
        "suchbegriff": q,
        "artikelProSeite": "5",
        "seite": page,
        "filterSPRACHE": "3"
    }
    data = await fetch_or_cached(base+suche, params=params)
    data = json.load(BytesIO(data))
    author_datas = set()
    for artikel in data["artikelliste"]:
        for personen in artikel["personen"]:
            if personen["typ"] == "Autor":
                author_datas.add((str(personen["identNr"]), personen.get("name")))
    coros = [scrape_author_data(identNr, name, metadata_only=True) for identNr, name in author_datas] # TODO LOGGGG
    ids = await asyncio.gather(*coros)
    return [id_ for id_ in ids if id_ is not None]


async def scrape_author_id_from_book(book_id: str):
    soup = await fetch_or_cached(base+book+book_id, xhr=False)
    if (a:=soup.find(class_="autor-name")) and (href:=a.get("href")):
            return strip_id_from_slug(href)
            
async def scrape_book_editions(book_id: str)-> tuple[list[dict], str]:
    data = await fetch_or_cached(base+book+book_id)
    data = json.load(BytesIO(data))[0]
    editions = []
    series_name = None
    for werk in data.get("werkArtikel", [data]):
        if werk["shop"]["identNr"] == 54: continue
        ed_info = {}
        ed_info["key"] = werk["ID"]["matnr"]
        ed_info["titel"] = werk["titel"]
        ed_info["bild"] = werk["media"]["bilder"][0]["urlTemplateFixedScaling"].format(resolutionKey="00")
        ed_info["medium"] = werk["shop"]["identNr"]
        if data["serie"]["hatSerienslider"] or data["serie"].get("nummer") or data["serie"].get("name"):
            cfg = ConfigManager()
            is_bndl = False
            for bndl in cfg.known_bundles.split(","):
                is_bndl = is_bndl or re.search(bndl, werk["titel"]) is not None
            if not is_bndl: # we only assign pos if not a bundle #TODO
                try:
                    ed_info["_pos"] = float(data["serie"].get("nummer"))
                except Exception:
                    ed_info["_pos"] = None
            if not series_name:
                series_name = clean_series_title(data["serie"].get("name"))
        editions.append(ed_info)
    return editions, series_name

async def scrape_author_data(author_id: str, name:str=None, metadata_only: bool = False):
    author_data={}
    author_data["key"] = author_id
    data = await fetch_or_cached(base+author+author_id, xhr=False)
    soup = await asyncio.to_thread(BeautifulSoup, data, "html.parser")
    if (avatar:=soup.find(class_="autor-avatar")) and (img:=avatar.find("img")):
        author_data["bild"] = img.get("src")
    if name:
        author_data["name"] = name
    elif (name:=soup.find(class_="autor-name")):
        author_data["name"] = name.get_text(strip=True)
    if (bio_container := soup.find(class_="autor-portrait")):
        if (bio_div := bio_container.find("div", class_="toggle-text-content")):
            author_data["bio"] = bio_div.get_text().strip()
    if metadata_only: 
        if author_data.get("name") is None:
            return
        return author_data
    author_data["_books"] = set()
    params = {
        "suchbegriff": author_data["name"],
        "artikelProSeite": "30",
        "seite": 1,
        "filterSPRACHE": "3",
        "sortierung": "Erscheinungsdatum_asc"
    }
    _data = await fetch_or_cached(base+suche+"/mehr-von-autor", params)
    data = json.load(BytesIO(_data))
    coros = []
    for i in range(2, data["paginierung"]["anzahlSeiten"]+1):
        coros.append(fetch_or_cached(base+suche+"/mehr-von-autor", {**params, "seite": i}))
    datas = [_data] + await asyncio.gather(*coros)
    for data in datas:
        data = json.load(BytesIO(data))
        for artikel in data["artikelliste"]:
            author_data["_books"].add(artikel["identifier"]["matnr"])
    return author_data

async def scrape_all_author_data(author_id: str) -> dict:
    author_data = await scrape_author_data(author_id)
    coros = [scrape_book_editions(book_edition_id) for book_edition_id in author_data.get("_books", set())]
    books = await asyncio.gather(*coros)
    return {"author_data": author_data, "books": books}

async def scrape_book_series(book_id: str):
    books = []
    params = {"max": 50, "page": 1}
    _data = await fetch_or_cached(base+series+book_id, params)
    data = json.load(BytesIO(_data))
    coros = []
    for i in range(2, data["totalPages"]+1):
        coros.append(fetch_or_cached(base+series+book_id, {**params, "page": i}))
    datas = [_data] + await asyncio.gather(*coros)
    for d in datas:
        d = json.load(BytesIO(d))
        for werk in d["sliderArtikelList"]:
            book_info = {}
            book_info["key"] = werk["ID"]["matnr"]
            book_info["titel"] = clean_title(werk["titel"], werk["serie"].get("name"), werk["serie"].get("nummer"))
            book_info["bild"] = werk["media"]["bilder"][0]["urlTemplateFixedScaling"].format(resolutionKey="00")
            book_info["medium"] = werk["shop"]["identNr"]
            cfg = ConfigManager()
            is_bndl = False
            for bndl in cfg.known_bundles.split(","):
                is_bndl = is_bndl or re.search(bndl, werk["titel"]) is not None
            if not is_bndl:
                try:
                    book_info["_pos"] = float(werk["serie"].get("nummer"))
                except Exception:
                    book_info["_pos"] = None
            books.append(book_info)
    print()
    return books

def strip_id(url: str):
    return url.strip("/").split("/")[-1].split("?")[0]
def strip_id_from_slug(url: str):
    return url.strip("/").split("/")[-1].split("?")[0].split("-")[-1]

def clean_title(title: str, series_title: str = None, series_pos: int = None):
    bak = title
    if series_title:
        title = re.sub(fr"\b{re.escape(series_title)}\W", "", title)
    if series_title and title == bak:
        title = re.sub(fr"\b{re.escape(series_title.replace('-', ' '))}\W", "", title)

    try:
        series_pos = round(float(series_pos))
    except Exception:
        series_pos = None
    title = re.sub(r"\(.*kürz.*\)", "", title, re.I) # remove (gekürzte Lesung) and alike
    title = strip_non_word(title)
    title = re.sub(fr"^(?:(?:b(?:(?:an)|)d)|(?:teil)|(?:folge)|)\W*0*{series_pos}", "", title, flags=re.UNICODE | re.I)# remove leading position
    title = re.sub(fr"(?:(?:b(?:(?:an)|)d)|(?:teil)|(?:folge)|)\W*0*{series_pos}$", "", title, flags=re.UNICODE | re.I)# remove traling position
    #### Known patterns ####
    title = title.replace(" - , Teil", "")
    ########################
    title = strip_non_word(title)
    title = reconstruct_parentheses(title)
    return title or bak.strip() # sanity check dont return empty string

def clean_series_title(title: str):
    bak = title
    #### Known patterns ####
    title = title.replace("Weitere Bände von ", "")
    ########################
    title = strip_non_word(title)
    title = re.sub(r"^Die", "", title, flags=re.UNICODE | re.M)
    title = re.sub(r"-*Reihe$", "", title, flags=re.UNICODE | re.M)
    title = re.sub(r"-*Serie$", "", title, flags=re.UNICODE | re.M)
    title = strip_non_word(title)
    title = reconstruct_parentheses(title)
    return title or bak.strip()

def reconstruct_parentheses(title: str):
    stack = []
    bracket_pairs = {'(': ')', '[': ']', '{': '}'}
    closing = set(bracket_pairs.values())
    for char in title:
        if char in bracket_pairs:
            stack.append(bracket_pairs[char])
        elif char in closing and stack and char == stack[-1]:
            stack.pop()
    while stack:
        title += stack.pop()
    return title

def strip_non_word(text: str):
    text = re.sub(r"^[\W]*", "", text, flags=re.UNICODE | re.M)
    return re.sub(r"[\W]*$", "", text, flags=re.UNICODE | re.M)

def fix_umlaut(text: str) -> str:
    text = re.sub(r"ä", "ae", text, flags=re.IGNORECASE)
    text = re.sub(r"ö", "oe", text, flags=re.IGNORECASE)
    text = re.sub(r"ü", "ue", text, flags=re.IGNORECASE)
    text = re.sub(r"ß", "ss", text, flags=re.IGNORECASE)
    return text

