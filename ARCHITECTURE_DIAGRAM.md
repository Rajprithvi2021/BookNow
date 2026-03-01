# BookNow Architecture Diagram

## System Architecture Overview

```
┌────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (Next.js)                          │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Pages                                                       │ │
│  │ • /             (Availability Calendar + Booking Form)     │ │
│  │ • /appointments (Search + List Appointments)               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                          ▲                                         │
│                          │ HTTP REST                               │
│                          │ • Idempotency-Key header (POST/DELETE)  │
│                          │ • Location: Repeat-call safety          │
│                          ▼                                         │
└────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────┐
│                    API LAYER (FastAPI Routes)                      │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ GET /api/availability?start_date=X&days=7                │  │
│  │ → Returns available slots for next 7 days                │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ POST /api/appointments  (Idempotent)                       │  │
│  │ Header: Idempotency-Key: {uuid}                           │  │
│  │ Body: {slot_id, customer_name, customer_email, notes}    │  │
│  │ → Stores in IdempotencyRecord cache                       │  │
│  │ → Returns 201 Created (or 409 Conflict if slot booked)   │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ DELETE /api/appointments/{id}  (Idempotent)               │  │
│  │ → Transitions status to CANCELLED                         │  │
│  │ → Never deletes (audit trail)                            │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ GET /api/appointments?email=X  (Search)                  │  │
│  │ → Returns appointments for email (all statuses)           │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ SQL Queries
                              │ Validation
                              │ Error handling (400, 409, 500)
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│              SERVICE LAYER (Business Logic)                        │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ AvailabilityService                                        │  │
│  │ • get_available_slots(start_date, days)                   │  │
│  │   → Query ONLY is_available=true slots                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ BookingService + PESSIMISTIC LOCKING                       │  │
│  │ ┌──────────────────────────────────────────────────────┐  │  │
│  │ │ BEGIN TRANSACTION                                    │  │  │
│  │ │   SELECT * FROM availability_slot WHERE id=slot_id   │  │  │
│  │ │   FOR UPDATE  ← CRITICAL: Row-level lock            │  │  │
│  │ │   (exclusive access, others wait)                    │  │  │
│  │ │                                                      │  │  │
│  │ │   IF is_available = true:                          │  │  │
│  │ │     INSERT appointment (status='CONFIRMED')        │  │  │
│  │ │     UPDATE availability_slot SET is_available=false│  │  │
│  │ │     INSERT notification (status='QUEUED')          │  │  │
│  │ │     RETURN 201 Created                             │  │  │
│  │ │   ELSE:                                            │  │  │
│  │ │     RETURN 409 Conflict (already booked)           │  │  │
│  │ │ COMMIT TRANSACTION                                 │  │  │
│  │ └──────────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │ → WHERE: Booking consistency enforced                │  │  │
│  └────────────────────────────────────────────────────────┘  │
│                          ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ IdempotencyService                                         │  │
│  │ • Stores Idempotency-Key → Response mapping            │  │
│  │ • On retry: KEY exists? Return cached response (no DB) │  │
│  │                                                         │  │
│  │ → WHERE: Repeat-call safety enforced                  │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ CancellationService + State Machine                       │  │
│  │ • cancel(appointment_id)                                 │  │
│  │   IF status IN [PENDING, CONFIRMED]:                    │  │
│  │     UPDATE appointments SET status='CANCELLED'          │  │
│  │     UPDATE availability_slot SET is_available=true     │  │
│  │   ELSE:                                                  │  │
│  │     Return 400 (already cancelled)                       │  │
│  │                                                         │  │
│  │ → Safe for idempotent DELETE calls                    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                          ▼                                         │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ NotificationService (Async Queue)                         │  │
│  │ • queue_notification(appointment_id, event, email)       │  │
│  │   → INSERT INTO notifications (status='QUEUED')         │  │
│  │   → Returns immediately (non-blocking)                  │  │
│  │ • process_queued_notifications()                        │  │
│  │   → Runs periodically (background worker)              │  │
│  │   → WHERE: Notification processing flow                │  │
│  └────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
                              ▲
                              │ ORM Queries
                              │ Transactions
                              │ Locks
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│             PERSISTENCE LAYER (PostgreSQL + SQLAlchemy)            │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ TABLE: availability_slot                                  │  │
│  │ • id (UUID, PK)                                          │  │
│  │ • slot_date (Date)                                       │  │
│  │ • slot_time (Time)                                       │  │
│  │ • is_available (Boolean) ← Updated by booking/cancel    │  │
│  │ • created_at (Timestamp)                                 │  │
│  │                                                          │  │
│  │ INDEX: (slot_date, slot_time) for fast queries         │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ TABLE: appointment                                         │  │
│  │ • id (UUID, PK)                                          │  │
│  │ • availability_slot_id (FK → availability_slot)          │  │
│  │ • customer_name (String)                                 │  │
│  │ • customer_email (String)                                │  │
│  │ • notes (Text, nullable)                                 │  │
│  │ • status (Enum: PENDING, CONFIRMED, CANCELLED)          │  │
│  │ • created_at (Timestamp)                                 │  │
│  │ • confirmed_at (Timestamp, nullable)                     │  │
│  │ • cancelled_at (Timestamp, nullable)                     │  │
│  │                                                          │  │
│  │ INDEX: (customer_email) for fast search                 │  │
│  │ CONSTRAINT: UNIQUE (availability_slot_id, status)       │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ TABLE: idempotency_record (Repeat-call safety)            │  │
│  │ • request_key (String, PK)  ← From Idempotency-Key header│  │
│  │ • method (String)                                        │  │
│  │ • endpoint (String)                                      │  │
│  │ • response_status (Integer)                              │  │
│  │ • response_body (JSON)  ← Cached response              │  │
│  │ • created_at (Timestamp)                                 │  │
│  │                                                          │  │
│  │ Logic on POST /appointments:                            │  │
│  │   1. Check if request_key exists → Return cached response │  │
│  │   2. If not: proceed with booking, save response        │  │
│  │   3. Next identical request → Step 1 returns cached    │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                     │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ TABLE: notification (Async Processing Queue)              │  │
│  │ • id (UUID, PK)                                          │  │
│  │ • appointment_id (FK → appointment)                      │  │
│  │ • event_type (String: 'confirmation', 'cancellation')    │  │
│  │ • status (Enum: QUEUED, SENT, FAILED)                   │  │
│  │ • recipient_email (String)                               │  │
│  │ • payload (JSON)  ← Subject, body, etc.                 │  │
│  │ • created_at (Timestamp)                                 │  │
│  │ • sent_at (Timestamp, nullable)                          │  │
│  │ • error_message (Text, nullable)  ← For debugging       │  │
│  │                                                          │  │
│  │ Workflow:                                               │  │
│  │   POST /appointments                                    │  │
│  │   → Service layer queues notification immediately      │  │
│  │   → INSERT notification (status='QUEUED')             │  │
│  │   → Returns 201 (fast, non-blocking)                   │  │
│  │       │                                                │  │
│  │       └──> Background worker runs every 5 seconds:    │  │
│  │           SELECT * FROM notification WHERE status=QUEUED │  │
│  │           → Call email service (SendGrid, SES, etc.)   │  │
│  │           → UPDATE status='SENT' + sent_at timestamp   │  │
│  │           → If error: status='FAILED' + error_message  │  │
│  │                                                        │  │
│  │ Guarantees:                                           │  │
│  │   • Booking succeeds regardless of notification status│  │
│  │   • Notifications retry until successful              │  │
│  │   • Complete audit trail of all notifications        │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                     │
│ ACID Properties:                                                  │
│ ✅ Atomicity:    Transactions all-or-nothing             │
│ ✅ Consistency:  Constraints enforce valid state         │
│ ✅ Isolation:    Row locks (SERIALIZABLE level)         │
│ ✅ Durability:   Persistent storage                     │
└────────────────────────────────────────────────────────────────────┘


## Concurrency Control Summary

### Scenario 1: Two Users Book Same Slot

```
Request 1: Click "Book 9am Monday"          Request 2: Click "Book 9am Monday"
│                                            │
├─ BEGIN TRANSACTION                         ├─ BEGIN TRANSACTION (waiting)
├─ SELECT FROM availability_slot id=X       
│  FOR UPDATE  ← LOCK acquired              
│                                            │ FOR UPDATE ← BLOCKED, waiting for lock
├─ Check: is_available=true ✓                
├─ INSERT appointment ✓                      
├─ UPDATE is_available=false ✓               
├─ INSERT notification ✓                     
├─ COMMIT ✓           ← Lock released        │
│ 201 Created                                │ FOR UPDATE ← LOCK acquired now
│                                            ├─ Check: is_available=false ✗
                                             ├─ ROLLBACK
                                             │ 409 Conflict
```

**Result**: First request succeeds. Second gets 409 Conflict. Zero double-bookings.

---

### Scenario 2: Network Retry (Idempotency)

```
Request 1: POST /appointments                Request 2: Retry (same data + key)
Idempotency-Key: abc123                      Idempotency-Key: abc123
│                                            │
├─ Check IdempotencyRecord: abc123 exists?  │
│  → No (first time)                        ├─ Check IdempotencyRecord: abc123 exists?
│  → Proceed with booking                   │  → YES! Found in cache
├─ Book appointment → 201 Created           ├─ Return cached response: 201 Created
├─ STORE (abc123 → 201 response)            │  (Zero DB work, zero duplication)
│                                            │
└─ 201 Created                               └─ 201 Created (instant)
   1 appointment created                        Same appointment (not duplicated)
```

**Result**: 1 appointment despite retries. Safe for network failures.

---

### Scenario 3: Async Notifications

```
POST /appointments → Service Layer
│
├─ Book appointment in transaction ✓
├─ INSERT notification (status='QUEUED') ✓
├─ COMMIT transaction ✓
└─ RETURN 201 Created ← Fast (~50ms inclusive)

          ↓ (separate background process)
          
Background Worker (runs every 5 seconds):
│
├─ SELECT * FROM notification WHERE status='QUEUED'
├─ Call email service (SendGrid, SES, etc.)
│  → If success: UPDATE status='SENT'
│  → If failure: UPDATE status='FAILED', store error
├─ Commit
└─ Next run: retry FAILED notifications
```

**Result**: 
- Booking is fast (not blocked by email service)
- Notifications eventually sent (with retries)
- Complete audit trail in DB


---

## Key Design Enforcement Points

| Component | Responsibility | How Enforced |
|-----------|-----------------|-------------|
| **Database (FOR UPDATE)** | Only 1 booking per slot | Row-level lock |
| **IdempotencyRecord table** | No duplicate bookings on retry | Request key + cached response |
| **Notification Queue** | Non-blocking notifications | Async worker polling |
| **Appointment.status** | Immutable history | Never delete, only CANCELLED |
| **AvailabilitySlot.is_available** | Consistent slot state | Updated atomically with booking |
| **Transaction boundaries** | All-or-nothing operations | SQLAlchemy session commit |


---

## What This Demonstrates

✅ **Correctness under concurrency** - Pessimistic locking (FOR UPDATE)
✅ **Data integrity** - ACID transactions + constraints
✅ **Repeat-call safety** - Idempotency keys + response cache
✅ **Non-blocking design** - Async notification queue
✅ **Audit trail** - Never delete, only status transitions
✅ **Error handling** - Meaningful error codes (409 Conflict, 400 Bad Request)
✅ **Separation of concerns** - Routes → Services → Database
✅ **Production readiness** - Logging, transaction handling, state machine
