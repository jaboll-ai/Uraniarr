from backend import scrape
# from backend import datamodels
# from backend import api
from bs4 import BeautifulSoup
# import rapidfuzz
import json

a , _ = scrape.scrape_book_editions("A1042624533")
print([b["medium"] for b in a])

print(scrape.clean_title("TKKG - Folge 97: Die Hand an den Sternen", series_title="TKKG"))

# a=rapidfuzz.fuzz.ratio("Georgia", "Will Trent - Georgia")
# print(a)
# from time import time
# t = time()
# print(scrape.clean_title("""
#                                     Die letzte Nacht (ungekürzt)
#                                         """, "Will Trent - Georgia ",  11))
# print(bool(BeautifulSoup().text))
# print(time()-t)
# a="()()"
# for c in a:
    # print(c=="(")
# print(b[0])

# b = {"a"" : "1}

# print(b["a"])

# b["a"] += 1

# print(b["a"])

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(api.app, host="0.0.0.0", port=8000)

    