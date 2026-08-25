"""Unit tests for RAG pipeline edge cases.

These tests verify that the RAG pipeline handles edge cases correctly.
They test empty documents, large documents, fallback scenarios, etc.

Tests follow TDD approach:
- Red: Write failing test
- Green: Make test pass
- Refactor: Improve code while keeping tests green
"""


import numpy as np
import pytest

# Test markers
pytestmark = [
    pytest.mark.unit,
    pytest.mark.rag,
]


class TestChunkingEdgeCases:
    """Test text chunking edge cases."""

    def test_chunking_empty_text(self):
        """Test that chunking handles empty text."""
        from app.tasks.process import chunk_text

        chunks = chunk_text("")
        assert chunks == [], "Empty text should return empty list"

    def test_chunking_whitespace_only(self):
        """Test that chunking handles whitespace-only text."""
        from app.tasks.process import chunk_text

        chunks = chunk_text("   \n\t  ")
        assert chunks == [], "Whitespace-only text should return empty list"

    def test_chunking_single_word(self):
        """Test that chunking handles single word."""
        from app.tasks.process import chunk_text

        chunks = chunk_text("hello")
        assert len(chunks) == 1, "Single word should return one chunk"
        assert chunks[0] == "hello"

    def test_chunking_exact_chunk_size(self):
        """Test that chunking handles text exactly at chunk size."""
        from app.tasks.process import chunk_text

        text = "a" * 1000
        chunks = chunk_text(text, chunk_size=1000, overlap=0)
        assert len(chunks) == 1, "Exact chunk size should return one chunk"

    def test_chunking_large_text(self):
        """Test that chunking handles very large text."""
        from app.tasks.process import chunk_text

        text = "word " * 100000  # 500KB of text
        chunks = chunk_text(text, chunk_size=1000, overlap=200)
        assert len(chunks) > 0, "Large text should produce chunks"
        assert len(chunks) < 1000, "Large text should not produce too many chunks"

    def test_chunking_preserves_content(self):
        """Test that chunking preserves all content."""
        from app.tasks.process import chunk_text

        text = "This is a test sentence. " * 100
        chunks = chunk_text(text, chunk_size=500, overlap=100)

        # Join chunks and verify content is preserved
        combined = " ".join(chunks)
        assert "This is a test sentence" in combined

    def test_chunking_overlap_works(self):
        """Test that chunking overlap works correctly."""
        from app.tasks.process import chunk_text

        text = "A" * 1000 + "B" * 1000
        chunks = chunk_text(text, chunk_size=1000, overlap=100)

        # With overlap, we should have more than 2 chunks
        assert len(chunks) >= 2, "Should have at least 2 chunks"


class TestEmbedderEdgeCases:
    """Test embedding edge cases."""

    def test_embedder_zero_vector_fallback(self):
        """Test that embedder returns zero vector when models unavailable."""
        from app.rag.embeddings.embedder import EmbeddingService

        service = EmbeddingService()
        vector = service.embed_query("test query")

        assert isinstance(vector, list), "Should return a list"
        assert len(vector) == 384, "Should return 384 dimensional vector (BGE-small)"
        assert all(v == 0.0 for v in vector), "Should be zero vector"

    def test_embedder_handles_empty_query(self):
        """Test that embedder handles empty query."""
        from app.rag.embeddings.embedder import EmbeddingService

        service = EmbeddingService()
        vector = service.embed_query("")

        assert isinstance(vector, list), "Should return a list"
        assert len(vector) == 384, "Should return 384 dimensional vector (BGE-small)"

    def test_embedder_handles_special_characters(self):
        """Test that embedder handles special characters."""
        from app.rag.embeddings.embedder import EmbeddingService

        service = EmbeddingService()
        vector = service.embed_query("!@#$%^&*()_+-=[]{}|;':\",./<>?")

        assert isinstance(vector, list), "Should return a list"
        assert len(vector) == 384, "Should return 384 dimensional vector (BGE-small)"

    def test_embedder_handles_very_long_query(self):
        """Test that embedder handles very long query."""
        from app.rag.embeddings.embedder import EmbeddingService

        service = EmbeddingService()
        long_query = "test " * 10000
        vector = service.embed_query(long_query)

        assert isinstance(vector, list), "Should return a list"
        assert len(vector) == 384, "Should return 384 dimensional vector (BGE-small)"


class TestRetrieverEdgeCases:
    """Test retriever edge cases."""

    def test_retriever_empty_index(self):
        """Test that retriever handles empty index."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()
        # The search method is async and requires db parameter
        # For unit testing, we test _local_search directly
        query_vector = np.random.rand(1536)
        results = retriever._local_search(query_vector, [], 5)

        assert results == [], "Empty index should return empty results"

    def test_retriever_no_matching_results(self):
        """Test that retriever handles no matching results."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()
        # Add some data directly to local store
        retriever._local_store[1] = [
            {
                "chunk_index": 0,
                "text": "test",
                "metadata": {},
                "embedding": np.zeros(1536).tolist(),
                "filename": "test.pdf",
                "department_id": 1,
            }
        ]

        # Search with very different query
        query_vector = np.ones(1536)
        results = retriever._local_search(query_vector, [], 5)

        # Should still return results (even if not relevant)
        assert len(results) <= 5, "Should not return more than top_k results"

    def test_retriever_top_k_limits_results(self):
        """Test that top_k parameter limits results."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()
        # Add many vectors directly to local store
        for i in range(100):
            retriever._local_store[i] = [
                {
                    "chunk_index": 0,
                    "text": f"doc {i}",
                    "metadata": {},
                    "embedding": np.random.rand(1536).tolist(),
                    "filename": f"doc_{i}.pdf",
                    "department_id": 1,
                }
            ]

        query_vector = np.random.rand(1536)
        results = retriever._local_search(query_vector, [], 10)

        assert len(results) == 10, "Should return exactly top_k results"

    def test_retriever_department_filtering(self):
        """Test that department filtering works correctly."""
        from app.rag.retriever.retriever import Retriever

        retriever = Retriever()
        # Add vectors with department metadata
        retriever._local_store[1] = [
            {
                "chunk_index": 0,
                "text": "doc 1",
                "metadata": {"department_id": 1},
                "embedding": np.random.rand(1536).tolist(),
                "filename": "doc1.pdf",
                "department_id": 1,
            }
        ]
        retriever._local_store[2] = [
            {
                "chunk_index": 0,
                "text": "doc 2",
                "metadata": {"department_id": 2},
                "embedding": np.random.rand(1536).tolist(),
                "filename": "doc2.pdf",
                "department_id": 2,
            }
        ]
        retriever._local_store[3] = [
            {
                "chunk_index": 0,
                "text": "doc 3",
                "metadata": {"department_id": 1},
                "embedding": np.random.rand(1536).tolist(),
                "filename": "doc3.pdf",
                "department_id": 1,
            }
        ]

        query_vector = np.random.rand(1536)
        results = retriever._local_search(query_vector, [1], 10)

        # All results should be from department 1
        for result in results:
            assert result["metadata"]["department_id"] == 1


class TestGeneratorEdgeCases:
    """Test LLM generator edge cases."""

    def test_generator_empty_documents(self):
        """Test that generator handles empty documents."""
        from app.rag.llm.generator import Generator

        generator = Generator()
        result = generator.generate("test query", [])

        assert isinstance(result, tuple), "Should return a tuple"
        assert len(result) == 3, "Should return 3 elements"

    def test_generator_fallback_without_llm(self):
        """Test that generator falls back when LLM unavailable."""
        from app.rag.llm.generator import Generator

        generator = Generator()
        docs = [{"document_id": 1, "filename": "test.pdf", "chunk_index": 0, "text": "test content", "score": 0.9}]
        result = generator.generate("test query", docs)

        assert isinstance(result, tuple), "Should return a tuple"
        assert len(result) == 3, "Should return 3 elements"

    def test_generator_handles_very_long_query(self):
        """Test that generator handles very long query."""
        from app.rag.llm.generator import Generator

        generator = Generator()
        long_query = "test " * 10000
        docs = [{"document_id": 1, "filename": "test.pdf", "chunk_index": 0, "text": "test content", "score": 0.9}]
        result = generator.generate(long_query, docs)

        assert isinstance(result, tuple), "Should return a tuple"

    def test_generator_handles_special_characters_in_query(self):
        """Test that generator handles special characters in query."""
        from app.rag.llm.generator import Generator

        generator = Generator()
        special_query = "!@#$%^&*()_+-=[]{}|;':\",./<>?"
        docs = [{"document_id": 1, "filename": "test.pdf", "chunk_index": 0, "text": "test content", "score": 0.9}]
        result = generator.generate(special_query, docs)

        assert isinstance(result, tuple), "Should return a tuple"

    def test_generator_includes_sources(self):
        """Test that generator includes sources in response."""
        from app.rag.llm.generator import Generator

        generator = Generator()
        docs = [
            {"document_id": 1, "filename": "doc1.pdf", "chunk_index": 0, "text": "test content 1", "score": 0.9},
            {"document_id": 2, "filename": "doc2.pdf", "chunk_index": 0, "text": "test content 2", "score": 0.8},
        ]
        result = generator.generate("test query", docs)

        # result is (answer, sources, avg_score)
        answer, sources, avg_score = result
        assert isinstance(sources, list), "Sources should be a list"
        assert len(sources) == 2, "Should have 2 sources"
