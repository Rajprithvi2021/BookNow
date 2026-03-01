# Custom exceptions for BookNow

class BookNowException(Exception):
    """Base exception for BookNow system."""
    status_code = 500
    error_code = "internal_error"

class DoubleBookingError(BookNowException):
    """Raised when attempting to book an already-booked slot."""
    status_code = 409
    error_code = "slot_already_booked"

class AppointmentNotFoundError(BookNowException):
    """Raised when appointment doesn't exist."""
    status_code = 404
    error_code = "appointment_not_found"

class InvalidStateTransitionError(BookNowException):
    """Raised when appointment state transition is invalid."""
    status_code = 409
    error_code = "invalid_state_transition"

class ValidationError(BookNowException):
    """Raised on input validation failure."""
    status_code = 400
    error_code = "validation_error"

class DatabaseError(BookNowException):
    """Raised on database operation failure."""
    status_code = 500
    error_code = "database_error"
