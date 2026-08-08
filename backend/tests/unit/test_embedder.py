from unittest.mock import MagicMock

from app.rag.embeddings.embedder import embedding_service


class TestEmbeddingService:
    def test_zero_vector_fallback_without_models(self, monkeypatch):
        monkeypatch.setattr(embedding_service, "_openai_client", None)
        monkeypatch.setattr(embedding_service, "_local_model", None)

        result = embedding_service.embed(["hello world", "second text"])
        assert len(result) == 2
        assert all(len(vec) == embedding_service.dimension for vec in result)
        assert all(all(v == 0.0 for v in vec) for vec in result)

    def test_embed_query_zero_vector_without_models(self, monkeypatch):
        monkeypatch.setattr(embedding_service, "_openai_client", None)
        monkeypatch.setattr(embedding_service, "_local_model", None)

        result = embedding_service.embed_query("a question")
        assert len(result) == embedding_service.dimension
        assert all(v == 0.0 for v in result)

    def test_embed_uses_openai_client(self, monkeypatch):
        fake_result = [[0.1, 0.2], [0.3, 0.4]]
        fake_client = MagicMock()
        fake_client.embed_documents.return_value = fake_result
        monkeypatch.setattr(embedding_service, "_openai_client", fake_client)
        monkeypatch.setattr(embedding_service, "_local_model", None)

        result = embedding_service.embed(["a", "b"])
        assert result == fake_result
        fake_client.embed_documents.assert_called_once()
