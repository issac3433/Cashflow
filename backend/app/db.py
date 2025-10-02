from sqlmodel import SQLModel, create_engine
from .core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

def init_db():
    # Import models before create_all
    from .models import User, Portfolio, Holding, DividendEvent, Price  # noqa
    SQLModel.metadata.create_all(engine)
