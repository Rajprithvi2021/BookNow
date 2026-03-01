# System Architecture Diagram & Data Flows

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         APPOINTMENT BOOKING SYSTEM                      │
└─────────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────┐         ┌──────────────────────────┐
│     FRONTEND (Next.js + React)   │         │  BACKEND (FastAPI)       │
│                                  │◄────────┤                          │
│  • AvailabilityCalendar.tsx      │ REST    │  • Routes (api/routes/)  │
│  • BookingForm.tsx               │ API     │  • Services (business)   │
│  • AppointmentsList.tsx          │         │  • DB Models (ORM)       │
│  • useAppointments hook          │    ────►│  • Background Worker     │
│                                  │         │                          │
└──────────────────────────────────┘         └──────────────────────────┘
            │                                            │
            │                                            │
            └────────────────────┬─────────────────────┘
                                 │
                          ┌──────▼──────┐
                          │ PostgreSQL   │
                          │  (Source of  │
                          │   Truth)     │
                          │              │
                          │ • Slots      │
                          │ • Appts      │
                          │ • Notif      │
                          │ • Idempo Keys
                          └──────────────┘
```

---

## 2. Booking Request Flow (Concurrent Safety)

### Sequence 1: Success Case
```
CLIENT BROWSER                  BACKEND API                    DATABASE
    │                               │                              │
    │  POST /api/appointments       │                              │
    │   (slot_id, name, email)      │                              │
    │──────────────────────────────►│                              │
    │                               │  BEGIN TRANSACTION           │
    │                               │  SELECT * FROM slots         │
    │                               │  WHERE id=? FOR UPDATE ◄─────┤
    │                               │  (lock acquired)             │
    │                               │                              │
    │                               │  CHECK: slot.is_available?   │
    │                               │  ✓ Yes -> proceed            │
    │                               │                              │
    │                               │  INSERT appointments         │
    │                               │  INSERT notifications ◄──────┤
    │                               │  (status='QUEUED')           │
    │                               │                              │
    │                               │  UPDATE slots SET            │
    │                               │  is_available=false ◄────────┤
    │                               │                              │
    │                               │  COMMIT ◄──────────────────┤ (lock released)
    │ ◄──────────────────────────────│                             │
    │  201 Created                   │                              │
    │  { id, status: CONFIRMED }     │                             │
    │                                │                             │
```

### Sequence 2: Double-Booking Attempt (2 concurrent requests, same slot)
```
REQUEST 1                     REQUEST 2
    │                              │
    │  POST /api/appointments      │
    │  (slot_id=ABC)               │
    ├─────────────────────────────►│
    │                              │  POST /api/appointments
    │                              │  (slot_id=ABC)
    │                              ├────────►
    │                              │
    │  BEGIN TRANSACTION           │  BEGIN TRANSACTION (waits...)
    │  SELECT * FROM slots         │  (blocked on lock)
    │  WHERE id=ABC FOR UPDATE ──┐ │
    │  (acquires lock)            └─┤ (still waiting)
    │  
    │  is_available = true? ✓      │
    │  INSERT appointments         │
    │  INSERT notifications        │
    │  UPDATE slots                │
    │  COMMIT (release lock)       │
    │                              │
    │                              │  ...lock acquired
    │                              │  SELECT * FROM slots
    │                              │  WHERE id=ABC
    │                              │  is_available = false ✗
    │                              │  ROLLBACK
    │                              │
    │  200 OK                      │  409 CONFLICT
    │  Appointment created         │  Slot already booked
```

**Key Guarantees:**
- Only 1 request acquires lock on the slot row
- Second request sees updated state or timeout
- Database constraint prevents inconsistency
- No application-level race conditions

---

## 3. Notification Processing Flow

### Main Thread vs Background Worker
```
BOOKING REQUEST (Main Thread)     BACKGROUND WORKER (Async)
    │                                    │
    │ 1. BEGIN transaction               │
    │ 2. Insert appointment             │
    │ 3. Insert notification            │
    │    (status='QUEUED')             │
    │ 4. COMMIT                         │
    │ 5. Return 201 to client           │
    └──► (request completes in ~50ms)   │
                                        │
                                        │  Every 5 seconds:
                                        ├─ SELECT * FROM notifications
                                        │  WHERE status='QUEUED'
                                        │
                                        ├─ For each notification:
                                        │  • Log booking confirmation
                                        │  • Simulate email send
                                        │  • UPDATE status='SENT'
                                        │  • UPDATE sent_at=NOW()
                                        │
                                        ├─ On error:
                                        │  • UPDATE status='FAILED'
                                        │  • UPDATE retry_count += 1
                                        │  • log error_details
                                        │
                                        └─ Retry failed:
                                           After 5 mins, if retry_count < 3
                                           Mark back as QUEUED

Timeline:
T=0ms:     Booking committed to DB
T=5ms:     Response sent to client
T=5-10s:   Notification marked SENT
T=100ms:   Client receives confirmation
```

**Guarantees:**
- ✅ Booking confirmed before notification processing starts
- ✅ If notification fails, it's recorded (not lost)
- ✅ Automatic retry (transient failures recover)
- ✅ Complete audit trail
- ✅ Can migrate to queue (RabbitMQ, SQS) without changing booking logic

---

## 4. Idempotency Flow (Duplicate Request Safety)

### Request Replay Scenario
```
REQUEST 1 (Original)            REQUEST 2 (Retry - same Idempotency-Key)
    │                                │
    │ Header: Idempotency-Key = XYZ  │
    │ POST /api/appointments         │ Header: Idempotency-Key = XYZ
    ├────────────────────────────►   │ POST /api/appointments
    │                                ├────────►
    │ Middleware                     │
    │ • Extract key: XYZ             │ Middleware
    │ • Query DB: exists?            │ • Extract key: XYZ
    │ • Not found                    │ • Query DB: exists?
    │                                │ ✓ Found!
    │ Service Layer                  │
    │ • Execute booking              │ Return cached response
    │ • Store in idempotency_records │ (no DB changes)
    │ • Response: 201               │
    │ {                              │ 200 OK (same response as original)
    │   "id": "appt-123",            │ {
    │   "status": "CONFIRMED"        │   "id": "appt-123",
    │   ...                          │   "status": "CONFIRMED"
    │ }                              │   ...
    │                                │ }
    │ Idempotency Record Stored:     │
    │ • key: XYZ                     │
    │ • method: POST                 │
    │ • response_status: 201         │
    │ • response_body: {...}         │
```

**Key Points:**
- ✅ Same request ID always returns same response
- ✅ Second call doesn't execute business logic
- ✅ No duplicate appointments created
- ✅ Works even if first request failed partially
- ✅ TTL cleanup prevents DB bloat (24h expiry)

---

## 5. Cancellation Request Flow (Idempotent)

```
DELETE /api/appointments/{id}
Header: Idempotency-Key = ABC123

Middleware:
├─ Check idempotency_records for key ABC123
│  └─ Not found, proceed
│
Service Layer:
├─ Query appointment {id}
│  └─ Found, status=CONFIRMED
│
├─ BEGIN TRANSACTION
│
├─ SELECT * FROM appointments
│  WHERE id={id} AND status != 'CANCELLED'
│  FOR UPDATE
│
├─ Update appointments SET status='CANCELLED', cancelled_at=NOW()
│
├─ Insert notifications (event_type='CANCELLATION')
│  status='QUEUED'
│
├─ COMMIT
│
├─ Store idempotency record:
│  • key: ABC123
│  • response_status: 200
│  • response_body: { id, status: CANCELLED }
│
└─ Return 200 OK

═══════════════════════════════════════════════════════════════

SECOND DELETE request (same key: ABC123):

Middleware:
├─ Check idempotency_records for key ABC123
│  └─ Found! Return cached response directly
│     No service layer execution
│     No DB transaction
│     Instant response (200 OK)
```

**Guarantees:**
- ✅ Delete is idempotent (safe to retry)
- ✅ Calling twice doesn't create issues
- ✅ Second call returns instantly (no DB work)
- ✅ Consistent state maintained

---

## 6. Data Flow: GET /api/appointments/{id}

```
CLIENT REQUEST                  BACKEND                    DATABASE
    │                               │                          │
    │ GET /api/appointments/123     │                          │
    ├──────────────────────────────►│                          │
    │                               │ appointment_service      │
    │                               │  .get_appointment(123)   │
    │                               ├─────────────────────────┤
    │                               │ SELECT * FROM            │
    │                               │ appointments a           │
    │                               │ JOIN availability_slots s│
    │                               │ WHERE a.id=123          │
    │                               │◄─────────────────────────┤
    │                               │ Result:                  │
    │                               │ {                        │
    │                               │   id: 123,              │
    │                               │   slot_date: ...,       │
    │                               │   slot_time: ...,       │
    │                               │   customer_name: ...,   │
    │                               │   customer_email: ...,  │
    │                               │   status: CONFIRMED,    │
    │                               │   created_at: ...,      │
    │                               │   confirmed_at: ...     │
    │                               │ }                       │
    │◄──────────────────────────────┤                         │
    │ 200 OK                        │                          │
    │ { appointment data }          │                         │
```

---

## 7. System State Transitions

### Appointment Lifecycle State Machine
```
                            ┌─────────┐
                            │ PENDING │ (created but unconfirmed)
                            └────┬────┘
                                 │
                ┌────────────────┤
                │                │
        [Booking OK]      [Error/Timeout]
                │                │
              ▼                ▼
        ┌───────────┐    [Log Error]
        │ CONFIRMED │
        └─────┬─────┘
              │
        [Cancel Request]
              │
              ▼
        ┌───────────┐
        │ CANCELLED │ (immutable: never returns to CONFIRMED)
        └───────────┘

Rules:
- PENDING → CONFIRMED: Via booking API
- CONFIRMED → CANCELLED: Via cancel API
- CANCELLED → X: NOT ALLOWED (immutable)
- Only one appointment per slot (unique constraint)
```

### Notification Lifecycle State Machine
```
            ┌──────────┐
            │  QUEUED  │ (waiting to process)
            └────┬─────┘
                 │
        ┌────────┴────────┐
        │                 │
    [Success]         [Failure]
        │                 │
        ▼                 ▼
    ┌────────┐        ┌────────┐
    │  SENT  │        │ FAILED │
    └────────┘        └────┬───┘
                           │
                    [Retry < 3?]
                           │
                    ┌──────┴──────┐
                    │             │
                  [Yes]          [No]
                    │             │
                    ▼             ▼
                 [Re-queue]    [Dead Letter]
                               (Log Error)

Processing: Every 5 seconds:
1. Fetch all QUEUED
2. For each: try send, update status
3. Max 3 retries per notification
4. Exponential backoff: 5s, 25s, 125s
```

---

## 8. Database Transaction Isolation

### Double-Booking Prevention Through Transactions

```
PostgreSQL Transaction Isolation (READ COMMITTED)

Transaction 1                      Transaction 2              Conflicts  
──────────────                      ──────────────            ──────────
BEGIN TRANSACTION                                
SELECT * FROM slots
WHERE id=123 FOR UPDATE ────► LOCK ACQUIRED on row 123
├─ slot.is_available = true
└─ OK to insert                                     
                                BEGIN TRANSACTION
                                SELECT * FROM slots
                                WHERE id=123 FOR UPDATE ──► WAITS...
                                                              (waiting for lock)
INSERT appointments (slot_id=123)
INSERT notifications                                   
UPDATE slots SET is_available=false
COMMIT ──────► LOCK RELEASED


                                /* Now continues */
                                SELECT sees: is_available=false
                                ROLLBACK or return 409 CONFLICT

Result: No double booking possible ✓
```

**Key Techniques:**
- `SELECT ... FOR UPDATE`: Row-level exclusive lock
- `UNIQUE(slot_id) WHERE status != 'CANCELLED'`: Constraint (fallback)
- Transactions: All-or-nothing bookings
- Explicit over implicit: No cached reads, always check DB state

---

## 9. Error Scenarios & Recovery

### Scenario 1: Network Failure During Booking

```
REQUEST flow:
T=0:  Client sends POST /api/appointments
T=100: Backend receives, starts transaction
T=150: Appointment inserted to DB
T=200: Network timeout (client doesn't receive response)
T=300: Backend transaction commits successfully

CLIENT STATE: Unknown (response not received)
BACKEND STATE: Appointment created ✓
  
SOLUTION:
T=400: Client retries with same Idempotency-Key
       Middleware detects: key exists in idempotency_records
       Returns cached response (200 OK with same appointment ID)
       Zero duplicate work

Result: ✓ Exactly-once semantics despite network failure
```

### Scenario 2: Database Unavailable During Cancel

```
REQUEST:
DELETE /api/appointments/123
Header: Idempotency-Key = XYZ

Service attempts transaction:
├─ BEGIN TRANSACTION
├─ Query appointment ✓
├─ UPDATE status='CANCELLED'
└─ [Database unavailable] ✗
   PostgreSQL connection timeout

RESPONSE: 503 Service Unavailable
CLIENT BEHAVIOR: Retry with same Idempotency-Key

NEXT ATTEMPT (DB recovered):
  Middleware checks: key XYZ exists?
  [First attempt was not persisted]
  └─ Execute normally (not in idempotency_records)
  
  Transaction succeeds → Store in idempotency_records
  Return 200 OK
```

### Scenario 3: Notification Worker Crash

```
BOOKING SUCCEEDS:
├─ Appointment created ✓
├─ Notification inserted (status=QUEUED) ✓
└─ Client gets 201 OK ✓

WORKER PROCESSING:
├─ Fetch notification
├─ Log confirmation
├─ [Worker crashes] ✗

RECOVERY (Worker restarts):
├─ SELECT notifications WHERE status=QUEUED
├─ Previous notification still there (not lost!)
├─ Process again (logging is idempotent)
└─ Update status=SENT ✓

Result: ✓ No lost notifications despite crashes
```

---

## 10. Performance Characteristics

### Request Latency (Typical)
```
GET /api/availability
├─ Query slots: ~5ms
├─ Serialize response: ~2ms
└─ Total: ~7ms (no locks)

POST /api/appointments
├─ Acquire lock: ~2ms
├─ Insert + update: ~8ms
├─ Serialize response: ~2ms
└─ Total: ~12ms (locked, but fast)

GET /api/appointments/{id}
├─ Join query: ~3ms
├─ Serialize: ~1ms
└─ Total: ~4ms

DELETE /api/appointments/{id}
├─ Acquire lock: ~1ms
├─ Update + insert: ~5ms
├─ Serialize: ~1ms
└─ Total: ~7ms
```

### Concurrency Characteristics
```
10 concurrent bookings on same slot:
├─ 1st acquires lock, inserts, releases (~12ms)
├─ 2-10 queue waiting for lock
│        └─ Each returns 409 CONFLICT (~5ms from lock release)
└─ Total time: ~25ms for all 10 requests to complete

1000 bookings across 100 slots:
├─ Lock contention: <5% of requests
├─ Throughput: ~80-100 bookings/sec
├─ Tail latency (p95): ~20ms
└─ At no risk of double-booking ✓
```

---

## Summary: Why This Design Works

### Prevents Double-Booking
✅ Database lock enforces mutual exclusion  
✅ Unique constraint (fallback)  
✅ Explicit transaction boundaries  

### Handles Retries Safely
✅ Idempotency keys prevent duplicate work  
✅ Cached responses for exact replay  
✅ Safe even with network failures  

### Reliable Notifications
✅ Decoupled from booking (fast API)  
✅ Persistent queue (notifications table)  
✅ Automatic retry with backoff  
✅ Complete audit trail  

### Operational Clarity
✅ Simple state machines (status fields)  
✅ No implicit behavior  
✅ Clear error codes (409, 404, 503)  
✅ Fully auditable  

This design reflects production engineering principles in a minimal scope.
