"""VectorQueryService — pgvector hybrid retrieval (D-06, D-07, D-08).

Hybrid retrieval = metadata/keyword filtering + pgvector cosine similarity.
Flow: query_text -> embed_text -> SELECT signals with cosine distance
ORDER BY embedding <=> query_vec WHERE filters applied -> Top-K results
with similarity scores. HNSW index ``signals_embedding_hnsw`` is used with an
adjustable ``ef_search`` (SET LOCAL, default 40).
"""

import logging
import uuid
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import select, or_, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models import Signal
from app.services.embeddings import EmbeddingError, embedding_service

logger = logging.getLogger(__name__)


class SearchError(Exception):
    """Raised when the hybrid search pipeline cannot produce results."""


class SearchFilters(BaseModel):
    """Optional metadata filters applied before cosine-similarity ranking.

    Result count is controlled exclusively by ``top_k`` on the search call.
    """

    signal_type: Optional[str] = None    # e.g. "CLINICAL_TRIAL"
    disease: Optional[str] = None        # e.g. "haemophilia_a"
    priority: Optional[str] = None       # e.g. "HIGH"


class SignalSearchResult(BaseModel):
    signal_id: str
    title: str
    content: str
    signal_type: str
    disease: str
    priority: str
    similarity_score: float              # 1 - cosine_distance (range 0-1)
    embedding_model_version: Optional[str] = None
    created_at: Optional[str] = None


class VectorQueryService:
    """True Hybrid retrieval: combines exact/substring keyword and identifier search with pgvector cosine similarity."""

    async def search(
        self,
        db: AsyncSession,
        query_text: str,
        top_k: int = 10,
        ef_search: int = 40,
        filters: Optional[SearchFilters] = None,
    ) -> List[SignalSearchResult]:
        """
        Hybrid search:
        1. Exact and substring search across external_id, pmid, nct_id, regulatory_id, fingerprint, signal_id, title, and content.
        2. Vector cosine similarity ranking on signals with embeddings.
        3. Merge, deduplicate, and rank results with metadata filters.
        """
        query_clean = query_text.strip()
        if not query_clean:
            return []

        results_dict = {}

        # ------------------------------------------------------------------
        # 1. Identifier and Keyword Search (Exact & Substring)
        # ------------------------------------------------------------------
        target_uuid = None
        try:
            target_uuid = uuid.UUID(query_clean)
        except (ValueError, TypeError):
            target_uuid = None

        id_conditions = [
            Signal.external_id.ilike(f"%{query_clean}%"),
            Signal.pmid.ilike(f"%{query_clean}%"),
            Signal.nct_id.ilike(f"%{query_clean}%"),
            Signal.regulatory_id.ilike(f"%{query_clean}%"),
            Signal.fingerprint.ilike(f"%{query_clean}%"),
            Signal.title.ilike(f"%{query_clean}%"),
            Signal.content.ilike(f"%{query_clean}%"),
        ]
        if target_uuid:
            id_conditions.append(Signal.signal_id == target_uuid)

        kw_stmt = select(Signal).where(or_(*id_conditions))
        if filters is not None:
            if filters.signal_type:
                kw_stmt = kw_stmt.where(Signal.signal_type == filters.signal_type)
            if filters.disease:
                kw_stmt = kw_stmt.where(Signal.disease == filters.disease)
            if filters.priority:
                kw_stmt = kw_stmt.where(Signal.priority == filters.priority)

        kw_stmt = kw_stmt.limit(top_k)
        try:
            kw_res = await db.execute(kw_stmt)
            for sig in kw_res.scalars().all():
                # Exact ID match receives 1.0 similarity score; keyword match receives 0.95
                is_exact_id = (
                    (sig.external_id and sig.external_id.lower() == query_clean.lower())
                    or (sig.pmid and sig.pmid.lower() == query_clean.lower())
                    or (sig.nct_id and sig.nct_id.lower() == query_clean.lower())
                    or (sig.regulatory_id and sig.regulatory_id.lower() == query_clean.lower())
                    or (sig.fingerprint and sig.fingerprint.lower() == query_clean.lower())
                    or (str(sig.signal_id).lower() == query_clean.lower())
                )
                score = 1.0 if is_exact_id else 0.95

                results_dict[str(sig.signal_id)] = SignalSearchResult(
                    signal_id=str(sig.signal_id),
                    title=sig.title,
                    content=sig.content,
                    signal_type=sig.signal_type,
                    disease=sig.disease,
                    priority=sig.priority,
                    similarity_score=score,
                    embedding_model_version=sig.embedding_model_version,
                    created_at=sig.created_at.isoformat() if sig.created_at else None,
                )
        except Exception as e:
            logger.warning(f"VectorQueryService: keyword search query failed: {e}")

        # ------------------------------------------------------------------
        # 2. Vector Cosine Similarity Search
        # ------------------------------------------------------------------
        try:
            query_vector = await embedding_service.embed_text(query_clean)

            # Set HNSW ef_search for transaction
            await db.execute(
                text("SELECT set_config('hnsw.ef_search', :ef_search, true)"),
                {"ef_search": str(ef_search)},
            )

            vec_stmt = (
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
                    vec_stmt = vec_stmt.where(Signal.signal_type == filters.signal_type)
                if filters.disease:
                    vec_stmt = vec_stmt.where(Signal.disease == filters.disease)
                if filters.priority:
                    vec_stmt = vec_stmt.where(Signal.priority == filters.priority)

            vec_res = await db.execute(vec_stmt)
            for signal, cosine_distance in vec_res.all():
                sig_id = str(signal.signal_id)
                sim_score = max(0.0, min(1.0, 1.0 - float(cosine_distance)))
                if sig_id in results_dict:
                    # Keep maximum of keyword boost or vector similarity
                    results_dict[sig_id].similarity_score = max(results_dict[sig_id].similarity_score, round(sim_score, 6))
                else:
                    results_dict[sig_id] = SignalSearchResult(
                        signal_id=sig_id,
                        title=signal.title,
                        content=signal.content,
                        signal_type=signal.signal_type,
                        disease=signal.disease,
                        priority=signal.priority,
                        similarity_score=round(sim_score, 6),
                        embedding_model_version=signal.embedding_model_version,
                        created_at=signal.created_at.isoformat() if signal.created_at else None,
                    )
        except Exception as e:
            logger.info(f"VectorQueryService: vector similarity search bypassed/unavailable: {e}")
            # If no keyword results either, raise SearchError
            if not results_dict:
                raise SearchError(f"Search retrieval unavailable: {e}") from e

        # ------------------------------------------------------------------
        # 3. Sort by similarity score descending and return Top-K
        # ------------------------------------------------------------------
        sorted_results = sorted(results_dict.values(), key=lambda r: r.similarity_score, reverse=True)
        return sorted_results[:top_k]


# Module-level singleton
vector_query_service = VectorQueryService()