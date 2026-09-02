"""guest quick-try: isolated upload <1MB with 10m TTL

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-02
"""

from typing import Sequence, Union

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "guest_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("guest_token", sa.String(length=64), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("original_filename", sa.String(length=500), nullable=False),
        sa.Column("file_path", sa.String(length=1000), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guest_documents_guest_token", "guest_documents", ["guest_token"])
    op.create_index("ix_guest_documents_expires_at", "guest_documents", ["expires_at"])

    op.create_table(
        "guest_chunks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("document_id", sa.Integer(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.Column("embedding", Vector(384), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["document_id"], ["guest_documents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_guest_chunks_document_id", "guest_chunks", ["document_id"])
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_guest_chunks_embedding ON guest_chunks USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 200);"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_guest_chunks_embedding")
    op.drop_index("ix_guest_chunks_document_id", table_name="guest_chunks")
    op.drop_table("guest_chunks")
    op.drop_index("ix_guest_documents_expires_at", table_name="guest_documents")
    op.drop_index("ix_guest_documents_guest_token", table_name="guest_documents")
    op.drop_table("guest_documents")
