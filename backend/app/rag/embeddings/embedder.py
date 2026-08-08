import logging
import time
from typing import List

from app.config.settings import settings
from app.monitoring.metrics import EMBEDDING_LATENCY

logger = logging.getLogger("eka")

try:
    from langchain_openai import OpenAIEmbeddings

    _openai_available = bool(settings.OPENAI_API_KEY)
except Exception:
    _openai_available = False

try:
    from sentence_transformers import SentenceTransformer

    _local_available = True
except Exception:
    _local_available = False


class EmbeddingService:
    def __init__(self):
        self._openai_client = None
        self._local_model = None
        self.dimension = settings.PGVECTOR_DIMENSION

        if settings.ENVIRONMENT == "testing":
            logger.info("Testing environment: embeddings disabled, using zero vectors")
            return

        if _openai_available:
            try:
                self._openai_client = OpenAIEmbeddings(
                    model=settings.OPENAI_EMBEDDING_MODEL,
                    openai_api_key=settings.OPENAI_API_KEY,
                )
                logger.info(f"Using OpenAI embeddings: {settings.OPENAI_EMBEDDING_MODEL}")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embeddings: {e}")

    def _ensure_local_model(self):
        if self._openai_client is not None or self._local_model is not None:
            return
        if not _local_available:
            return
        try:
            self._local_model = SentenceTransformer(settings.EMBEDDING_MODEL_LOCAL)
            self.dimension = self._local_model.get_sentence_embedding_dimension()
            logger.info(f"Using local embeddings: {settings.EMBEDDING_MODEL_LOCAL} (dim={self.dimension})")
        except Exception as e:
            logger.warning(f"Failed to initialize local model: {e}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        start = time.time()
        if self._openai_client:
            result = self._openai_client.embed_documents(texts)
        else:
            self._ensure_local_model()
            if self._local_model:
                result = self._local_model.encode(texts, show_progress_bar=False).tolist()
            else:
                result = [[0.0] * self.dimension for _ in texts]
                logger.warning("No embedding model available, using zero vectors")

        elapsed = (time.time() - start) * 1000
        EMBEDDING_LATENCY.observe(elapsed)
        return result

    def embed_query(self, text: str) -> List[float]:
        start = time.time()
        if self._openai_client:
            result = self._openai_client.embed_query(text)
        else:
            self._ensure_local_model()
            if self._local_model:
                result = self._local_model.encode([text], show_progress_bar=False)[0].tolist()
            else:
                result = [0.0] * self.dimension

        elapsed = (time.time() - start) * 1000
        EMBEDDING_LATENCY.observe(elapsed)
        return result


embedding_service = EmbeddingService()
