"""API route handlers for appointments and availability."""

from fastapi import APIRouter, Depends, HTTPException, Header, Query
from sqlalchemy.orm import Session
from datetime import date, timedelta
from uuid import UUID, uuid4
import uuid as uuid_module

from src.db.connection import get_db_session
from src.api.schemas import (
    AvailabilitySlotResponse, AvailabilitySlotsResponse,
    BookAppointmentRequest, AppointmentResponse,
    AppointmentsListResponse, CancelAppointmentRequest,
    HealthResponse
)
from src.services.appointment_service import AppointmentService
from src.services.availability_service import AvailabilityService
from src.services.idempotency_service import IdempotencyService
from src.utils.exceptions import DoubleBookingError, AppointmentNotFoundError
from src.utils.logger import logger


router = APIRouter(prefix="/api")


# ============================================================================
# Health & Status
# ============================================================================

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse()


# ============================================================================
# Availability Endpoints
# ============================================================================

@router.get(
    "/availability",
    response_model=AvailabilitySlotsResponse,
    summary="Get available appointment slots",
    description="Returns all unbooked slots for the requested date range.",
    tags=["Availability"]
)
async def get_availability(
    start_date: date = Query(..., description="Start date (YYYY-MM-DD)"),
    days: int = Query(7, ge=1, le=30, description="Number of days to show"),
    session: Session = Depends(get_db_session)
):
    """Get available slots for booking."""
    
    slots = AvailabilityService.get_available_slots(
        session=session,
        start_date=start_date,
        num_days=days
    )
    
    return AvailabilitySlotsResponse(
        slots=[AvailabilitySlotResponse.from_orm(slot) for slot in slots],
        count=len(slots)
    )


# ============================================================================
# Appointment Endpoints
# ============================================================================

@router.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=201,
    summary="Book an appointment",
    description="Creates a new appointment with double-booking prevention.",
    tags=["Appointments"]
)
async def book_appointment(
    request: BookAppointmentRequest,
    idempotency_key: UUID = Header(
        ...,
        description="Unique UUID for idempotent request handling"
    ),
    session: Session = Depends(get_db_session)
):
    """
    Book an appointment for a given availability slot.
    
    **Concurrency Protection:**
    - Pessimistic locking (SELECT FOR UPDATE)
    - Unique DB constraint: one active appointment per slot
    - Guaranteed no double-booking
    
    **Idempotency:**
    - Send same Idempotency-Key header on retry
    - Will return same response without executing twice
    - TTL: 24 hours
    
    **Query Parameters:**
    - slot_id: UUID of the availability slot
    - customer_name: Full name
    - customer_email: Email address
    - notes: Optional booking notes
    """
    
    try:
        # Check idempotency cache
        cached = IdempotencyService.get_cached_response(
            session=session,
            idempotency_key=idempotency_key
        )
        if cached:
            return AppointmentResponse(**cached["body"])
        
        # Book appointment (with locking)
        appointment = AppointmentService.book_appointment(
            session=session,
            slot_id=request.slot_id,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            idempotency_key=idempotency_key,
            notes=request.notes
        )
        
        # Cache response for future identical requests
        response_data = {
            "id": str(appointment.id),
            "availability_slot_id": str(appointment.availability_slot_id),
            "customer_name": appointment.customer_name,
            "customer_email": appointment.customer_email,
            "notes": appointment.notes,
            "status": appointment.status.value,
            "idempotency_key": str(appointment.idempotency_key),
            "created_at": appointment.created_at,
            "confirmed_at": appointment.confirmed_at,
            "cancelled_at": appointment.cancelled_at,
        }
        
        IdempotencyService.store_response(
            session=session,
            idempotency_key=idempotency_key,
            method="POST",
            path="/api/appointments",
            status=201,
            body=response_data
        )
        
        logger.info(f"Appointment created: {appointment.id}")
        
        return AppointmentResponse.from_orm(appointment)
        
    except DoubleBookingError as e:
        logger.warning(f"Double-booking prevention: {e}")
        raise HTTPException(status_code=409, detail=str(e))
    except AppointmentNotFoundError as e:
        logger.warning(f"Not found: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in book_appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Get appointment details",
    tags=["Appointments"]
)
async def get_appointment(
    appointment_id: UUID,
    session: Session = Depends(get_db_session)
):
    """Get details of a specific appointment."""
    
    appointment = AppointmentService.get_appointment(
        session=session,
        appointment_id=appointment_id
    )
    
    if not appointment:
        raise HTTPException(
            status_code=404,
            detail=f"Appointment {appointment_id} not found"
        )
    
    return AppointmentResponse.from_orm(appointment)


@router.delete(
    "/appointments/{appointment_id}",
    response_model=AppointmentResponse,
    summary="Cancel an appointment",
    description="Cancellation is idempotent - safe to call multiple times.",
    tags=["Appointments"]
)
async def cancel_appointment(
    appointment_id: UUID,
    request: CancelAppointmentRequest = None,
    session: Session = Depends(get_db_session)
):
    """
    Cancel an appointment.
    
    **Idempotency:**
    - Cancellation is idempotent via state machine
    - Already cancelled? Returns cached state
    - Safe to call multiple times with same ID
    """
    
    try:
        appointment = AppointmentService.cancel_appointment(
            session=session,
            appointment_id=appointment_id
        )
        
        logger.info(f"Appointment cancelled: {appointment_id}")
        
        return AppointmentResponse.from_orm(appointment)
        
    except AppointmentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error cancelling appointment: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/appointments",
    response_model=AppointmentsListResponse,
    summary="List appointments by email",
    tags=["Appointments"]
)
async def list_appointments(
    email: str = Query(..., description="Customer email address"),
    include_cancelled: bool = Query(True, description="Include cancelled appointments"),
    session: Session = Depends(get_db_session)
):
    """Get all appointments for a customer."""
    
    appointments = AppointmentService.get_appointments_by_email(
        session=session,
        email=email,
        include_cancelled=include_cancelled
    )
    
    return AppointmentsListResponse(
        appointments=[AppointmentResponse.from_orm(a) for a in appointments],
        count=len(appointments)
    )
