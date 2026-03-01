"""Database connection setup and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool, StaticPool
from src.core.config import settings
from src.utils.logger import logger

# Create engine with connection pooling
# For SQLite in-memory, use StaticPool to maintain a single connection
# and allow cross-thread access
engine = create_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
    poolclass=StaticPool if "sqlite:///:memory:" in settings.database_url else None,
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
    """Initialize database (create tables and seed sample data)."""
    try:
        from src.db.models import Base, AvailabilitySlot, Appointment, IdempotencyRecord, Notification
        from datetime import date, time, timedelta
        from uuid import uuid4
        
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
        # Reseed availability slots every startup to ensure current slots
        session = SessionLocal()
        
        # Clear old slots and related data
        session.query(Notification).delete()
        session.query(Appointment).delete()
        session.query(IdempotencyRecord).delete()
        session.query(AvailabilitySlot).delete()
        session.commit()
        logger.info("Cleared old availability slots")
        
        logger.info("Seeding fresh availability slots...")
        today = date.today()
        
        # Create sample slots for 3 months (90 days)
        # 4 slots per day = 360 total slots
        for day_offset in range(90):
            slot_date = today + timedelta(days=day_offset)
            
            # 4 slots per day at different times
            times = [
                time(9, 0),   # 9:00 AM
                time(11, 0),  # 11:00 AM
                time(14, 0),  # 2:00 PM
                time(16, 0),  # 4:00 PM
            ]
            
            for slot_time in times:
                slot = AvailabilitySlot(
                    id=uuid4(),
                    slot_date=slot_date,
                    slot_time=slot_time,
                    duration_minutes=60,
                    is_available=True
                )
                session.add(slot)
        
        session.commit()
        logger.info(f"Successfully seeded 360 availability slots (90 days × 4 slots/day) starting from {today}")
        
        session.close()
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
