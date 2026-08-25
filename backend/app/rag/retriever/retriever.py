import asyncio
import logging
import os
from typing import List, Optional

import numpy as np

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
    results = []
    for row in rows:
        score = float(row.score) if row.score is not None else 0.0
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
        self._local_store = {}

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

        if _pgvector_available:
            if db is not None:
                return await self._async_pgvector_search(db, query_vector, department_ids, k)
            return self._sync_pgvector_search(query_vector, department_ids, k)

        return self._local_search(query_vector, department_ids, k)

    def _local_search(self, query_vector: List[float], department_ids: List[int], top_k: int) -> List[dict]:
        results = []
        query_np = np.array(query_vector, dtype=np.float32)

        for doc_id, chunks in self._local_store.items():
            for chunk in chunks:
                if department_ids and chunk.get("department_id") not in department_ids:
                    continue
                chunk_vec = np.array(chunk["embedding"], dtype=np.float32)
                denom = np.linalg.norm(query_np) * np.linalg.norm(chunk_vec)
                score = float(np.dot(query_np, chunk_vec) / (denom + 1e-10)) if denom > 0 else 0.0
                if score >= settings.SIMILARITY_THRESHOLD:
                    results.append(
                        {
                            "document_id": doc_id,
                            "filename": chunk.get("filename", ""),
                            "chunk_index": chunk["chunk_index"],
                            "text": chunk["text"],
                            "metadata": chunk.get("metadata", {}),
                            "score": score,
                        }
                    )

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

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

        for i, chunk in enumerate(chunks):
            doc_id = document_id
            if doc_id not in self._local_store:
                self._local_store[doc_id] = []
            self._local_store[doc_id].append(
                {
                    "chunk_index": chunk["chunk_index"],
                    "text": chunk["text"],
                    "metadata": {**chunk["metadata"], "department_id": department_id},
                    "embedding": embeddings[i],
                    "filename": filename,
                    "department_id": department_id,
                }
            )

        if _pgvector_available:
            # Intentionally raises on failure so the Celery task marks the
            # document FAILED instead of silently losing searchability.
            self._pgvector_store(document_id, chunks, embeddings, filename, department_id)

    def evict_document(self, document_id: int):
        """Drop cached local-store entries when a document is deleted."""
        self._local_store.pop(document_id, None)

    def _pgvector_store(
        self, document_id: int, chunks: List[dict], embeddings: List[List[float]], filename: str, department_id: int
    ):
        sql = sa_text("UPDATE chunks SET embedding = CAST(:vec AS vector) WHERE id = :chunk_id")
        with get_sync_engine().connect() as conn:
            for i, chunk in enumerate(chunks):
                conn.execute(sql, {"vec": _build_vector_str(embeddings[i]), "chunk_id": chunk["chunk_id"]})
            conn.commit()


retriever = Retriever()
