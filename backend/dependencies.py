import re
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.config import ConfigManager
from fastapi import Request
import logging
from rapidfuzz import fuzz

async def get_session(request: Request):
    async with AsyncSession(request.app.state.engine) as session:
        yield session

def get_cfg_manager(request: Request) -> ConfigManager:
    return request.app.state.cfg_manager

def get_logger() -> logging.Logger:
    return logging.getLogger('uvicorn.error')

def get_error_logger() -> logging.Logger:
    return logging.getLogger('uraniarr.err')

def get_scorer():
    def prepare(s: str) -> str:
        s = s.lower()
        s = re.sub(r"[-–—]", " ", s)       # replace dashes with spaces
        s = re.sub(r"[.:;,_!?()\"']", " ", s)  # remove or space punctuation
        s = re.sub(r"\s+", " ", s).strip() # collapse multiple spaces
        return s
    def smart_ratio(query: str, choice: str,  *args, **kwargs):
        q=prepare(query)
        c=prepare(choice)
        if len(query) < 3 or len(choice) < 3:
            return fuzz.ratio(q, c, *args, **kwargs)
        return fuzz.token_set_ratio(q, c, *args, **kwargs)

    return smart_ratio