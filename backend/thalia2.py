import cloudscraper
from bs4 import BeautifulSoup

def get_refs(soup: BeautifulSoup):
    refs = {}
    for a in soup.find_all(class_="layered-link"):
        if refs.get(a["caption"]) and not "download" in a.find("dl-product")["product-avail"].lower():
            continue
        refs[a["caption"]]=a["href"]
    if len(refs) < 3: #fallback
        print("fallback")
        for ul in soup.find_all("ul",class_="optionen", attrs={'data-formattyp': 'format'}):
            for a in ul.find_all("a", class_="element-card-select formatkachel-link"):
                key = a.find("span", class_="element-text-standard").text.strip()
                if not refs.get(key): 
                    refs[key]=base+a["href"]
    return refs

scraper = cloudscraper.create_scraper()

#author ***REMOVED***/include/suche/personenportrait/v1/backliste/852812?ajax=true&pagesize=48&filterSPRACHE=3

base = "***REMOVED***"
url = "/shop/home/artikeldetails/A1072896281"

response = scraper.get(base+url)
while response.status_code != 200:
    response = scraper.get(base+url)
    
with open("test1.html", "w") as f:
    f.write(response.text)

soup = BeautifulSoup(response.text, "html.parser")
refs = get_refs(soup)

print(refs)