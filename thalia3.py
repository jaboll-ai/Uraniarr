from backend.app import _get_soup_or_throw

base = "https://www.thalia.de"
url = "/shop/home/artikeldetails/A1072896281"

soup = _get_soup_or_throw(base+url)

with open("thalia.html", "w") as f:
    f.write(soup.prettify())
    
if (div:=soup.find("div", class_="artikelbild-container")) and (img:=div.find("img")): 
    print(img.get("src"))
