from sqlmodel import create_engine
from pathlib import Path

(Path('.') / "data").mkdir(parents=True, exist_ok=True)
DATABASE_URL = "sqlite:///data/database.db"
engine = create_engine(DATABASE_URL)