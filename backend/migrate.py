"""Database setup entrypoint: pgvector extension + Alembic migrations.

Run before starting the API or workers on a fresh deployment:
    python migrate.py

Equivalent to:
    CREATE EXTENSION IF NOT EXISTS vector;
    alembic upgrade head
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from sqlalchemy import text

from app.db.sync_engine import get_sync_engine


def main() -> int:
    engine = get_sync_engine()
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    print("pgvector extension ready")

    from alembic.config import Config

    from alembic import command

    alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
    command.upgrade(alembic_cfg, "head")
    print("Migrations applied")
    return 0


if __name__ == "__main__":
    sys.exit(main())
