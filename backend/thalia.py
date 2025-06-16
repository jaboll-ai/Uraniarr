import cloudscraper
from bs4 import BeautifulSoup

scraper = cloudscraper.create_scraper()

#author https://www.thalia.de/include/suche/personenportrait/v1/backliste/852812?ajax=true&pagesize=48&filterSPRACHE=3
#pagesize max 48
#page: p
# sort top beweretung : sfsd
# presi aufsteigend sfpa
# preis absteigend sfpd
# erscheinung aufsteigend sfea
# erscheinung absteigend sfed
# bester treffer sfmd
# The product URL
base = "https://www.thalia.de"
url = "/include/suche/personenportrait/v1/backliste/852812?ajax=true&pagesize=48&filterSPRACHE=3"
# Make the request
response = scraper.get(base+url)
# Parse the HTML content
soup = BeautifulSoup(response.text, "html.parser")


for li in soup.find_all("li", class_="tm-produktliste__eintrag artikel"):
    for a in li.find_all("a"):
        book = BeautifulSoup(scraper.get(base+a["href"]).text, "html.parser")
        # Look through all detail sections
        for section in book.find_all("section", class_="artikeldetail"):
            heading = section.find("h3", class_="element-text-standard-strong detailbezeichnung")
            if heading and "Erscheinungsdatum" in heading.get_text(strip=True):
                data = section.find("p", class_="element-text-standard single-value")
                if data:
                    h1 = book.find("h1", class_="element-headline-medium titel")
                    print(''.join(h1.find_all(string=True, recursive=False)).strip(), data.get_text(strip=True))
