from celery import Celery

from app.config.settings import settings

celery_app = Celery(
    "eka",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.process"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,
    task_time_limit=600,
    task_routes={
        "app.tasks.process.process_document_task": {"queue": "document_processing"},
    },
)

if __name__ == "__main__":
    celery_app.start()
