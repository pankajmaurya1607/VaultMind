import logging

from celery import shared_task

from app.models.document import Document, DocumentStatus

logger = logging.getLogger("eka")


@shared_task(bind=True, max_retries=3)
def check_failed_documents(self):
    """Periodically check for documents that failed processing and log alerts."""
    from sqlalchemy.orm import Session

    from app.db.sync_engine import get_sync_engine

    engine = get_sync_engine()
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
