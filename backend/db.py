from sqlmodel import create_engine
from pathlib import Path

Path('./config').mkdir(parents=True, exist_ok=True)
DATABASE_URL = "sqlite:///config/database.db"
engine = create_engine(DATABASE_URL)