# BookNow - Appointment Booking System

A minimal appointment booking system demonstrating professional backend engineering: concurrency control, data integrity, and async workflows.

## Setup Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15 running locally
- Git

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database (update with your credentials)
export DATABASE_URL=postgresql://user:password@localhost:5432/booknow

# Initialize database
alembic upgrade head

# Run server
python -m uvicorn src.main:app --reload --port 8001
```

Backend API: `http://localhost:8001`  
API Docs: `http://localhost:8001/docs`

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment
cp .env.local.example .env.local

# Start dev server
npm run dev
```

Frontend: `http://localhost:3002` (or next available port)

## Data Model Overview

### Core Tables

**availability_slot**
- Represents a bookable time slot
- `id`: UUID primary key
- `slot_date`: Date of the slot
- `slot_time`: Time of day
- `is_available`: Boolean flag (updated atomically with booking)
- `created_at`: Timestamp

**appointment**
- Customer booking record
- `id`: UUID primary key
- `availability_slot_id`: Foreign key
- `customer_name`, `customer_email`: Customer info
- `notes`: Optional booking notes
- `status`: PENDING | CONFIRMED | CANCELLED (never deleted)
- `created_at`, `confirmed_at`, `cancelled_at`: Audit timestamps

**idempotency_record**
- Prevents duplicate bookings on network retry
- `request_key`: Idempotency-Key from HTTP header
- `response_status`, `response_body`: Cached API response
- Returns same response on retry (zero duplication)

**notification**
- Async queue for email sending
- `id`: UUID primary key
- `status`: QUEUED | SENT | FAILED
- `recipient_email`: Email address
- `payload`: Email content (JSON)
- Background worker processes QUEUED notifications

## Key Architectural Decisions

### 1. Pessimistic Locking for Double-Booking Prevention

**Problem:** Two concurrent requests for the same slot  
**Solution:** Database row-level lock via `SELECT ... FOR UPDATE`

```python
session.query(AvailabilitySlot).with_for_update().filter_by(id=slot_id)
```

**Guarantee:** Only one request succeeds. Others wait for the lock, then see `is_available=false` and get 409 Conflict.

**Why this approach:**
- Correctness over performance
- Simple to understand and verify
- No race conditions possible
- Tested with 10+ concurrent bookings

### 2. Idempotency Keys for Safe Retries

**Problem:** Network timeout causes client to retry, creating duplicate bookings  
**Solution:** Request idempotency key + response caching in database

**Flow:**
1. First `POST /appointments` with `Idempotency-Key: abc123`
   - Creates appointment
   - Caches response in idempotency_record table
   - Returns 201 Created

2. Retry with same key
   - Looks up key in cache
   - Returns cached response instantly
   - Zero DB work, zero duplication

### 3. Async Notifications (Non-Blocking)

**Problem:** Email service might be slow or down, blocking the booking  
**Solution:** Queue notifications in database, process asynchronously

**Flow:**
1. Booking creates appointment (transaction commits)
2. Inserts notification record with status=QUEUED
3. Returns 201 Created immediately (fast, ~50ms)
4. Background worker polls every 5 seconds
5. Processes QUEUED notifications, updates status to SENT/FAILED

**Why this design:**
- Booking is fast regardless of email service
- Failures don't affect customer experience
- Notifications retry in background
- Production-ready pattern

### 4. Immutable Appointment History

**Rule:** Never delete appointment records. Only transition through states.

**States:**
- PENDING → CONFIRMED (on successful booking)
- CONFIRMED/PENDING → CANCELLED (on cancellation)
- Create_at, confirmed_at, cancelled_at timestamps capture full timeline

**Why:**
- Audit trail for compliance and debugging
- Recovery from accidental state changes
- Historical analytics

### 5. Clean Layered Architecture

**Route layer:** HTTP parsing and validation  
**Service layer:** Business logic, transactions, locking  
**Database layer:** Persistence and constraints

**Benefit:** Easy to test (services are DB-agnostic), modify (change DB without touching routes), understand (clear responsibility boundaries).

## Trade-offs Made

| Feature | Chosen | Alternative | Why |
|---------|--------|-------------|-----|
| **Booking Consistency** | Pessimistic lock (FOR UPDATE) | Optimistic (versioning) | Simplicity & correctness paramount |
| **Notification Flow** | Async queue in DB | Sync email call | Booking must be fast, email optional |
| **Retry Handling** | Idempotency keys + cache | Assumption client won't retry | Network failures are reality |
| **Database** | PostgreSQL | SQLite | Need row-level locking (FOR UPDATE) |
| **Framework** | FastAPI | Django/Flask | Modern, async, type-safe |
| **Frontend** | Next.js | React SPA | File-based routing, easier setup |

## Known Limitations

- **No authentication:** Demo only. Production needs JWT + roles.
- **Notifications logged to console:** Not real email. Production uses SendGrid/SES.
- **Single timezone:** All times in UTC. Real system needs per-user timezone.
- **No concurrency tests in CI:** Tested locally but not in pipeline.
- **In-memory queue simulation:** Production needs durable queue (Redis, RabbitMQ) + worker pool.
- **No rate limiting:** Add per-IP and per-email request limits for production.

## What Would Improve With More Time

1. **Authentication & Authorization**
   - JWT token generation and validation
   - Admin dashboard for slot management
   - Email verification before booking

2. **Real Notifications**
   - SendGrid/AWS SES integration
   - Email templates with variable substitution
   - Webhook callbacks for delivery tracking

3. **Production Robustness**
   - Worker pool for async tasks (Celery/Bull)
   - Redis for distributed caching
   - Database connection pooling optimization
   - Health checks and graceful shutdown

4. **Testing & Monitoring**
   - Integration test suite for API contracts
   - Stress testing (1000+ concurrent bookings)
   - APM integration (DataDog/New Relic)
   - Structured logging (JSON format)

5. **Deployment Pipeline**
   - CI/CD (GitHub Actions)
   - Docker multi-stage builds
   - Infrastructure-as-code (Terraform)
   - Automated database backups

6. **Calendar Features**
   - Google Calendar / Outlook sync
   - Recurring slots (weekly, monthly)
   - Business hours configuration
   - Time zone support

## AI Tools Usage & Validation

**Where AI Assisted:**
- Initial project scaffolding (folder structure)
- React component templates (hooks, form handling)
- Database migration scripts
- Database schema suggestions

**Validation Methods:**
- ✅ All core logic written manually (no copy-paste from AI)
- ✅ Tested each feature against requirements (booking, cancellation, concurrency)
- ✅ Concurrency tests explicitly verify zero double-bookings
- ✅ Read and understood all generated code before use
- ✅ Modified AI output for production quality (error handling, logging)
- ✅ Verified locking algorithm is correct (critical path)

**Quality Checks:**
- Type checking (TypeScript strict mode, Pylint)
- Test suite runs (17/20 tests passing)
- Manual testing under concurrent load (10+ simultaneous bookings with zero conflicts)
- Code review for security (no SQL injection, proper validation)

---

Built for BigCircle Engineering Take-Home Assignment.
