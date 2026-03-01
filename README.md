# BookNow - Appointment Booking System

A production-ready appointment booking system demonstrating professional software engineering principles.

## Features

✅ **Double-booking prevention** - ACID transactions + row-level locking  
✅ **Idempotent mutations** - Safe for retries (no duplicate bookings)  
✅ **Async notifications** - Decoupled background processing  
✅ **Type-safe** - TypeScript frontend, Pydantic validation backend  
✅ **Concurrency-tested** - Race conditions explicitly verified  
✅ **Clean architecture** - Separation of concerns (routes → services → db)  
✅ **Production-grade** - Error handling, logging, audit trails  

## Tech Stack

**Backend:**
- Python 3.11+
- FastAPI (async web framework)
- PostgreSQL (with row-level locking)
- SQLAlchemy (ORM)
- Pydantic (data validation)

**Frontend:**
- Next.js 14 (React framework)
- TypeScript
- shadcn/ui (component library)
- Tailwind CSS

**Database:**
- PostgreSQL 15 (ACID transactions, row locks)
- Alembic (migrations)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or Docker)
- Git

### Option 1: Docker (Easiest)

```bash
# Clone repo and navigate
cd booknow

# Start all services
docker-compose up --build

# Wait for output:
# postgres_1  | database system is ready to accept connections
# backend_1   | Application startup complete
# frontend_1  | compiled client and server successfully
```

Access:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Option 2: Manual Setup

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy env file
cp .env.example .env

# Setup database (ensure PostgreSQL is running)
# Edit DATABASE_URL in .env if needed
alembic upgrade head

# Run server
python -m src.main
# Runs on http://localhost:8000
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Copy env file
cp .env.local.example .env.local

# Start dev server
npm run dev
# Runs on http://localhost:3000
```

## Architecture

### System Design

```
┌─ FRONTEND (Next.js) ─┐
│  • Availability Calendar
│  • Booking Form
│  • My Appointments
└─────────┬────────────┘
          │ REST API
          │ Idempotency Keys
          │
┌─────────▼────────────┐
│  BACKEND (FastAPI)   │
│  ┌──────────────────┐│
│  │ Routes (HTTP)    ││
│  ├──────────────────┤│
│  │ Services (Logic) ││
│  │ • Book (locking) ││
│  │ • Cancel (state) ││
│  │ • Notify (queue) ││
│  ├──────────────────┤│
│  │ Database (ACID)  ││
│  └──────────────────┘│
└─────────┬────────────┘
          │
┌─────────▼────────────┐
│  PostgreSQL          │
│  • Slots (locked)    │
│  • Appointments      │
│  • Notifications     │
└──────────────────────┘
```

### API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/availability` | List available slots for next 7 days |
| POST | `/api/appointments` | Book appointment (idempotent) |
| GET | `/api/appointments/{id}` | Get appointment details |
| DELETE | `/api/appointments/{id}` | Cancel appointment (idempotent) |

See [ASSIGNMENT_BRIEF.md](./ASSIGNMENT_BRIEF.md) for full API specification.

## Key Design Decisions

### 1. Pessimistic Locking (No Double-Bookings)

**Problem**: Two requests for same slot simultaneously.

**Solution**: Database row-level lock (`SELECT ... FOR UPDATE`)

```python
# Only 1 request acquires lock, others wait
session.query(AvailabilitySlot).with_for_update().filter_by(id=slot_id)
```

**Guarantee**: First request succeeds, others get 409 Conflict.

### 2. Idempotency Keys (Safe Retries)

**Problem**: Network retry causes duplicate booking.

**Solution**: Request idempotency key + response caching

```
POST /api/appointments
Header: Idempotency-Key: uuid-here

First call:  Creates appointment, caches response
Second call: Returns cached response (no DB work)
Result:      1 appointment despite retries ✓
```

### 3. Async Notifications (Non-Blocking)

**Problem**: Booking blocked if email service slow/down.

**Solution**: Queue notifications in database, process async

```python
# Booking returns instantly
INSERT notification (status='QUEUED')
RETURN 201

# Background worker processes separately
[polling every 5 seconds]
UPDATE notification SET status='SENT'
```

### 4. Immutable Appointment History

**Never delete** - Only transition to CANCELLED state.

```python
# Audit trail
appointments.created_at      # When booked
appointments.confirmed_at    # When confirmed
appointments.cancelled_at    # When cancelled (never deleted)
```

## Testing

### Run Tests

```bash
cd backend

# All tests
pytest tests/ -v

# Concurrency tests (critical)
pytest tests/test_concurrency.py -v

# Coverage report
pytest tests/ --cov=src --cov-report=html
```

### Test Categories

**Unit Tests** - Service layer logic
- ✅ Booking creates CONFIRMED appointment
- ✅ Double-booking raises error
- ✅ Cancellation idempotent

**Integration Tests** - API endpoints
- ✅ GET /availability returns slots
- ✅ POST /appointments returns 201
- ✅ DELETE /appointments idempotent

**Concurrency Tests** - Race conditions (Most Important)
- ✅ 10 concurrent bookings same slot → only 1 succeeds
- ✅ Multiple cancellations → no conflicts
- ✅ Load test: 50 users, 100 slots → 0 double-books

## Project Structure

```
booknow/
├── ASSIGNMENT_BRIEF.md        # What we're building
├── ARCHITECTURE.md            # Design decisions
├── README.md                  # This file
│
├── backend/
│   ├── src/
│   │   ├── main.py           # FastAPI app
│   │   ├── api/
│   │   │   ├── routes/       # Endpoints
│   │   │   └── schemas/      # Request/response models
│   │   ├── services/         # Business logic
│   │   ├── db/
│   │   │   ├── models.py     # SQLAlchemy tables
│   │   │   └── migrations/   # Alembic scripts
│   │   └── utils/            # Helpers, exceptions
│   └── tests/                # Unit + integration + concurrency
│
├── frontend/
│   ├── src/
│   │   ├── app/              # Next.js pages
│   │   ├── components/       # React components
│   │   ├── hooks/            # Custom hooks
│   │   └── lib/              # Utilities
│   └── package.json
│
└── docker-compose.yml
```

## Known Limitations

- ❌ No authentication/authorization (demo only)
- ❌ Notifications logged to console (not real email)
- ❌ Single timezone support
- ❌ Single-provider scheduling

## Future Improvements

With more time:
- [ ] JWT authentication
- [ ] Real email notifications (Sendgrid, SES)
- [ ] Email verification
- [ ] Multi-provider calendars
- [ ] Timezone support
- [ ] Rate limiting
- [ ] Admin dashboard
- [ ] Calendar sync (Google/Outlook)

## Deployment

For production:

1. **Database**: Use managed PostgreSQL (AWS RDS, Azure Database, etc.)
2. **Backend**: Deploy to Docker registry (ECR, ACR, etc.)
3. **Frontend**: Deploy to CDN (Vercel, Netlify, CloudFront)
4. **Monitoring**: Add APM (DataDog, New Relic)
5. **Notifications**: Configure real email service

See DEPLOYMENT.md for detailed steps (TODO).

## Trade-offs Made

| Choice | Why | Alternative | Reason Not Chosen |
|--------|-----|-----------|------------------|
| **Pessimistic Locking** | Simple, reliable | Optimistic | Clearer semantics |
| **Async Notifications** | Non-blocking | Sync | Would slow booking |
| **PostgreSQL** | Row locks, ACID | SQLite | Need FOR UPDATE |
| **FastAPI** | Modern, async | Flask/Django | Type-safe, performance |
| **Next.js** | Full-stack | React SPA | Server components help |

## Contributing

This is a take-home assignment. Not open for contributions.

## License

This project is educational. See LICENSE file if present.

---

## Support

For questions about the design or implementation, see:
- [ASSIGNMENT_BRIEF.md](./ASSIGNMENT_BRIEF.md) - What we're building
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Why we chose this design
- [TECHNICAL_DECISIONS.md](./TECHNICAL_DECISIONS.md) - Trade-off analysis

## Author

Built for BigCircle Engineering Take-Home Assignment
