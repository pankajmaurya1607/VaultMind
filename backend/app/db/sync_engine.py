from typing import Optional

from app.config.settings import settings

try:
    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine
except Exception:  # pragma: no cover - optional dependency path
    create_engine = None
    Engine = None

_sync_engine: Optional[Engine] = None


def get_sync_engine() -> "Engine":
    """Shared synchronous engine for Celery workers and sync code paths.

    Reuses a single connection pool instead of creating a new engine per operation.
    """
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(settings.DATABASE_URL_SYNC, pool_pre_ping=True)
    return _sync_engine
