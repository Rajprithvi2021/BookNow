"""FastAPI application initialization and middleware."""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import uuid as uuid_module

from src.core.config import Settings
from src.api.routes import router
from src.utils.exceptions import BookNowException
from src.utils.logger import logger


def create_app(settings: Settings = None) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        settings: Settings object (uses defaults if None)
    
    Returns:
        Configured FastAPI app instance
    """
    
    if settings is None:
        settings = Settings()
    
    app = FastAPI(
        title="BookNow API",
        description="Appointment booking system with concurrency control",
        version="1.0.0"
    )
    
    # ========================================================================
    # Middleware
    # ========================================================================
    
    # CORS: Allow frontend to access API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url] if settings.frontend_url else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*", "Idempotency-Key"],
    )
    
    # Error handler middleware
    app.add_middleware(ErrorHandlerMiddleware)
    
    # Request ID middleware (for tracing)
    app.add_middleware(RequestIDMiddleware)
    
    # ========================================================================
    # Routes
    # ========================================================================
    
    app.include_router(router)
    
    # ========================================================================
    # Startup/Shutdown
    # ========================================================================
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize database on startup."""
        from src.db.connection import init_db
        init_db()
        logger.info("Database initialized")
    
    return app


# ============================================================================
# Custom Middleware
# ============================================================================

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Convert custom exceptions to HTTP responses."""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except BookNowException as e:
            logger.warning(f"BookNow error: {e}")
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.__class__.__name__,
                    "message": str(e),
                    "request_id": request.headers.get("X-Request-ID")
                }
            )
        except Exception as e:
            logger.error(f"Unhandled exception: {e}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={
                    "error": "InternalServerError",
                    "message": "An unexpected error occurred",
                    "request_id": request.headers.get("X-Request-ID")
                }
            )


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Add request ID to all requests for tracing."""
    
    async def dispatch(self, request: Request, call_next):
        # Use existing request ID or generate new one
        request_id = request.headers.get("X-Request-ID", str(uuid_module.uuid4()))
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        
        return response


# ============================================================================
# Application Entry Point
# ============================================================================

# Create app instance (for uvicorn)
app = create_app()
