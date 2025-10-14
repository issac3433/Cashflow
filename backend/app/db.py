# app/db.py
from sqlmodel import SQLModel, Session, create_engine
import os

# If you already load from core.config, you can import settings instead of os.getenv:
# from app.core.config import settings
# DATABASE_URL = settings.DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./cashflow.db")

# echo=True is handy while debugging; switch to False later
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)

def get_session():
    """FastAPI dependency that yields a scoped Session."""
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    """Create tables at startup (imports models so SQLModel sees them)."""
    # Import inside the function to avoid circular imports at import time.
    from app import models  # registers models with SQLModel.metadata
    SQLModel.metadata.create_all(engine)
