import logging

from celery import shared_task
from sqlalchemy import func

from app.config.settings import settings
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
    """Refresh Prometheus gauges that need DB/Redis state.

    Runs every minute via beat so scraped /metrics values stay current even
    when the API process itself hasn't served relevant requests recently.
    """
    try:
        import redis as redis_lib
        from sqlalchemy.orm import Session

        from app.db.sync_engine import get_sync_engine
        from app.monitoring.metrics import DOCUMENTS_TOTAL, QUEUE_SIZE

        engine = get_sync_engine()
        counts: dict = {}
        with Session(engine) as db:
            rows = db.query(Document.status, func.count()).group_by(Document.status).all()
            counts = {status.value if hasattr(status, "value") else status: n for status, n in rows}

        for status_value in ("pending", "processing", "ready", "failed"):
            DOCUMENTS_TOTAL.labels(status=status_value).set(counts.get(status_value, 0))

        queue_depth = 0
        try:
            client = redis_lib.Redis.from_url(settings.REDIS_URL)
            queue_depth = sum(client.llen(q) for q in ("document_processing", "celery"))
            client.close()
        except Exception as exc:
            logger.debug("Queue depth unavailable: %s", exc)
        QUEUE_SIZE.set(queue_depth)

        logger.debug("Metrics gauges updated")
    except Exception as exc:
        logger.error(f"Metrics update failed: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def prune_blacklisted_tokens(self):
    """Daily cleanup: drop revoked-token rows older than the refresh lifetime."""
    from sqlalchemy.orm import Session

    from app.config.settings import settings
    from app.db.sync_engine import get_sync_engine
    from app.repositories.auth import AuthRepository

    engine = get_sync_engine()
    try:
        with Session(engine) as db:
            pruned = AuthRepository(db).prune_expired(settings.REFRESH_TOKEN_EXPIRE_DAYS)
            db.commit()
            if pruned:
                logger.info(f"Pruned {pruned} expired blacklisted tokens")
    except Exception as exc:
        logger.error(f"Failed to prune blacklisted tokens: {exc}")
        raise self.retry(exc=exc, countdown=300)
