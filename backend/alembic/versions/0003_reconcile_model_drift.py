"""Reconcile migration drift between 0001 and the SQLAlchemy models.

- audit_logs.details: JSON -> TEXT (model uses Text; code stores strings)
- messages.session_id: add ON DELETE CASCADE (model declares it; deleting a
  chat session previously orphaned its messages)
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE audit_logs ALTER COLUMN details TYPE TEXT USING details::text")
    op.execute(
        "ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_session_id_fkey"
    )
    op.execute(
        "ALTER TABLE messages ADD CONSTRAINT messages_session_id_fkey "
        "FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE"
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_session_id_fkey"
    )
    op.execute(
        "ALTER TABLE messages ADD CONSTRAINT messages_session_id_fkey "
        "FOREIGN KEY (session_id) REFERENCES chat_sessions(id)"
    )
    op.execute("ALTER TABLE audit_logs ALTER COLUMN details TYPE JSON USING NULL")
