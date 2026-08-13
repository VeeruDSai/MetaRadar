from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.db.session import get_db
from app.core.config import settings
from app.models import ConnectorState
from app.connectors import ALL_CONNECTORS
from app.schemas import (
    HealthResponse, HealthReadyResponse, HealthModelsResponse, HealthConnectorsResponse, ConnectorHealthStatus
)

router = APIRouter()

_CONNECTOR_NAMES = {
    "pubmed": "NCBI PubMed",
    "clinical_trials": "ClinicalTrials.gov",
    "newsapi": "NewsAPI",
    "fda": "OpenFDA / FDA Regulatory",
    "ema": "EMA RSS / Decisions",
}


@router.get("", response_model=HealthResponse)
async def get_health():
    """Liveness check: process is alive."""
    return HealthResponse()


@router.get("/ready", response_model=HealthReadyResponse)
async def get_health_ready(db: AsyncSession = Depends(get_db)):
    """Readiness check: requires DB. Redis check is non-blocking."""
    db_ok = False
    redis_ok = False
    redis_warning = None

    # Check Database (mandatory)
    try:
        res = await db.execute(text("SELECT 1"))
        db_ok = bool(res.scalar() == 1)
    except Exception as e:
        db_ok = False

    # Check Redis (non-blocking)
    try:
        redis_client = Redis.from_url(settings.REDIS_URL, socket_timeout=2.0)
        await redis_client.ping()
        await redis_client.aclose()
        redis_ok = True
    except Exception as e:
        redis_ok = False
        redis_warning = f"Redis cache unavailable: {str(e)}"

    overall_status = "ready" if db_ok else "degraded"
    return HealthReadyResponse(
        status=overall_status,
        database=db_ok,
        redis=redis_ok,
        redis_warning=redis_warning
    )


@router.get("/models", response_model=HealthModelsResponse)
async def get_health_models():
    """Reports provider & model initialization availability."""
    return HealthModelsResponse(
        llm_provider=settings.LLM_PROVIDER,
        gemma_available=True,  # Detected at runtime
        grok_configured=bool(settings.XAI_API_KEY),
        grok_fallback_enabled=settings.ENABLE_GROK_FALLBACK,
        bart_degraded_available=True,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_revision=settings.EMBEDDING_MODEL_REVISION,
        embedding_dimension=settings.EMBEDDING_DIMENSION
    )


@router.get("/connectors", response_model=HealthConnectorsResponse)
async def get_health_connectors(session: AsyncSession = Depends(get_db)):
    """Reports each live connector's honest status (D-22).

    Reads the latest ConnectorState row per source for accurate
    last_success / quota_remaining in ONE batched query (avoids one DB
    connection attempt per connector); degrades to in-memory state when the
    DB is unavailable so the endpoint never fabricates values or 500s on
    auxiliary failure (fail-degrade pattern per signals.py).
    """
    preloaded = None  # None = DB read unavailable -> in-memory status
    try:
        result = await session.execute(
            select(ConnectorState).where(
                ConnectorState.source_id.in_([c.source_id for c in ALL_CONNECTORS])
            )
        )
        preloaded = {}
        for row in result.scalars().all():
            prev = preloaded.get(row.source_id)
            if prev is None or (row.updated_at or datetime.min) >= (prev.updated_at or datetime.min):
                preloaded[row.source_id] = row
    except Exception:
        preloaded = None

    statuses = []
    for connector in ALL_CONNECTORS:
        try:
            connector_status = await connector.get_status(
                None, preloaded.get(connector.source_id) if preloaded else None
            )
        except Exception:
            connector_status = await connector.get_status(None)
        statuses.append(
            ConnectorHealthStatus(
                source_id=connector_status.source_id,
                name=_CONNECTOR_NAMES.get(connector_status.source_id, connector_status.source_id),
                status=connector_status.status,
                freshness_class=connector.freshness_class,
                quota_remaining=connector_status.quota_remaining,
                last_success=connector_status.last_success,
                last_error=connector_status.last_error,
            )
        )
    return HealthConnectorsResponse(connectors=statuses)
