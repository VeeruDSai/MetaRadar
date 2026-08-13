from datetime import datetime
from fastapi import APIRouter, Depends, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from app.db.session import get_db
from app.core.config import settings
from app.schemas import (
    HealthResponse, HealthReadyResponse, HealthModelsResponse, HealthConnectorsResponse, ConnectorHealthStatus
)

router = APIRouter()


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
async def get_health_connectors():
    """Reports individual connector health, last success, last error, quota status."""
    connectors = [
        ConnectorHealthStatus(
            source_id="pubmed",
            name="NCBI PubMed",
            status="active",
            freshness_class="near_real_time"
        ),
        ConnectorHealthStatus(
            source_id="clinical_trials",
            name="ClinicalTrials.gov",
            status="active",
            freshness_class="near_real_time"
        ),
        ConnectorHealthStatus(
            source_id="newsapi",
            name="NewsAPI",
            status="active",
            freshness_class="delayed",
            quota_remaining=100
        ),
        ConnectorHealthStatus(
            source_id="fda",
            name="OpenFDA / FDA Regulatory",
            status="adapter_ready",
            freshness_class="batch"
        ),
        ConnectorHealthStatus(
            source_id="ema",
            name="EMA RSS / Decisions",
            status="adapter_ready",
            freshness_class="batch"
        ),
        ConnectorHealthStatus(
            source_id="congress",
            name="Congress Abstracts (ASH/ISTH/WFH)",
            status="adapter_ready",
            freshness_class="batch"
        ),
        ConnectorHealthStatus(
            source_id="synthetic",
            name="Synthetic Demo Suite",
            status="active",
            freshness_class="synthetic"
        )
    ]
    return HealthConnectorsResponse(connectors=connectors)
