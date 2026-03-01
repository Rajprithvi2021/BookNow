# Directory Structure & Project Setup Plan

## Project Root Layout
```
appointment-booking-system/
├── README.md                          # Main project readme with setup instructions
├── ARCHITECTURE.md                    # This architecture document
├── docker-compose.yml                 # Local development environment
├── .gitignore                         # Git ignore rules
├── .env.example                       # Environment variables template
│
├── backend/                           # Python FastAPI backend
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py                   # FastAPI app initialization & startup
│   │   │
│   │   ├── api/                      # HTTP API layer
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── health.py         # GET /health
│   │   │   │   ├── availability.py   # GET /api/availability
│   │   │   │   └── appointments.py   # POST, GET, DELETE /api/appointments
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── requests.py       # Pydantic input models
│   │   │   │   └── responses.py      # Pydantic output models
│   │   │   ├── middleware/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── error_handler.py  # Global exception handling
│   │   │   │   └── idempotency.py    # Idempotency key middleware
│   │   │   └── dependencies.py       # FastAPI Depends() utilities
│   │   │
│   │   ├── core/                     # Core configuration
│   │   │   ├── __init__.py
│   │   │   ├── config.py             # Settings from env vars
│   │   │   ├── constants.py          # Business rules (hours, duration)
│   │   │   └── enums.py              # Shared enums (AppointmentStatus, etc)
│   │   │
│   │   ├── db/                       # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── connection.py         # SQLAlchemy engine & session factory
│   │   │   ├── models.py             # SQLAlchemy ORM models
│   │   │   ├── base.py               # Base class for models
│   │   │   └── migrations/
│   │   │       ├── env.py            # Alembic config
│   │   │       ├── script.py.mako    # Alembic template
│   │   │       └── versions/
│   │   │           └── (migration files here)
│   │   │
│   │   ├── services/                 # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── base_service.py       # Base service with common patterns
│   │   │   ├── appointment_service.py   # Booking, cancellation logic
│   │   │   ├── availability_service.py  # Slot availability queries
│   │   │   ├── notification_service.py  # Queue + background processing
│   │   │   └── idempotency_service.py   # Idempotency key tracking
│   │   │
│   │   ├── utils/                    # Utility functions
│   │   │   ├── __init__.py
│   │   │   ├── logger.py             # Structured logging setup
│   │   │   ├── exceptions.py         # Custom exception classes
│   │   │   ├── validators.py         # Input validation helpers
│   │   │   └── datetime_utils.py     # Date/time utilities
│   │   │
│   │   └── background/               # Background tasks
│   │       ├── __init__.py
│   │       └── notification_worker.py # Async notification processor
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py               # pytest fixtures & configuration
│   │   ├── test_unit/
│   │   │   ├── __init__.py
│   │   │   ├── services/
│   │   │   │   ├── test_appointment_service.py
│   │   │   │   ├── test_availability_service.py
│   │   │   │   └── test_idempotency_service.py
│   │   │   └── utils/
│   │   │       └── test_validators.py
│   │   └── test_integration/
│   │       ├── __init__.py
│   │       ├── test_concurrency.py    # Race condition tests
│   │       ├── test_idempotency.py    # Retry safety tests
│   │       ├── test_api_endpoints.py  # Full request/response tests
│   │       └── fixtures/
│   │           └── test_data.py       # Test data setup
│   │
│   ├── requirements.txt               # Python dependencies
│   ├── .env.example                   # Backend env vars template
│   ├── alembic.ini                    # Database migration config
│   ├── pytest.ini                     # Testing config
│   └── README.md                      # Backend-specific setup
│
├── frontend/                          # Next.js React frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx             # Root layout (navbar, providers)
│   │   │   ├── page.tsx               # Home: availability + booking form
│   │   │   ├── appointments/
│   │   │   │   └── page.tsx           # View existing bookings
│   │   │   └── error.tsx              # Error boundary
│   │   │
│   │   ├── components/
│   │   │   ├── (shared components)
│   │   │   ├── availability/
│   │   │   │   ├── AvailabilityCalendar.tsx
│   │   │   │   └── SlotCard.tsx
│   │   │   ├── booking/
│   │   │   │   ├── BookingForm.tsx
│   │   │   │   ├── BookingDialog.tsx
│   │   │   │   └── SuccessMessage.tsx
│   │   │   ├── appointments/
│   │   │   │   ├── AppointmentsList.tsx
│   │   │   │   ├── AppointmentCard.tsx
│   │   │   │   └── CancelDialog.tsx
│   │   │   └── common/
│   │   │       ├── Header.tsx
│   │   │       ├── LoadingState.tsx
│   │   │       ├── ErrorAlert.tsx
│   │   │       └── Footer.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── api-client.ts          # Fetch wrapper + idempotency key gen
│   │   │   ├── utils.ts               # Formatting & misc helpers
│   │   │   └── constants.ts           # API URL, config
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAppointments.ts     # Fetch user's appointments
│   │   │   ├── useAvailability.ts     # Fetch available slots
│   │   │   ├── useBooking.ts          # Booking form state & submission
│   │   │   └── useMutation.ts         # Generic mutation hook
│   │   │
│   │   ├── types/
│   │   │   └── api.ts                 # TypeScript interfaces for API
│   │   │
│   │   └── styles/
│   │       └── globals.css            # Tailwind + global styles
│   │
│   ├── public/
│   │   └── (static assets)
│   │
│   ├── .env.local.example             # Frontend env vars template
│   ├── next.config.js                 # Next.js configuration
│   ├── tailwind.config.js             # Tailwind CSS config
│   ├── tsconfig.json                  # TypeScript configuration
│   ├── package.json
│   ├── package-lock.json
│   └── README.md                      # Frontend-specific setup
│
└── docs/
    ├── ARCHITECTURE.md                # High-level system design
    ├── API_SPEC.md                    # Detailed API endpoint documentation
    ├── CONCURRENCY_DESIGN.md          # Race condition analysis & solutions
    ├── DATABASE_SCHEMA.md             # SQL schema & relationships
    ├── TESTING_STRATEGY.md            # Testing approach & examples
    └── DEPLOYMENT.md                  # Docker, environment setup
```

---

## Backend Structure Rationale

### Layer Separation
```
API Routes (endpoints)
    ↓
Middleware (auth, validation, error handling)
    ↓
Services (business logic, transactions)
    ↓
Database Models (ORM, queries)
    ↓
PostgreSQL (source of truth)
```

### File Purposes

**`api/routes/`** - FastAPI route handlers
- Thin layer: parse request → call service → return response
- No business logic here
- All validation via Pydantic schemas

**`api/schemas/`** - Request/Response models
- Pydantic definitions for input validation
- Ensures type safety on API boundary
- Auto-generates OpenAPI/Swagger docs

**`services/`** - Business logic & transactions
- Core appointment booking logic
- Database transactions with locking
- Notification queue management
- Idempotency key handling
- All invariants enforced here

**`db/models.py`** - SQLAlchemy ORM definitions
- Table definitions
- Relationships
- Database constraints
- No transactions here (handled in services)

**`utils/exceptions.py`** - Custom exceptions
- `DoubleBookingError` - slot already taken
- `AppointmentNotFoundError` - cancel non-existent
- `IdempotencyKeyMismatchError` - conflicting idempotency
- Middleware converts to HTTP responses

**`background/notification_worker.py`** - Async task processor
- Runs every N seconds
- Polls notifications table for QUEUED status
- Updates status to SENT or FAILED
- Retries with exponential backoff

### Import Pattern
```python
# routes/appointments.py references:
from ..services.appointment_service import AppointmentService
from ..schemas.requests import BookAppointmentRequest

# services/appointment_service.py references:
from ..db.models import Appointment, AvailabilitySlot
from ..utils.exceptions import DoubleBookingError

# models.py has NO imports from services/
# (prevents circular imports)
```

---

## Frontend Structure Rationale

### Component Organization
```
Page (route-level)
  └─ Components (UI + state)
      ├─ Hook (data fetching)
      ├─ shadcn/ui primitives (Button, Input, Dialog)
      └─ Utility functions
```

### File Purposes

**`app/page.tsx`** - Home page
- Shows availability calendar + booking form
- Fetches initial slot data server-side
- Hydrates with interactive components

**`components/availability/AvailabilityCalendar.tsx`** - Slot display
- 7-day grid of time slots
- Visual indication of booked/available
- Click to select for booking

**`components/booking/BookingForm.tsx`** - Input form
- Name, email, notes fields
- Form validation
- Submit handler with loading state

**`hooks/useAppointments.ts`** - Data fetching
- Fetch user's bookings (by email)
- Refetch after booking/cancel
- Error/loading states

**`lib/api-client.ts`** - HTTP client wrapper
- Wraps fetch
- Injects idempotency key
- Retry logic for transient failures
- Structured error handling

**`types/api.ts`** - TypeScript interfaces
```typescript
interface AvailableSlot {
  id: string;
  date: string;
  time: string;
  isBooked: boolean;
}

interface Appointment {
  id: string;
  status: 'CONFIRMED' | 'CANCELLED';
  slotDate: string;
  customerName: string;
  customerEmail: string;
  // ...
}
```

---

## Database Schema Overview

### Tables & Relationships
```sql
CREATE TABLE availability_slots (
  id UUID PRIMARY KEY,
  slot_date DATE NOT NULL,
  slot_time TIME NOT NULL,
  is_available BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(slot_date, slot_time)
);

CREATE TABLE appointments (
  id UUID PRIMARY KEY,
  availability_slot_id UUID NOT NULL REFERENCES availability_slots(id),
  customer_name VARCHAR(255) NOT NULL,
  customer_email VARCHAR(255) NOT NULL,
  notes TEXT,
  status ENUM('PENDING', 'CONFIRMED', 'CANCELLED') DEFAULT 'PENDING',
  idempotency_key UUID UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  confirmed_at TIMESTAMP,
  cancelled_at TIMESTAMP,
  version INT DEFAULT 1,
  UNIQUE(availability_slot_id) WHERE status != 'CANCELLED'
);

CREATE TABLE notifications (
  id UUID PRIMARY KEY,
  appointment_id UUID NOT NULL REFERENCES appointments(id),
  event_type ENUM('BOOKING_CONFIRMATION', 'CANCELLATION_CONFIRMATION'),
  status ENUM('QUEUED', 'SENT', 'FAILED') DEFAULT 'QUEUED',
  recipient_email VARCHAR(255) NOT NULL,
  payload JSONB NOT NULL,
  error_details TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  sent_at TIMESTAMP,
  retry_count INT DEFAULT 0
);

CREATE TABLE idempotency_records (
  idempotency_key UUID PRIMARY KEY,
  method VARCHAR(10) NOT NULL,
  resource_path TEXT NOT NULL,
  response_status INT NOT NULL,
  response_body JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  ttl_expires_at TIMESTAMP
);
```

---

## Development Workflow

### Phase 1: Setup
- [ ] Initialize git repo
- [ ] Create backend/frontend directories
- [ ] Setup Python venv + FastAPI project skeleton
- [ ] Setup Next.js project with TypeScript
- [ ] Create docker-compose.yml with PostgreSQL

### Phase 2: Backend Database & Services
- [ ] Define SQLAlchemy models
- [ ] Create Alembic migrations
- [ ] Implement appointment_service.py (book + lock logic)
- [ ] Implement availability_service.py (queries)
- [ ] Implement idempotency_service.py
- [ ] Write unit tests for services

### Phase 3: Backend API
- [ ] Implement route handlers (GET availability, POST appointment, DELETE)
- [ ] Add error handling middleware
- [ ] Add idempotency middleware
- [ ] Implement health check endpoint
- [ ] Write integration tests

### Phase 4: Background Processing
- [ ] Implement notification_service.py (queue management)
- [ ] Implement notification_worker.py (async task)
- [ ] Integrate with main.py startup
- [ ] Write tests for notification retry logic

### Phase 5: Frontend
- [ ] Create Next.js pages
- [ ] Build components with shadcn/ui
- [ ] Implement hooks for data fetching
- [ ] Build api-client with idempotency
- [ ] Handle loading/error states
- [ ] Test flow: view → book → cancel

### Phase 6: Integration & Polish
- [ ] End-to-end testing (concurrent bookings)
- [ ] Load testing
- [ ] Documentation + API spec
- [ ] Docker compose setup validation
- [ ] README with setup instructions

---

## Implementation Principles

### Code Quality
✅ **Type safety**: Use TypeScript frontend, type hints backend  
✅ **Separation of concerns**: Routes → Services → DB  
✅ **DRY**: Shared validators, constants, error handlers  
✅ **Testability**: Mock services, test in isolation  

### Error Handling
✅ **Specific exceptions**: Don't use generic Exception  
✅ **Middleware conversion**: Exceptions → HTTP responses  
✅ **Client feedback**: Clear error messages in responses  
✅ **Logging**: Every error logged with context  

### Concurrency
✅ **Database locks**: FOR UPDATE on critical sections  
✅ **Transactional integrity**: All-or-nothing booking  
✅ **Idempotency**: Every mutation repeatable  
✅ **Testing**: Verify race conditions resolved  

---

## Next Steps

1. ✅ **Architecture approved** (this document)
2. → **Initialize project structure** (create directories, files)
3. → **Database schema & migrations**
4. → **Service layer implementation**
5. → **API endpoints**
6. → **Frontend components**
7. → **Integration testing**
8. → **Documentation & README**

---

Ready to proceed with implementation? I'll create the directory structure and start coding services layer next.
