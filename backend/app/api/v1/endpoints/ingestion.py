import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import SourceHealthLog, RawSignalBronze
from app.services.ingestion import IngestionService
from app.workflows.runner import PipelineRunner
from app.core.logging import get_logger

logger = get_logger("ingestion_router")

router = APIRouter()


class IngestionRunRequest(BaseModel):
    connector_ids: Optional[List[str]] = Field(
        default=None,
        description="Optional list of connector IDs to run: pubmed, clinical_trials, fda, ema, newsapi. If None, runs all."
    )
    force_backfill: bool = Field(
        default=False,
        description="Whether to force backfill window replay instead of incremental rolling window."
    )


class IngestionSyncLiveRequest(BaseModel):
    connector_ids: Optional[List[str]] = Field(
        default=None,
        description="Connector IDs to execute before pipeline promotion."
    )
    batch_size: int = Field(
        default=50,
        description="Max signals to promote through LangGraph pipeline."
    )


@router.post(
    "/ingestion/run",
    summary="Trigger Live Connector Ingestion",
    description="Fetches live biomedical data from public APIs into raw_signals_bronze and logs health status."
)
async def trigger_ingestion_run(
    request: Optional[IngestionRunRequest] = None,
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    connector_ids = request.connector_ids if request else None
    force_backfill = request.force_backfill if request else False

    service = IngestionService(session)
    result = await service.run_connectors(
        connector_ids=connector_ids,
        force_backfill=force_backfill
    )
    return result


@router.post(
    "/ingestion/sync-live",
    summary="Live Ingest & End-to-End Pipeline Sync",
    description="Fetches live data from public APIs into bronze, then promotes unpromoted records through the LangGraph intelligence pipeline."
)
async def trigger_ingest_and_pipeline_sync(
    request: Optional[IngestionSyncLiveRequest] = None,
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    connector_ids = request.connector_ids if request else None
    batch_size = request.batch_size if request else 50

    # 1. Fetch live bronze records via connectors
    ingest_service = IngestionService(session)
    ingest_telemetry = await ingest_service.run_connectors(connector_ids=connector_ids)

    # 2. Run LangGraph intelligence pipeline to promote bronze into silver signals and gold confluences
    runner = PipelineRunner(session=session)
    final_state = await runner.run(batch_size=batch_size)

    errors = final_state.get("errors", [])
    pipeline_status = "completed" if len(errors) == 0 else "partial"

    # Honest run status derived from per-source connector results — never an
    # unconditional "success" (AGENTS.md rule #4: no fabricated behavior).
    source_statuses = [r.get("status") for r in (ingest_telemetry.get("results") or {}).values()]
    ingestion_status = (
        "success"
        if source_statuses and all(s == "HEALTHY" for s in source_statuses)
        else "partial"
    )

    return {
        "status": ingestion_status,
        "ingestion": ingest_telemetry,
        "pipeline": {
            "pipeline_run_id": final_state.get("pipeline_run_id"),
            "status": pipeline_status,
            "signals_processed": final_state.get("signals_processed", 0),
            "role_briefs_count": len(final_state.get("role_briefs", [])),
            "developments_count": len(final_state.get("developments", [])),
            "confluences_count": len(final_state.get("confluent_stories", [])),
            "contradictions_count": len(final_state.get("redteam_flags", [])),
            "missing_signals_count": len(final_state.get("missing_signals", [])),
            "errors": errors,
        }
    }


@router.get(
    "/ingestion/status",
    summary="Get Ingestion Health & Queue Status",
    description="Returns recent connector health logs and unpromoted bronze queue count."
)
async def get_ingestion_status(
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    # Unpromoted bronze count (SQL COUNT — never materialize every row)
    unpromoted_stmt = (
        select(func.count())
        .select_from(RawSignalBronze)
        .where(RawSignalBronze.pipeline_run_id.is_(None))
    )
    unpromoted_res = await session.execute(unpromoted_stmt)
    unpromoted_count = int(unpromoted_res.scalar() or 0)

    # Recent health logs per source
    logs_stmt = select(SourceHealthLog).order_by(desc(SourceHealthLog.checked_at)).limit(20)
    logs_res = await session.execute(logs_stmt)
    recent_logs = [
        {
            "id": str(log.id),
            "log_id": str(log.id),
            "source_id": log.source_id,
            "connector_status": log.connector_status,
            "latency_ms": log.latency_ms,
            "http_status": log.http_status,
            "records_fetched": log.records_fetched,
            "records_accepted": log.records_accepted,
            "records_rejected": log.records_rejected,
            "last_error": log.last_error,
            "checked_at": log.checked_at.isoformat() if log.checked_at else None,
        }
        for log in logs_res.scalars().all()
    ]

    return {
        "unpromoted_bronze_count": unpromoted_count,
        "recent_health_logs": recent_logs,
    }
