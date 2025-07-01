from sqlmodel import create_engine

DATABASE_URL = "sqlite:///data/database.db"
engine = create_engine(DATABASE_URL)