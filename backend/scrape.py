from bs4 import BeautifulSoup
import cloudscraper
import re
from pickle import dump, load
from time import time
from fastapi import HTTPException

base="***REMOVED***"
book="/shop/home/artikeldetails/"
series="/api/serienslider/v2/"
author="/autor/-"
author_books="/include/suche/personenportrait/v1/backliste/"

scraper = cloudscraper.create_scraper()
try: _cache = load(open("cache","rb"))
except FileNotFoundError: _cache = {}
hits = 0

def scrape_search(q: str, page: int = 1):
    url = "/suche"
    params = {
        "sq": q,
        "pagesize": "48",
        "p": page,
        "filterSPRACHE": "3",
        "ajax": "true"
    }
    soup = soup_or_cached(url, params=params)
    i = 0
    author_datas = {}
    for artikel in soup.find_all(class_="artikel"):
        if i >= 5: break
        if artikel.find(class_="autoren-wrapper"):
            if a:=artikel.find("a", class_="element-link-toplevel"):
                author_id=scrape_author_id_from_book(strip_id(a["href"]))
                i+=1
                if author_id in author_datas: continue
                data = scrape_author_data(author_id, metadata_only=True)
                if data.get("key") and data.get("name"): author_datas[author_id] = data
    return list(author_datas.values())


def scrape_author_id_from_book(book_id: str):
    soup = soup_or_cached(base+book+book_id)
    if (a:=soup.find(class_="autor-name")) and (href:=a.get("href")):
            return strip_author_id(href)
            
def scrape_book_editions(book_id: str):
    ed_ids = []
    soup = soup_or_cached(base+book+book_id)
    for a in soup.find_all(class_="layered-link"):
        ed_ids.append(strip_id(a["href"]))
     # just so we dont miss anything
    for ul in soup.find_all("ul",class_="optionen", attrs={'data-formattyp': 'format'}):
        for a in ul.find_all("a", class_="element-card-select formatkachel-link"):
            if not (e:=strip_id(a["href"])) in ed_ids: 
                ed_ids.append(e)
    if len(ed_ids) == 0:
        ed_ids = [book_id] # if the only edition is the one we are looking at
    series = clean_series_title(s) if (h2:=soup.find("h2", id="serien-slider")) and (s:=h2.find(string=True)) else None
    editions = []
    for e_id in ed_ids:
        ed_infos = {}
        e_soup = soup if e_id == book_id else soup_or_cached(base+book+e_id) #use cached soup for one api-hit less
        ed_infos["key"] = e_id
        if (t:=e_soup.find(class_="element-headline-medium titel")) and (titel:=t.find(string=True, recursive=False)):
            ed_infos["titel"] = titel.strip()
        if (a:=e_soup.find(class_="autor-name")) and (href:=a.get("href")):
            ed_infos["autor_key"] = strip_author_id(href)
        if (div:=e_soup.find(class_="artikelbild-container")) and (img:=div.find("img")): 
            ed_infos[f"bild"] = img.get("src")
        elif (panel:=e_soup.find("tab-panel", attrs={"data-tab": "bilder", "role": "tabpanel"})) and (li:=panel.find("li", attrs={"data-type": "image"})) and (img:=li.find("img")):
            ed_infos[f"bild"] = img.get("src")
        details = e_soup.find("div", class_="details-default")
        for ad in details.find_all("section", class_="artikeldetail"):
            if not (info := ad.find("h3", class_="element-text-standard-strong detailbezeichnung")): continue
            info = info.get_text(strip=True).lower().replace(" ", "_")
            d = ad.find("p") or ad.find("a")
            if d:
                ed_infos[info.lower()] = d.get_text(strip=True)
        ed_infos["medium"] = None #init
        if (a:=e_soup.find("a",attrs={"data-status": "active"})):
            for span in a.find_all("span"):
                if (typ:=span.get("data-typ")):
                    ed_infos["medium"] = typ
                    continue
            
        editions.append(ed_infos)
                    
    return editions, series

def scrape_author_data(author_id: str, metadata_only: bool = False):
    author_data={}
    author_data["key"] = author_id
    soup = soup_or_cached(base+author+author_id)
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
    author_data["_books"] = []
    params = {
        "p": 1,
        "pagesize": 48,
        "filterSPRACHE": 3
    }
    while True:
        books_soup = soup_or_cached(base+author_books+author_id, params=params)
        if books_soup.find("suche-keine-treffer"): break
        for li in books_soup.find_all("li"):
            for a in li.find_all("a"):
                author_data["_books"].append(strip_id(a["href"]))
        params["p"] += 1
    return author_data

def scrape_book_series(book_id: str):
    books = {}
    params = {"seite": 1}
    while True:
        soup = soup_or_cached(base+series+book_id, params)
        if soup.text == "": break
        for li in soup.find_all("li"):
            if (a:=li.find("a", "tm-produkt-link")) and (book_li:=a.get("href")):
                idx = None
                for badge in li.find_all(class_="tm-badges__badge"):
                    b=badge.get_text(strip=True).lower()
                    if "band" in b: idx = float(b.split(" ")[-1])
                books.setdefault(idx, []).append(strip_id(book_li))
        params["seite"] += 1
    return books

def strip_id(url: str):
    return url.strip("/").split("/")[-1].split("?")[0]
def strip_author_id(url: str):
    return url.strip("/").split("/")[-1].split("?")[0].split("-")[-1]

def clean_title(title: str, series_title: str = None, series_pos: int = None):
    bak = title
    if series_title:
        title = title.replace(series_title, "")
    
    series_pos = series_pos or ""
    title = strip_non_word(title)
    title = re.sub(fr"^(?:(?:b(?:(?:an)|)d)|(?:teil)|)\W*{series_pos}", "", title, flags=re.UNICODE | re.I)# remove leading position
    title = re.sub(fr"(?:(?:b(?:(?:an)|)d)|(?:teil)|)\W*{series_pos}$", "", title, flags=re.UNICODE | re.I)# remove traling position
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
    title = re.sub(r"-Reihe$", "", title, flags=re.UNICODE | re.M)
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

def soup_or_cached(url: str, params: dict = {}, skip_cache=False):
    key = (url, tuple(sorted(params.items())))

    if not skip_cache and key in _cache:
        if time() - _cache[key]["time"] < 60*60*24*5:
            print(f"read entry from cache for {key=}")
            return _cache[key]["soup"]

    soup = get_soup(url, params)
    _cache[key] = {"time": time(),"soup":soup}
    
    with open("cache", "wb") as f:
        dump(_cache, f)
    return soup

def get_soup(url: str, params = {}):
    global hits
    hits += 1
    if "thalia" not in url:
        url = base+url
    try:
        response = scraper.get(url, params=params)
    except Exception as e:
        raise HTTPException(status_code=500, detail="at "+url+"?"+"&".join([f"{k}={v}" for k,v in params.items()]))
    if response.status_code != 200: raise HTTPException(status_code=response.status_code, detail="at "+url+"?"+"&".join([f"{k}={v}" for k,v in params.items()]))
    soup = BeautifulSoup(response.text, "html.parser")
    with open("fuckyou.html", "w") as f:
        f.write(soup.prettify())
    return soup


if __name__ == "__main__":
    pass
    #data["titel"] = soup.find(class_="element-headline-medium titel").find(string=True, recursive=False).strip()
    # infos = ["Erscheinungsdatum", "Sprache"]
    # for ad in soup.find_all(class_="artikeldetail"):
    #     info = ad.find(class_="element-text-standard-strong detailbezeichnung").get_text(strip=True) 
    #     if info in infos:
    #         data[info.lower()] = ad.find("p").text.strip()