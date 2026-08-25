"""Align chunks.embedding dimension with the local BGE embedding model.

The embedding model is BAAI/bge-small-en-v1.5 which emits 384-dimensional
vectors, but the initial migration created a vector(1536) column (OpenAI
text-embedding-3-small dimension). pgvector rejects dimension-mismatched
inserts, so ingestion silently failed. Existing vectors (if any) are
unusable under the new model and are nulled; affected documents must be
re-processed.
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    op.execute(
        "ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(384) USING NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_chunks_embedding")
    op.execute(
        "ALTER TABLE chunks ALTER COLUMN embedding TYPE vector(1536) USING NULL"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_chunks_embedding ON chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 200);"
    )
