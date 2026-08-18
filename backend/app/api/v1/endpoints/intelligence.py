from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from app.db.session import get_db
from app.models import (
    Confluence,
    LifecycleEvent,
    Contradiction,
    WatchItem,
    Development,
    Asset,
    Evidence,
    Signal,
)
from app.schemas.intelligence import (
    ConfluenceAlertItem,
    LifecycleTimelineItem,
    ContradictionItem,
    MissingSignalWatchItem,
)

router = APIRouter()


def utc_now():
    return datetime.now(timezone.utc)


@router.get("/confluence", response_model=List[ConfluenceAlertItem])
async def get_confluence_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve multi-source intelligence confluence alerts with development context."""
    query = (
        select(
            Confluence,
            Development.title.label("development_title"),
        )
        .outerjoin(Development, Confluence.development_id == Development.development_id)
        .order_by(Confluence.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(query)
    rows = result.all()

    alerts = []
    for conf, dev_title in rows:
        # Fetch associated signals for evidence preview
        sig_query = (
            select(Signal.signal_id, Signal.title, Signal.signal_type, Signal.published_at)
            .where(Signal.development_id == conf.development_id)
            .order_by(Signal.published_at.desc())
            .limit(5)
        )
        sig_res = await db.execute(sig_query)
        sig_rows = sig_res.all()
        signals_data = [
            {
                "signal_id": str(s[0]),
                "title": s[1],
                "signal_type": s[2],
                "published_at": s[3].isoformat() if s[3] else None,
            }
            for s in sig_rows
        ]

        alerts.append(
            ConfluenceAlertItem(
                confluence_id=conf.confluence_id,
                development_id=conf.development_id,
                development_title=dev_title or "Unassigned Development",
                signal_count=conf.signal_count,
                confluence_type=conf.confluence_type,
                created_at=conf.created_at,
                signals=signals_data,
            )
        )
    return alerts


@router.get("/lifecycles", response_model=List[LifecycleTimelineItem])
async def get_lifecycle_timelines(
    disease: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve chronological lifecycle timeline events for developments and drug assets."""
    query = (
        select(
            LifecycleEvent,
            Development.title.label("development_title"),
            Development.disease.label("disease"),
            Asset.brand_name.label("asset_name"),
        )
        .join(Development, LifecycleEvent.development_id == Development.development_id)
        .outerjoin(Asset, Development.asset_id == Asset.asset_id)
    )
    if disease:
        query = query.where(Development.disease.ilike(f"%{disease}%"))

    query = query.order_by(LifecycleEvent.event_date.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    timelines = []
    for event, dev_title, dev_disease, asset_name in rows:
        timelines.append(
            LifecycleTimelineItem(
                lifecycle_id=event.lifecycle_id,
                development_id=event.development_id,
                development_title=dev_title,
                disease=dev_disease,
                asset_name=asset_name,
                stage=event.stage,
                event_date=event.event_date,
                notes=event.notes,
            )
        )
    return timelines


@router.get("/red-team", response_model=List[ContradictionItem])
async def get_red_team_contradictions(
    severity: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve pairwise Red-Team contradiction alerts."""
    query = select(Contradiction)
    if severity:
        query = query.where(Contradiction.severity == severity.upper())

    query = query.order_by(Contradiction.detected_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    contradictions = result.scalars().all()

    items = []
    for c in contradictions:
        items.append(
            ContradictionItem(
                contradiction_id=c.contradiction_id,
                claim_a_id=c.claim_a_id,
                claim_b_id=c.claim_b_id,
                rule_id=c.rule_id,
                rule_name=c.rule_name,
                severity=c.severity,
                confidence=c.confidence,
                description=c.description,
                detected_at=c.detected_at,
                claim_a_excerpt=f"Primary evidence claim for {c.claim_a_id}",
                claim_b_excerpt=f"Contradicting evidence claim for {c.claim_b_id}",
            )
        )
    return items


@router.get("/missing-signals", response_model=List[MissingSignalWatchItem])
async def get_missing_signals(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve missing signal watch items and overdue expected events."""
    query = (
        select(
            WatchItem,
            Development.title.label("development_title"),
        )
        .outerjoin(Development, WatchItem.development_id == Development.development_id)
    )
    if status:
        query = query.where(WatchItem.status == status)

    query = query.order_by(WatchItem.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    now = utc_now()
    items = []
    for watch, dev_title in rows:
        # Calculate days since creation vs monitoring window
        age_days = (now - watch.created_at).days if watch.created_at else 0
        overdue = max(0, age_days - watch.monitoring_window_days)
        confidence = min(0.95, 0.5 + (0.05 * (overdue // 10))) if overdue > 0 else 0.5

        items.append(
            MissingSignalWatchItem(
                watch_id=watch.watch_id,
                development_id=watch.development_id,
                development_title=dev_title or "Portfolio Monitoring",
                trigger_event=watch.trigger_event,
                expected_event=watch.expected_event,
                monitoring_window_days=watch.monitoring_window_days,
                responsible_function=watch.responsible_function,
                status=watch.status,
                confidence=confidence,
                days_overdue=overdue,
                created_at=watch.created_at,
            )
        )
    return items
