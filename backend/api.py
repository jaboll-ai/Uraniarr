from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, SQLModel, create_engine, select, or_
from bs4 import BeautifulSoup
import cloudscraper
from backend.datamodels import Book, Reihe
from time import sleep
import re

base="***REMOVED***"
book="/shop/home/artikeldetails/"
series="/api/serienslider/v2/"

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

