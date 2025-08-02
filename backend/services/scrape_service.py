import re
import asyncio
from backend.services.request_service import fetch_or_cached
from bs4 import BeautifulSoup
from io import BytesIO
import json

base="https://www.thalia.de"
book="/api/2003/artikel/v4/"
series="/api/2003/serienartikel/v4/"
author="/autor/-"
author_books="/include/suche/personenportrait/v1/backliste/"


async def scrape_search(q: str, page: int = 1):
    url = "/api/rest/suche/v5"
    params = {
        "suchbegriff": q,
        "artikelProSeite": "5",
        "seite": page,
        "filterSPRACHE": "3"
    }
    data = await fetch_or_cached(base+url, params=params)
    print(data)
    data = json.load(BytesIO(data))
    author_datas = set()
    for artikel in data["artikelliste"]:
        for personen in artikel["personen"]:
            if personen["typ"] == "Autor":
                author_datas.add(str(personen["identNr"]))
    return [await scrape_author_data(identNr, metadata_only=True) for identNr in author_datas]


async def scrape_author_id_from_book(book_id: str):
    soup = await fetch_or_cached(base+book+book_id)
    if (a:=soup.find(class_="autor-name")) and (href:=a.get("href")):
            return strip_id_from_slug(href)
            
async def scrape_book_editions(book_id: str)-> tuple[list[dict], str]:
    data = await fetch_or_cached(base+book+book_id)
    data = json.load(BytesIO(data))[0]
    editions = []
    series = None
    for werk in data["werkArtikel"]:
        ed_info = {}
        ed_info["key"] = werk["ID"]["matnr"]
        ed_info["titel"] = werk["titel"]
        ed_info["bild"] = werk["media"]["bilder"][0]["migrationUrlTemplateFixedScaling"].format(resolutionKey="00")
        ed_info["medium"] = werk["shop"]["identNr"]
        if data["serie"]["hatSerienslider"]:
            ed_info["_pos"] = data["serie"]["nummer"]
            if not series:
                series = clean_series_title(data["serie"]["name"])
        editions.append(ed_info)
    return editions, series

async def scrape_author_data(author_id: str, metadata_only: bool = False):
    author_data={}
    author_data["key"] = author_id
    data = await fetch_or_cached(base+author+author_id)
    soup = await asyncio.to_thread(BeautifulSoup, data, "html.parser")
    if (avatar:=soup.find(class_="autor-avatar")) and (img:=avatar.find("img")):
        author_data["bild"] = img.get("src")
    if (name:=soup.find(class_="autor-name")):
        author_data["name"] = name.get_text(strip=True)
    if (bio_container := soup.find(class_="autor-portrait")):
        if (bio_div := bio_container.find("div", class_="toggle-text-content")):
            author_data["bio"] = bio_div.get_text().strip()
    if metadata_only: return author_data
    #pagesize max 48
    #page: p
    # sort top beweretung : sfsd
    # presi aufsteigend sfpa
    # preis absteigend sfpd
    # erscheinung aufsteigend sfea
    # erscheinung absteigend sfed
    # bester treffer sfmd
    # deutsch filterSPRACHE=3
    author_data["_books"] = set()
    params = {
        "p": 1,
        "pagesize": 48,
        "filterSPRACHE": 3,
        "sort": "sfea"
    }
    while True:
        data = await fetch_or_cached(base+author_books+author_id, params=params)
        books_soup = await asyncio.to_thread(BeautifulSoup, data, "html.parser")
        if books_soup.find("suche-keine-treffer"): break
        for li in books_soup.find_all("li"):
            for a in li.find_all("a"):
                author_data["_books"].add(strip_id(a["href"]))
        params["p"] += 1
    return author_data

async def scrape_all_author_data(author_id: str) -> dict:
    author_data = await scrape_author_data(author_id)
    coros = [scrape_book_editions(book_edition_id) for book_edition_id in author_data.get("_books", set())]
    books = await asyncio.gather(*coros)
    return {"author_data": author_data, "books": books}

async def scrape_book_series(book_id: str):
    books = {}
    params = {"max": 50, "page": 1}
    data = await fetch_or_cached(base+series+book_id, params)
    data = json.load(BytesIO(data))
    for i in range(data["totalPages"]):
        for book in data["sliderArtikelList"]:
            pass
        params["page"] = i+1
    params["page"] += 1
    return books

def strip_id(url: str):
    return url.strip("/").split("/")[-1].split("?")[0]
def strip_id_from_slug(url: str):
    return url.strip("/").split("/")[-1].split("?")[0].split("-")[-1]

def clean_title(title: str, series_title: str = None, series_pos: int = None):
    bak = title
    if series_title:
        title = title.replace(series_title, "")
    if series_title and title == bak:
        title = title.replace(series_title.replace("-", " "), "")
    
    series_pos = series_pos or ""
    title = strip_non_word(title)
    title = re.sub(fr"^(?:(?:b(?:(?:an)|)d)|(?:teil)|(?:folge)|)\W*0*{series_pos}", "", title, flags=re.UNICODE | re.I)# remove leading position
    title = re.sub(fr"(?:(?:b(?:(?:an)|)d)|(?:teil)|)\W*0*{series_pos}$", "", title, flags=re.UNICODE | re.I)# remove traling position
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

