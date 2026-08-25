import logging
import time
from typing import List

from app.config.settings import settings
from app.monitoring.metrics import EMBEDDING_LATENCY

logger = logging.getLogger("eka")

try:
    from sentence_transformers import SentenceTransformer

    _local_available = True
except Exception:
    _local_available = False


class EmbeddingService:
    def __init__(self):
        self._local_model = None
        self.dimension = settings.PGVECTOR_DIMENSION

        if settings.ENVIRONMENT == "testing":
            logger.info("Testing environment: embeddings disabled, using zero vectors")
            return

        # Always try to use local BGE model (free, no API key needed)
        if _local_available:
            try:
                self._local_model = SentenceTransformer(settings.EMBEDDING_MODEL_LOCAL)
                self.dimension = self._local_model.get_sentence_embedding_dimension()
                logger.info(f"Using local embeddings: {settings.EMBEDDING_MODEL_LOCAL} (dim={self.dimension})")
            except Exception as e:
                logger.warning(f"Failed to initialize local model: {e}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        start = time.time()
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
        if self._local_model:
            result = self._local_model.encode([text], show_progress_bar=False)[0].tolist()
        else:
            result = [0.0] * self.dimension

        elapsed = (time.time() - start) * 1000
        EMBEDDING_LATENCY.observe(elapsed)
        return result


embedding_service = EmbeddingService()
