from sqlmodel.ext.asyncio.session import AsyncSession
from backend.db import engine
from backend.config import ConfigManager

async def get_session():
    async with AsyncSession(engine) as session:
        yield session

def get_cfg_manager():
    return ConfigManager()