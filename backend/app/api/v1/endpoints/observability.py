import time
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.session import get_db
from app.models import Source, SourceHealthLog, PipelineRun, AuditLog
from app.schemas import ActivityLogItem
from app.schemas.registry import SourceHealthLogItem, SourceRegistryItem

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/observability/activity", response_model=List[ActivityLogItem])
async def get_system_activity(
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve recent system activity logs, pipeline executions, and operational audit events."""
    activity_items: List[ActivityLogItem] = []

    # 1. Fetch recent Pipeline Runs
    try:
        runs_query = select(PipelineRun).order_by(desc(PipelineRun.started_at)).limit(limit)
        runs_res = await db.execute(runs_query)
        runs = runs_res.scalars().all()

        for r in runs:
            level = "INFO" if r.status in ("completed", "success") else ("ERROR" if r.status in ("failed", "error") else "WARNING")
            duration = 0.0
            if r.completed_at and r.started_at:
                duration = round((r.completed_at - r.started_at).total_seconds() * 1000, 2)

            activity_items.append(
                ActivityLogItem(
                    id=r.pipeline_run_id,
                    timestamp=r.started_at,
                    level=level,
                    service="pipeline_engine",
                    component="PipelineRunner",
                    event=f"pipeline.{r.status}",
                    status=r.status,
                    duration_ms=duration,
                    pipeline_run_id=str(r.pipeline_run_id),
                    message=f"Pipeline run {r.status}: {r.signals_created} signals created, {r.signals_updated} updated, {r.errors_count} errors.",
                    details={
                        "trigger": r.trigger,
                        "signals_fetched": r.signals_fetched,
                        "duplicates_removed": r.duplicates_removed,
                        "error_summary": r.error_summary,
                    }
                )
            )
    except Exception as e:
        logger.debug(f"PipelineRun activity query skipped: {e}")

    # 2. Fetch recent Source Health Logs
    try:
        logs_query = select(SourceHealthLog).order_by(desc(SourceHealthLog.checked_at)).limit(limit)
        logs_res = await db.execute(logs_query)
        health_logs = logs_res.scalars().all()

        for hl in health_logs:
            level = "INFO" if hl.connector_status == "HEALTHY" else ("ERROR" if hl.connector_status in ("ERROR", "AUTH_FAILED") else "WARNING")
            activity_items.append(
                ActivityLogItem(
                    id=hl.id,
                    timestamp=hl.checked_at,
                    level=level,
                    service="ingestion_connectors",
                    component=f"{hl.source_id.capitalize()}Connector",
                    event=f"connector.{hl.connector_status.lower()}",
                    status=hl.connector_status,
                    duration_ms=float(hl.latency_ms) if hl.latency_ms else None,
                    pipeline_run_id=str(hl.pipeline_run_id) if hl.pipeline_run_id else None,
                    message=f"Connector {hl.source_id} state is {hl.connector_status} ({hl.records_fetched} fetched, {hl.records_accepted} accepted).",
                    details={
                        "http_status": hl.http_status,
                        "last_error": hl.last_error,
                        "records_rejected": hl.records_rejected,
                    }
                )
            )
    except Exception as e:
        logger.debug(f"SourceHealthLog activity query skipped: {e}")

    # Sort all activity combined by timestamp desc
    activity_items.sort(key=lambda x: x.timestamp, reverse=True)
    return activity_items[:limit]


@router.get("/sources/health", response_model=List[SourceRegistryItem])
async def get_sources_health(db: AsyncSession = Depends(get_db)):
    """Retrieve live health telemetry across all configured source connectors."""
    try:
        query = select(Source).order_by(Source.source_id)
        result = await db.execute(query)
        sources = result.scalars().all()
    except Exception as e:
        logger.debug(f"Sources query skipped: {e}")
        sources = []

    items = []
    for s in sources:
        items.append(
            SourceRegistryItem(
                source_id=s.source_id,
                name=s.name,
                freshness_class=s.freshness_class,
                syndication_group=s.syndication_group,
                status=s.status,
                quota_remaining=s.quota_remaining,
                last_success=s.last_success,
                connector_status=s.connector_status or "NEVER_CONNECTED",
                last_attempted=s.last_attempted,
                latency_ms=s.latency_ms,
                records_fetched=s.records_fetched or 0,
                records_accepted=s.records_accepted or 0,
                records_rejected=s.records_rejected or 0,
                http_status=s.http_status,
            )
        )
    return items
