# Appointment Booking System - Architecture Design

## Executive Summary

A minimal but production-ready appointment booking system emphasizing:
- **Consistency**: ACID guarantees for double-booking prevention
- **Idempotency**: Safe retry semantics for all mutations
- **Reliability**: Proper async notification handling with audit trails
- **Observability**: Clear separation of concerns and failure paths

---

## 1. Problem Analysis & Critical Invariants

### What Must Never Happen
1. **Double Booking**: Same slot booked twice under any circumstances (race conditions, retries)
2. **Inconsistent Cancellation**: Calling cancel twice should be safe (idempotent)
3. **Lost Notifications**: Booking confirmed but notification never sent/recorded
4. **Data Races**: Concurrent requests breaking state

### Design Principles
- **Database as source of truth**: All consistency enforced at persistence layer
- **Explicit over implicit**: Request idempotency keys, status fields, timestamps
- **Async-first notifications**: Never block booking on notification delivery
- **Immutable audit trail**: Every state change is recorded

---

## 2. Tech Stack Rationale

### Backend: Python + FastAPI
**Why?**
- Type-safe endpoints with Pydantic validation
- Async-native (important for concurrent booking handling)
- Cleaner separation of services vs. routes
- Declarative middleware for cross-cutting concerns
- Easy concurrency testing and debugging

### Database: PostgreSQL
**Why?**
- Row-level locking for pessimistic concurrency control
- ACID transactions (critical for double-booking prevention)
- Temporal data queries (availability window)
- Native JSON for flexible schema (notifications, notes)
- Better than SQLite for concurrent writes

### Frontend: Next.js 14 + TypeScript + shadcn/ui
**Why?**
- Server components for initial data load (availability)
- Full-stack framework reduces API surface area
- TypeScript catches frontend data model mismatches
- shadcn/ui provides accessibility baseline

### Async Processing: In-Process Background Tasks
**Why?**
- Scope is small; separate message queue (RabbitMQ, etc.) not needed yet
- Python's `asyncio` + scheduled tasks sufficient
- Simpler deployment story for assignment context
- **But designed so it could migrate to Celery/Queue later without major refactoring**

---

## 3. Data Model

### Core Tables

#### `availability_slots`
```
- id: UUID (primary key)
- slot_date: DATE
- slot_time: TIME
- duration_minutes: INT (default 60)
- is_available: BOOLEAN (soft flag, not authoritative)
- created_at: TIMESTAMP
```

**Constraint**: Unique constraint on (slot_date, slot_time)  
**Purpose**: Pre-populated with business availability (e.g., 7 days of 9am-5pm slots)

#### `appointments`
```
- id: UUID (primary key)
- availability_slot_id: UUID (foreign key, NOT NULL)
- customer_name: VARCHAR(255)
- customer_email: VARCHAR(255)
- notes: TEXT (nullable)
- status: ENUM (PENDING, CONFIRMED, CANCELLED)
- idempotency_key: UUID (unique, prevents duplicate bookings)
- created_at: TIMESTAMP
- confirmed_at: TIMESTAMP (nullable)
- cancelled_at: TIMESTAMP (nullable)
- version: INT (optimistic lock, default 1)

Constraints:
- Foreign key to availability_slots (cascade delete not used)
- Unique(idempotency_key) - prevents double submissions
- Unique(availability_slot_id) WHERE status != 'CANCELLED' - no double booking
```

**Design Decisions**:
- `status` field is explicit state machine (no implicit inference)
- Never delete appointments (audit trail)
- `idempotency_key` as NATURAL KEY for mutations
- `version` for optimistic locking alternative to row locks

#### `notifications`
```
- id: UUID (primary key)
- appointment_id: UUID (foreign key)
- event_type: ENUM (BOOKING_CONFIRMATION, CANCELLATION_CONFIRMATION)
- status: ENUM (QUEUED, SENT, FAILED)
- recipient_email: VARCHAR(255)
- payload: JSONB (stores full notification content)
- error_details: TEXT (nullable, for debugging failures)
- created_at: TIMESTAMP
- sent_at: TIMESTAMP (nullable)
- retry_count: INT (default 0)

Constraint: Foreign key to appointments
```

**Purpose**: Complete audit trail of notification intent and delivery

#### `idempotency_records` (optional but recommended)
```
- idempotency_key: UUID (primary key)
- method: VARCHAR(10) (POST, DELETE)
- resource_path: TEXT
- response_status: INT
- response_body: JSONB
- created_at: TIMESTAMP
- ttl_expires_at: TIMESTAMP (cleanup after 24h)

Constraint: Expire records after 24 hours
```

**Purpose**: Replay exact responses for idempotent retries

---

## 4. Concurrency Control Strategy

### Option A: Pessimistic Locking (Chosen)
**When booking arrives:**
```
BEGIN TRANSACTION
  SELECT * FROM availability_slots WHERE id = ? FOR UPDATE
  CHECK: is slot still available?
  INSERT INTO appointments (slot_id, ...)
  INSERT INTO notifications (event_type='BOOKING_CONFIRMATION', status='QUEUED')
  UPDATE availability_slots SET is_available = false
COMMIT
```

**Pros:**
- Simple to reason about; no race window
- Database serializes concurrent requests
- Clear failure semantics

**Cons:**
- Slight latency under high concurrency (acceptable for appointment booking)

### Option B: Optimistic Locking (Alternative)
Uses `version` field in appointments. On cancel: `WHERE id = ? AND version = ?`  
Combined with unique constraint: `UNIQUE(slot_id) WHERE status != 'CANCELLED'`

**Fallback strategy**: If constraint violation or version mismatch, return HTTP 409 Conflict and let client retry.

---

## 5. Idempotency Protocol

### Request Level
Every mutation (POST /appointments, DELETE /appointments/{id}) includes:
```
Header: Idempotency-Key: <UUID>
```

### Server Processing
```
1. Check idempotency_records table for matching key
2. If found:
   - Return cached response (HTTP 200 with result)
   - Do not execute business logic again
3. If not found:
   - Execute booking/cancellation
   - Store request & response in idempotency_records
   - Return result
```

### Guarantees
- **Same request, same response** (even if called 100 times)
- **No side effects** (second call doesn't double-book or double-notify)
- **Replay-safe** (can safely retry without external coordination)

---

## 6. Notification Handling

### Design: Decoupled Async with Persistence

**Flow:**
```
1. Booking transaction commits
   ├─ appointments record created
   └─ notifications record created (status=QUEUED)

2. Background task (runs every 5 seconds):
   ├─ Fetch all notifications WHERE status = 'QUEUED'
   ├─ For each:
   │  ├─ Log booking confirmation to console/file
   │  ├─ Update notifications.status = 'SENT'
   │  └─ Update notifications.sent_at
   └─ If error: status = 'FAILED', increment retry_count

3. Recovery:
   - Periodic job retries FAILED notifications (max 3 retries)
   - Dead letter: Log to error tracking after max retries
```

### Why This Design?
- ✅ Booking request completes fast (notification is background concern)
- ✅ Complete audit: every notification attempt recorded
- ✅ Retryable: transient failures automatically recover
- ✅ Observable: query notifications table for delivery status
- ✅ Testable: can verify notification was queued without waiting for async

### Migration Path
Switch to proper queue (Celery, RabbitMQ) later by:
- Changing notification job producer from DB insert to queue publish
- Changing notification job consumer from polling to message listener
- **Zero change to booking logic**

---

## 7. API Contract

### 1. GET /api/availability
```
Query: startDate (YYYY-MM-DD, defaults to today)
Response:
{
  "availableSlots": [
    {
      "id": "uuid",
      "date": "2026-03-02",
      "time": "09:00",
      "isBooked": false
    },
    ...
  ],
  "nextAvailableAfter": "2026-03-02T09:00:00Z"
}
```

### 2. POST /api/appointments
```
Header: Idempotency-Key: <UUID>
Body:
{
  "slotId": "uuid",
  "customerName": "John Doe",
  "customerEmail": "john@example.com",
  "notes": "optional note" (optional)
}
Response (201 Created):
{
  "id": "appointment-uuid",
  "status": "CONFIRMED",
  "confirmedAt": "2026-03-02T09:00:00Z",
  "notificationStatus": "QUEUED"
}
```

### 3. GET /api/appointments/{id}
```
Response:
{
  "id": "uuid",
  "slotDate": "2026-03-02",
  "slotTime": "09:00",
  "customerName": "John Doe",
  "status": "CONFIRMED",
  "notificationStatus": "SENT",
  "createdAt": "2026-03-02T08:50:00Z",
  "confirmedAt": "2026-03-02T08:50:10Z"
}
```

### 4. DELETE /api/appointments/{id}
```
Header: Idempotency-Key: <UUID>
Response (200 OK):
{
  "id": "uuid",
  "status": "CANCELLED",
  "cancelledAt": "2026-03-02T09:10:00Z"
}
```

**Idempotency guarantee**: Calling DELETE 5 times with same idempotency key returns same response, only first call makes state change.

---

## 8. Error Handling & Edge Cases

### Double-Booking Attempt
```
Scenario: Two concurrent requests for same slot
Database behavior:
- First request: acquires lock, inserts appointment, succeeds
- Second request: waits for lock, checks slot status, gets 409 CONFLICT
Response: 
{
  "error": "slot_already_booked",
  "message": "This time slot was just booked. Please refresh availability.",
  "status": 409
}
```

### Duplicate Submission
```
Scenario: Client resends same booking request (network retry)
Server behavior:
- Check idempotency_key in idempotency_records
- Return cached response (200) with original booking ID
- Zero duplicate work
```

### Cancel Non-Existent Appointment
```
Scenario: DELETE /appointments/invalid-id
Response:
{
  "error": "not_found",
  "message": "Appointment does not exist",
  "status": 404
}
```

### Cancel Already-Cancelled Appointment
```
Scenario: Two concurrent cancellations with DIFFERENT idempotency keys
First request: succeeds, status → CANCELLED
Second request: 
- Checks WHERE id = ? AND status != 'CANCELLED'
- No row matches, returns 409 CONFLICT
Response:
{
  "error": "invalid_state_transition",
  "message": "Appointment is already cancelled",
  "status": 409
}
```

**OR** with idempotency key replay:
- If keys are same, returns cached response
- If keys differ, returns conflict (forces client to use same key for retry)

---

## 9. Directory Structure

```
appointment-booking-system/
├── README.md (setup + architecture overview)
├── docker-compose.yml (postgres + app)
│
├── backend/
│   ├── src/
│   │   ├── __init__.py
│   │   ├── main.py (FastAPI app + startup)
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── availability.py (GET /api/availability)
│   │   │   │   ├── appointments.py (POST, GET, DELETE)
│   │   │   │   └── health.py (GET /health)
│   │   │   ├── schemas/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── requests.py (Pydantic models for input)
│   │   │   │   └── responses.py (Pydantic models for output)
│   │   │   └── dependencies.py (FastAPI dependency injection)
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py (env vars, settings)
│   │   │   └── constants.py (business rules: business hours, duration)
│   │   │
│   │   ├── db/
│   │   │   ├── __init__.py
│   │   │   ├── connection.py (PostgreSQL connection pool)
│   │   │   ├── models.py (SQLAlchemy ORM definitions)
│   │   │   └── migrations/ (Alembic migration scripts)
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── appointment_service.py (booking logic + locking)
│   │   │   ├── availability_service.py (slot queries)
│   │   │   ├── notification_service.py (queue + background worker)
│   │   │   └── idempotency_service.py (idempotency key handling)
│   │   │
│   │   ├── utils/
│   │   │   ├── __init__.py
│   │   │   ├── logger.py (structured logging)
│   │   │   ├── exceptions.py (custom exception classes)
│   │   │   └── validators.py (email, date format, etc.)
│   │   │
│   │   └── middleware/
│   │       ├── __init__.py
│   │       ├── error_handler.py (exception → HTTP response)
│   │       └── idempotency.py (idempotency key extraction + validation)
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py (pytest fixtures)
│   │   ├── test_concurrency.py (double-booking prevention)
│   │   ├── test_idempotency.py (retry safety)
│   │   ├── test_appointment_service.py (business logic)
│   │   └── test_api.py (endpoint integration)
│   │
│   ├── requirements.txt
│   ├── .env.example
│   └── alembic.ini
│
├── frontend/
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx (root layout)
│   │   │   ├── page.tsx (main booking page)
│   │   │   ├── appointments/
│   │   │   │   └── page.tsx (view existing bookings)
│   │   │   └── api/
│   │   │       └── appointments/ (optional: next.js route handlers)
│   │   │
│   │   ├── components/
│   │   │   ├── AvailabilityCalendar.tsx
│   │   │   │   └── Shows 7-day grid with bookable slots
│   │   │   ├── BookingForm.tsx
│   │   │   │   └── Input: name, email, note
│   │   │   ├── AppointmentsList.tsx
│   │   │   │   └── Shows booked + cancelled appointments
│   │   │   ├── ConfirmationDialog.tsx
│   │   │   ├── LoadingState.tsx
│   │   │   └── ErrorAlert.tsx
│   │   │
│   │   ├── lib/
│   │   │   ├── api-client.ts (fetch wrapper with idempotency key)
│   │   │   ├── utils.ts (formatting, validation)
│   │   │   └── constants.ts (API URL, defaults)
│   │   │
│   │   ├── types/
│   │   │   └── index.ts (TypeScript interfaces for API responses)
│   │   │
│   │   └── hooks/
│   │       ├── useAppointments.ts (fetch + state management)
│   │       └── useBooking.ts (booking form state)
│   │
│   ├── public/ (static assets)
│   ├── package.json
│   └── .env.local.example
│
└── docs/
    ├── ARCHITECTURE.md (this file)
    ├── API_SPEC.md (detailed endpoint documentation)
    ├── CONCURRENCY_DESIGN.md (race condition analysis)
    └── DEPLOYMENT.md (docker, env setup)
```

---

## 10. Key Implementation Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Concurrency** | Pessimistic locking (FOR UPDATE) | Simple, guaranteed no race window |
| **Idempotency** | Database record + key header | Deterministic replays, audit trail |
| **Notifications** | In-process async queue | Sufficient for scope; easy migration path |
| **Cancellation** | Status flag, never delete | Audit trail; idempotent by design |
| **Double-book prevention** | Unique constraint + transaction lock | Database enforces; application can't forget |
| **Slots** | Pre-populated table | Query efficiency; explicit availability control |
| **Timestamps** | created_at, confirmed_at, cancelled_at | Complete timeline for debugging |

---

## 11. Known Limitations & Future Work

### Current Scope
- ❌ No authentication/authorization (any client can book/cancel)
- ❌ No timezone handling (assumes single TZ)
- ❌ No multi-provider scheduling
- ❌ Notifications logged only (no actual email/SMS)

### Improvements with More Time
1. **Auth layer**: JWT or OAuth for admin/user roles
2. **Email integration**: Real SMTP with Sendgrid/AWS SES
3. **Better notification**: Celery queue instead of polling
4. **Calendar sync**: Merge with Google Calendar
5. **Rate limiting**: Prevent booking spam
6. **Availability management**: UI for adjusting slots by admin

---

## 12. Testing Strategy

### Unit Tests (Services layer)
- `test_appointment_service.py`: Booking logic, state transitions
- `test_availability_service.py`: Slot queries, date range logic

### Concurrency Tests
- Spawn 10 concurrent requests for same slot, verify only 1 succeeds
- Verify race conditions between book + cancel

### Idempotency Tests
- Submit same request 5 times, verify identical response
- Verify no duplicate appointments created

### Integration Tests
- Full request/response cycle through API
- Database state verification

### Load Test (optional)
- 50 concurrent users booking over 100 slots
- Monitor for double-books, measure latency

---

## 13. Deployment Checklist

- [ ] PostgreSQL running (isolated database)
- [ ] Backend env vars set (.env file)
- [ ] Database migrations run (Alembic)
- [ ] Initial availability slots populated
- [ ] Frontend API URL points to backend
- [ ] CORS properly configured
- [ ] Logging/monitoring connected
- [ ] Health check endpoint responsive
- [ ] Can book, view, cancel through UI

---

## Summary

This design prioritizes:
✅ **Correctness first** - ACID guarantees, no race conditions  
✅ **Clear semantics** - Explicit status, idempotency keys, audit trail  
✅ **Production-ready** - Error handling, retry logic, observability  
✅ **Maintainable** - Service layer separation, testable design  
✅ **Extensible** - Easy migration path for notifications, auth, scaling  

The implementation should reflect these principles, not just function but work well.
