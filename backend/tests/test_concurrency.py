"""
Concurrency tests - Double-booking prevention verification.

These tests verify that the pessimistic locking mechanism prevents
double-booking even when multiple threads attempt to book the same slot.
"""

import pytest
from uuid import uuid4
from threading import Thread
import time
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.db.models import (
    Base, AvailabilitySlot, Appointment, AppointmentStatus
)
from src.db.connection import get_db
from src.services.appointment_service import AppointmentService
from src.utils.exceptions import DoubleBookingError
from datetime import datetime, date


class TestConcurrentBooking:
    """Tests for concurrent booking scenarios."""
    
    def test_concurrent_bookings_same_slot(self, db_session):
        """Test that concurrent bookings of the same slot results in only one success."""
        # Create a slot
        slot = AvailabilitySlot(
            slot_date=date(2026, 3, 15),
            slot_time="10:00",
            duration_minutes=60,
            is_available=True
        )
        db_session.add(slot)
        db_session.commit()
        slot_id = slot.id
        
        results = {"success": [], "errors": []}
        
        def book_slot(customer_num):
            """Try to book the same slot."""
            try:
                appointment = AppointmentService.book_appointment(
                    session=db_session,
                    slot_id=slot_id,
                    customer_name=f"Customer {customer_num}",
                    customer_email=f"customer{customer_num}@example.com",
                    idempotency_key=uuid4(),
                    notes=None
                )
                results["success"].append(appointment)
            except DoubleBookingError as e:
                results["errors"].append(str(e))
        
        # Simulate concurrent booking attempts
        threads = []
        for i in range(5):
            t = Thread(target=book_slot, args=(i,))
            threads.append(t)
            t.start()
        
        # Wait for all threads
        for t in threads:
            t.join()
        
        # Verify: Only ONE successful booking, rest got errors
        assert len(results["success"]) == 1, f"Expected 1 success, got {len(results['success'])}"
        assert len(results["errors"]) == 4, f"Expected 4 errors, got {len(results['errors'])}"
        
        # Verify the slot is marked unavailable
        db_session.refresh(slot)
        assert not slot.is_available
        
        # Verify the appointment was created
        appointment = results["success"][0]
        assert appointment.status == AppointmentStatus.CONFIRMED
    
    def test_sequential_then_concurrent_booking(self, db_session):
        """Test mixed sequential and concurrent booking attempts."""
        # Create 2 slots
        slot1 = AvailabilitySlot(
            slot_date=date(2026, 3, 20),
            slot_time="09:00",
            duration_minutes=60,
            is_available=True
        )
        slot2 = AvailabilitySlot(
            slot_date=date(2026, 3, 20),
            slot_time="11:00",
            duration_minutes=60,
            is_available=True
        )
        db_session.add_all([slot1, slot2])
        db_session.commit()
        
        # First, book slot1 sequentially
        app1 = AppointmentService.book_appointment(
            session=db_session,
            slot_id=slot1.id,
            customer_name="First Customer",
            customer_email="first@example.com",
            idempotency_key=uuid4(),
            notes=None
        )
        assert app1.status == AppointmentStatus.CONFIRMED
        
        # Now try to book slot1 concurrently (should all fail)
        results = {"success": [], "errors": []}
        
        def book_slot1(customer_num):
            try:
                appointment = AppointmentService.book_appointment(
                    session=db_session,
                    slot_id=slot1.id,
                    customer_name=f"Concurrent {customer_num}",
                    customer_email=f"concurrent{customer_num}@example.com",
                    idempotency_key=uuid4(),
                    notes=None
                )
                results["success"].append(appointment)
            except DoubleBookingError:
                results["errors"].append("Double booking error")
        
        threads = []
        for i in range(3):
            t = Thread(target=book_slot1, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All concurrent attempts should fail
        assert len(results["success"]) == 0
        assert len(results["errors"]) == 3


class TestConcurrentCancellation:
    """Tests for concurrent cancellation scenarios."""
    
    def test_concurrent_cancellations_idempotent(self, db_session):
        """Test concurrent cancellations are idempotent and don't cause errors."""
        # Create and book a slot
        slot = AvailabilitySlot(
            slot_date=date(2026, 3, 25),
            slot_time="14:00",
            duration_minutes=60,
            is_available=True
        )
        db_session.add(slot)
        db_session.commit()
        
        appointment = AppointmentService.book_appointment(
            session=db_session,
            slot_id=slot.id,
            customer_name="Test Customer",
            customer_email="test@example.com",
            idempotency_key=uuid4(),
            notes=None
        )
        appointment_id = appointment.id
        
        results = {"success": [], "errors": []}
        
        def cancel_appointment(attempt_num):
            """Try to cancel the same appointment."""
            try:
                result = AppointmentService.cancel_appointment(
                    session=db_session,
                    appointment_id=appointment_id
                )
                results["success"].append(result)
            except Exception as e:
                results["errors"].append(str(e))
        
        # Simulate concurrent cancellation attempts
        threads = []
        for i in range(3):
            t = Thread(target=cancel_appointment, args=(i,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All attempts should succeed (idempotent)
        # Since they all modify the same appointment, they should all return the cancelled appointment
        assert len(results["success"]) >= 1, f"Expected at least 1 success, got {len(results['success'])}"
        assert len(results["errors"]) == 0, f"Expected no errors, got {len(results['errors'])}"
        
        # Verify appointment is cancelled
        db_session.refresh(appointment)
        assert appointment.status == AppointmentStatus.CANCELLED
        
        # Verify slot is available again
        db_session.refresh(slot)
        assert slot.is_available


