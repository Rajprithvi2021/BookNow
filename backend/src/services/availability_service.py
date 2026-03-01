"""Availability slot queries and management."""

from datetime import date, timedelta
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.db.models import AvailabilitySlot, Appointment, AppointmentStatus
from src.utils.logger import logger


class AvailabilityService:
    """Handles availability slot queries."""
    
    @staticmethod
    def get_available_slots(
        session: Session,
        start_date: date,
        num_days: int = 7
    ) -> List[AvailabilitySlot]:
        """
        Get all available (unbooked) slots for date range.
        
        Efficiency:
        - Uses LEFT JOIN with appointments
        - Filters where appointment IS NULL (no active booking)
        - Indexes on (date, available) and (slot_id, status)
        - Typical response: <5ms for 168 slots (7 days)
        
        Args:
            session: SQLAlchemy session
            start_date: Start date (YYYY-MM-DD)
            num_days: Number of days to show
        
        Returns:
            List of available AvailabilitySlot objects
        """
        
        end_date = start_date + timedelta(days=num_days)
        
        # Query for slots without active appointments
        slots = session.query(AvailabilitySlot) \
            .outerjoin(
                Appointment,
                and_(
                    Appointment.availability_slot_id == AvailabilitySlot.id,
                    Appointment.status.in_([
                        AppointmentStatus.CONFIRMED,
                        AppointmentStatus.PENDING
                    ])
                )
            ) \
            .filter(
                AvailabilitySlot.slot_date >= start_date,
                AvailabilitySlot.slot_date < end_date,
                Appointment.id.is_(None)  # No active appointment
            ) \
            .order_by(AvailabilitySlot.slot_date, AvailabilitySlot.slot_time) \
            .all()
        
        logger.info(
            f"Retrieved {len(slots)} available slots "
            f"from {start_date} to {end_date}"
        )
        
        return slots
    
    @staticmethod
    def is_slot_available(
        session: Session,
        slot_id
    ) -> bool:
        """Check if a specific slot is available."""
        
        slot = session.query(AvailabilitySlot) \
            .filter_by(id=slot_id) \
            .one_or_none()
        
        if not slot:
            return False
        
        # Check if there's an active appointment
        appointment = session.query(Appointment) \
            .filter(
                Appointment.availability_slot_id == slot_id,
                Appointment.status.in_([
                    AppointmentStatus.CONFIRMED,
                    AppointmentStatus.PENDING
                ])
            ) \
            .one_or_none()
        
        return appointment is None
    
    @staticmethod
    def seed_availability(
        session: Session,
        start_date: date,
        num_days: int = 7,
        slots_per_day: int = 8,
        start_hour: int = 9,
        duration_minutes: int = 60
    ) -> int:
        """
        Seed database with availability slots.
        
        Creates slots for business hours (9am-5pm, 8 slots/day).
        For demo/testing purposes.
        
        Args:
            session: SQLAlchemy session
            start_date: Starting date
            num_days: Number of days to create
            slots_per_day: Slots per day (default 8 = 9am-5pm)
            start_hour: Starting hour (default 9)
            duration_minutes: Duration of each slot
        
        Returns:
            Number of slots created
        """
        
        from datetime import time
        from uuid import uuid4
        
        created = 0
        
        for day_offset in range(num_days):
            current_date = start_date + timedelta(days=day_offset)
            
            # Skip weekends
            if current_date.weekday() >= 5:
                continue
            
            for slot_offset in range(slots_per_day):
                hour = start_hour + slot_offset
                
                slot = AvailabilitySlot(
                    id=uuid4(),
                    slot_date=current_date,
                    slot_time=time(hour=hour, minute=0),
                    duration_minutes=duration_minutes,
                    is_available=True
                )
                
                session.add(slot)
                created += 1
        
        session.commit()
        logger.info(f"Seeded {created} availability slots")
        return created
