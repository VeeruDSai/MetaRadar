"""VectorQueryService — pgvector hybrid retrieval (D-06, D-07, D-08).

Hybrid retrieval = metadata/keyword filtering + pgvector cosine similarity.
Flow: query_text -> embed_text -> SELECT signals with cosine distance
ORDER BY embedding <=> query_vec WHERE filters applied -> Top-K results
with similarity scores. HNSW index ``signals_embedding_hnsw`` is used with an
adjustable ``ef_search`` (SET LOCAL, default 40).
"""

import logging
from typing import List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Signal
from app.services.embeddings import EmbeddingError, embedding_service

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Raised when the hybrid search pipeline cannot produce results."""


class SearchFilters(BaseModel):
    """Optional metadata filters applied before cosine-similarity ranking."""

    signal_type: Optional[str] = None    # e.g. "CLINICAL_TRIAL"
    disease: Optional[str] = None        # e.g. "haemophilia_a"
    priority: Optional[str] = None       # e.g. "HIGH"
    limit: int = Field(default=10, ge=1, le=100)


class SignalSearchResult(BaseModel):
    signal_id: str
    title: str
    content: str
    signal_type: str
    disease: str
    priority: str
    similarity_score: float              # 1 - cosine_distance (range 0-1)
    embedding_model_version: Optional[str]
    created_at: Optional[str]


class VectorQueryService:
    """Hybrid vector search over the ``signals.embedding`` pgvector column."""

    async def search(
        self,
        db: AsyncSession,
        query_text: str,
        top_k: int = 10,
        ef_search: int = 40,
        filters: Optional[SearchFilters] = None,
    ) -> List[SignalSearchResult]:
        """Hybrid search: embed query, apply metadata filters, cosine similarity rank."""
        # 1. Embed the query text (384-dim, fastembed CPU)
        try:
            query_vector = await embedding_service.embed_text(query_text)
        except EmbeddingError as e:
            logger.warning(f"VectorQueryService: query embedding failed: {e}")
            raise SearchError("Embedding failed for query") from e

        # 2. Set HNSW ef_search for this transaction (D-08: adjustable ef_search).
        # set_config(..., is_local=true) scopes the GUC to the transaction,
        # matching the previous SET LOCAL semantics, with a bound parameter.
        await db.execute(
            text("SELECT set_config('hnsw.ef_search', :ef_search, true)"),
            {"ef_search": str(ef_search)},
        )

        # 3. Build the hybrid query: metadata filters + cosine similarity rank
        stmt = (
            select(
                Signal,
                Signal.embedding.cosine_distance(query_vector).label("cosine_distance")
            )
            .where(Signal.embedding.isnot(None))
            .order_by(Signal.embedding.cosine_distance(query_vector))
            .limit(top_k)
        )

        if filters is not None:
            if filters.signal_type:
                stmt = stmt.where(Signal.signal_type == filters.signal_type)
            if filters.disease:
                stmt = stmt.where(Signal.disease == filters.disease)
            if filters.priority:
                stmt = stmt.where(Signal.priority == filters.priority)

        # 4. Execute and map to result models with similarity scores
        result = await db.execute(stmt)
        rows = result.all()

        results: List[SignalSearchResult] = []
        for signal, cosine_distance in rows:
            # cosine_distance is in [-2, 2] for normalized vectors; clamp to [0, 1]
            similarity_score = max(0.0, min(1.0, 1.0 - float(cosine_distance)))
            results.append(
                SignalSearchResult(
                    signal_id=str(signal.signal_id),
                    title=signal.title,
                    content=signal.content,
                    signal_type=signal.signal_type,
                    disease=signal.disease,
                    priority=signal.priority,
                    similarity_score=round(similarity_score, 6),
                    embedding_model_version=signal.embedding_model_version,
                    created_at=signal.created_at.isoformat() if signal.created_at else None,
                )
            )
        return results


# Module-level singleton
vector_query_service = VectorQueryService()