# Database initialization script
# Run this to seed initial data into the database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create tables
create schema if not exists public;

-- Note: SQLAlchemy will create tables automatically
-- This file is here for future reference

-- Example: Create availability slots for demo
-- INSERT INTO availability_slots (id, slot_date, slot_time, duration_minutes, is_available, created_at)
-- VALUES (
--     gen_random_uuid(),
--     CURRENT_DATE + INTERVAL '1 day',
--     '09:00:00',
--     60,
--     true,
--     CURRENT_TIMESTAMP
-- );
