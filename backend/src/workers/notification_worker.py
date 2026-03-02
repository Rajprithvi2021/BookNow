"""Background worker for processing notifications."""

import asyncio
from datetime import datetime
import logging
from sqlalchemy.orm import Session

from src.db.connection import SessionLocal
from src.services.notification_service import NotificationService
from src.utils.logger import logger


class NotificationWorker:
    """Background worker for processing queued notifications."""
    
    _task = None
    _stop_event = None
    
    @classmethod
    async def start(cls, interval_seconds: int = 5):
        """
        Start the notification worker background task.
        
        Args:
            interval_seconds: How often to check for queued notifications (default 5 seconds)
        """
        cls._stop_event = asyncio.Event()
        cls._task = asyncio.create_task(cls._run(interval_seconds))
        logger.info(f"Notification worker started (interval: {interval_seconds}s)")
    
    @classmethod
    async def stop(cls):
        """Stop the notification worker."""
        if cls._stop_event:
            cls._stop_event.set()
        if cls._task:
            try:
                await cls._task
            except asyncio.CancelledError:
                pass
        logger.info("Notification worker stopped")
    
    @classmethod
    async def _run(cls, interval_seconds: int):
        """
        Main worker loop.
        
        Periodically checks for queued notifications and processes them.
        """
        try:
            while not cls._stop_event.is_set():
                try:
                    # Get a fresh database session
                    session: Session = SessionLocal()
                    
                    # Process all queued notifications
                    processed = NotificationService.process_queued_notifications(session)
                    
                    if processed > 0:
                        logger.info(f"Processed {processed} notifications")
                    
                    session.close()
                    
                except Exception as e:
                    logger.error(f"Error in notification worker: {e}", exc_info=True)
                
                # Wait before next check (or until stop event)
                try:
                    await asyncio.wait_for(
                        cls._stop_event.wait(),
                        timeout=interval_seconds
                    )
                except asyncio.TimeoutError:
                    # This is expected - timeout means continue the loop
                    pass
                    
        except Exception as e:
            logger.error(f"Fatal error in notification worker: {e}", exc_info=True)
            raise
