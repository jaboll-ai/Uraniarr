from sqlmodel.ext.asyncio.session import AsyncSession
from backend.db import engine
from backend.config import ConfigManager
from fastapi import Request
import logging

async def get_session():
    async with AsyncSession(engine) as session:
        yield session

def get_cfg_manager(request: Request) -> ConfigManager:
    return request.app.state.cfg_manager

def get_logger() -> logging.Logger:
    return logging.getLogger('uvicorn.error')