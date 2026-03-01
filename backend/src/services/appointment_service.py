"""Appointment booking service with concurrency control.

Core algorithm: Pessimistic locking (row-level FOR UPDATE)
Prevents double-booking under ANY concurrent scenario.
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.db.models import (
    Appointment, AvailabilitySlot, Notification,
    AppointmentStatus, NotificationEventType, NotificationStatus
)
from src.utils.exceptions import DoubleBookingError, AppointmentNotFoundError
from src.utils.logger import logger


class AppointmentService:
    """Handles appointment booking with ACID guarantees."""
    
    @staticmethod
    def book_appointment(
        session: Session,
        slot_id: UUID,
        customer_name: str,
        customer_email: str,
        idempotency_key: UUID,
        notes: Optional[str] = None
    ) -> Appointment:
        """
        Book an appointment with double-booking prevention.
        
        Algorithm:
        1. BEGIN TRANSACTION
        2. SELECT slot FOR UPDATE (acquire exclusive lock)
        3. Check is_available
        4. INSERT appointment (status=CONFIRMED)
        5. INSERT notification (status=QUEUED)
        6. UPDATE slot is_available=false
        7. COMMIT (lock released)
        
        The lock ensures only ONE request can proceed for a given slot.
        Other requests wait, then see is_available=false and get 409 Conflict.
        
        Args:
            session: SQLAlchemy session
            slot_id: UUID of availability slot
            customer_name: Customer full name
            customer_email: Customer email
            idempotency_key: UUID for deduplication on retry
            notes: Optional booking notes
        
        Returns:
            Appointment object with status=CONFIRMED
        
        Raises:
            DoubleBookingError: Slot was just booked by another request
            ValueError: Invalid input
        """
        
        try:
            # CRITICAL: Acquire exclusive row lock on this slot
            # This is the key to preventing double-booking
            slot = session.query(AvailabilitySlot) \
                .with_for_update() \
                .filter_by(id=slot_id) \
                .one()
            
        except Exception:
            raise AppointmentNotFoundError(f"Slot {slot_id} not found")
        
        # Check availability (protected by lock)
        if not slot.is_available:
            raise DoubleBookingError(
                f"Slot {slot_id} on {slot.slot_date} {slot.slot_time} already booked"
            )
        
        try:
            # Create appointment
            appointment = Appointment(
                availability_slot_id=slot_id,
                customer_name=customer_name,
                customer_email=customer_email,
                notes=notes,
                status=AppointmentStatus.CONFIRMED,
                idempotency_key=idempotency_key,
                confirmed_at=datetime.utcnow()
            )
            session.add(appointment)
            session.flush()  # Get ID without committing
            
            # Queue confirmation notification
            notification = Notification(
                appointment_id=appointment.id,
                event_type=NotificationEventType.BOOKING_CONFIRMATION,
                status=NotificationStatus.QUEUED,
                recipient_email=customer_email,
                payload={
                    "appointment_id": str(appointment.id),
                    "customer_name": customer_name,
                    "customer_email": customer_email,
                    "slot_date": str(slot.slot_date),
                    "slot_time": str(slot.slot_time),
                    "notes": notes,
                    "event": "BOOKING_CONFIRMATION",
                    "confirmed_at": datetime.utcnow().isoformat()
                }
            )
            session.add(notification)
            
            # Mark slot unavailable
            slot.is_available = False
            
            # COMMIT: All changes atomic
            session.commit()
            
            logger.info(
                f"Appointment booked: {appointment.id} "
                f"for {customer_email} on {slot.slot_date} {slot.slot_time}"
            )
            
            return appointment
            
        except IntegrityError as e:
            session.rollback()
            # Could be: idempotency key duplicate, or slot constraint violation
            if "idempotency_key" in str(e):
                # This request was already processed
                # Query and return the existing appointment
                existing = session.query(Appointment) \
                    .filter_by(idempotency_key=idempotency_key) \
                    .one()
                return existing
            raise DoubleBookingError("Slot already booked") from e
    
    @staticmethod
    def cancel_appointment(
        session: Session,
        appointment_id: UUID
    ) -> Appointment:
        """
        Cancel an appointment (idempotent operation).
        
        Idempotency guaranteed by state machine:
        - If already CANCELLED: return it (no error)
        - If CONFIRMED: transition to CANCELLED
        - Safe to call multiple times
        
        Args:
            session: SQLAlchemy session
            appointment_id: UUID of appointment to cancel
        
        Returns:
            Appointment with status=CANCELLED
        
        Raises:
            AppointmentNotFoundError: Appointment doesn't exist
        """
        
        appointment = session.query(Appointment) \
            .filter_by(id=appointment_id) \
            .one_or_none()
        
        if not appointment:
            raise AppointmentNotFoundError(
                f"Appointment {appointment_id} not found"
            )
        
        # Idempotency: already cancelled? Just return it
        if appointment.status == AppointmentStatus.CANCELLED:
            logger.info(
                f"Appointment {appointment_id} already cancelled, "
                f"returning cached state"
            )
            return appointment
        
        # Transition to CANCELLED
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.utcnow()
        
        # Queue cancellation notification
        notification = Notification(
            appointment_id=appointment.id,
            event_type=NotificationEventType.CANCELLATION_CONFIRMATION,
            status=NotificationStatus.QUEUED,
            recipient_email=appointment.customer_email,
            payload={
                "appointment_id": str(appointment.id),
                "customer_name": appointment.customer_name,
                "customer_email": appointment.customer_email,
                "event": "CANCELLATION_CONFIRMATION",
                "cancelled_at": datetime.utcnow().isoformat()
            }
        )
        session.add(notification)
        
        session.commit()
        
        logger.info(f"Appointment {appointment_id} cancelled")
        
        return appointment
    
    @staticmethod
    def get_appointment(
        session: Session,
        appointment_id: UUID
    ) -> Optional[Appointment]:
        """Get appointment details."""
        return session.query(Appointment) \
            .filter_by(id=appointment_id) \
            .one_or_none()
    
    @staticmethod
    def get_appointments_by_email(
        session: Session,
        email: str,
        include_cancelled: bool = True
    ) -> list[Appointment]:
        """Get all appointments for a customer."""
        query = session.query(Appointment) \
            .filter_by(customer_email=email)
        
        if not include_cancelled:
            query = query.filter(
                Appointment.status != AppointmentStatus.CANCELLED
            )
        
        return query.order_by(Appointment.created_at.desc()).all()
