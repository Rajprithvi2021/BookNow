"""
Integration tests for API endpoints.

Tests the full request-response cycle including:
- Idempotency key handling
- Error responses
- Data validation
- HTTP status codes
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import date, time

from src.main import create_app
from src.core.config import Settings


@pytest.fixture
def app():
    """Create test app instance."""
    settings = Settings()
    return create_app(settings)


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def setup_slots(client):
    """Seed some availability slots for testing."""
    from datetime import timedelta
    from uuid import uuid4
    
    start_date = date(2024, 12, 15)
    slots = []
    
    # This would normally be done via admin endpoint or management command
    # For now, we'll just mark what SHOULD exist
    return {"start_date": start_date, "days": 7}


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_check(self, client):
        """Test health check returns 200."""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"


class TestAvailabilityEndpoint:
    """Tests for availability slots endpoint."""
    
    def test_get_availability(self, client, setup_slots):
        """
        Test retrieving available slots.
        
        Note: Requires slots to be seeded in database first.
        This test documents the expected behavior.
        """
        params = {
            "start_date": str(setup_slots["start_date"]),
            "days": setup_slots["days"]
        }
        response = client.get("/api/availability", params=params)
        
        assert response.status_code == 200
        data = response.json()
        assert "slots" in data
        assert "count" in data
        assert isinstance(data["slots"], list)


class TestBookingEndpoint:
    """Tests for appointment booking endpoint."""
    
    def test_book_appointment_requires_idempotency_key(self, client):
        """Test that booking without Idempotency-Key header fails."""
        payload = {
            "slot_id": str(uuid4()),
            "customer_name": "Test User",
            "customer_email": "test@example.com",
        }
        
        response = client.post("/api/appointments", json=payload)
        
        # Should fail without idempotency key
        assert response.status_code in [400, 422]
    
    def test_book_appointment_invalid_email(self, client):
        """Test validation of email format."""
        payload = {
            "slot_id": str(uuid4()),
            "customer_name": "Test User",
            "customer_email": "not-an-email",
        }
        
        response = client.post(
            "/api/appointments",
            json=payload,
            headers={"Idempotency-Key": str(uuid4())}
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]
    
    def test_book_appointment_missing_name(self, client):
        """Test that customer name is required."""
        payload = {
            "slot_id": str(uuid4()),
            "customer_email": "test@example.com",
        }
        
        response = client.post(
            "/api/appointments",
            json=payload,
            headers={"Idempotency-Key": str(uuid4())}
        )
        
        # Should fail validation
        assert response.status_code in [400, 422]


class TestCancelEndpoint:
    """Tests for appointment cancellation endpoint."""
    
    def test_cancel_nonexistent_appointment(self, client):
        """Test cancelling a nonexistent appointment returns 404."""
        response = client.delete(
            f"/api/appointments/{uuid4()}"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["message"].lower()


class TestAppointmentListEndpoint:
    """Tests for listing appointments by email."""
    
    def test_list_appointments_requires_email(self, client):
        """Test that email parameter is required."""
        response = client.get("/api/appointments")
        
        # Should fail without email
        assert response.status_code in [400, 422]
    
    def test_list_appointments_valid_email(self, client):
        """Test listing appointments with valid email."""
        response = client.get(
            "/api/appointments",
            params={"email": "test@example.com"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "appointments" in data
        assert "count" in data
