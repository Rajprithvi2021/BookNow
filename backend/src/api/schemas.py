"""Request and response schemas for API endpoints."""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, date, time
from uuid import UUID
from typing import Optional, List


# ============================================================================
# Availability Schemas
# ============================================================================

class AvailabilitySlotResponse(BaseModel):
    """Availability slot response."""
    id: UUID
    slot_date: date
    slot_time: time
    duration_minutes: int
    is_available: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class AvailabilitySlotsResponse(BaseModel):
    """List of available slots."""
    slots: List[AvailabilitySlotResponse]
    count: int


# ============================================================================
# Appointment Schemas
# ============================================================================

class BookAppointmentRequest(BaseModel):
    """Request to book appointment."""
    slot_id: UUID = Field(..., description="UUID of availability slot")
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: EmailStr
    notes: Optional[str] = Field(None, max_length=1000)


class AppointmentResponse(BaseModel):
    """Appointment details."""
    id: UUID
    availability_slot_id: UUID
    customer_name: str
    customer_email: str
    notes: Optional[str]
    status: str  # "PENDING", "CONFIRMED", "CANCELLED"
    idempotency_key: UUID
    created_at: datetime
    confirmed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    
    class Config:
        from_attributes = True


class AppointmentsListResponse(BaseModel):
    """List of appointments."""
    appointments: List[AppointmentResponse]
    count: int


class CancelAppointmentRequest(BaseModel):
    """Request to cancel appointment."""
    reason: Optional[str] = Field(None, max_length=500)


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """API error response."""
    error: str
    message: str
    request_id: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(ErrorResponse):
    """Validation error with field details."""
    details: Optional[dict] = None


# ============================================================================
# Health Check
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str = "1.0.0"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
