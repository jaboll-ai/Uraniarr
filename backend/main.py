import asyncio
from contextlib import asynccontextmanager, suppress
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from cloudscraper import create_scraper

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from backend.db import engine
from backend.routers import sabnzbdapi, tapi, api
from backend.exceptions import BaseError
from backend.config import ConfigManager
from backend.services.filehelper import poll_folder
from backend.services.request_service import set_scraper

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = ConfigManager()
    task = asyncio.create_task(poll_folder(cfg.import_poll_interval))
    if cfg.playwright: 
        playwright = await Stealth().use_async(async_playwright()).__aenter__()
        browser = await playwright.chromium.launch(headless=True)
    else:
        browser = create_scraper()
    set_scraper(browser)
    try:
        yield
    finally:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task
        await browser.close()
        await playwright.stop()

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO ENV
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
SQLModel.metadata.create_all(engine)

@app.exception_handler(BaseError)
async def handle_scrape_error(request: Request, exc: BaseError):
    return JSONResponse(status_code=exc.status_code or 404, content={"detail": exc.detail or "", "type": exc.type}) 


app.include_router(tapi.router)
app.include_router(sabnzbdapi.router)
app.include_router(api.router)
