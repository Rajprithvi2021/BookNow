"""Database connection setup and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from src.core.config import settings
from src.utils.logger import logger

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=NullPool if "sqlite" in settings.database_url else None,
    pool_pre_ping=True,  # Verify connections before using
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db_session() -> Session:
    """Dependency for FastAPI routes to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def init_db():
    """Initialize database (create tables)."""
    try:
        from src.db.models import Base
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
