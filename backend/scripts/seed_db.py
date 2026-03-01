#!/usr/bin/env python
"""
Database initialization script.

Run this BEFORE starting the API to seed availability slots.
"""

from datetime import date, time, timedelta
from uuid import uuid4

from src.db.connection import SessionLocal, init_db
from src.db.models import AvailabilitySlot
from src.utils.logger import logger


def seed_availability_slots():
    """Seed database with demo availability slots."""
    
    init_db()
    session = SessionLocal()
    
    try:
        # Check if already seeded
        count = session.query(AvailabilitySlot).count()
        if count > 0:
            logger.info(f"Database already seeded ({count} slots exist)")
            return count
        
        logger.info("Seeding availability slots...")
        
        # Create slots for next 14 days
        start_date = date.today()
        slots_created = 0
        
        for day_offset in range(14):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            # Create 8 slots per day (9am-5pm, 1 hour each)
            for hour in range(9, 17):
                slot = AvailabilitySlot(
                    id=uuid4(),
                    slot_date=current_date,
                    slot_time=time(hour=hour, minute=0),
                    duration_minutes=60,
                    is_available=True
                )
                session.add(slot)
                slots_created += 1
        
        session.commit()
        logger.info(f"✅ Created {slots_created} availability slots")
        return slots_created
        
    except Exception as e:
        logger.error(f"Error seeding slots: {e}")
        session.rollback()
        raise
    finally:
        session.close()


if __name__ == "__main__":
    seed_availability_slots()
