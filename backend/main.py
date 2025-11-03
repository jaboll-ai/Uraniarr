import asyncio
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel

from backend.db import engine
from backend.routers import dapi, tapi, api
from backend.exceptions import BaseError
from backend.config import ConfigManager
from backend.services.filehelper import poll_folder, rescan_files
from backend.services.request_service import reload_scraper
from backend.services.indexer import *
from backend.services.downloader import *

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    cfg = ConfigManager()
    app.state.cfg_manager = cfg
    app.state.indexer = ProwlarrService() if cfg.indexer_prowlarr else NewznabService()
    if cfg.downloader_type == "sab":
        app.state.downloader = SABDownloader()
    else:
        cfg.downloader_type = "sab" #TODO other downloaders
        app.state.downloader = SABDownloader()
    task_poll_folder = asyncio.create_task(poll_folder(app.state))
    task_rescan_files = asyncio.create_task(rescan_files(app.state))
    try:
        await reload_scraper(app.state)
    except BaseError:
        app.state.cfg_manager.playwright = False
        await reload_scraper(app.state)
    try:
        yield
    finally:
        try:
            with suppress(Exception):
                task_poll_folder.cancel()
            with suppress(asyncio.CancelledError):
                await task_poll_folder
            with suppress(Exception):
                task_rescan_files.cancel()
            with suppress(asyncio.CancelledError):
                await task_rescan_files
            with suppress(Exception):
                await app.state.browser.close()
            with suppress(Exception):
                await app.state.playwright.stop()
        except Exception: pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], #TODO ENV
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(BaseError)
async def handle_scrape_error(request: Request, exc: BaseError):
    print(exc.detail)
    return JSONResponse(status_code=exc.status_code or 404, content={"detail": exc.detail or "", "type": exc.type}) 


app.include_router(tapi.router)
app.include_router(dapi.router)
app.include_router(api.router)
