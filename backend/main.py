import asyncio
from contextlib import asynccontextmanager, suppress
import logging
import time
import os

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from backend.db import init_db
from backend.routers import dapi, tapi, api
from backend.exceptions import BaseError
from backend.config import ConfigManager
from backend.services.jobs import init_jobs, stop_jobs
from backend.services.request import reload_scraper
from backend.services.indexer import *
from backend.services.downloader import *
from backend.dependencies import get_error_logger, get_logger



def init_err_log(cfg: ConfigManager):
    uraniarr_err = get_error_logger()
    uraniarr_err.propagate = False
    uraniarr_err.setLevel(logging.ERROR)
    file_handler = logging.FileHandler(f"{cfg.config_dir}/errors.log")
    file_handler.setLevel(logging.ERROR)
    formatter = logging.Formatter(
        fmt="-"*50+"\n%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    formatter.converter = time.localtime
    file_handler.setFormatter(formatter)
    uraniarr_err.addHandler(file_handler)

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = ConfigManager(os.getenv("CONFIG_DIR", "./config"))
    init_err_log(cfg)
    app.state.engine = await init_db(cfg)
    app.state.cfg_manager = cfg
    app.state.indexer = ProwlarrService() if cfg.indexer_prowlarr else NewznabService()
    if cfg.downloader_type == "sab":
        app.state.downloader = SABDownloader()
    else:
        cfg.downloader_type = "sab" #TODO other downloaders
        app.state.downloader = SABDownloader()
    init_jobs(app.state)
    try:
        await reload_scraper(app.state)
    except BaseError as e:
        get_logger().error(f"Failed to initialize scraper, falling back to cloudscraper. Further information: {e.detail}")
        app.state.cfg_manager.playwright = False
        await reload_scraper(app.state)
    try:
        yield
    finally:
        try:
            await stop_jobs(app.state)
            with suppress(Exception):
                await app.state.browser.close()
            with suppress(Exception):
                await app.state.playwright.stop()
        except Exception: pass


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_URLS", "*").split(","), #TODO ENV
    allow_credentials=True,
    allow_methods=os.getenv("ALLOWED_METHODS", "*").split(","),
    allow_headers=os.getenv("ALLOWED_HEADERS", "*").split(","),
)

@app.exception_handler(BaseError)
async def handle_scrape_error(request: Request, exc: BaseError):
    get_logger().error(exc.detail)
    return JSONResponse(status_code=exc.status_code or 404, content={"detail": exc.detail or "", "type": exc.type, "exception": str(exc.exception)})

@app.exception_handler(Exception)
async def handle_all_error(request: Request, exc: Exception):
    if not isinstance(exc, BaseError):
        get_error_logger().exception(exc)
    return JSONResponse(status_code=500, content={"detail": str(exc), "type": "UnexpectedError"})

app.include_router(tapi.router)
app.include_router(dapi.router)
app.include_router(api.router)
