from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.config import settings

# replace asyncpg with psycopg2 for sync operations
DATABASE_URL = settings.database_url.replace("+asyncpg", "+psycopg2")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    """Dependency for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
