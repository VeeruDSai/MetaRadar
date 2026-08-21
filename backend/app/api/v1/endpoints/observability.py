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
    except Exception:
        # An outage must never look like "no activity" — surface it loudly.
        logger.error("PipelineRun activity query failed — activity feed is degraded", exc_info=True)

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
    except Exception:
        logger.error("SourceHealthLog activity query failed — activity feed is degraded", exc_info=True)

    # Sort all activity combined by timestamp desc
    activity_items.sort(key=lambda x: x.timestamp, reverse=True)
    return activity_items[:limit]


@router.get("/sources/health", response_model=List[SourceRegistryItem])
async def get_sources_health(db: AsyncSession = Depends(get_db)):
    """Retrieve live health telemetry across all configured source connectors, reconciled with latest health logs."""
    try:
        query = select(Source).order_by(Source.source_id)
        result = await db.execute(query)
        sources = result.scalars().all()
    except Exception:
        logger.error("Sources query failed — registry health is degraded", exc_info=True)
        sources = []

    # Query latest SourceHealthLog per source_id
    latest_logs: Dict[str, SourceHealthLog] = {}
    try:
        log_query = select(SourceHealthLog).order_by(desc(SourceHealthLog.checked_at)).limit(100)
        log_res = await db.execute(log_query)
        all_logs = log_res.scalars().all()
        for l in all_logs:
            if l.source_id not in latest_logs:
                latest_logs[l.source_id] = l
    except Exception:
        logger.error("Latest health-logs query failed — registry health is degraded", exc_info=True)

    from app.core.config import configuration_error_for

    items = []
    seen_ids = set()

    for s in sources:
        seen_ids.add(s.source_id)
        hl = latest_logs.get(s.source_id)

        config_err = configuration_error_for(s.source_id)
        if config_err:
            conn_status = "CONFIGURATION_ERROR"
            last_err = config_err
            err_msg = config_err
        else:
            conn_status = hl.connector_status if hl else (s.connector_status or "NEVER_CONNECTED")
            last_err = hl.last_error if hl else s.last_error
            err_msg = s.configuration_error_message

        latency = int(hl.latency_ms) if (hl and hl.latency_ms is not None) else s.latency_ms
        fetched = hl.records_fetched if (hl and hl.records_fetched is not None) else (s.records_fetched or 0)
        accepted = hl.records_accepted if (hl and hl.records_accepted is not None) else (s.records_accepted or 0)
        rejected = hl.records_rejected if (hl and hl.records_rejected is not None) else (s.records_rejected or 0)
        last_att = hl.checked_at if hl else s.last_attempted
        last_succ = hl.checked_at if (hl and hl.connector_status == "HEALTHY") else s.last_success
        http_code = hl.http_status if (hl and hl.http_status is not None) else s.http_status

        items.append(
            SourceRegistryItem(
                source_id=s.source_id,
                name=s.name,
                freshness_class=s.freshness_class,
                syndication_group=s.syndication_group,
                status=s.status,
                quota_remaining=s.quota_remaining,
                last_success=last_succ,
                last_error=last_err,
                connector_status=conn_status,
                last_attempted=last_att,
                latency_ms=latency,
                records_fetched=fetched,
                records_accepted=accepted,
                records_rejected=rejected,
                http_status=http_code,
                configuration_error_message=err_msg,
            )
        )

    return items
