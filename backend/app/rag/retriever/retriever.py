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

_GUEST_SEARCH_SQL = """
    SELECT c.id, c.text, c.metadata, c.chunk_index, c.document_id,
           1 - (c.embedding <=> CAST(:vec AS vector)) as score,
           d.original_filename as original_filename
    FROM guest_chunks c
    JOIN guest_documents d ON d.id = c.document_id
    WHERE c.embedding IS NOT NULL
      AND d.guest_token = :guest_token
      AND d.expires_at > NOW()
      AND 1 - (c.embedding <=> CAST(:vec AS vector)) >= :threshold
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
        # Embedding encode is CPU-bound sync code - offload it.
        query_vector = await asyncio.to_thread(embedding_service.embed_query, query)

        # Fallback for zero vectors (local without torch)
        if self._is_zero_vector(query_vector):
            return await self._keyword_search(query, department_ids, k, db)

        if db is not None:
            results = await self._async_pgvector_search(db, query_vector, department_ids, k)
            if not results:
                return await self._keyword_search(query, department_ids, k, db)
            return results
        results = self._sync_pgvector_search(query_vector, department_ids, k)
        if not results:
            return await self._keyword_search(query, department_ids, k, db)
        return results

    async def _keyword_search(self, query: str, department_ids: List[int], top_k: int, db: Optional[AsyncSession] = None) -> List[dict]:
        words = [w for w in query.lower().split() if len(w) > 2]
        if not words:
            words = [query.lower()]
        like_clauses = " OR ".join([f"c.text ILIKE :w{i}" for i in range(len(words))])
        dept_filter = ""
        params: dict = {"top_k": top_k}
        for i, w in enumerate(words):
            params[f"w{i}"] = f"%{w}%"
        if department_ids:
            placeholders = ", ".join(f":d{i}" for i in range(len(department_ids)))
            dept_filter = f"AND d.department_id IN ({placeholders})"
            for i, dept_id in enumerate(department_ids):
                params[f"d{i}"] = dept_id
        sql_str = f"""
            SELECT c.id, c.text, c.metadata, c.chunk_index, c.document_id,
                   0.85 as score,
                   d.filename as original_filename
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.embedding IS NOT NULL
              AND ({like_clauses})
              {dept_filter}
            ORDER BY c.chunk_index
            LIMIT :top_k
        """
        sql = sa_text(sql_str)
        if db is not None:
            result = await db.execute(sql, params)
            rows = result.fetchall()
        else:
            with get_sync_engine().connect() as conn:
                rows = conn.execute(sql, params).fetchall()
        return _rows_to_results(rows)

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

    def store_guest_chunks(self, document_id: int, chunks: List[dict]):
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed(texts)
        sql = sa_text("UPDATE guest_chunks SET embedding = CAST(:vec AS vector) WHERE id = :chunk_id")
        with get_sync_engine().connect() as conn:
            for i, chunk in enumerate(chunks):
                conn.execute(sql, {"vec": _build_vector_str(embeddings[i]), "chunk_id": chunk["chunk_id"]})
            conn.commit()

    def _is_zero_vector(self, vec: List[float]) -> bool:
        return all(v == 0.0 for v in vec) or embedding_service._local_model is None

    async def search_guest(self, query: str, guest_token: str, top_k: int = None, db: Optional[AsyncSession] = None) -> List[dict]:
        k = top_k or settings.TOP_K
        query_vector = await asyncio.to_thread(embedding_service.embed_query, query)
        # Fallback to keyword search when embeddings are zero vectors (local dev without torch)
        if self._is_zero_vector(query_vector):
            return await self._keyword_search_guest(query, guest_token, k, db)

        vector_str = _build_vector_str(query_vector)
        sql = sa_text(_GUEST_SEARCH_SQL)
        params = {"vec": vector_str, "guest_token": guest_token, "threshold": settings.SIMILARITY_THRESHOLD, "top_k": k}
        if db is not None:
            result = await db.execute(sql, params)
            rows = result.fetchall()
        else:
            with get_sync_engine().connect() as conn:
                rows = conn.execute(sql, params).fetchall()
        results = _rows_to_results(rows)
        # If vector search returns empty (e.g. threshold too high), fallback to keyword
        if not results:
            return await self._keyword_search_guest(query, guest_token, k, db)
        return results

    async def _keyword_search_guest(self, query: str, guest_token: str, top_k: int, db: Optional[AsyncSession] = None) -> List[dict]:
        # Simple ILIKE keyword search - works without embeddings, good for Try with zero vectors
        # Split query into words and search for any word
        words = [w for w in query.lower().split() if len(w) > 2]
        if not words:
            words = [query.lower()]
        # Build OR conditions
        like_clauses = " OR ".join([f"c.text ILIKE :w{i}" for i in range(len(words))])
        sql_str = f"""
            SELECT c.id, c.text, c.metadata, c.chunk_index, c.document_id,
                   0.85 as score,
                   d.original_filename as original_filename
            FROM guest_chunks c
            JOIN guest_documents d ON d.id = c.document_id
            WHERE d.guest_token = :guest_token
              AND d.expires_at > NOW()
              AND ({like_clauses})
            ORDER BY c.chunk_index
            LIMIT :top_k
        """
        sql = sa_text(sql_str)
        params: dict = {"guest_token": guest_token, "top_k": top_k}
        for i, w in enumerate(words):
            params[f"w{i}"] = f"%{w}%"
        if db is not None:
            result = await db.execute(sql, params)
            rows = result.fetchall()
        else:
            with get_sync_engine().connect() as conn:
                rows = conn.execute(sql, params).fetchall()
        # If still no results, return first chunks (so LLM at least sees something)
        if not rows:
            fallback_sql = sa_text("""
                SELECT c.id, c.text, c.metadata, c.chunk_index, c.document_id,
                       0.5 as score,
                       d.original_filename as original_filename
                FROM guest_chunks c
                JOIN guest_documents d ON d.id = c.document_id
                WHERE d.guest_token = :guest_token AND d.expires_at > NOW()
                ORDER BY c.chunk_index LIMIT :top_k
            """)
            if db is not None:
                result = await db.execute(fallback_sql, {"guest_token": guest_token, "top_k": top_k})
                rows = result.fetchall()
            else:
                with get_sync_engine().connect() as conn:
                    rows = conn.execute(fallback_sql, {"guest_token": guest_token, "top_k": top_k}).fetchall()
        return _rows_to_results(rows)

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
