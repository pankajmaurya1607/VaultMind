import logging
import time
from typing import List

from app.config.settings import settings
from app.monitoring.metrics import EMBEDDING_LATENCY

logger = logging.getLogger("eka")

try:
    from fastembed import TextEmbedding

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

        # Local BGE model via FastEmbed ONNX (CPU-only, ~67MB, no torch/CUDA).
        if _local_available:
            try:
                self._local_model = TextEmbedding(model_name=settings.EMBEDDING_MODEL_LOCAL)
                self.dimension = self._resolve_dim(settings.EMBEDDING_MODEL_LOCAL)
                logger.info(f"Using local embeddings: {settings.EMBEDDING_MODEL_LOCAL} (dim={self.dimension})")
            except Exception as e:
                logger.warning(f"Failed to initialize local model: {e}")

    @staticmethod
    def _resolve_dim(model_name: str) -> int:
        """Look up the embedding dim from FastEmbed's static model registry (no inference)."""
        try:
            for m in TextEmbedding.list_supported_models():
                name = m.get("model") if isinstance(m, dict) else getattr(m, "model", None)
                dim = m.get("dim") if isinstance(m, dict) else getattr(m, "dim", None)
                if name == model_name and dim:
                    return int(dim)
        except Exception:
            pass
        return settings.PGVECTOR_DIMENSION

    def embed(self, texts: List[str]) -> List[List[float]]:
        start = time.time()
        if self._local_model and texts:
            result = [vec.tolist() for vec in self._local_model.embed(texts)]
        elif self._local_model:
            result = []
        else:
            result = [[0.0] * self.dimension for _ in texts]
            logger.warning("No embedding model available, using zero vectors")

        elapsed = (time.time() - start) * 1000
        EMBEDDING_LATENCY.observe(elapsed)
        return result

    def embed_query(self, text: str) -> List[float]:
        start = time.time()
        if self._local_model:
            try:
                # query_embed applies the retrieval query prefix for BGE models.
                result = next(iter(self._local_model.query_embed([text]))).tolist()
            except (AttributeError, TypeError, StopIteration):
                result = next(iter(self._local_model.embed([text]))).tolist()
        else:
            result = [0.0] * self.dimension

        elapsed = (time.time() - start) * 1000
        EMBEDDING_LATENCY.observe(elapsed)
        return result


embedding_service = EmbeddingService()
