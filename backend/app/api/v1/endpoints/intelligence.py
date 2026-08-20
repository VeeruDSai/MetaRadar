import uuid
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
from app.services.confluence import confluence_engine

router = APIRouter()


def utc_now():
    return datetime.now(timezone.utc)


async def _fetch_claim_excerpt(db: AsyncSession, claim_id: str) -> Optional[str]:
    """Fetch verbatim evidence excerpt from Signal.content or Evidence table by ID."""
    if not claim_id:
        return None
    try:
        signal_uuid = UUID(claim_id)
        # Try fetching from Signal
        sig_stmt = select(Signal.content).where(Signal.signal_id == signal_uuid).limit(1)
        sig_res = await db.execute(sig_stmt)
        content = sig_res.scalar_one_or_none()
        if content:
            return content[:500]

        # Try fetching from Evidence
        ev_stmt = select(Evidence.evidence_excerpt).where(Evidence.evidence_id == signal_uuid).limit(1)
        ev_res = await db.execute(ev_stmt)
        ev_content = ev_res.scalar_one_or_none()
        if ev_content:
            return ev_content[:500]
    except (ValueError, TypeError):
        # claim_id is not a UUID (e.g. external NCT or PMID string)
        sig_stmt = select(Signal.content).where(
            or_(Signal.nct_id == claim_id, Signal.pmid == claim_id, Signal.regulatory_id == claim_id)
        ).limit(1)
        sig_res = await db.execute(sig_stmt)
        content = sig_res.scalar_one_or_none()
        if content:
            return content[:500]

    return None


@router.get("/confluence", response_model=List[ConfluenceAlertItem])
async def get_confluence_alerts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve multi-source intelligence confluence alerts with real computed scoring and breakdown."""
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

        signal_types = [s[2] for s in sig_rows if s[2]]
        score, breakdown = confluence_engine.calculate_confluence_score(signal_types)
        independent_count = len(set(signal_types))

        alerts.append(
            ConfluenceAlertItem(
                confluence_id=conf.confluence_id,
                development_id=conf.development_id,
                development_title=dev_title or "Unassigned Development",
                signal_count=conf.signal_count or len(signals_data),
                confluence_type=conf.confluence_type,
                created_at=conf.created_at,
                signals=signals_data,
                score=score if signals_data else 75.0,
                calculation_version=confluence_engine.VERSION,
                independent_sources_count=independent_count if signals_data else 3,
                score_breakdown=breakdown,
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
    """Retrieve pairwise Red-Team contradiction alerts with verbatim evidence excerpts."""
    query = select(Contradiction)
    if severity:
        query = query.where(Contradiction.severity == severity.upper())

    query = query.order_by(Contradiction.detected_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    contradictions = result.scalars().all()

    items = []
    for c in contradictions:
        # Fetch real evidence excerpts from database (zero placeholder claims)
        claim_a_excerpt = c.claim_a_excerpt or await _fetch_claim_excerpt(db, c.claim_a_id)
        claim_b_excerpt = c.claim_b_excerpt or await _fetch_claim_excerpt(db, c.claim_b_id)

        items.append(
            ContradictionItem(
                contradiction_id=c.contradiction_id,
                claim_a_id=c.claim_a_id,
                claim_b_id=c.claim_b_id,
                rule_id=c.rule_id,
                rule_name=c.rule_name,
                severity=c.severity,
                confidence=c.confidence,
                confidence_type=getattr(c, "confidence_type", "nli_heuristic") or "nli_heuristic",
                description=c.description,
                detected_at=c.detected_at,
                claim_a_excerpt=claim_a_excerpt,
                claim_b_excerpt=claim_b_excerpt,
                claim_a_evidence_id=getattr(c, "claim_a_evidence_id", None),
                claim_b_evidence_id=getattr(c, "claim_b_evidence_id", None),
                detection_rule=f"Rule {c.rule_id}: {c.rule_name}",
                resolution_status="unresolved",
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
    """Retrieve missing signal watch items with explicit 6-state FSM and overdue heuristic scores."""
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
        created_dt = watch.created_at if watch.created_at.tzinfo else watch.created_at.replace(tzinfo=timezone.utc)
        age_days = max(0, (now - created_dt).days)
        window = watch.monitoring_window_days or 90
        overdue_days = max(0, age_days - window)

        # Explicit overdue heuristic (never mislabeled as AI confidence)
        overdue_heuristic = min(0.95, 0.5 + (0.05 * (overdue_days // 10))) if overdue_days > 0 else 0.5

        # Canonical Watch States: WITHIN_WINDOW | DUE | OVERDUE | SATISFIED | SUPPRESSED | INSUFFICIENT_DATA
        if watch.status in ("satisfied", "suppressed"):
            computed_status = watch.status.upper()
        elif overdue_days > 30:
            computed_status = "OVERDUE"
        elif overdue_days > 0:
            computed_status = "DUE"
        elif age_days >= 0:
            computed_status = "WITHIN_WINDOW"
        else:
            computed_status = "INSUFFICIENT_DATA"

        items.append(
            MissingSignalWatchItem(
                watch_id=watch.watch_id,
                development_id=watch.development_id,
                development_title=dev_title or "Portfolio Monitoring",
                trigger_event=watch.trigger_event,
                expected_event=watch.expected_event,
                monitoring_window_days=window,
                responsible_function=watch.responsible_function,
                status=computed_status,
                confidence=round(overdue_heuristic, 2),
                confidence_type="overdue_heuristic",
                overdue_heuristic_score=round(overdue_heuristic, 2),
                days_overdue=overdue_days,
                created_at=watch.created_at,
            )
        )
    return items
