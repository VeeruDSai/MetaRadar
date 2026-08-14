"""POST /api/v1/search — hybrid vector search endpoint (D-07).

One contract, two consumers: the Phase 4 frontend consumes this directly and
Ask Athena / node_synthesize call the same VectorQueryService internally.
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.vector_query import (
    SearchError,
    SearchFilters,
    SignalSearchResult,
    vector_query_service,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    filters: Optional[SearchFilters] = None
    top_k: int = Field(default=10, ge=1, le=100)
    ef_search: int = Field(default=40, ge=1, le=1000)


class SearchResponse(BaseModel):
    results: List[SignalSearchResult]
    total: int
    query: str
    ef_search_used: int


@router.post("", response_model=SearchResponse)
async def search_signals(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """
    Hybrid vector search: embed query, apply filters, return Top-K signals by cosine similarity.
    Requires signals to have embeddings (NULL-embedding rows excluded).
    """
    try:
        results = await vector_query_service.search(
            db=db,
            query_text=request.query,
            top_k=request.top_k,
            ef_search=request.ef_search,
            filters=request.filters,
        )
    except SearchError as e:
        logger.warning(f"Search endpoint failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search service unavailable: {e}",
        )
    except Exception as e:
        logger.exception("Search endpoint: unexpected failure")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service unavailable: database error",
        )

    return SearchResponse(
        results=results,
        total=len(results),
        query=request.query,
        ef_search_used=request.ef_search,
    )