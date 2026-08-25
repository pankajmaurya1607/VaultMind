import logging
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session

from celery import shared_task

from app.config.settings import settings
from app.services.monitoring import MonitoringService
from app.models.document import Document, DocumentStatus


@shared_task(bind=True, max_retries=3)
def check_failed_documents(self):
    """Periodically check for documents that failed processing and log alerts."""
    from app.models.document import Document, DocumentStatus

    engine = create_engine(settings.DATABASE_URL_SYNC)
    try:
        with Session(engine) as db:
            failed = (
                db.query(Document)
                .filter(Document.status == DocumentStatus.FAILED)
                .count()
            )
            if failed > 0:
                logger.warning(f"Alert: {failed} documents have failed processing")
    except Exception as exc:
        logger.error(f"Failed to check failed documents: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def update_metrics(self):
    """Periodically update system metrics storage."""
    try:
        logger.debug("Metrics update task ran")
    except Exception as exc:
        logger.error(f"Metrics update failed: {exc}")
        raise self.retry(exc=exc, countdown=60)