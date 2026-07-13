import os
import json
import logging
from typing import List
import numpy as np
from app.config.settings import settings
from app.rag.embeddings.embedder import embedding_service

logger = logging.getLogger("eka")

try:
    import pgvector
    from sqlalchemy import text
    _pgvector_available = True
except Exception:
    _pgvector_available = False


class Retriever:
    def __init__(self):
        self.vector_store_dir = "vector_store"
        os.makedirs(self.vector_store_dir, exist_ok=True)
        self._local_store = {}

    def search(self, query: str, department_ids: List[int], top_k: int = None) -> List[dict]:
        k = top_k or settings.TOP_K
        query_vector = embedding_service.embed_query(query)

        if _pgvector_available:
            try:
                return self._pgvector_search(query_vector, department_ids, k)
            except Exception as e:
                logger.warning(f"PGVector search failed, falling back to local: {e}")

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
                    results.append({
                        "document_id": doc_id,
                        "filename": chunk.get("filename", ""),
                        "chunk_index": chunk["chunk_index"],
                        "text": chunk["text"],
                        "metadata": chunk.get("metadata", {}),
                        "score": score,
                    })

        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _pgvector_search(self, query_vector: List[float], department_ids: List[int], top_k: int) -> List[dict]:
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.DATABASE_URL_SYNC)
        vector_str = "[" + ",".join(str(v) for v in query_vector) + "]"

        dept_filter = ""
        if department_ids:
            ids = ",".join(str(d) for d in department_ids)
            dept_filter = f"AND d.department_id IN ({ids})"

        sql = text(f"""
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

        with engine.connect() as conn:
            rows = conn.execute(sql).fetchall()

        results = []
        for row in rows:
            score = float(row.score) if row.score is not None else 0.0
            results.append({
                "document_id": row.document_id,
                "filename": row.original_filename,
                "chunk_index": row.chunk_index,
                "text": row.text,
                "metadata": row.metadata,
                "score": score,
            })
        return results

    def store_chunks(self, document_id: int, chunks: List[dict], filename: str, department_id: int):
        texts = [c["text"] for c in chunks]
        embeddings = embedding_service.embed(texts)

        for i, chunk in enumerate(chunks):
            doc_id = document_id
            if doc_id not in self._local_store:
                self._local_store[doc_id] = []
            self._local_store[doc_id].append({
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "metadata": {**chunk["metadata"], "department_id": department_id},
                "embedding": embeddings[i],
                "filename": filename,
                "department_id": department_id,
            })

        if _pgvector_available:
            try:
                self._pgvector_store(document_id, chunks, embeddings, filename, department_id)
            except Exception as e:
                logger.warning(f"PGVector store failed: {e}")

    def _pgvector_store(self, document_id: int, chunks: List[dict], embeddings: List[List[float]], filename: str, department_id: int):
        from sqlalchemy import create_engine, text
        engine = create_engine(settings.DATABASE_URL_SYNC)
        with engine.connect() as conn:
            for i, chunk in enumerate(chunks):
                vec_str = "[" + ",".join(str(v) for v in embeddings[i]) + "]"
                sql = text(f"""
                    UPDATE chunks SET embedding = '{vec_str}'::vector
                    WHERE id = {chunk['chunk_id']}
                """)
                conn.execute(sql)
            conn.commit()


retriever = Retriever()
