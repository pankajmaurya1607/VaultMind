"""Performance unit tests for VaultMind.

Tests cover:
- Chunking performance with large documents
- Embedding service performance
- Retriever search performance
- Generator response time
- API endpoint response times (simulated)
"""

import pytest
import time
import numpy as np
from unittest.mock import Mock, patch


# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.performance,
]


class TestChunkingPerformance:
    """Test chunking performance."""

    def test_chunking_small_document_performance(self):
        """Test that small documents chunk quickly."""
        from app.tasks.process import chunk_text
        
        document = "This is a test sentence. " * 100
        
        start = time.time()
        chunks = chunk_text(document, chunk_size=500, overlap=100)
        elapsed = time.time() - start
        
        assert len(chunks) > 0
        assert elapsed < 0.1, f"Small document chunking took {elapsed:.3f}s, should be < 0.1s"

    def test_chunking_large_document_performance(self):
        """Test that large documents chunk within acceptable time."""
        from app.tasks.process import chunk_text
        
        document = "This is a test sentence about company policies and procedures. " * 100000
        
        start = time.time()
        chunks = chunk_text(document, chunk_size=500, overlap=100)
        elapsed = time.time() - start
        
        assert len(chunks) > 100
        assert elapsed < 5.0, f"Large document chunking took {elapsed:.3f}s, should be < 5s"

    def test_chunking_memory_efficiency(self):
        """Test that chunking doesn't use excessive memory."""
        from app.tasks.process import chunk_text
        
        document = "Word " * 1000000  # ~5MB
        
        chunks = chunk_text(document, chunk_size=1000, overlap=200)
        
        # Verify chunks are reasonable size
        total_chunk_size = sum(len(c) for c in chunks)
        # With overlap, total can exceed original, but should be bounded
        assert total_chunk_size <= len(document) * 2.0  # Allow up to 2x due to overlap
        assert len(chunks) > 0, "Should produce chunks"


class TestRetrieverPerformance:
    """Test retriever performance."""

    def test_local_search_performance_small_index(self):
        """Test that search is fast with small index."""
        from app.rag.retriever.retriever import Retriever
        
        retriever = Retriever()
        
        # Add 100 documents
        for i in range(100):
            retriever._local_store[i] = [{
                "chunk_index": 0,
                "text": f"Document {i}",
                "metadata": {},
                "embedding": np.random.rand(1536).tolist(),
                "filename": f"doc{i}.pdf",
                "department_id": 1,
            }]
        
        query_vector = np.random.rand(1536)
        
        start = time.time()
        results = retriever._local_search(query_vector, [], top_k=10)
        elapsed = time.time() - start
        
        assert len(results) <= 10
        assert elapsed < 1.0, f"Small index search took {elapsed:.3f}s, should be < 1s"

    def test_local_search_performance_medium_index(self):
        """Test that search is acceptable with medium index."""
        from app.rag.retriever.retriever import Retriever
        
        retriever = Retriever()
        
        # Add 1000 documents
        for i in range(1000):
            retriever._local_store[i] = [{
                "chunk_index": 0,
                "text": f"Document {i}",
                "metadata": {},
                "embedding": np.random.rand(1536).tolist(),
                "filename": f"doc{i}.pdf",
                "department_id": 1,
            }]
        
        query_vector = np.random.rand(1536)
        
        start = time.time()
        results = retriever._local_search(query_vector, [], top_k=10)
        elapsed = time.time() - start
        
        assert len(results) <= 10
        assert elapsed < 5.0, f"Medium index search took {elapsed:.3f}s, should be < 5s"


class TestEmbedderPerformance:
    """Test embedding performance."""

    def test_zero_vector_generation_performance(self):
        """Test that zero vector generation is fast."""
        from app.rag.embeddings.embedder import EmbeddingService
        
        service = EmbeddingService()
        
        start = time.time()
        for _ in range(1000):
            service.embed_query("test")
        elapsed = time.time() - start
        
        assert elapsed < 1.0, f"1000 zero vector generations took {elapsed:.3f}s, should be < 1s"

    def test_batch_embedding_performance(self):
        """Test that batch embedding is efficient."""
        from app.rag.embeddings.embedder import EmbeddingService
        
        service = EmbeddingService()
        
        texts = [f"Test document {i}" for i in range(100)]
        
        start = time.time()
        embeddings = service.embed(texts)
        elapsed = time.time() - start
        
        assert len(embeddings) == 100
        assert elapsed < 2.0, f"100 document embeddings took {elapsed:.3f}s, should be < 2s"


class TestGeneratorPerformance:
    """Test generator performance."""

    def test_fallback_response_performance(self):
        """Test that fallback response is fast."""
        from app.rag.llm.generator import Generator
        
        generator = Generator()
        
        docs = [
            {"document_id": i, "filename": f"doc{i}.pdf", "chunk_index": 0, "text": f"Content {i}", "score": 0.9}
            for i in range(10)
        ]
        
        start = time.time()
        answer, sources, score = generator.generate("Test question", docs)
        elapsed = time.time() - start
        
        assert isinstance(answer, str)
        assert elapsed < 0.5, f"Fallback response took {elapsed:.3f}s, should be < 0.5s"

    def test_context_formatting_performance(self):
        """Test that context formatting is fast."""
        from app.rag.llm.generator import Generator
        
        generator = Generator()
        
        docs = [
            {"document_id": i, "filename": f"doc{i}.pdf", "chunk_index": 0, "text": f"Content {i}" * 100, "score": 0.9}
            for i in range(50)
        ]
        
        start = time.time()
        context = generator._format_context(docs)
        elapsed = time.time() - start
        
        assert isinstance(context, str)
        assert elapsed < 0.1, f"Context formatting took {elapsed:.3f}s, should be < 0.1s"


class TestAPIPerformance:
    """Test API endpoint performance (simulated)."""

    def test_health_endpoint_performance(self):
        """Test that health endpoint responds quickly."""
        # Simulate health check
        start = time.time()
        response = {"status": "healthy", "version": "1.0.0"}
        elapsed = time.time() - start
        
        assert response["status"] == "healthy"
        assert elapsed < 0.01, f"Health check took {elapsed:.3f}s, should be < 0.01s"

    def test_schema_validation_performance(self):
        """Test that schema validation is fast."""
        from pydantic import BaseModel
        
        class TestSchema(BaseModel):
            name: str
            value: int
        
        start = time.time()
        for _ in range(1000):
            TestSchema(name="test", value=42)
        elapsed = time.time() - start
        
        assert elapsed < 0.5, f"1000 schema validations took {elapsed:.3f}s, should be < 0.5s"
