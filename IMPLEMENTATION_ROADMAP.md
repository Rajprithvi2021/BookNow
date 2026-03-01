# Technical Implementation Roadmap & Checklist

## Overview
This document breaks down the implementation into phases with specific deliverables, acceptance criteria, and testing requirements.

**Total Estimated Effort**: 4-6 hours  
**Implementation Phases**: 6 (can be done sequentially or in parallel)

---

## Phase 1: Project Setup & Infrastructure (30-45 min)

### Goals
- Initialize both backend and frontend projects
- Setup version control and environment
- Create Docker environment for PostgreSQL
- Prepare testing infrastructure

### Deliverables

#### Backend Setup
```
backend/
├── .env (development config)
├── requirements.txt (Python dependencies)
├── pyproject.toml (optional, modern Python packaging)
├── pytest.ini (test configuration)
├── .python-version (for pyenv)
├── Dockerfile (for containerization)
└── src/
    └── __init__.py
```

**Dependencies to Install:**
```
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg[binary]==3.17.0  # PostgreSQL adapter
pydantic==2.5.0
python-dotenv==1.0.0
alembic==1.12.1  # Database migrations
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2  # For testing
```

**Backend .env.example:**
```env
DATABASE_URL=postgresql://user:password@localhost:5432/appointments_db
DEBUG=True
LOG_LEVEL=INFO
NOTIFICATION_POLL_INTERVAL=5
MAX_NOTIFICATION_RETRIES=3
API_PORT=8000
API_HOST=0.0.0.0
FRONTEND_URL=http://localhost:3000
```

#### Frontend Setup
```
frontend/
├── .env.local (development config)
├── next.config.js
├── tailwind.config.js
├── tsconfig.json
├── package.json
├── package-lock.json
├── postcss.config.js
└── src/
    ├── app/
    │   └── layout.tsx
    └── styles/
        └── globals.css
```

**Frontend .env.local.example:**
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=Appointment Booking System
```

**Frontend Dependencies:**
```json
{
  "dependencies": {
    "next": "14.0.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@radix-ui/react-dialog": "latest",
    "@radix-ui/react-form": "latest",
    "@radix-ui/react-label": "latest",
    "@radix-ui/react-slot": "latest",
    "class-variance-authority": "latest",
    "clsx": "latest",
    "tailwind-merge": "latest",
    "tailwindcss": "latest",
    "shadcn-ui": "latest"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^18",
    "@types/react-dom": "^18",
    "typescript": "^5",
    "autoprefixer": "latest",
    "postcss": "latest"
  }
}
```

#### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: appointments_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: appointments_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U appointments_user"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Optional: Add backend and frontend services later
  
volumes:
  postgres_data:
```

### Acceptance Criteria
- [ ] Python 3.11+ activated in venv
- [ ] FastAPI imports work (no errors)
- [ ] PostgreSQL runs in Docker (health check passes)
- [ ] Next.js dev server starts without errors
- [ ] TypeScript compilation succeeds
- [ ] All dependencies installed

### Testing
```bash
# Backend
python -c "import fastapi; print(fastapi.__version__)"

# Frontend  
npm run build  # Should complete without errors

# Docker
docker-compose up --build
# Wait for "postgres_1 | database system is ready to accept connections"
docker-compose down
```

---

## Phase 2: Database Schema & Migrations (45-60 min)

### Goals
- Define SQLAlchemy ORM models
- Create Alembic migrations
- Initialize database
- Write schema tests

### Deliverables

#### SQLAlchemy Models (`src/db/models.py`)

```python
from sqlalchemy import (
    Column, String, DateTime, Date, Time, Boolean, 
    Enum, ForeignKey, UniqueConstraint, Integer, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import uuid
import enum

Base = declarative_base()

class AppointmentStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"

class NotificationEventType(str, enum.Enum):
    BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION"
    CANCELLATION_CONFIRMATION = "CANCELLATION_CONFIRMATION"

class NotificationStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    SENT = "SENT"
    FAILED = "FAILED"

class AvailabilitySlot(Base):
    __tablename__ = "availability_slots"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slot_date = Column(Date, nullable=False)
    slot_time = Column(Time, nullable=False)
    duration_minutes = Column(Integer, default=60)
    is_available = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    appointments = relationship("Appointment", back_populates="slot")
    
    __table_args__ = (
        UniqueConstraint('slot_date', 'slot_time', name='unique_slot_datetime'),
    )

class Appointment(Base):
    __tablename__ = "appointments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    availability_slot_id = Column(UUID(as_uuid=True), ForeignKey("availability_slots.id"), nullable=False)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    notes = Column(String, nullable=True)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.PENDING)
    idempotency_key = Column(UUID(as_uuid=True), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    confirmed_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    version = Column(Integer, default=1)
    
    slot = relationship("AvailabilitySlot", back_populates="appointments")
    notifications = relationship("Notification", back_populates="appointment")
    
    __table_args__ = (
        UniqueConstraint(
            'availability_slot_id', 
            postgresql_where=(status != AppointmentStatus.CANCELLED),
            name='unique_available_slot'
        ),
    )

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUID(as_uuid=True), ForeignKey("appointments.id"), nullable=False)
    event_type = Column(Enum(NotificationEventType), nullable=False)
    status = Column(Enum(NotificationStatus), default=NotificationStatus.QUEUED)
    recipient_email = Column(String(255), nullable=False)
    payload = Column(JSON, nullable=False)
    error_details = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    
    appointment = relationship("Appointment", back_populates="notifications")

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    
    idempotency_key = Column(UUID(as_uuid=True), primary_key=True)
    method = Column(String(10), nullable=False)
    resource_path = Column(String, nullable=False)
    response_status = Column(Integer, nullable=False)
    response_body = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    ttl_expires_at = Column(DateTime, nullable=True)
```

#### Alembic Initialization
```bash
cd backend
alembic init migrations
```

**First Migration** (`versions/001_initial_schema.py`):
```python
# Auto-generate from models:
alembic revision --autogenerate -m "Initial schema"

# Then verify and run:
alembic upgrade head
```

### Acceptance Criteria
- [ ] All 4 tables created in PostgreSQL
- [ ] Unique constraints in place
- [ ] Foreign keys established
- [ ] Indexes on commonly queried columns
- [ ] Alembic migration runs cleanly
- [ ] `psql` can query tables successfully

### Testing
```bash
# Verify schema
psql -h localhost -U appointments_user -d appointments_db \
  -c \dt  # List tables

# Test connection
python -c "
from src.db.connection import get_db
db = next(get_db())
print('Connection successful')
"
```

---

## Phase 3: Service Layer Implementation (90-120 min)

### Goals
- Implement core business logic
- Handle concurrency (pessimistic locking)
- Establish idempotency
- Write unit tests

### Deliverables

#### 1. `src/services/availability_service.py`
```python
"""
Services for querying available appointment slots.
"""

class AvailabilityService:
    
    @staticmethod
    def get_available_slots(
        session: Session,
        start_date: date,
        days: int = 7
    ) -> List[dict]:
        """
        Get all available slots for next N days.
        
        Returns slots that:
        - Fall within date range
        - Are marked is_available=true
        - Don't have confirmed appointments
        """
        # Implementation
        pass

    @staticmethod
    def is_slot_available(session: Session, slot_id: UUID) -> bool:
        """Check if a specific slot is available."""
        pass
```

#### 2. `src/services/appointment_service.py`
```python
"""
Core appointment booking logic with concurrency guarantees.
"""

class AppointmentService:
    
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
        Book appointment with double-booking prevention.
        
        Algorithm:
        1. BEGIN TRANSACTION
        2. SELECT slot FOR UPDATE (acquire lock)
        3. Check is_available
        4. INSERT appointment
        5. INSERT notification (QUEUED)
        6. UPDATE slot is_available=false
        7. COMMIT
        
        Raises:
        - DoubleBookingError if slot taken
        - SlotNotFoundError if slot doesn't exist
        """
        try:
            session.begin_nested()  # Savepoint
            
            # Acquire exclusive lock
            slot = session.query(AvailabilitySlot).with_for_update().filter_by(id=slot_id).one()
            
            # Check availability
            if not slot.is_available:
                raise DoubleBookingError(f"Slot {slot_id} already booked")
            
            # Create appointment
            appointment = Appointment(
                availability_slot_id=slot_id,
                customer_name=customer_name,
                customer_email=customer_email,
                notes=notes,
                status=AppointmentStatus.CONFIRMED,
                idempotency_key=idempotency_key,
                confirmed_at=datetime.utcnow(),
                version=1
            )
            session.add(appointment)
            session.flush()  # Get ID
            
            # Queue notification
            notification = Notification(
                appointment_id=appointment.id,
                event_type=NotificationEventType.BOOKING_CONFIRMATION,
                status=NotificationStatus.QUEUED,
                recipient_email=customer_email,
                payload={
                    "appointment_id": str(appointment.id),
                    "customer_name": customer_name,
                    "slot_date": str(slot.slot_date),
                    "slot_time": str(slot.slot_time)
                }
            )
            session.add(notification)
            
            # Mark slot unavailable
            slot.is_available = False
            
            session.commit()
            return appointment
            
        except IntegrityError:
            session.rollback()
            raise DoubleBookingError("Slot already booked by another request")
    
    @staticmethod
    def cancel_appointment(
        session: Session,
        appointment_id: UUID
    ) -> Appointment:
        """
        Cancel appointment idempotently.
        
        Safe to call multiple times (uses status field).
        """
        session.begin_nested()
        
        appointment = session.query(Appointment).filter_by(id=appointment_id).one_or_none()
        if not appointment:
            raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")
        
        # Idempotency: already cancelled?
        if appointment.status == AppointmentStatus.CANCELLED:
            return appointment
        
        # Mark cancelled
        appointment.status = AppointmentStatus.CANCELLED
        appointment.cancelled_at = datetime.utcnow()
        
        # Queue cancellation notification
        notification = Notification(
            appointment_id=appointment.id,
            event_type=NotificationEventType.CANCELLATION_CONFIRMATION,
            status=NotificationStatus.QUEUED,
            recipient_email=appointment.customer_email,
            payload={"appointment_id": str(appointment.id)}
        )
        session.add(notification)
        
        session.commit()
        return appointment
    
    @staticmethod
    def get_appointment(
        session: Session,
        appointment_id: UUID
    ) -> Optional[Appointment]:
        """Fetch appointment details."""
        return session.query(Appointment).filter_by(id=appointment_id).one_or_none()
```

#### 3. `src/services/idempotency_service.py`
```python
"""
Idempotency key handling for mutation operations.
"""

class IdempotencyService:
    
    @staticmethod
    def get_cached_response(
        session: Session,
        idempotency_key: UUID
    ) -> Optional[dict]:
        """
        Check if this key was already processed.
        Return cached response if found.
        """
        record = session.query(IdempotencyRecord).filter_by(
            idempotency_key=idempotency_key
        ).one_or_none()
        
        if record:
            return {
                "status": record.response_status,
                "body": record.response_body
            }
        return None
    
    @staticmethod
    def store_response(
        session: Session,
        idempotency_key: UUID,
        method: str,
        path: str,
        status: int,
        body: dict
    ) -> None:
        """Store request result for future idempotent replays."""
        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            method=method,
            resource_path=path,
            response_status=status,
            response_body=body,
            ttl_expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        session.add(record)
        session.commit()
```

#### 4. `src/services/notification_service.py`
```python
"""
Notification queue management and background processing.
"""

class NotificationService:
    
    @staticmethod
    def queue_notification(
        session: Session,
        appointment_id: UUID,
        event_type: str,
        recipient_email: str,
        payload: dict
    ) -> Notification:
        """Queue a notification for async processing."""
        notification = Notification(
            appointment_id=appointment_id,
            event_type=event_type,
            status=NotificationStatus.QUEUED,
            recipient_email=recipient_email,
            payload=payload
        )
        session.add(notification)
        session.commit()
        return notification
    
    @staticmethod
    def process_queued_notifications(session: Session) -> int:
        """
        Background job: process all QUEUED notifications.
        
        For each:
        1. Log confirmation (simulated)
        2. Mark SENT
        3. On error: mark FAILED, increment retry_count
        """
        queued = session.query(Notification).filter_by(
            status=NotificationStatus.QUEUED
        ).all()
        
        processed_count = 0
        
        for notification in queued:
            try:
                # Simulate sending notification
                logger.info(f"Sending {notification.event_type} to {notification.recipient_email}")
                
                # Simulated send logic
                # In real system: call Sendgrid, AWS SES, etc.
                
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                session.commit()
                processed_count += 1
                
            except Exception as e:
                notification.status = NotificationStatus.FAILED
                notification.error_details = str(e)
                notification.retry_count += 1
                session.commit()
                logger.error(f"Failed to send notification {notification.id}: {e}")
        
        return processed_count
    
    @staticmethod
    def retry_failed_notifications(
        session: Session,
        max_retries: int = 3
    ) -> int:
        """
        Retry FAILED notifications that haven't exceeded max_retries.
        """
        failed = session.query(Notification).filter(
            Notification.status == NotificationStatus.FAILED,
            Notification.retry_count < max_retries
        ).all()
        
        for notification in failed:
            notification.status = NotificationStatus.QUEUED
            notification.error_details = None
        
        session.commit()
        return len(failed)
```

### Unit Tests (`tests/test_unit/services/`)

**test_appointment_service.py**
```python
def test_book_appointment_success(db_session):
    """Booking creates appointment with CONFIRMED status."""
    slot = create_test_slot(db_session, date(2026, 3, 2), time(9, 0))
    
    appointment = AppointmentService.book_appointment(
        db_session,
        slot_id=slot.id,
        customer_name="John Doe",
        customer_email="john@example.com",
        idempotency_key=uuid4(),
    )
    
    assert appointment.status == AppointmentStatus.CONFIRMED
    assert appointment.confirmed_at is not None
    assert appointment.customer_email == "john@example.com"

def test_double_booking_raises_error(db_session):
    """Booking same slot twice raises DoubleBookingError."""
    slot = create_test_slot(db_session, date(2026, 3, 2), time(9, 0))
    key1, key2 = uuid4(), uuid4()
    
    # First booking succeeds
    AppointmentService.book_appointment(db_session, slot.id, "Jane", "jane@x.com", key1)
    
    # Second booking fails
    with pytest.raises(DoubleBookingError):
        AppointmentService.book_appointment(db_session, slot.id, "John", "john@x.com", key2)

def test_cancel_appointment_idempotent(db_session):
    """Cancelling twice is safe (idempotent)."""
    appointment = create_test_appointment(db_session, AppointmentStatus.CONFIRMED)
    
    # First cancel
    result1 = AppointmentService.cancel_appointment(db_session, appointment.id)
    
    # Second cancel (same result, no error)
    result2 = AppointmentService.cancel_appointment(db_session, appointment.id)
    
    assert result1.id == result2.id
    assert result2.status == AppointmentStatus.CANCELLED
```

**test_idempotency_service.py**
```python
def test_cache_response_on_first_request(db_session):
    """First request stores response for replay."""
    key = uuid4()
    
    # No cache initially
    assert IdempotencyService.get_cached_response(db_session, key) is None
    
    # Store response
    IdempotencyService.store_response(
        db_session, key, "POST", "/api/appointments",
        status=201,
        body={"id": "appt-123", "status": "CONFIRMED"}
    )
    
    # Cache hit on second call
    cached = IdempotencyService.get_cached_response(db_session, key)
    assert cached is not None
    assert cached["status"] == 201

def test_idempotency_key_expires(db_session):
    """Old idempotency records are cleaned up after TTL."""
    key = uuid4()
    IdempotencyService.store_response(db_session, key, "POST", "/", 201, {})
    
    # Fast-forward time (or manually update)
    record = db_session.query(IdempotencyRecord).filter_by(idempotency_key=key).one()
    record.ttl_expires_at = datetime.utcnow() - timedelta(hours=1)
    db_session.commit()
    
    # Cleanup job would remove expired records
    # (implementation detail)
```

### Acceptance Criteria
- [ ] All 4 services implemented with core logic
- [ ] Unit tests pass (100% coverage of services)
- [ ] Concurrency test succeeds (multiple concurrent bookings)
- [ ] Idempotency test passes (duplicate requests safe)
- [ ] Database transactions use proper isolation
- [ ] Error handling in place

### Testing
```bash
pytest tests/test_unit/services/ -v
```

---

## Phase 4: API Routes & Endpoints (60-90 min)

### Goals
- Define HTTP endpoints
- Implement request/response models
- Add error handling middleware
- Add idempotency middleware

### Deliverables

#### Request/Response Schemas (`src/api/schemas/`)

**requests.py**
```python
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID

class BookAppointmentRequest(BaseModel):
    slot_id: UUID
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_email: EmailStr
    notes: Optional[str] = Field(None, max_length=1000)

class GetAvailabilityRequest(BaseModel):
    start_date: Optional[date] = Field(None)
    days: int = Field(default=7, ge=1, le=30)
```

**responses.py**
```python
from pydantic import BaseModel
from uuid import UUID
from datetime import datetime, date, time

class AvailableSlotResponse(BaseModel):
    id: UUID
    date: date
    time: time
    is_booked: bool

class AppointmentResponse(BaseModel):
    id: UUID
    status: str
    customer_name: str
    customer_email: str
    slot_date: date
    slot_time: time
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    notes: Optional[str] = None
```

#### Routes (`src/api/routes/`)

**health.py**
```python
@router.get("/health")
async def health_check(session: Session = Depends(get_db_session)):
    """System health check."""
    try:
        # Test DB connection
        session.execute(text("SELECT 1"))
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```

**availability.py**
```python
@router.get("/api/availability")
async def get_availability(
    start_date: Optional[date] = Query(None),
    days: int = Query(7, ge=1, le=30),
    session: Session = Depends(get_db_session)
):
    """
    Get available appointments for next N days.
    
    Query:
    - start_date: Start date (YYYY-MM-DD), defaults to today
    - days: Number of days (1-30), default 7
    
    Response: List of slots with availability
    """
    if start_date is None:
        start_date = date.today()
    
    slots = AvailabilityService.get_available_slots(session, start_date, days)
    
    return {
        "availableSlots": [
            {
                "id": str(slot.id),
                "date": str(slot.slot_date),
                "time": str(slot.slot_time),
                "isBooked": not slot.is_available
            }
            for slot in slots
        ]
    }
```

**appointments.py**
```python
@router.post("/api/appointments", status_code=201)
async def book_appointment(
    request: BookAppointmentRequest,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session)
):
    """
    Book an appointment.
    
    Header: Idempotency-Key (UUID)
    Body: {slot_id, customer_name, customer_email, notes?}
    
    Response: 201 Created with appointment details
    Errors: 409 Conflict (double-booking), 400 Bad Request (validation)
    """
    # Check idempotency cache
    cached = IdempotencyService.get_cached_response(session, idempotency_key)
    if cached:
        return cached["body"], cached["status"]
    
    try:
        appointment = AppointmentService.book_appointment(
            session,
            slot_id=request.slot_id,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            idempotency_key=idempotency_key,
            notes=request.notes
        )
        
        response_data = {
            "id": str(appointment.id),
            "status": appointment.status.value,
            "confirmedAt": appointment.confirmed_at.isoformat(),
            "customerName": appointment.customer_name,
            "customerEmail": appointment.customer_email
        }
        
        # Store for idempotent replays
        IdempotencyService.store_response(
            session, idempotency_key, "POST", "/api/appointments",
            status=201, body=response_data
        )
        
        return response_data, 201
        
    except DoubleBookingError:
        return {"error": "slot_already_booked", "message": "This slot was just booked"}, 409
    except Exception as e:
        return {"error": "booking_failed", "message": str(e)}, 400

@router.get("/api/appointments/{appointment_id}")
async def get_appointment(
    appointment_id: UUID,
    session: Session = Depends(get_db_session)
):
    """Get appointment details."""
    appointment = AppointmentService.get_appointment(session, appointment_id)
    
    if not appointment:
        return {"error": "not_found"}, 404
    
    return {
        "id": str(appointment.id),
        "status": appointment.status.value,
        "customerName": appointment.customer_name,
        "customerEmail": appointment.customer_email,
        "slotDate": str(appointment.slot.slot_date),
        "slotTime": str(appointment.slot.slot_time),
        "confirmedAt": appointment.confirmed_at.isoformat() if appointment.confirmed_at else None,
        "cancelledAt": appointment.cancelled_at.isoformat() if appointment.cancelled_at else None,
        "notes": appointment.notes
    }

@router.delete("/api/appointments/{appointment_id}")
async def cancel_appointment(
    appointment_id: UUID,
    idempotency_key: UUID = Header(..., alias="Idempotency-Key"),
    session: Session = Depends(get_db_session)
):
    """
    Cancel an appointment (idempotent).
    
    Header: Idempotency-Key (UUID)
    Response: 200 OK with updated appointment
    """
    # Check idempotency cache
    cached = IdempotencyService.get_cached_response(session, idempotency_key)
    if cached:
        return cached["body"], cached["status"]
    
    try:
        appointment = AppointmentService.cancel_appointment(session, appointment_id)
        
        response_data = {
            "id": str(appointment.id),
            "status": appointment.status.value,
            "cancelledAt": appointment.cancelled_at.isoformat() if appointment.cancelled_at else None
        }
        
        IdempotencyService.store_response(
            session, idempotency_key, "DELETE", f"/api/appointments/{appointment_id}",
            status=200, body=response_data
        )
        
        return response_data, 200
        
    except AppointmentNotFoundError:
        return {"error": "not_found"}, 404
```

#### Middleware (`src/api/middleware/`)

**error_handler.py**
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup/shutdown."""
    # Startup
    logger.info("Application starting")
    yield
    # Shutdown
    logger.info("Application shutting down")

def add_error_handlers(app: FastAPI):
    """Register global exception handlers."""
    
    @app.exception_handler(DoubleBookingError)
    async def double_booking_handler(request, exc):
        return JSONResponse(
            status_code=409,
            content={"error": "slot_already_booked", "message": str(exc)}
        )
    
    @app.exception_handler(AppointmentNotFoundError)
    async def not_found_handler(request, exc):
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": str(exc)}
        )
    
    @app.exception_handler(Exception)
    async def generic_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"error": "internal_error", "message": "Internal server error"}
        )
```

**idempotency.py**
```python
# Optional middleware for extracting idempotency key
# Can also be passed as route parameter
```

#### Main App (`src/main.py`)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio

from src.api import routes
from src.api.middleware import error_handlers
from src.core import config
from src.background.notification_worker import start_notification_worker

@asynccontextmanager
async def lifespan(app: FastAPI):
    """App lifecycle management."""
    # Startup
    logger.info("Starting appointment booking system")
    
    # Start background workers
    notification_task = asyncio.create_task(start_notification_worker())
    
    yield
    
    # Shutdown
    logger.info("Shutting down")
    notification_task.cancel()

app = FastAPI(
    title="Appointment Booking API",
    description="Minimal appointment booking system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routes.health.router)
app.include_router(routes.availability.router)
app.include_router(routes.appointments.router)

# Error handlers
error_handlers.add_error_handlers(app)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=config.API_HOST,
        port=config.API_PORT
    )
```

### Integration Tests (`tests/test_integration/`)

**test_api_endpoints.py**
```python
def test_book_appointment_success(client, db_session):
    """POST /api/appointments creates appointment."""
    slot = create_test_slot(db_session)
    
    response = client.post(
        "/api/appointments",
        json={
            "slot_id": str(slot.id),
            "customer_name": "John Doe",
            "customer_email": "john@example.com",
            "notes": "Please remind me 24h before"
        },
        headers={"Idempotency-Key": str(uuid4())}
    )
    
    assert response.status_code == 201
    assert response.json()["status"] == "CONFIRMED"

def test_double_booking_returns_409(client, db_session):
    """Booking same slot twice returns 409 Conflict."""
    slot = create_test_slot(db_session)
    
    # First booking
    client.post(
        "/api/appointments",
        json={...},
        headers={"Idempotency-Key": str(uuid4())}
    )
    
    # Second booking same slot
    response = client.post(
        "/api/appointments",
        json={...},
        headers={"Idempotency-Key": str(uuid4())}
    )
    
    assert response.status_code == 409
    assert "already_booked" in response.json()["error"]
```

### Acceptance Criteria
- [ ] GET /health returns 200
- [ ] GET /api/availability returns slot list
- [ ] POST /api/appointments with valid input returns 201
- [ ] POST /api/appointments (double-book) returns 409
- [ ] GET /api/appointments/{id} returns appointment details
- [ ] DELETE /api/appointments/{id} returns 200 with CANCELLED status
- [ ] Idempotency key prevents duplicates
- [ ] All error cases return proper status codes

### Testing
```bash
pytest tests/test_integration/test_api_endpoints.py -v
python -m pytest tests/ --cov=src
```

---

## Phase 5: Frontend Components (90-120 min)

### Goals
- Build Next.js pages and components
- Integrate with shadcn/ui
- Implement data fetching hooks
- Handle error states

### Deliverables

#### Next.js Pages

**app/page.tsx** (Home - Book Appointment)
```typescript
'use client';

import { useState } from 'react';
import AvailabilityCalendar from '@/components/availability/AvailabilityCalendar';
import BookingForm from '@/components/booking/BookingForm';
import ConfirmationDialog from '@/components/ConfirmationDialog';
import ErrorAlert from '@/components/ErrorAlert';

export default function HomePage() {
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [bookingError, setBookingError] = useState(null);
  
  return (
    <main className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-6">Book an Appointment</h1>
      
      {bookingError && <ErrorAlert message={bookingError} />}
      
      <div className="grid grid-cols-2 gap-8">
        <AvailabilityCalendar onSlotSelect={setSelectedSlot} />
        <BookingForm selectedSlot={selectedSlot} />
      </div>
      
      {showConfirmation && <ConfirmationDialog ... />}
    </main>
  );
}
```

**app/appointments/page.tsx** (View Bookings)
```typescript
'use client';

import { useEffect, useState } from 'react';
import AppointmentsList from '@/components/appointments/AppointmentsList';
import { useAppointments } from '@/hooks/useAppointments';

export default function AppointmentsPage() {
  const [email, setEmail] = useState('');
  const { appointments, loading, error, fetch } = useAppointments();
  
  const handleSearch = () => {
    fetch(email);
  };
  
  return (
    <main className="container mx-auto py-8">
      <h1 className="text-2xl font-bold mb-4">My Appointments</h1>
      
      <div className="flex gap-4 mb-4">
        <input
          type="email"
          placeholder="Enter your email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Button onClick={handleSearch}>Search</Button>
      </div>
      
      {loading && <p>Loading...</p>}
      {error && <ErrorAlert message={error} />}
      {appointments && <AppointmentsList appointments={appointments} />}
    </main>
  );
}
```

#### Components

**components/availability/AvailabilityCalendar.tsx**
```typescript
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useAvailability } from '@/hooks/useAvailability';

interface Props {
  onSlotSelect: (slot: any) => void;
}

export default function AvailabilityCalendar({ onSlotSelect }: Props) {
  const { slots, loading } = useAvailability();
  
  if (loading) return <div>Loading slots...</div>;
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Available Slots (Next 7 Days)</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-3 gap-2">
          {slots.map((slot) => (
            <Button
              key={slot.id}
              variant={slot.isBooked ? "disabled" : "outline"}
              onClick={() => onSlotSelect(slot)}
              disabled={slot.isBooked}
            >
              {slot.date} {slot.time}
            </Button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
```

**components/booking/BookingForm.tsx**
```typescript
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { useBooking } from '@/hooks/useBooking';

interface Props {
  selectedSlot: any;
}

export default function BookingForm({ selectedSlot }: Props) {
  const { form, isLoading, onSubmit } = useBooking(selectedSlot);
  
  if (!selectedSlot) {
    return <p className="text-gray-500">Select a time slot first</p>;
  }
  
  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)}>
        <FormField
          name="customer_name"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Name</FormLabel>
              <FormControl>
                <Input placeholder="John Doe" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          name="customer_email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="john@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <FormField
          name="notes"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Notes (Optional)</FormLabel>
              <FormControl>
                <Textarea placeholder="Any special requests..." {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        
        <Button type="submit" disabled={isLoading}>
          {isLoading ? 'Booking...' : 'Book Appointment'}
        </Button>
      </form>
    </Form>
  );
}
```

**components/appointments/AppointmentsList.tsx**
```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import AppointmentCard from './AppointmentCard';

interface Props {
  appointments: any[];
}

export default function AppointmentsList({ appointments }: Props) {
  return (
    <div className="space-y-4">
      {appointments.length === 0 ? (
        <p className="text-gray-500">No appointments found</p>
      ) : (
        appointments.map((appt) => (
          <AppointmentCard key={appt.id} appointment={appt} />
        ))
      )}
    </div>
  );
}
```

**components/appointments/AppointmentCard.tsx**
```typescript
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useAppointments } from '@/hooks/useAppointments';

interface Props {
  appointment: any;
}

export default function AppointmentCard({ appointment }: Props) {
  const { cancel } = useAppointments();
  const [isCancelling, setIsCancelling] = React.useState(false);
  
  const handleCancel = async () => {
    setIsCancelling(true);
    try {
      await cancel(appointment.id);
    } finally {
      setIsCancelling(false);
    }
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>{appointment.customer_name}</CardTitle>
        <Badge variant={appointment.status === 'CONFIRMED' ? 'default' : 'secondary'}>
          {appointment.status}
        </Badge>
      </CardHeader>
      <CardContent>
        <p><strong>Date:</strong> {appointment.slotDate}</p>
        <p><strong>Time:</strong> {appointment.slotTime}</p>
        <p><strong>Email:</strong> {appointment.customerEmail}</p>
        {appointment.notes && <p><strong>Notes:</strong> {appointment.notes}</p>}
        
        {appointment.status === 'CONFIRMED' && (
          <Button
            variant="destructive"
            onClick={handleCancel}
            disabled={isCancelling}
          >
            Cancel Appointment
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
```

#### Custom Hooks

**hooks/useAvailability.ts**
```typescript
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface AvailableSlot {
  id: string;
  date: string;
  time: string;
  isBooked: boolean;
}

export function useAvailability() {
  const [slots, setSlots] = useState<AvailableSlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchSlots = async () => {
      try {
        setLoading(true);
        const response = await apiClient.get('/api/availability');
        setSlots(response.availableSlots);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };
    
    fetchSlots();
  }, []);
  
  return { slots, loading, error };
}
```

**hooks/useBooking.ts**
```typescript
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { apiClient } from '@/lib/api-client';

const bookingSchema = z.object({
  customer_name: z.string().min(1),
  customer_email: z.string().email(),
  notes: z.string().optional()
});

export function useBooking(selectedSlot: any) {
  const [isLoading, setIsLoading] = useState(false);
  const form = useForm({
    resolver: zodResolver(bookingSchema)
  });
  
  const onSubmit = async (data: any) => {
    if (!selectedSlot) return;
    
    setIsLoading(true);
    try {
      const response = await apiClient.post('/api/appointments', {
        slot_id: selectedSlot.id,
        ...data
      });
      
      // Show confirmation
      alert(`Appointment confirmed! ID: ${response.id}`);
      form.reset();
      
    } catch (error) {
      form.setError('root', { message: error.message });
    } finally {
      setIsLoading(false);
    }
  };
  
  return { form, isLoading, onSubmit };
}
```

**hooks/useAppointments.ts**
```typescript
import { useState } from 'react';
import { apiClient } from '@/lib/api-client';

export function useAppointments() {
  const [appointments, setAppointments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetch = async (email: string) => {
    try {
      setLoading(true);
      // Implementation: query backend for appointments by email
      // GET /api/appointments?email=...
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  const cancel = async (appointmentId: string) => {
    try {
      await apiClient.delete(`/api/appointments/${appointmentId}`);
      // Refetch appointments
      setAppointments(appointments.filter(a => a.id !== appointmentId));
    } catch (err) {
      setError(err.message);
    }
  };
  
  return { appointments, loading, error, fetch, cancel };
}
```

#### API Client

**lib/api-client.ts**
```typescript
import { v4 as uuidv4 } from 'uuid';

class ApiClient {
  baseUrl: string;
  
  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
  }
  
  private generateIdempotencyKey(): string {
    return uuidv4();
  }
  
  async request(
    method: 'GET' | 'POST' | 'DELETE',
    path: string,
    options?: any
  ) {
    const headers = {
      'Content-Type': 'application/json',
      ...options?.headers
    };
    
    // Add idempotency key for mutations
    if (['POST', 'DELETE'].includes(method)) {
      headers['Idempotency-Key'] = this.generateIdempotencyKey();
    }
    
    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers,
      body: options?.body ? JSON.stringify(options.body) : undefined
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || `HTTP ${response.status}`);
    }
    
    return response.json();
  }
  
  get(path: string, options?: any) {
    return this.request('GET', path, options);
  }
  
  post(path: string, body: any, options?: any) {
    return this.request('POST', path, { ...options, body });
  }
  
  delete(path: string, options?: any) {
    return this.request('DELETE', path, options);
  }
}

export const apiClient = new ApiClient();
```

### Acceptance Criteria
- [ ] Home page renders without errors
- [ ] AvailabilityCalendar loads and displays slots
- [ ] Can select slot and fill booking form
- [ ] Booking submits successfully (201 response)
- [ ] Appointments page shows booked appointments
- [ ] Can cancel appointment
- [ ] Error messages display properly
- [ ] Responsive design (mobile + desktop)

### Testing
```bash
npm run build
npm run dev
# Test at http://localhost:3000
```

---

## Phase 6: Background Processing & Integration (60-90 min)

### Goals
- Implement notification worker
- Test concurrent scenarios
- Write integration tests
- Final polish and documentation

### Deliverables

#### Background Worker (`src/background/notification_worker.py`)

```python
"""Background notification processing."""

import asyncio
from datetime import datetime
from src.db.connection import SessionLocal
from src.services.notification_service import NotificationService
from src.utils.logger import logger

async def notification_worker():
    """
    Background task: process queued notifications every N seconds.
    
    Runs continuously in background.
    """
    while True:
        try:
            session = SessionLocal()
            
            # Process queued notifications
            processed = NotificationService.process_queued_notifications(session)
            if processed > 0:
                logger.info(f"Processed {processed} notifications")
            
            # Retry failed notifications
            retried = NotificationService.retry_failed_notifications(session, max_retries=3)
            if retried > 0:
                logger.info(f"Retried {retried} failed notifications")
            
            session.close()
            
        except Exception as e:
            logger.error(f"Notification worker error: {e}")
        
        finally:
            # Wait before next poll
            await asyncio.sleep(5)  # configurable interval

async def start_notification_worker():
    """Start notification worker task."""
    await notification_worker()
```

#### Concurrency Tests (`tests/test_integration/test_concurrency.py`)

```python
import asyncio
import pytest
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

def test_concurrent_bookings_same_slot(db_session):
    """
    10 concurrent requests for same slot.
    Only 1 should succeed, others return 409 Conflict.
    """
    slot = create_test_slot(db_session)
    
    def book_attempt():
        service = AppointmentService()
        try:
            return service.book_appointment(
                db_session, slot.id, "Test", "test@example.com",
                idempotency_key=uuid4()
            )
        except DoubleBookingError:
            return None
    
    # Run 10 concurrent bookings
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(lambda _: book_attempt(), range(10)))
    
    # Verify: exactly 1 succeeded, 9 failed
    successes = [r for r in results if r is not None]
    assert len(successes) == 1
    assert successes[0].status == AppointmentStatus.CONFIRMED
    
    # Verify database consistency
    appts = db_session.query(Appointment).filter_by(
        availability_slot_id=slot.id
    ).all()
    assert len(appts) == 1

def test_concurrent_cancel_attempts(db_session):
    """
    Multiple concurrent cancels of same appointment.
    Should handle gracefully (idempotent).
    """
    appt = create_test_appointment(db_session, AppointmentStatus.CONFIRMED)
    
    def cancel_attempt():
        try:
            return AppointmentService.cancel_appointment(db_session, appt.id)
        except Exception as e:
            return str(e)
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: cancel_attempt(), range(5)))
    
    # All should succeed or return same result
    assert all(r is not None for r in results)
    
    # DB should show single cancelled appointment
    db_appt = db_session.query(Appointment).filter_by(id=appt.id).one()
    assert db_appt.status == AppointmentStatus.CANCELLED

def test_idempotency_under_stress(db_session):
    """
    Submit same booking 5 times concurrently.
    Only 1 appointment created despite multiple requests.
    """
    slot = create_test_slot(db_session)
    key = uuid4()
    
    def book_with_key():
        return AppointmentService.book_appointment(
            db_session, slot.id, "John", "john@x.com",
            idempotency_key=key
        )
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(lambda _: book_with_key(), range(5)))
    
    # All results should have same appointment ID
    appointment_ids = [r.id for r in results]
    assert len(set(appointment_ids)) == 1  # All same ID
    
    # Only 1 appointment in DB
    appts = db_session.query(Appointment).filter_by(
        availability_slot_id=slot.id
    ).all()
    assert len(appts) == 1
```

#### Idempotency Tests (`tests/test_integration/test_idempotency.py`)

```python
def test_booking_idempotency_retry(db_session):
    """
    Submit booking twice with same idempotency key.
    Second returns same response without creating duplicate.
    """
    slot = create_test_slot(db_session)
    key = uuid4()
    
    # First booking
    appt1 = AppointmentService.book_appointment(
        db_session, slot.id, "Jane", "jane@x.com", key
    )
    
    # Second booking (same key, simulating retry)
    appt2 = AppointmentService.book_appointment(
        db_session, slot.id, "Jane", "jane@x.com", key
    )
    
    # Should return same appointment ID
    assert appt1.id == appt2.id
    
    # Only 1 appointment created
    count = db_session.query(Appointment).filter_by(availability_slot_id=slot.id).count()
    assert count == 1

def test_cancel_idempotency_retry(db_session):
    """
    Submit cancel twice with same idempotency key.
    Both should succeed idempotently.
    """
    appt = create_test_appointment(db_session, AppointmentStatus.CONFIRMED)
    key = uuid4()
    
    # First cancel
    result1 = AppointmentService.cancel_appointment(db_session, appt.id)
    result1_cached = IdempotencyService.store_response(
        db_session, key, "DELETE", f"/api/appointments/{appt.id}",
        status=200, body={"id": str(appt.id), "status": "CANCELLED"}
    )
    
    # Retrieve from cache
    cached = IdempotencyService.get_cached_response(db_session, key)
    
    # Should return same result
    assert cached is not None
    assert cached["status"] == 200
```

#### End-to-End Test

**tests/test_integration/test_e2e.py**
```python
def test_full_booking_flow(client, db_session):
    """
    Complete user flow:
    1. Get available slots
    2. Book appointment
    3. View appointment
    4. Cancel appointment
    """
    
    # Step 1: Get availability
    resp1 = client.get("/api/availability?days=7")
    assert resp1.status_code == 200
    slots = resp1.json()["availableSlots"]
    assert len(slots) > 0
    slot_id = slots[0]["id"]
    
    # Step 2: Book
    key1 = str(uuid4())
    resp2 = client.post(
        "/api/appointments",
        json={
            "slot_id": slot_id,
            "customer_name": "Alice",
            "customer_email": "alice@example.com",
            "notes": "Please print reminder"
        },
        headers={"Idempotency-Key": key1}
    )
    assert resp2.status_code == 201
    appt_id = resp2.json()["id"]
    
    # Step 3: Get appointment
    resp3 = client.get(f"/api/appointments/{appt_id}")
    assert resp3.status_code == 200
    assert resp3.json()["status"] == "CONFIRMED"
    
    # Step 4: Cancel
    key2 = str(uuid4())
    resp4 = client.delete(
        f"/api/appointments/{appt_id}",
        headers={"Idempotency-Key": key2}
    )
    assert resp4.status_code == 200
    assert resp4.json()["status"] == "CANCELLED"
    
    # Verify: slot is now available again
    resp5 = client.get("/api/availability?days=7")
    updated_slots = resp5.json()["availableSlots"]
    slot_updated = next(s for s in updated_slots if s["id"] == slot_id)
    assert slot_updated["isBooked"] == False
```

### Acceptance Criteria
- [ ] Notification worker starts with app
- [ ] Processes QUEUED notifications within 5 seconds
- [ ] Concurrent booking test passes (no double-books)
- [ ] Idempotency test passes (no duplicate appointments)
- [ ] End-to-end test passes (full booking flow)
- [ ] Load test (50+ concurrent requests) passes
- [ ] All integration tests pass
- [ ] API response times < 100ms under load

### Testing
```bash
# Run all tests
pytest tests/ -v

# Concurrency tests only
pytest tests/test_integration/test_concurrency.py -v

# Load test
pytest tests/test_integration/test_load.py -v --benchmark-only

# E2E test
pytest tests/test_integration/test_e2e.py -v
```

---

## Phase 7: Documentation & Final Polish (30-45 min)

### Goals
- Write comprehensive README
- Create API specification document
- Diagram system architecture
- Final testing and validation

### Deliverables

#### README.md (Root)
```markdown
# Appointment Booking System

Minimal but production-ready appointment booking system built with Python FastAPI + Next.js.

## Features

✅ Double-booking prevention (ACID guarantees)
✅ Idempotent mutations (safe for retries)
✅ Async notification processing with audit trail
✅ Type-safe API (Pydantic + TypeScript)
✅ Comprehensive error handling
✅ Full test coverage (unit + integration + concurrency)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Docker & Docker Compose (optional)

### Setup with Docker

```bash
docker-compose up
```

Backend: http://localhost:8000
Frontend: http://localhost:3000

### Manual Setup

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m src.main
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Architecture

[See ARCHITECTURE.md](./ARCHITECTURE.md) for detailed design.

Key principles:
- Database as source of truth
- Explicit state machines
- Decoupled notification processing
- Complete audit trails

## API Endpoints

[See API_SPEC.md](./docs/API_SPEC.md) for full specification.

- GET /api/availability - List available slots
- POST /api/appointments - Book appointment (idempotent)
- GET /api/appointments/{id} - Get appointment details
- DELETE /api/appointments/{id} - Cancel appointment (idempotent)

## Testing

```bash
# Unit + integration tests
pytest tests/ -v

# Concurrency tests
pytest tests/test_integration/test_concurrency.py -v

# Load testing
pytest tests/test_integration/test_load.py -v
```

## Data Model

**availability_slots**: Pre-populated appointment slots
**appointments**: Customer bookings with status (PENDING, CONFIRMED, CANCELLED)
**notifications**: Notification queue and audit trail
**idempotency_records**: Cached responses for safe retries

[See docs/DATABASE_SCHEMA.md](./docs/DATABASE_SCHEMA.md)

## Key Design Decisions

1. **Pessimistic Locking**: Row-level locks prevent double-booking. Simple, reliable.
2. **Idempotency Keys**: All mutations include UUID to prevent duplicates on retries.
3. **Immutable Cancellation**: Cancelled appointments never revert (audit trail).
4. **Async Notifications**: Decoupled from booking (fast API, reliable delivery).
5. **In-Process Queue**: Sufficient for scope; easy migration to Celery/RabbitMQ.

## Known Limitations

- No authentication/authorization
- Notifications logged (not emailed)
- Single timezone support
- Single-provider scheduling only

## Future Improvements

- [ ] Real email notifications (Sendgrid, SES)
- [ ] Multi-provider scheduling
- [ ] Timezone support
- [ ] Admin calendar management UI
- [ ] Rate limiting
- [ ] Calendar sync (Google, Outlook)

## Deployment

Production checklist:
- [ ] Use managed PostgreSQL
- [ ] Set strong env passwords
- [ ] Configure real email service
- [ ] Enable HTTPS
- [ ] Setup monitoring/logging
- [ ] Load test before launch

See [docs/DEPLOYMENT.md](./docs/DEPLOYMENT.md) for detailed steps.
```

#### API_SPEC.md
```markdown
# API Specification

## GET /api/availability

Get available appointment slots for next N days.

**Query Parameters:**
- `start_date` (optional): YYYY-MM-DD format, defaults to today
- `days` (optional): Number of days (1-30), default 7

**Response:**
```json
{
  "availableSlots": [
    {
      "id": "uuid",
      "date": "2026-03-02",
      "time": "09:00",
      "isBooked": false
    }
  ]
}
```

## POST /api/appointments

Book an appointment (idempotent).

**Headers:**
- `Idempotency-Key` (required): UUID to prevent duplicate bookings on retry

**Request Body:**
```json
{
  "slot_id": "uuid",
  "customer_name": "John Doe",
  "customer_email": "john@example.com",
  "notes": "optional text"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "status": "CONFIRMED",
  "confirmedAt": "2026-03-02T09:00:00Z",
  "customerName": "John Doe",
  "customerEmail": "john@example.com"
}
```

**Errors:**
- `400 Bad Request`: Invalid input
- `409 Conflict`: Slot already booked
- `500 Internal Error`: Server error

## GET /api/appointments/{id}

Get appointment details.

**Response:**
```json
{
  "id": "uuid",
  "status": "CONFIRMED",
  "customerName": "John Doe",
  "customerEmail": "john@example.com",
  "slotDate": "2026-03-02",
  "slotTime": "09:00",
  "confirmedAt": "2026-03-02T09:00:00Z",
  "notes": "optional note"
}
```

## DELETE /api/appointments/{id}

Cancel appointment (idempotent).

**Headers:**
- `Idempotency-Key` (required): UUID

**Response (200 OK):**
```json
{
  "id": "uuid",
  "status": "CANCELLED",
  "cancelledAt": "2026-03-02T09:10:00Z"
}
```

**Errors:**
- `404 Not Found`: Appointment doesn't exist
- `409 Conflict`: Already cancelled
```

#### docs/CONCURRENCY_DESIGN.md
Content showing race condition analysis, locking strategy, and test scenarios.

#### docs/DATABASE_SCHEMA.md
SQL schema with constraints, indexes, relationships.

#### Architecture Diagram (Excalidraw format)
Visual representation of API, services, DB, notification flow.

### Acceptance Criteria
- [ ] README covers setup, architecture, API
- [ ] API spec documents all endpoints with examples
- [ ] Concurrency design documented with diagrams
- [ ] All code commented and clear
- [ ] Trade-offs documented
- [ ] Known limitations listed
- [ ] Future improvements identified

### Final Validation Checklist
- [ ] Code runs without errors
- [ ] All tests pass (unit + integration + concurrency)
- [ ] API spec matches implementation
- [ ] Error handling works for all scenarios
- [ ] Idempotency tested thoroughly
- [ ] Notifications process correctly
- [ ] Frontend runs without errors
- [ ] Docker setup validated
- [ ] README is clear and complete

---

## Summary of Phases

| Phase | Focus | Effort | Status |
|-------|-------|--------|--------|
| 1 | Setup & infrastructure | 30-45min | Not started |
| 2 | Database & models | 45-60min | Not started |
| 3 | Service layer | 90-120min | Not started |
| 4 | API routes | 60-90min | Not started |
| 5 | Frontend | 90-120min | Not started |
| 6 | Background + tests | 60-90min | Not started |
| 7 | Docs + polish | 30-45min | Not started |
| **Total** | **Full system** | **4-6 hours** | **Ready to begin** |

---

## Quality Gates

Before each phase submission:
✅ Code compiles/runs without errors
✅ Tests pass for that phase
✅ No console errors or warnings
✅ Type safety (TypeScript + type hints)
✅ Clear commit messages

---

Now let's start coding! Which phase would you like to begin with?
