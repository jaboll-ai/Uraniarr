from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from backend.config import ConfigManager


async def init_db(cfg: ConfigManager):
    DATABASE_URL = f"sqlite+aiosqlite:///{cfg.config_dir.as_posix()}/database.db"
    engine = create_async_engine(DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    return engine