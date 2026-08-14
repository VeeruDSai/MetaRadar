"""EmbeddingService — fastembed (ONNX, CPU) embedding runtime (D-03).

Model identity: sentence-transformers/all-MiniLM-L6-v2 (384-dim, REQ-P3-1),
loaded lazily and cached in-process. Only fastembed + stdlib are used — no
torch / full sentence-transformers stack (D-03). fastembed's ``embed()`` is
synchronous CPU work, so every public method is async and offloads the actual
inference to the default executor via ``asyncio.get_running_loop().run_in_executor``
so callers never block the event loop.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastembed import TextEmbedding

from app.core.config import settings
from app.services.deduplication import chunk_text_for_embedding

logger = logging.getLogger(__name__)


class EmbeddingError(Exception):
    """Raised when embedding generation fails for any reason.

    Never silently returns a zero-vector — callers must handle or propagate.
    """


# Module-level lazy singleton (loaded on first use, cached for process lifetime)
_model: Optional[TextEmbedding] = None


class EmbeddingService:
    """Fastembed-backed 384-dim embedding service.

    Public API is fully async; inference is offloaded to the event loop's
    default executor so it never blocks async callers.
    """

    def __init__(self) -> None:
        self.model_name: str = settings.EMBEDDING_MODEL
        self.dimension: int = settings.EMBEDDING_DIMENSION
        self.max_seq_length: int = settings.EMBEDDING_MAX_SEQ_LENGTH
        self._model: Optional[TextEmbedding] = None

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------
    def _get_model(self) -> TextEmbedding:
        """Returns the lazily-loaded, in-process cached TextEmbedding instance.

        Model identity matches ``settings.EMBEDDING_MODEL`` exactly. Never
        reloads between calls in the same process.
        """
        if self._model is None:
            logger.info(f"Loading fastembed TextEmbedding model: {self.model_name}")
            self._model = TextEmbedding(self.model_name)
        return self._model

    def _embed_sync(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Synchronous embedding call — runs inside the executor."""
        try:
            model = self._get_model()
            vectors = list(model.embed(texts, batch_size=batch_size))
            return [v.tolist() for v in vectors]
        except Exception as e:
            raise EmbeddingError(f"Embedding failed: {e}") from e

    def _validate_vector(self, vector: List[float]) -> List[float]:
        """Enforces the 384-dim contract before returning (REQ-P3-1)."""
        if len(vector) != self.dimension:
            raise EmbeddingError(
                f"Embedding failed: unexpected dimensionality {len(vector)} (expected {self.dimension})"
            )
        return vector

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text chunk. Returns a 384-float vector."""
        loop = asyncio.get_running_loop()
        vectors = await loop.run_in_executor(None, self._embed_sync, [text])
        return self._validate_vector(vectors[0])

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text chunks. Returns a list of 384-float vectors."""
        if not texts:
            return []
        loop = asyncio.get_running_loop()
        vectors = await loop.run_in_executor(None, self._embed_sync, texts)
        return [self._validate_vector(v) for v in vectors]

    async def embed_signal(self, signal: Dict[str, Any]) -> List[float]:
        """Compose embedding text from a signal dict per D-02 and embed it.

        Text source: ``title + content + signal_type``, chunked via
        ``chunk_text_for_embedding`` (256 tokens / EMBEDDING_MAX_SEQ_LENGTH).
        Returns a 384-float vector.
        """
        title = str(signal.get("title") or "")
        content = str(signal.get("content") or "")
        signal_type = str(signal.get("signal_type") or "")
        composed = f"{title} {content} {signal_type}".strip()
        chunked = chunk_text_for_embedding(composed, max_tokens=self.max_seq_length)
        if not chunked:
            raise EmbeddingError("Embedding failed: empty signal text")
        return await self.embed_text(chunked)


# Module-level singleton — import and use directly
embedding_service = EmbeddingService()