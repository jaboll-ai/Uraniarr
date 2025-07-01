from sqlmodel import Session
from backend.db import engine
from backend.config import ConfigManager

def get_session():
    with Session(engine) as session:
        yield session

def get_cfg_manager():
    return ConfigManager()