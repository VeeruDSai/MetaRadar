import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.db.session import get_db
from app.core.config import settings, configuration_error_for
from app.models import ConnectorState, Source
from app.connectors import ALL_CONNECTORS
from app.schemas import (
    HealthResponse, HealthReadyResponse, HealthModelsResponse, HealthConnectorsResponse, ConnectorHealthStatus
)

router = APIRouter()

logger = logging.getLogger(__name__)

# Timezone-aware epoch used to normalize NULL timestamps in comparisons.
# Never compare tz-aware datetimes against naive datetime.min — that raises
# TypeError and (behind a broad except) silently aborts the whole preload loop.
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

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
    """Reports real provider & model initialization availability. No fabricated telemetry."""
    from app.providers.gemma import GemmaProvider
    provider = GemmaProvider()
    try:
        gemma_available = await provider.is_available()   # actual HTTP GET to Ollama /api/tags
    finally:
        # Close the lazily-created httpx.AsyncClient so the connection pool
        # is not leaked on every /health/models poll.
        await provider.aclose()
    return HealthModelsResponse(
        llm_provider=settings.LLM_PROVIDER,
        ollama_host=settings.OLLAMA_HOST,
        gemma_available=gemma_available,
        grok_configured=bool(settings.XAI_API_KEY),
        grok_fallback_enabled=settings.ENABLE_GROK_FALLBACK,
        bart_degraded_available=True,
        embedding_model=settings.EMBEDDING_MODEL,
        embedding_revision=settings.EMBEDDING_MODEL_REVISION,
        embedding_dimension=settings.EMBEDDING_DIMENSION
    )


@router.get("/connectors", response_model=HealthConnectorsResponse)
async def get_health_connectors(session: AsyncSession = Depends(get_db)):
    """Reports each live connector's honest status (D-22, REQ-P8-06, REQ-P8-07)."""
    preloaded_sources = {}
    preloaded_states = {}
    try:
        src_res = await session.execute(
            select(Source).where(Source.source_id.in_([c.source_id for c in ALL_CONNECTORS]))
        )
        for s in src_res.scalars().all():
            preloaded_sources[s.source_id] = s

        state_res = await session.execute(
            select(ConnectorState).where(ConnectorState.source_id.in_([c.source_id for c in ALL_CONNECTORS]))
        )
        for row in state_res.scalars().all():
            prev = preloaded_states.get(row.source_id)
            if prev is None:
                preloaded_states[row.source_id] = row
            elif (row.updated_at or _EPOCH) >= (prev.updated_at or _EPOCH):
                preloaded_states[row.source_id] = row
    except Exception:
        logger.warning(
            "Failed to preload connector states; falling back to per-connector lookups",
            exc_info=True,
        )

    statuses = []
    for connector in ALL_CONNECTORS:
        config_err = configuration_error_for(connector.source_id)
        source_row = preloaded_sources.get(connector.source_id)
        state_row = preloaded_states.get(connector.source_id)

        if config_err:
            statuses.append(
                ConnectorHealthStatus(
                    source_id=connector.source_id,
                    name=_CONNECTOR_NAMES.get(connector.source_id, connector.source_id),
                    status="CONFIGURATION_ERROR",
                    freshness_class=connector.freshness_class,
                    quota_remaining=0,
                    last_success=source_row.last_success if source_row else None,
                    last_attempted=source_row.last_attempted if source_row else None,
                    last_error=config_err,
                    connector_status="CONFIGURATION_ERROR",
                    latency_ms=source_row.latency_ms if source_row else None,
                    records_fetched=source_row.records_fetched if source_row else 0,
                    records_accepted=source_row.records_accepted if source_row else 0,
                    records_rejected=source_row.records_rejected if source_row else 0,
                    http_status=source_row.http_status if source_row else None,
                    configuration_error_message=config_err,
                )
            )
            continue

        if source_row:
            statuses.append(
                ConnectorHealthStatus(
                    source_id=connector.source_id,
                    name=_CONNECTOR_NAMES.get(connector.source_id, source_row.name or connector.source_id),
                    status=source_row.connector_status or "NEVER_CONNECTED",
                    freshness_class=source_row.freshness_class or connector.freshness_class,
                    quota_remaining=source_row.quota_remaining,
                    last_success=source_row.last_success,
                    last_attempted=source_row.last_attempted,
                    last_error=source_row.last_error,
                    connector_status=source_row.connector_status or "NEVER_CONNECTED",
                    latency_ms=source_row.latency_ms,
                    records_fetched=source_row.records_fetched or 0,
                    records_accepted=source_row.records_accepted or 0,
                    records_rejected=source_row.records_rejected or 0,
                    http_status=source_row.http_status,
                    configuration_error_message=source_row.configuration_error_message,
                )
            )
            continue

        try:
            conn_status = await connector.get_status(None, state_row)
        except Exception:
            conn_status = await connector.get_status(None)

        statuses.append(
            ConnectorHealthStatus(
                source_id=conn_status.source_id,
                name=_CONNECTOR_NAMES.get(conn_status.source_id, conn_status.source_id),
                status=conn_status.status,
                freshness_class=connector.freshness_class,
                quota_remaining=conn_status.quota_remaining,
                last_success=conn_status.last_success,
                last_error=conn_status.last_error,
                connector_status="NEVER_CONNECTED",
            )
        )

    return HealthConnectorsResponse(connectors=statuses)

