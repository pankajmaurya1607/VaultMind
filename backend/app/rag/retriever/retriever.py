import asyncio
import logging
import os
from typing import List, Optional

from app.config.settings import settings
from app.db.sync_engine import get_sync_engine
from app.rag.embeddings.embedder import embedding_service

logger = logging.getLogger("eka")

try:
    from sqlalchemy import text as sa_text
    from sqlalchemy.ext.asyncio import AsyncSession

    _pgvector_available = True
except Exception:  # pragma: no cover - optional dependency path
    _pgvector_available = False
    sa_text = None
    AsyncSession = None


def _build_vector_str(vector: List[float]) -> str:
    return "[" + ",".join(str(v) for v in vector) + "]"


_SEARCH_SQL_TEMPLATE = """
    SELECT c.id, c.text, c.metadata, c.chunk_index, c.document_id,
           1 - (c.embedding <=> CAST(:vec AS vector)) as score,
           d.filename as original_filename
    FROM chunks c
    JOIN documents d ON d.id = c.document_id
    WHERE c.embedding IS NOT NULL
      AND 1 - (c.embedding <=> CAST(:vec AS vector)) >= :threshold
      {dept_filter}
    ORDER BY score DESC
    LIMIT :top_k
"""


def _build_search_query(department_ids: List[int]):
    """Parameterized similarity search. All values are bound - never interpolated."""
    if department_ids:
        placeholders = ", ".join(f":d{i}" for i in range(len(department_ids)))
        dept_filter = f"AND d.department_id IN ({placeholders})"
    else:
        dept_filter = ""
        department_ids = []
    sql = sa_text(_SEARCH_SQL_TEMPLATE.format(dept_filter=dept_filter))
    return sql


def _search_params(vector_str: str, department_ids: List[int], top_k: int) -> dict:
    params = {"vec": vector_str, "threshold": settings.SIMILARITY_THRESHOLD, "top_k": top_k}
    for i, dept_id in enumerate(department_ids or []):
        params[f"d{i}"] = dept_id
    return params


def _rows_to_results(rows) -> List[dict]:
    import math

    results = []
    for row in rows:
        score = float(row.score) if row.score is not None else 0.0
        # PGVector returns NaN for zero-vector cosine (host testing with zero embeddings)
        if math.isnan(score) or math.isinf(score):
            score = 0.0
        results.append(
            {
                "document_id": row.document_id,
                "filename": row.original_filename,
                "chunk_index": row.chunk_index,
                "text": row.text,
                "metadata": row.metadata,
                "score": score,
            }
        )
    return results


class Retriever:
    def __init__(self):
        self.vector_store_dir = "vector_store"
        os.makedirs(self.vector_store_dir, exist_ok=True)

    async def search(
        self,
        query: str,
        department_ids: List[int],
        top_k: int = None,
        db: Optional[AsyncSession] = None,
    ) -> List[dict]:
        k = top_k or settings.TOP_K
        # SentenceTransformer.encode is CPU-bound sync code - offload it.
        query_vector = await asyncio.to_thread(embedding_service.embed_query, query)

        if db is not None:
            return await self._async_pgvector_search(db, query_vector, department_ids, k)
        return self._sync_pgvector_search(query_vector, department_ids, k)

    def _sync_pgvector_search(self, query_vector: List[float], department_ids: List[int], top_k: int) -> List[dict]:
        vector_str = _build_vector_str(query_vector)
        sql = _build_search_query(department_ids)

        with get_sync_engine().connect() as conn:
            rows = conn.execute(sql, _search_params(vector_str, department_ids, top_k)).fetchall()

        return _rows_to_results(rows)

    async def _async_pgvector_search(
        self,
        db: AsyncSession,
        query_vector: List[float],
        department_ids: List[int],
        top_k: int,
    ) -> List[dict]:
        vector_str = _build_vector_str(query_vector)
        sql = _build_search_query(department_ids)
        result = await db.execute(sql, _search_params(vector_str, department_ids, top_k))
        rows = result.fetchall()
        return _rows_to_results(rows)

    def store_chunks(self, document_id: int, chunks: List[dict], filename: str, department_id: int):
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed(texts)

        # Directly persist to PGVector - raises on failure so Celery marks FAILED
        self._pgvector_store(document_id, chunks, embeddings, filename, department_id)

    def evict_document(self, document_id: int):
        """No-op in minimal mode: PGVector is source of truth, local cache removed."""
        pass

    def _pgvector_store(
        self, document_id: int, chunks: List[dict], embeddings: List[List[float]], filename: str, department_id: int
    ):
        sql = sa_text("UPDATE chunks SET embedding = CAST(:vec AS vector) WHERE id = :chunk_id")
        with get_sync_engine().connect() as conn:
            for i, chunk in enumerate(chunks):
                conn.execute(sql, {"vec": _build_vector_str(embeddings[i]), "chunk_id": chunk["chunk_id"]})
            conn.commit()


retriever = Retriever()
