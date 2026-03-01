# BookNow - Appointment Booking System
## Take-Home Assignment Brief

**Project**: BookNow (Minimal Appointment Booking System)  
**Scope**: 4-6 hour implementation  
**Submission**: Git repository + working system  
**Evaluation**: Production-grade code architecture

---

## 📋 What We're Building

A minimal but **production-ready** appointment booking system that demonstrates:

✅ **Concurrency correctness** - No double-bookings under any circumstances  
✅ **Data integrity** - ACID transactions protect critical operations  
✅ **Idempotent mutations** - Safe to retry requests without side effects  
✅ **Clean architecture** - Clear separation of routes, services, and database  
✅ **Failure handling** - Graceful errors with proper HTTP semantics  
✅ **Async workflows** - Notifications processed in background  
✅ **Testability** - Concurrency scenarios explicitly tested  

---

## 🎯 The Requirements

### Functional Requirements

1. **View Availability**
   - Show available time slots for next 7 days
   - Display as clean calendar UI

2. **Book Appointment**
   - Capture: customer name, email, time slot, optional notes
   - Return: confirmation with appointment ID
   - Prevent: double-booking (core invariant)

3. **Cancel Appointment**
   - Allow customer to cancel booked appointment
   - Ensure: cancellation is idempotent (can call multiple times safely)
   - Prevent: inconsistent state

4. **Send Confirmation**
   - After booking: queue notification
   - Design: async processing (don't block booking)
   - Simulate: log to console/file (real email not required)

### Technical Requirements

**Backend:**
- Node.js or Python ✅ **Choose: Python + FastAPI**
- Any database ✅ **Choose: PostgreSQL**
- Any framework ✅ **Choose: FastAPI**

**Frontend:**
- React or React-based ✅ **Choose: Next.js**
- Must use shadcn/ui ✅ **Yes**

**Not Allowed:**
- ❌ Backend boilerplates/prebuilt architectures
- ❌ We show OUR structure, not framework defaults

---

## 🏗️ Architecture Overview

### High-Level Design

```
┌─────────────────────────────────────────────────────────┐
│                    BOOKNOW SYSTEM                       │
└─────────────────────────────────────────────────────────┘

FRONTEND (Next.js + React + shadcn/ui)
    │
    ├─── Pages:
    │    ├─ / (home - book appointment)
    │    └─ /my-appointments (view & cancel)
    │
    └─── Components:
         ├─ AvailabilityCalendar (slot picker)
         ├─ BookingForm (name, email, notes)
         └─ AppointmentsList (past bookings)

    ↓↑ REST API + Idempotency-Key header

BACKEND (FastAPI + PostgreSQL)
    │
    ├─── API Routes: /api/availability, /api/appointments
    │
    ├─── Services (business logic):
    │    ├─ AppointmentService (booking + locking)
    │    ├─ AvailabilityService (slot queries)
    │    └─ NotificationService (async queue)
    │
    └─── Database (PostgreSQL):
         ├─ availability_slots
         ├─ appointments
         ├─ notifications
         └─ (idempotency cache - optional)

BACKGROUND WORKER
    └─── Process notifications queue (async)
```

---

## 🔐 Critical Algorithms

### 1. Double-Booking Prevention (Pessimistic Locking)

**Problem**: Two requests arrive for same slot simultaneously.  
**Solution**: Row-level database lock.

```python
BEGIN TRANSACTION
  SELECT * FROM slots WHERE id=? FOR UPDATE  # Lock acquired
  if slot.available:
      INSERT appointment
  COMMIT  # Lock released
```

**Guarantee**: Only 1 appointment per slot, guaranteed by database.

### 2. Idempotent Mutations (Request Keys)

**Problem**: Network retry causes duplicate requests.  
**Solution**: Idempotency key + response caching.

```python
POST /api/appointments
Header: Idempotency-Key: <UUID>

# First request: execute, cache response
# Second request (same key): return cached response
# Result: 1 appointment, even with 10 retries
```

### 3. Idempotent Cancellation (State Machine)

**Problem**: Two cancel requests arrive for same appointment.  
**Solution**: Status field + state validation.

```python
def cancel(appointment_id):
    appt = query(appointment_id)
    if appt.status == 'CANCELLED':
        return appt  # Already done, just return
    appt.status = 'CANCELLED'
    save(appt)
    return appt
```

**Guarantee**: Calling cancel 5 times = same result, no errors.

### 4. Async Notifications with Retries (Fault Tolerance)

**Problem**: Email service might be temporarily down.  
**Solution**: Persistent queue + exponential backoff.

```python
booking → INSERT notification (status='QUEUED')
          ↓ (return 201 immediately)
          ↓
background_worker (every 5 sec):
  ├─ Fetch notifications WHERE status='QUEUED'
  ├─ Try send, on error:
  │  └─ status='FAILED', retry_count++
  │  └─ Retry with delay: 2^retry_count
  └─ If success: status='SENT'
```

**Guarantee**: Notification attempt recorded (auditable).

---

## 📊 Data Model

### Tables

**availability_slots**
```sql
id (UUID) PRIMARY KEY
date (DATE)
time (TIME)
is_available (BOOLEAN)
created_at (TIMESTAMP)

CONSTRAINT: UNIQUE(date, time)
```

**appointments**
```sql
id (UUID) PRIMARY KEY
availability_slot_id (UUID) FK → slots
customer_name (VARCHAR)
customer_email (VARCHAR)
notes (TEXT) nullable
status (ENUM: CONFIRMED, CANCELLED)
created_at (TIMESTAMP)
confirmed_at (TIMESTAMP) nullable
cancelled_at (TIMESTAMP) nullable

CONSTRAINT: UNIQUE(slot_id) WHERE status != 'CANCELLED'
  (only 1 active appointment per slot)
```

**notifications**
```sql
id (UUID) PRIMARY KEY
appointment_id (UUID) FK → appointments
event_type (ENUM: BOOKING_CONFIRMED, CANCELLATION_CONFIRMED)
status (ENUM: QUEUED, SENT, FAILED)
recipient_email (VARCHAR)
payload (JSON)
created_at (TIMESTAMP)
sent_at (TIMESTAMP) nullable
retry_count (INT)
```

---

## 🚀 API Endpoints

### GET /api/availability
```
Query: ?start_date=2026-03-02&days=7

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
  ]
}
```

### POST /api/appointments
```
Header: Idempotency-Key: <UUID>

Body:
{
  "slotId": "uuid",
  "customerName": "John Doe",
  "customerEmail": "john@example.com",
  "notes": "optional"
}

Response (201 Created):
{
  "id": "uuid",
  "status": "CONFIRMED",
  "confirmedAt": "2026-03-02T09:00:00Z"
}

Error (409 Conflict):
{
  "error": "slot_already_booked",
  "message": "This slot was just booked"
}
```

### GET /api/appointments/{id}
```
Response:
{
  "id": "uuid",
  "status": "CONFIRMED",
  "customerName": "John Doe",
  "customerEmail": "john@example.com",
  "slotDate": "2026-03-02",
  "slotTime": "09:00",
  "confirmedAt": "...",
  "notes": "..."
}
```

### DELETE /api/appointments/{id}
```
Header: Idempotency-Key: <UUID>

Response (200 OK):
{
  "id": "uuid",
  "status": "CANCELLED",
  "cancelledAt": "..."
}
```

---

## 🧪 Testing Strategy

### Unit Tests (Services)
- ✅ Booking creates appointment with CONFIRMED status
- ✅ Booking same slot twice raises DoubleBookingError
- ✅ Cancelling same appointment twice is safe (idempotent)

### Integration Tests (API)
- ✅ GET /availability returns slots
- ✅ POST /appointments with valid input returns 201
- ✅ POST /appointments (double-book) returns 409 Conflict
- ✅ DELETE /appointments idempotent (same result on retry)

### Concurrency Tests (Critical)
- ✅ 10 concurrent bookings for same slot → only 1 succeeds
- ✅ Multiple concurrent cancellations → safe (no conflicts)
- ✅ Stress test: 50 concurrent users, 100 slots → 0 double-books

### E2E Tests (User Flow)
- ✅ User views availability
- ✅ User books appointment
- ✅ User views their appointment
- ✅ User cancels appointment

---

## 📁 Project Structure (Git-Ready)

```
booknow/
├── .git/ (initialized)
├── .gitignore
├── README.md
├── ARCHITECTURE.md
│
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── pytest.ini
│   │
│   ├── src/
│   │   ├── main.py (FastAPI app)
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── availability.py
│   │   │   │   ├── appointments.py
│   │   │   │   └── health.py
│   │   │   └── schemas/
│   │   │       ├── requests.py
│   │   │       └── responses.py
│   │   │
│   │   ├── services/
│   │   │   ├── appointment_service.py (core logic)
│   │   │   ├── availability_service.py
│   │   │   └── notification_service.py
│   │   │
│   │   ├── db/
│   │   │   ├── models.py (SQLAlchemy)
│   │   │   ├── connection.py
│   │   │   └── migrations/ (Alembic)
│   │   │
│   │   └── utils/
│   │       ├── exceptions.py (custom errors)
│   │       └── logger.py
│   │
│   └── tests/
│       ├── test_services.py (unit)
│       ├── test_api.py (integration)
│       └── test_concurrency.py (race conditions)
│
├── frontend/
│   ├── .env.local.example
│   ├── package.json
│   │
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx (home)
│   │   │   └── appointments/page.tsx
│   │   │
│   │   ├── components/
│   │   │   ├── AvailabilityCalendar.tsx
│   │   │   ├── BookingForm.tsx
│   │   │   └── AppointmentsList.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useAvailability.ts
│   │   │   ├── useBooking.ts
│   │   │   └── useAppointments.ts
│   │   │
│   │   └── lib/
│   │       └── api-client.ts
│   │
│   └── tailwind.config.js
│
└── docker-compose.yml (PostgreSQL dev environment)
```

---

## ✅ Key Design Decisions

| Decision | Choice | Why |
|----------|--------|-----|
| **Concurrency** | Pessimistic locking (FOR UPDATE) | Simple, reliable, no race windows |
| **Idempotency** | Request keys + response cache | Industry standard (Stripe pattern) |
| **Notifications** | Async queue in DB | Decoupled, auditable, resilient |
| **Cancellation** | Status field state machine | Idempotent by design |
| **Database** | PostgreSQL | Row locks, ACID, JSONB support |
| **Backend** | FastAPI | Modern, type-safe, async-native |
| **Frontend** | Next.js | Full-stack, TypeScript, shadcn/ui ready |
| **Testing** | Unit + Integration + Concurrency | Verify correctness at every level |

---

## ⏱️ Implementation Timeline (4-6 hours)

| Phase | Task | Time | Status |
|-------|------|------|--------|
| 0 | Setup projects, git, dirs | 20 min | ⏳ Next |
| 1 | Database (models, migrations) | 30 min | ⏳ After setup |
| 2 | Services (booking, idempotency) | 60 min | ⏳ Core logic |
| 3 | API routes | 45 min | ⏳ Endpoints |
| 4 | Frontend (components, hooks) | 90 min | ⏳ UI |
| 5 | Tests (unit + integration + concurrency) | 45 min | ⏳ Validation |
| 6 | Polish & documentation | 30 min | ⏳ Final |
| **Total** | **Complete system** | **~5 hours** | ✅ Realistic |

---

## 🎓 What This Demonstrates

### Engineering Maturity (10+ Years Experience)
- ✅ Understands why row locking matters
- ✅ Knows idempotency prevents disasters
- ✅ Sees async processing as fundamental
- ✅ Tests concurrency, not just happy path
- ✅ Documents trade-offs
- ✅ Ships working product with polish

### Production-Grade Quality
- ✅ No double-bookings possible (database enforces)
- ✅ Safe to retry (idempotency keys)
- ✅ Graceful failure (typed exceptions, clear errors)
- ✅ Observable (logging, audit trail)
- ✅ Testable (clean layers, mockable services)

### Professional Judgment
- ✅ Scope realistic for 4-6 hours
- ✅ Priorities clear (correctness > features)
- ✅ Trade-offs documented (why we chose this)
- ✅ Extensible (easy to add email/auth/caching later)

---

## 📝 Deliverables Checklist

On submission, repo includes:

```
✅ Working system (no syntax errors, runs locally)
✅ Database schema (PostgreSQL, migrations)
✅ API endpoints (all 4 specified)
✅ Frontend (booking flow works)
✅ Tests (at least concurrency scenarios)
✅ README.md (setup + architecture)
✅ ARCHITECTURE.md (design decisions)
✅ .gitignore (no secrets, deps)
✅ docker-compose.yml (postgres dev env)
✅ .env.example files (config template)
```

---

## 🚀 Success Criteria

**Code Quality**: Clear, readable, well-structured  
**Correctness**: Concurrency tests pass (core invariant: no double-booking)  
**Architecture**: Clean separation (routes → services → db)  
**Documentation**: README explains setup + key decisions  
**Completeness**: All 4 functional requirements implemented  
**Polish**: No TODO comments, handles edge cases, proper error messages  

---

## 🎯 Remember

This is **not about building the biggest system**, it's about:

1. **Demonstrating thoughtfulness** - Why did you choose THIS architecture?
2. **Handling concurrency correctly** - Double-booking MUST not be possible
3. **Writing production-grade code** - Not a hobby project
4. **Making yourself productive** - Shipped in 4-6 hours with full testing
5. **Explaining trade-offs** - What you chose and why

**Quality > Quantity. Finished > Perfect.**

---

## Next Steps

✅ Design complete  
✅ Decisions documented  
✅ Architecture clear  

⏳ **Starting Phase 0: Project Setup**

Ready to build BookNow? 🚀
