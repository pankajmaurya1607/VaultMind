"""Unit tests for RAG pipeline integration.

These tests verify the complete RAG pipeline works correctly.
They test document processing, chunking, embedding, storage, and retrieval.

All tests use pre-computed vectors to avoid external API calls.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import numpy as np


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.rag,
]


def _make_vector(dim=1536, seed=0):
    rng = np.random.RandomState(seed)
    v = rng.rand(dim).astype(np.float32)
    v = v / (np.linalg.norm(v) + 1e-10)
    return v


def _make_doc(doc_id, chunk_index, text, seed, department_id=1):
    vec = _make_vector(seed=seed)
    return {
        "chunk_index": chunk_index,
        "text": text,
        "metadata": {"source": f"doc{doc_id}.pdf", "department_id": department_id},
        "embedding": vec.tolist(),
        "filename": f"doc{doc_id}.pdf",
        "department_id": department_id,
    }


class TestDocumentProcessingPipeline:
    """Test document processing pipeline integration."""

    def test_chunking_to_embedding_flow(self):
        """Test that chunking produces valid chunks."""
        from app.tasks.process import chunk_text

        document = "This is a test document. " * 100

        chunks = chunk_text(document, chunk_size=500, overlap=100)
        assert len(chunks) > 0, "Should produce chunks"
        assert all(isinstance(c, str) for c in chunks), "Each chunk should be a string"
        assert all(len(c) > 0 for c in chunks), "Each chunk should be non-empty"

    def test_embedding_to_storage_flow(self):
        """Test that embeddings can be stored in local store."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()

        chunks = [
            {"chunk_index": 0, "text": "Test chunk 1", "metadata": {"source": "test1.pdf"}},
            {"chunk_index": 1, "text": "Test chunk 2", "metadata": {"source": "test2.pdf"}},
        ]

        retriever.store_chunks(document_id=1, chunks=chunks, filename="test.pdf", department_id=1)

        assert 1 in retriever._local_store, "Should store chunks in local store"
        assert len(retriever._local_store[1]) == 2, "Should store 2 chunks"

    def test_retrieval_after_storage(self):
        """Test that retrieval works after storage with known vectors."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()

        retriever._local_store[1] = [_make_doc(1, 0, "Python programming", seed=1)]

        query_vector = _make_vector(seed=1)
        results = retriever._local_search(query_vector, [], top_k=5)

        assert len(results) > 0, "Should return results"
        assert results[0]["text"] == "Python programming"

    def test_department_filtering_after_storage(self):
        """Test that department filtering works after storage."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()

        retriever._local_store[1] = [_make_doc(1, 0, "HR policy", seed=10, department_id=1)]
        retriever._local_store[2] = [_make_doc(2, 0, "Engineering docs", seed=20, department_id=2)]

        query_vector = _make_vector(seed=5)
        results = retriever._local_search(query_vector, [1], top_k=10)

        for result in results:
            assert result["metadata"]["department_id"] == 1


class TestQueryProcessingPipeline:
    """Test query processing pipeline integration."""

    def test_local_search_returns_scored_results(self):
        """Test that local search returns properly scored results."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()

        retriever._local_store[1] = [
            _make_doc(1, 0, "Company remote work policy", seed=1),
            _make_doc(1, 1, "Vacation days policy", seed=2),
        ]
        retriever._local_store[2] = [
            _make_doc(2, 0, "Engineering architecture", seed=3),
        ]

        query_vector = _make_vector(seed=1)
        results = retriever._local_search(query_vector, [], top_k=3)

        assert len(results) <= 3
        assert all("score" in r for r in results)
        assert all("text" in r for r in results)
        assert all("filename" in r for r in results)

    def test_relevance_ranking(self):
        """Test that results are ranked by relevance score."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()

        query = _make_vector(seed=42)

        exact_match = query.copy()
        partial_match = _make_vector(seed=99)

        retriever._local_store[1] = [{
            "chunk_index": 0,
            "text": "Exact match",
            "metadata": {"source": "a.pdf"},
            "embedding": exact_match.tolist(),
            "filename": "a.pdf",
            "department_id": 1,
        }]
        retriever._local_store[2] = [{
            "chunk_index": 0,
            "text": "Partial match",
            "metadata": {"source": "b.pdf"},
            "embedding": partial_match.tolist(),
            "filename": "b.pdf",
            "department_id": 1,
        }]

        results = retriever._local_search(query, [], top_k=2)

        assert len(results) >= 1
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True), "Results should be sorted by score desc"

    def test_large_document_chunking_and_storage(self):
        """Test processing of large documents through chunking and storage."""
        from app.tasks.process import chunk_text
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()

        large_doc = "This is a test sentence about company policies. " * 10000

        chunks = chunk_text(large_doc, chunk_size=500, overlap=100)
        assert len(chunks) > 10, "Large document should produce many chunks"

        chunk_dicts = [
            {"chunk_index": i, "text": chunk, "metadata": {"source": "large_doc.pdf"}}
            for i, chunk in enumerate(chunks)
        ]
        retriever.store_chunks(document_id=1, chunks=chunk_dicts, filename="large_doc.pdf", department_id=1)

        assert len(retriever._local_store[1]) == len(chunks), "Should store all chunks"

    def test_multiple_document_retrieval(self):
        """Test retrieval across multiple documents."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()

        for doc_id in range(1, 6):
            retriever._local_store[doc_id] = [_make_doc(doc_id, 0, f"Document {doc_id} content", seed=doc_id)]

        query_vector = _make_vector(seed=3)
        results = retriever._local_search(query_vector, [], top_k=3)

        assert len(results) <= 3, "Should return at most top_k results"
        assert len(results) > 0, "Should return some results"

    def test_threshold_filters_irrelevant(self):
        """Test that similarity threshold filters irrelevant results."""
        from app.rag.retriever.retriever import Retriever
        from app.config.settings import settings

        retriever = Retriever()

        orthogonal = np.zeros(1536, dtype=np.float32)
        orthogonal[768] = 1.0

        retriever._local_store[1] = [{
            "chunk_index": 0,
            "text": "Completely unrelated document",
            "metadata": {"source": "unrelated.pdf"},
            "embedding": orthogonal.tolist(),
            "filename": "unrelated.pdf",
            "department_id": 1,
        }]

        query = np.zeros(1536, dtype=np.float32)
        query[0] = 1.0

        results = retriever._local_search(query, [], top_k=5)

        for r in results:
            assert r["score"] >= settings.SIMILARITY_THRESHOLD
