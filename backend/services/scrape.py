import re
import asyncio
from backend.dependencies import get_logger
from backend.services.request import fetch_or_cached
from bs4 import BeautifulSoup
from io import BytesIO
import json
from backend.config import ConfigManager
import os

base = os.getenv("VENDOR")
book="/api/2003/artikel/v4/"
series="/api/2003/serienartikel/v4/"
author="/autor/-"
suche = "/api/rest/suche/v5"

async def scrape_search(q: str, cfg: ConfigManager, page: int = 1):
    params = {
        "suchbegriff": q,
        "artikelProSeite": "5",
        "seite": page,
        "filterSPRACHE": get_language(cfg),
    }
    data = await fetch_or_cached(cfg, base+suche, params=params)
    data = json.load(BytesIO(data))
    author_datas = set()
    for artikel in data["artikelliste"]:
        for personen in artikel.get("personen", []):
            if personen["typ"] == "Autor":
                author_datas.add((str(personen["identNr"]), personen.get("name")))
    coros = [scrape_author_data(identNr, cfg, name, metadata_only=True) for identNr, name in author_datas] # TODO LOGGGG
    ids = await asyncio.gather(*coros)
    return [id_ for id_ in ids if id_ is not None]

async def scrape_book_editions(book_id: str, cfg)-> tuple[list[dict], str]:
    data = await fetch_or_cached(cfg, base+book+book_id)
    data = json.load(BytesIO(data))[0]
    editions = []
    series_name = None
    for k in data["kategoriePfade"]:
        for j in k:
            if j["text"] == "Bundles":
                return editions, series_name
    for werk in data.get("werkArtikel", [data]):
        if werk["shop"]["identNr"] == 54: continue
        ed_info = {}
        ed_info["key"] = werk["ID"]["matnr"]
        ed_info["titel"] = werk["titel"]
        ed_info["bild"] = werk["media"]["bilder"][0]["urlTemplateFixedScaling"].format(resolutionKey="00")
        ed_info["medium"] = werk["shop"]["identNr"]
        if data["serie"]["hatSerienslider"] or data["serie"].get("nummer") or data["serie"].get("name"):
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
    get_logger().log(5, f"Found {len(editions)} editions for {book_id}")
    return editions, series_name

async def scrape_author_data(author_id: str, cfg: ConfigManager, name:str=None, metadata_only: bool = False):
    author_data={}
    author_data["key"] = author_id
    data = await fetch_or_cached(cfg, base+author+author_id, xhr=False)
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
        "filterSPRACHE": get_language(cfg),
        "sortierung": "Erscheinungsdatum_asc"
    }
    _data = await fetch_or_cached(cfg, base+suche+"/mehr-von-autor", params)
    data = json.load(BytesIO(_data))
    coros = []
    for i in range(2, data["paginierung"]["anzahlSeiten"]+1):
        coros.append(fetch_or_cached(cfg, base+suche+"/mehr-von-autor", {**params, "seite": i}))
    datas = [_data] + await asyncio.gather(*coros)
    for data in datas:
        data = json.load(BytesIO(data))
        for artikel in data["artikelliste"]:
            author_data["_books"].add(artikel["identifier"]["matnr"])
    get_logger().log(5, f"Found {len(author_data['_books'])} books for {author_data['name']}")
    return author_data

async def scrape_all_author_data(author_id: str, cfg: ConfigManager, name: str) -> dict:
    author_data = await scrape_author_data(author_id, cfg, name=name)
    coros = [scrape_book_editions(book_edition_id, cfg) for book_edition_id in author_data.get("_books", set())]
    books = await asyncio.gather(*coros)
    return {"author_data": author_data, "books": books}

async def scrape_book_series(book_id: str, cfg: ConfigManager):
    books = []
    params = {"max": 50, "page": 1}
    _data = await fetch_or_cached(cfg, base+series+book_id, params)
    data = json.load(BytesIO(_data))
    coros = []
    for i in range(2, data["totalPages"]+1):
        coros.append(fetch_or_cached(cfg, base+series+book_id, {**params, "page": i}))
    datas = [_data] + await asyncio.gather(*coros)
    for d in datas:
        d = json.load(BytesIO(d))
        for werk in d["sliderArtikelList"]:
            book_info = {}
            book_info["key"] = werk["ID"]["matnr"]
            book_info["titel"] = clean_title(werk["titel"], werk["serie"].get("name"), werk["serie"].get("nummer"))
            book_info["bild"] = werk["media"]["bilder"][0]["urlTemplateFixedScaling"].format(resolutionKey="00")
            book_info["medium"] = werk["shop"]["identNr"]
            is_bndl = False
            for bndl in cfg.known_bundles.split(","):
                is_bndl = is_bndl or re.search(bndl, werk["titel"]) is not None
            if not is_bndl:
                try:
                    book_info["_pos"] = float(werk["serie"].get("nummer"))
                except Exception:
                    book_info["_pos"] = None
            books.append(book_info)
    return books

def get_language(cfg: ConfigManager):
    mapping = lang_map = {
        "en": 1, "eng": 1,
        "de": 3, "deu": 3, "ger": 3,
        "fr": 2, "fra": 2, "fre": 2,
        "es": 84, "spa": 84,
        "it": 88, "ita": 88,
        "tr": 975, "tur": 975,
        "pt": 981, "por": 981,
        "fi": 985, "fin": 985,
        "nl": 90, "nld": 90, "dut": 90,
        "pl": 83, "pol": 83,
        "ru": 5, "rus": 5,
        "ar": 982, "ara": 982,
        "hu": 987, "hun": 987,
        "ca": 984, "cat": 984,
        "sv": 91, "swe": 91,
        "hr": 1021, "hrv": 1021,
        "hi": 81, "hin": 81,
        "el": 980, "ell": 980, "gre": 980,
        "uk": 1016, "ukr": 1016,
        "vi": 976, "vie": 976,
        "zh": 7, "zho": 7, "chi": 7
    }
    return mapping.get(cfg.language, 3)

def strip_id(url: str):
    return url.strip("/").split("/")[-1].split("?")[0]
def strip_id_from_slug(url: str):
    return url.strip("/").split("/")[-1].split("?")[0].split("-")[-1]

def clean_title(title: str, series_title: str = None, series_pos: int = None, can_be_empty: bool = False):
    bak = title

    title = fix_diaeresis(title)
    if series_title:
        title = re.sub(fr"\b(?:(?:der)|(?:die)|(?:das)|)\W*{re.escape(series_title)}\W", "", title, flags=re.UNICODE | re.I)
    if series_title and title == bak:
        title = re.sub(fr"\b(?:(?:der)|(?:die)|(?:das)|)\W*{re.escape(series_title.replace('-', ' '))}\W", "", title, flags=re.UNICODE | re.I)

    try:
        series_pos = int(float(series_pos))
    except Exception:
        series_pos = None
    title = re.sub(r"\(.*kürz.*\)", "", title, re.I) # remove (gekürzte Lesung) and alike
    title = strip_non_word(title)
    title = re.sub(fr"^(?:(?:b(?:(?:an)|)d)|(?:teil)|(?:folge)|(?:buch)|)\W*0*{series_pos}", "", title, flags=re.UNICODE | re.I)# remove leading position
    title = re.sub(fr"(?:(?:b(?:(?:an)|)d)|(?:teil)|(?:folge)|(?:buch)|)\W*0*{series_pos}$", "", title, flags=re.UNICODE | re.I)# remove traling position
    #### Known patterns ####
    title = title.replace(" - , Teil", "")
    ########################
    title = strip_non_word(title)
    title = reconstruct_parentheses(title)
    if can_be_empty:
        return title
    return title or bak.strip() # sanity check dont return empty string

def clean_series_title(title: str):
    bak = title
    #### Known patterns ####
    title = title.replace("Weitere Bände von ", "")
    ########################
    title = fix_diaeresis(title)
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

def fix_diaeresis(title: str):
    title = title.replace("a¨", "ä")
    title = title.replace("o¨", "ö")
    title = title.replace("u¨", "ü")
    title = title.replace("A¨", "Ä")
    title = title.replace("O¨", "Ö")
    title = title.replace("U¨", "Ü")
    return title

def strip_non_word(text: str):
    text = re.sub(r"^[\W]*", "", text, flags=re.UNICODE | re.M)
    return re.sub(r"[\W]*$", "", text, flags=re.UNICODE | re.M)

def strip_pos(text: str):
    return re.sub(r"(?:(?:b(?:(?:an)|)d)|(?:teil)|(?:folge)|(?:buch)|)\W*\d+\W*-*\W*", "", text, flags=re.UNICODE | re.I)

def fix_umlaut(text: str) -> str:
    text = re.sub(r"ä", "ae", text, flags=re.IGNORECASE)
    text = re.sub(r"ö", "oe", text, flags=re.IGNORECASE)
    text = re.sub(r"ü", "ue", text, flags=re.IGNORECASE)
    text = re.sub(r"ß", "ss", text, flags=re.IGNORECASE)
    return text

def has_umlaut(text: str) -> bool:
    regex = r"[äöüß]"
    return bool(re.search(regex, text, flags=re.IGNORECASE))

