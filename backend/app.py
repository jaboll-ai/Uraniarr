from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, create_engine
from bs4 import BeautifulSoup
import cloudscraper
from backend.datamodels import Book
from time import sleep

base="***REMOVED***"
book="/shop/home/artikeldetails/"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Might make docker env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine("sqlite:///data/database.db")
scraper = cloudscraper.create_scraper()
SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session

def fetch_search(q: str):
    url = "/suche"
    params = {
        "ajax": "true",
        "sq": q,
        "pagesize": "24",
    }
    soup = _get_soup_or_throw(url, params=params)
    
@app.get("/books/{book_id}")
def build_book(book_id: str): # for better titles call with hörbuch download id
    soup = _get_soup_or_throw(base+book+book_id)
    with open("thalia.html", "w") as f:
        f.write(soup.prettify())
    infos = ["Erscheinungsdatum", "Sprache"]
    data = _get_books_ids(soup)
    for ad in soup.find_all(class_="artikeldetail"):
        info = ad.find(class_="element-text-standard-strong detailbezeichnung").get_text(strip=True) 
        if info in infos:
            data[info.lower()] = ad.find("p").text.strip()
    data["titel"] = soup.find(class_="element-headline-medium titel").find(text=True, recursive=False).strip()
    data["autor"] = soup.find(href=lambda href: href and "/autor/" in href).get_text(strip=True)
    __get_book_editions(data)
    # TODO get Series
    
    print(data)
    return Book(**data)

def __get_book_editions(refs: dict[str, str]):
    booktypes = ["hörbuch", "taschenbuch", "hardcover", "ebook"]
    for booktype in booktypes:
        if book_id:=refs.get(booktype):
            soup = _get_soup_or_throw(base+book+book_id)
            if (div:=soup.find("div", class_="artikelbild-container")) and (img:=div.find("img")): 
                refs[f"bild_{booktype}"] = img.get("src")
            elif (panel:=soup.find("tab-panel", attrs={"data-tab": "bilder", "role": "tabpanel"})) and (li:=panel.find("li", attrs={"data-type": "image"})) and (img:=li.find("img")):
                refs[f"bild_{booktype}"] = img.get("src")
            
def _get_books_ids(soup: BeautifulSoup):
    refs = {}
    for a in soup.find_all(class_="layered-link"):
        if refs.get(a["caption"]) and not "download" in a.find("dl-product")["product-avail"].lower():
            continue
        refs[a["caption"]]=a["href"].split("/")[-1][:11]
    if len(refs) < 3: #fallback
        for ul in soup.find_all("ul",class_="optionen", attrs={'data-formattyp': 'format'}):
            for a in ul.find_all("a", class_="element-card-select formatkachel-link"):
                key = a.find("span", class_="element-text-standard").text.strip()
                if not refs.get(key): 
                    refs[key.lower()]=a["href"].split("/")[-1][:11]
    return refs

def _get_soup_or_throw(url: str):
    if "thalia" not in url:
        url = base+url
    response = scraper.get(url)
    errors = 0
    while response.status_code != 200 and errors < 20:
        errors += 1
        sleep(1)
        print(f"{response.status_code} error. Tries: {errors}")
        response = scraper.get(base+url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


@app.post("/add/author/")
async def add_author(key: str, session: Session = Depends(get_session)):
    pass