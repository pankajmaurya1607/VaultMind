import logging
import os
from typing import List, Optional

import numpy as np

from app.config.settings import settings
from app.rag.embeddings.embedder import embedding_service

logger = logging.getLogger("eka")

try:
    from sqlalchemy import create_engine
    from sqlalchemy import text as sa_text
    from sqlalchemy.ext.asyncio import AsyncSession

    _pgvector_available = True
except Exception:
    _pgvector_available = False
    AsyncSession = None


def _build_vector_str(vector: List[float]) -> str:
    return "[" + ",".join(str(v) for v in vector) + "]"


def _build_search_query(vector_str: str, department_ids: List[int], top_k: int):
    dept_filter = ""
    if department_ids:
        ids = ",".join(str(d) for d in department_ids)
        dept_filter = f"AND d.department_id IN ({ids})"
    return sa_text(f"""
        SELECT c.id, c.text, c.metadata, c.chunk_index, c.document_id,
               1 - (c.embedding <=> '{vector_str}'::vector) as score,
               d.filename as original_filename
        FROM chunks c
        JOIN documents d ON d.id = c.document_id
        WHERE c.embedding IS NOT NULL
          AND 1 - (c.embedding <=> '{vector_str}'::vector) >= {settings.SIMILARITY_THRESHOLD}
        {dept_filter}
        ORDER BY score DESC
        LIMIT {top_k}
    """)


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
        query_vector = embedding_service.embed_query(query)

        if _pgvector_available:
            if db is not None:
                try:
                    return await self._async_pgvector_search(db, query_vector, department_ids, k)
                except Exception as e:
                    logger.warning(f"Async PGVector search failed: {e}")
            else:
                try:
                    return self._sync_pgvector_search(query_vector, department_ids, k)
                except Exception as e:
                    logger.warning(f"Sync PGVector search failed, falling back to local: {e}")

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
        engine = create_engine(settings.DATABASE_URL_SYNC)
        vector_str = _build_vector_str(query_vector)
        sql = _build_search_query(vector_str, department_ids, top_k)

        with engine.connect() as conn:
            rows = conn.execute(sql).fetchall()

        return _rows_to_results(rows)

    async def _async_pgvector_search(
        self,
        db: AsyncSession,
        query_vector: List[float],
        department_ids: List[int],
        top_k: int,
    ) -> List[dict]:
        vector_str = _build_vector_str(query_vector)
        sql = _build_search_query(vector_str, department_ids, top_k)
        result = await db.execute(sql)
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
            try:
                self._pgvector_store(document_id, chunks, embeddings, filename, department_id)
            except Exception as e:
                logger.warning(f"PGVector store failed: {e}")

    def _pgvector_store(
        self, document_id: int, chunks: List[dict], embeddings: List[List[float]], filename: str, department_id: int
    ):
        engine = create_engine(settings.DATABASE_URL_SYNC)
        with engine.connect() as conn:
            for i, chunk in enumerate(chunks):
                vec_str = _build_vector_str(embeddings[i])
                sql = sa_text(f"""
                    UPDATE chunks SET embedding = '{vec_str}'::vector
                    WHERE id = {chunk["chunk_id"]}
                """)
                conn.execute(sql)
            conn.commit()


retriever = Retriever()
