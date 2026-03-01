"""Notification service with async queue management."""

from datetime import datetime
from uuid import UUID
from typing import List
from sqlalchemy.orm import Session

from src.db.models import Notification, NotificationStatus
from src.utils.logger import logger


class NotificationService:
    """Manages notification queue and delivery."""
    
    @staticmethod
    def queue_notification(
        session: Session,
        appointment_id: UUID,
        event_type: str,
        recipient_email: str,
        payload: dict
    ) -> Notification:
        """Queue a notification for async processing."""
        
        notification = Notification(
            appointment_id=appointment_id,
            event_type=event_type,
            status=NotificationStatus.QUEUED,
            recipient_email=recipient_email,
            payload=payload
        )
        session.add(notification)
        session.commit()
        
        logger.info(
            f"Notification queued: {event_type} to {recipient_email}"
        )
        
        return notification
    
    @staticmethod
    def process_queued_notifications(session: Session) -> int:
        """
        Process all QUEUED notifications.
        
        Background worker job that runs periodically.
        For this demo: logs to console (simulates notification sending).
        
        In production:
        - Call real SMTP (Sendgrid, SES, etc.)
        - Integrate with APM for monitoring
        - Update sent_at timestamp
        
        Args:
            session: SQLAlchemy session
        
        Returns:
            Number of notifications processed
        """
        
        queued = session.query(Notification) \
            .filter_by(status=NotificationStatus.QUEUED) \
            .all()
        
        processed = 0
        
        for notification in queued:
            try:
                # Simulate sending notification
                _send_notification_simulated(notification)
                
                # Mark as sent
                notification.status = NotificationStatus.SENT
                notification.sent_at = datetime.utcnow()
                session.commit()
                
                processed += 1
                
                logger.info(
                    f"Notification sent: {notification.event_type} "
                    f"to {notification.recipient_email}"
                )
                
            except Exception as e:
                # Mark as failed, increment retry count
                notification.status = NotificationStatus.FAILED
                notification.error_details = str(e)
                notification.retry_count += 1
                session.commit()
                
                logger.error(
                    f"Failed to send notification {notification.id}: {e}"
                )
        
        return processed
    
    @staticmethod
    def retry_failed_notifications(
        session: Session,
        max_retries: int = 3
    ) -> int:
        """
        Retry FAILED notifications that haven't exceeded max retries.
        
        Uses exponential backoff:
        Delay = 2^retry_count seconds
        """
        
        failed = session.query(Notification) \
            .filter(
                Notification.status == NotificationStatus.FAILED,
                Notification.retry_count < max_retries
            ) \
            .all()
        
        for notification in failed:
            # Reset to QUEUED for retry
            notification.status = NotificationStatus.QUEUED
            notification.error_details = None
        
        session.commit()
        
        logger.info(f"Retrying {len(failed)} failed notifications")
        
        return len(failed)


def _send_notification_simulated(notification: Notification) -> None:
    """
    Simulate sending a notification.
    
    In production, this would:
    - Call SMTP server
    - Send SMS
    - Call webhook
    - etc.
    
    For this demo, we just log it.
    """
    
    logger.info(f"[NOTIFICATION] {notification.event_type}")
    logger.info(f"  To: {notification.recipient_email}")
    logger.info(f"  Data: {notification.payload}")
