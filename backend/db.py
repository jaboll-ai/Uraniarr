from sqlalchemy.ext.asyncio import create_async_engine
from backend.config import ConfigManager

DATABASE_URL = f"sqlite+aiosqlite:///{ConfigManager.config_dir.as_posix()}/database.db"
engine = create_async_engine(DATABASE_URL)