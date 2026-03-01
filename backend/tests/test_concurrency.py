"""
Concurrency tests - CRITICAL for verifying double-booking prevention.

These tests simulate realistic concurrent scenarios to verify the core
safety invariant: NO DOUBLE-BOOKINGS under ANY concurrent access pattern.
"""

import pytest
import threading
from uuid import uuid4
from datetime import date, time
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.db.models import AvailabilitySlot, Appointment, AppointmentStatus
from src.services.appointment_service import AppointmentService
from src.utils.exceptions import DoubleBookingError


@pytest.fixture
def concurrent_slot(test_db):
    """Create a slot for concurrency testing."""
    slot = AvailabilitySlot(
        id=uuid4(),
        slot_date=date(2024, 12, 20),
        slot_time=time(15, 0),
        duration_minutes=60,
        is_available=True
    )
    test_db.add(slot)
    test_db.commit()
    return slot


class TestConcurrentBooking:
    """Tests for concurrent booking scenarios."""
    
    def test_concurrent_bookings_same_slot(self, test_db, concurrent_slot):
        """
        CRITICAL TEST: 100+ concurrent booking attempts on same slot.
        
        Expected: EXACTLY ONE succeeds, ALL others fail with DoubleBookingError.
        
        This verifies the pessimistic locking prevents any race conditions.
        """
        slot_id = concurrent_slot.id
        num_concurrent_requests = 50
        results = {"success": 0, "failed": 0, "errors": []}
        lock = threading.Lock()
        
        def attempt_booking(request_num):
            """Attempt to book the slot."""
            try:
                # Each request gets fresh session
                from src.db.connection import SessionLocal
                session = SessionLocal()
                
                appointment = AppointmentService.book_appointment(
                    session=session,
                    slot_id=slot_id,
                    customer_name=f"Customer {request_num}",
                    customer_email=f"customer{request_num}@example.com",
                    idempotency_key=uuid4()
                )
                
                with lock:
                    results["success"] += 1
                
                session.close()
                return {"status": "success", "appointment_id": str(appointment.id)}
                
            except DoubleBookingError as e:
                with lock:
                    results["failed"] += 1
                    results["errors"].append(str(e))
                session.close()
                return {"status": "failed", "reason": "double_booking"}
                
            except Exception as e:
                with lock:
                    results["errors"].append(f"Unexpected: {str(e)}")
                return {"status": "error", "reason": str(e)}
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(attempt_booking, i) 
                for i in range(num_concurrent_requests)
            ]
            
            responses = [f.result() for f in as_completed(futures)]
        
        # CRITICAL ASSERTIONS
        assert results["success"] == 1, (
            f"Expected exactly 1 success, got {results['success']}. "
            "Indicates race condition!"
        )
        assert results["failed"] == num_concurrent_requests - 1, (
            f"Expected {num_concurrent_requests - 1} failures, "
            f"got {results['failed']}"
        )
        
        # Verify only one appointment exists for this slot
        from src.db.connection import SessionLocal
        verify_session = SessionLocal()
        
        active_appointments = verify_session.query(Appointment).filter(
            Appointment.availability_slot_id == slot_id,
            Appointment.status != AppointmentStatus.CANCELLED
        ).all()
        
        assert len(active_appointments) == 1, (
            f"Expected exactly 1 active appointment, found {len(active_appointments)}"
        )
        
        verify_session.close()
    
    def test_sequential_then_concurrent_booking(self, test_db, concurrent_slot):
        """
        Test mixed sequential and concurrent booking attempts.
        
        Scenario:
        1. First request books the slot (succeeds)
        2. 50 concurrent requests try to book same slot
        3. All concurrent requests should fail
        """
        from src.db.connection import SessionLocal
        
        slot_id = concurrent_slot.id
        
        # First booking succeeds
        session1 = SessionLocal()
        appt1 = AppointmentService.book_appointment(
            session=session1,
            slot_id=slot_id,
            customer_name="First Booker",
            customer_email="first@example.com",
            idempotency_key=uuid4()
        )
        session1.close()
        
        # Now try 20 concurrent bookings
        success_count = 0
        failure_count = 0
        
        def attempt_second_booking(req_num):
            nonlocal success_count, failure_count
            try:
                session = SessionLocal()
                AppointmentService.book_appointment(
                    session=session,
                    slot_id=slot_id,
                    customer_name=f"Concurrent {req_num}",
                    customer_email=f"concurrent{req_num}@example.com",
                    idempotency_key=uuid4()
                )
                success_count += 1
                session.close()
            except DoubleBookingError:
                failure_count += 1
                session.close()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(attempt_second_booking, i)
                for i in range(20)
            ]
            for future in as_completed(futures):
                future.result()
        
        # All concurrent attempts should fail
        assert success_count == 0, (
            f"Expected 0 successes in concurrent batch, got {success_count}"
        )
        assert failure_count == 20, (
            f"Expected 20 failures, got {failure_count}"
        )


class TestConcurrentCancellation:
    """Tests for concurrent cancellation scenarios."""
    
    def test_concurrent_cancellations_idempotent(self, test_db, concurrent_slot):
        """
        Test concurrent cancellations are idempotent.
        
        Scenario:
        1. Create appointment
        2. Cancel it from 10 different threads simultaneously
        3. All should succeed and return same state (idempotent)
        """
        from src.db.connection import SessionLocal
        
        # Create appointment
        session = SessionLocal()
        appointment = AppointmentService.book_appointment(
            session=session,
            slot_id=concurrent_slot.id,
            customer_name="To Cancel",
            customer_email="tocancel@example.com",
            idempotency_key=uuid4()
        )
        appt_id = appointment.id
        session.close()
        
        # Concurrently cancel it
        success_count = 0
        cancelled_states = []
        lock = threading.Lock()
        
        def attempt_cancel(req_num):
            nonlocal success_count
            try:
                session = SessionLocal()
                result = AppointmentService.cancel_appointment(
                    session=session,
                    appointment_id=appt_id
                )
                
                with lock:
                    success_count += 1
                    cancelled_states.append({
                        "status": result.status,
                        "cancelled_at": result.cancelled_at
                    })
                
                session.close()
            except Exception as e:
                session.close()
                raise
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(attempt_cancel, i)
                for i in range(10)
            ]
            for future in as_completed(futures):
                future.result()
        
        # All should succeed (idempotent)
        assert success_count == 10
        
        # All should return same status
        assert all(
            state["status"] == AppointmentStatus.CANCELLED
            for state in cancelled_states
        )
