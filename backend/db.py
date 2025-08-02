from sqlmodel import create_engine
from backend.config import ConfigManager

DATABASE_URL = f"sqlite:///{ConfigManager.config_dir.as_posix()}/database.db"
engine = create_engine(DATABASE_URL)