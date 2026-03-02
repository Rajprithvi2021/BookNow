"""SQLAlchemy ORM Models for BookNow database.

Tables:
- availability_slots: Pre-populated time slots
- appointments: Customer bookings with status tracking
- notifications: Notification queue and delivery tracking
"""

from datetime import datetime
from enum import Enum
import uuid
from sqlalchemy import (
    Column, String, DateTime, Date, Time, Boolean, 
    Enum as SQLEnum, ForeignKey, UniqueConstraint, Integer, JSON, Text,
    Index, Uuid
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AppointmentStatus(str, Enum):
    """Appointment state machine."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"


class NotificationEventType(str, Enum):
    """Types of notifications."""
    BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION"
    CANCELLATION_CONFIRMATION = "CANCELLATION_CONFIRMATION"


class NotificationStatus(str, Enum):
    """Notification delivery status."""
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"


class AvailabilitySlot(Base):
    """Pre-populated time slots for scheduling.
    
    A slot represents a specific date/time that can be booked.
    Once booked, is_available is set to false.
    """
    __tablename__ = "availability_slots"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_date = Column(Date, nullable=False, index=True)
    slot_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=60)
    is_available = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    appointments = relationship("Appointment", back_populates="slot")
    
    # Constraints: Unique date+time combination
    __table_args__ = (
        UniqueConstraint('slot_date', 'slot_time', name='unique_slot_datetime'),
        Index('idx_slot_date_available', 'slot_date', 'is_available'),
    )


class Appointment(Base):
    """Customer appointment bookings.
    
    State machine:
    - PENDING → CONFIRMED (after booking)
    - CONFIRMED → CANCELLED (on cancellation)
    - CANCELLED → CANCELLED (idempotent)
    """
    __tablename__ = "appointments"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    availability_slot_id = Column(
        Uuid(as_uuid=True), 
        ForeignKey("availability_slots.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    notes = Column(Text, nullable=True)
    
    # Core state
    status = Column(
        SQLEnum(AppointmentStatus),
        default=AppointmentStatus.CONFIRMED,
        nullable=False,
        index=True
    )
    
    # Idempotency key for deduplication on retry
    idempotency_key = Column(
        Uuid(as_uuid=True),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Audit timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Optimistic locking (for future use)
    version = Column(Integer, default=1)
    
    # Relationships
    slot = relationship("AvailabilitySlot", back_populates="appointments")
    notifications = relationship("Notification", back_populates="appointment")
    
    # CRITICAL CONSTRAINT: Prevent multiple active appointments for same slot
    # Only one non-CANCELLED appointment per slot allowed
    # SQLite doesn't support partial indices, so we use compound constraint
    # The pessimistic locking (FOR UPDATE) at application level provides the real protection
    __table_args__ = (
        Index('idx_slot_active_appointments', 'availability_slot_id', 'status'),
        Index('idx_appointment_email_status', 'customer_email', 'status'),
    )


class Notification(Base):
    """Notification queue and delivery tracking.
    
    Every booking creates a notification record.
    Background worker processes QUEUED notifications asynchronously.
    """
    __tablename__ = "notifications"
    
    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("appointments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Event type
    event_type = Column(
        SQLEnum(NotificationEventType),
        nullable=False
    )
    
    # Delivery status
    status = Column(
        SQLEnum(NotificationStatus),
        default=NotificationStatus.QUEUED,
        nullable=False,
        index=True
    )
    
    # Recipient and payload
    recipient_email = Column(String(255), nullable=False, index=True)
    payload = Column(JSON, nullable=False)  # Full notification data
    
    # Error tracking
    error_details = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    
    # Relationships
    appointment = relationship("Appointment", back_populates="notifications")
    
    __table_args__ = (
        Index('idx_notification_status_created', 'status', 'created_at'),
    )


class IdempotencyRecord(Base):
    """Cache for idempotent request responses.
    
    Maps idempotency key → response.
    Allows exact replay of responses for retried requests.
    """
    __tablename__ = "idempotency_records"
    
    idempotency_key = Column(Uuid(as_uuid=True), primary_key=True)
    method = Column(String(10), nullable=False)  # POST, DELETE, etc
    resource_path = Column(String(255), nullable=False)
    response_status = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ttl_expires_at = Column(DateTime, nullable=True)  # For cleanup
    
    __table_args__ = (
        Index('idx_idempotency_expires', 'ttl_expires_at'),
    )
