from bs4 import BeautifulSoup
import cloudscraper
from time import sleep

base="***REMOVED***"
book="/shop/home/artikeldetails/"
series="/api/serienslider/v2/"

scraper = cloudscraper.create_scraper()

def fetch_search(q: str):
    url = "/suche"
    params = {
        "ajax": "true",
        "sq": q,
        "pagesize": "24",
    }
    soup = get_soup_or_throw(url, params=params)
    
def build_book(book_id: str): # for better titles call with hörbuch download id
    soup = get_soup_or_throw(base+book+book_id)
    with open("thalia.html", "w") as f:
        f.write(soup.prettify())
    infos = ["Erscheinungsdatum", "Sprache"]
    data = get_books_editions(soup)
    for ad in soup.find_all(class_="artikeldetail"):
        info = ad.find(class_="element-text-standard-strong detailbezeichnung").get_text(strip=True) 
        if info in infos:
            data[info.lower()] = ad.find("p").text.strip()
    data["titel"] = soup.find(class_="element-headline-medium titel").find(text=True, recursive=False).strip()
    data["autor"] = soup.find(href=lambda href: href and "/autor/" in href).get_text(strip=True)
    get_book_images(data)
    # TODO get Series
    return data

def build_series(book_id: str):
    soup = get_soup_or_throw(base+series+book_id)
    if (h2:=soup.find("h2", id="serien-slider")): 
        title = h2.get_text(strip=True)[18:]
    else: return None
    url = base+series+book_id
    p = 0
    while not soup.text == "":
        soup = get_soup_or_throw(url, params={"seite": p})
        for li in soup.find_all("li"):
            if (a:=li.find("a", class_="element-link-toplevel tm-produkt-link")) and (book_li:=a.get("href")):
                id = strip_id(book_li)
        p += 1

def get_book_images(refs: dict[str, str]):
    booktypes = ["hörbuch", "ebook", "taschenbuch", "hardcover"]
    for booktype in booktypes:
        if book_id:=refs.get(booktype):
            soup = get_soup_or_throw(base+book+book_id)
            if (div:=soup.find("div", class_="artikelbild-container")) and (img:=div.find("img")): 
                refs[f"bild_{booktype}"] = img.get("src")
            elif (panel:=soup.find("tab-panel", attrs={"data-tab": "bilder", "role": "tabpanel"})) and (li:=panel.find("li", attrs={"data-type": "image"})) and (img:=li.find("img")):
                refs[f"bild_{booktype}"] = img.get("src")
            
def get_books_editions(soup: BeautifulSoup):
    refs = {}
    for a in soup.find_all(class_="layered-link"):
        if refs.get(a["caption"]) and not "download" in a.find("dl-product")["product-avail"].lower():
            continue
        refs[a["caption"]]=strip_id(a["href"])
    if len(refs) < 3: #fallback
        for ul in soup.find_all("ul",class_="optionen", attrs={'data-formattyp': 'format'}):
            for a in ul.find_all("a", class_="element-card-select formatkachel-link"):
                key = a.find("span", class_="element-text-standard").text.strip()
                if not refs.get(key): 
                    refs[key.lower()]=strip_id(a["href"])
                
    return refs

def strip_id(url: str):
    return url.split("/")[-1][:11]

def get_book_by_foreign(id: str):
    pass

def get_soup_or_throw(url: str, params = {}):
    if "thalia" not in url:
        url = base+url
    response = scraper.get(url, params=params)
    errors = 0
    while response.status_code != 200 and errors < 20:
        errors += 1
        sleep(1)
        print(f"{response.status_code} error. Tries: {errors}")
        response = scraper.get(url, params=params)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup
