"""Idempotency key handling for mutation operations."""

from datetime import datetime, timedelta
from uuid import UUID
from typing import Optional
from sqlalchemy.orm import Session

from src.db.models import IdempotencyRecord
from src.utils.logger import logger


class IdempotencyService:
    """Handles idempotent request deduplication."""
    
    @staticmethod
    def get_cached_response(
        session: Session,
        idempotency_key: UUID
    ) -> Optional[dict]:
        """
        Check if this key was already processed.
        
        If found: return cached response (no DB work done).
        If not found: return None (process the request).
        
        Args:
            session: SQLAlchemy session
            idempotency_key: UUID from Idempotency-Key header
        
        Returns:
            Cached response dict or None
        """
        
        record = session.query(IdempotencyRecord) \
            .filter_by(idempotency_key=idempotency_key) \
            .one_or_none()
        
        if record:
            logger.info(f"Idempotency cache HIT for key {idempotency_key}")
            return {
                "status": record.response_status,
                "body": record.response_body
            }
        
        return None
    
    @staticmethod
    def store_response(
        session: Session,
        idempotency_key: UUID,
        method: str,
        path: str,
        status: int,
        body: dict,
        ttl_hours: int = 24
    ) -> None:
        """
        Store request result for future idempotent replays.
        
        Args:
            session: SQLAlchemy session
            idempotency_key: UUID from Idempotency-Key header
            method: HTTP method (POST, DELETE, etc)
            path: Request path (/api/appointments, etc)
            status: HTTP status code (201, 200, etc)
            body: Response body (JSON-serializable dict)
            ttl_hours: How long to keep record (default 24h)
        """
        
        record = IdempotencyRecord(
            idempotency_key=idempotency_key,
            method=method,
            resource_path=path,
            response_status=status,
            response_body=body,
            ttl_expires_at=datetime.utcnow() + timedelta(hours=ttl_hours)
        )
        session.add(record)
        session.commit()
        
        logger.info(
            f"Idempotency record stored: {method} {path} → {status}"
        )
    
    @staticmethod
    def cleanup_expired_records(session: Session) -> int:
        """
        Delete idempotency records that have expired.
        
        Should be run periodically (background job).
        """
        
        expired = session.query(IdempotencyRecord) \
            .filter(
                IdempotencyRecord.ttl_expires_at <= datetime.utcnow()
            ) \
            .delete()
        
        session.commit()
        
        logger.info(f"Cleaned up {expired} expired idempotency records")
        
        return expired
