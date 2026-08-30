import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    AuditLog,
    CalibrationFeedback,
)
from app.models.auth import User
from app.api.deps import get_current_user, get_optional_user
from app.schemas.intelligence import (
    ConfluenceAlertItem,
    ConfluenceInspectResponse,
    ConfluenceEvidenceSourceItem,
    LifecycleTimelineItem,
    ContradictionItem,
    MissingSignalWatchItem,
    FunctionStatsResponse,
    FunctionCalibrationProfile,
    CalibrationStatusResponse,
    LeadershipSummaryResponse,
)
from app.services.confluence import SIGNAL_TYPE_WEIGHTS, confluence_engine

router = APIRouter()



def utc_now():
    return datetime.now(timezone.utc)


def _derive_external_id(row) -> str:
    """Derive a stable external identifier for evidence traceability.

    Prefers real source identifiers (pmid / nct / regulatory), then a truncated
    fingerprint, then the signal UUID. Shared by the confluence list and inspect
    handlers so both views render identical external_id values.
    """
    pmid, nct_id, reg_id = row[9], row[10], row[11]
    fingerprint, signal_id = row[4], row[0]
    return pmid or nct_id or reg_id or (fingerprint[:12] if fingerprint else str(signal_id))


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
        # Fetch associated signals with full provenance & content excerpts
        sig_query = (
            select(
                Signal.signal_id,
                Signal.title,
                Signal.signal_type,
                Signal.source_id,
                Signal.fingerprint,
                Signal.canonical_url,
                Signal.content,
                Signal.published_at,
                Signal.retrieved_at,
                Signal.pmid,
                Signal.nct_id,
                Signal.regulatory_id,
            )
            .where(Signal.development_id == conf.development_id)
            .order_by(Signal.published_at.desc())
            .limit(10)
        )
        sig_res = await db.execute(sig_query)
        sig_rows = sig_res.all()

        signals_data = []
        evidence_sources = []
        signal_types = []
        distinct_source_ids = set()

        for s in sig_rows:
            ext_id = _derive_external_id(s)
            signals_data.append({
                "signal_id": str(s[0]),
                "title": s[1],
                "signal_type": s[2],
                "source_id": s[3],
                "external_id": ext_id,
                "canonical_url": s[5],
                "published_at": s[7].isoformat() if s[7] else None,
            })
            if s[2]:
                signal_types.append(s[2])
            if s[3]:
                distinct_source_ids.add(s[3])

            # Canonical engine weights — keeps evidence points identical to score_breakdown.
            pts = SIGNAL_TYPE_WEIGHTS.get((s[2] or "").upper(), 10.0)

            source_name = s[3] or "External Biomedical API"
            if s[3] == "pubmed":
                source_name = "PubMed Central / E-Utilities"
            elif s[3] == "clinical_trials":
                source_name = "ClinicalTrials.gov API v2"
            elif s[3] == "fda":
                source_name = "OpenFDA Drug Data"
            elif s[3] == "ema":
                source_name = "EMA RSS Stream"

            evidence_sources.append(
                ConfluenceEvidenceSourceItem(
                    source_name=source_name,
                    source_type=s[2] or "CLINICAL_TRIAL",
                    external_id=_derive_external_id(s),
                    source_url=s[5],
                    retrieved_at=s[8],
                    published_at=s[7],
                    verbatim_excerpt=(s[6] or s[1])[:400],
                    points_contributed=pts,
                )
            )

        score, breakdown = confluence_engine.calculate_confluence_score(signal_types)
        independent_count = len(distinct_source_ids)
        drivers_str = ", ".join(f"{k} (+{v}pts)" for k, v in breakdown.items())
        reasoning = (
            f"Multi-source convergence score of {score:.1f} calculated across {independent_count} independent source types "
            f"within a 48h sliding window. Drivers: {drivers_str}."
            if signal_types else "Baseline multi-source confluence score."
        )

        alerts.append(
            ConfluenceAlertItem(
                confluence_id=conf.confluence_id,
                development_id=conf.development_id,
                development_title=dev_title or "Unassigned Development",
                signal_count=conf.signal_count or len(signals_data),
                confluence_type=conf.confluence_type,
                created_at=conf.created_at,
                signals=signals_data,
                score=score if signals_data else 0.0,
                calculation_version=confluence_engine.VERSION,
                independent_sources_count=independent_count if signals_data else 0,
                score_breakdown=breakdown,
                reasoning=reasoning,
                evidence_sources=evidence_sources,
            )
        )
    return alerts


@router.get("/confluence/{confluence_id}/inspect", response_model=ConfluenceInspectResponse)
async def inspect_confluence(
    confluence_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Backward Trace Inspectability: Answers 'Why this confluence score?' with full verbatim citations,
    source URLs, retrieval timestamps, and exact mathematical breakdown.
    """
    conf_stmt = (
        select(
            Confluence,
            Development.title.label("development_title"),
        )
        .outerjoin(Development, Confluence.development_id == Development.development_id)
        .where(Confluence.confluence_id == confluence_id)
        .limit(1)
    )
    res = await db.execute(conf_stmt)
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail=f"Confluence alert '{confluence_id}' not found")

    conf, dev_title = row

    sig_query = (
        select(
            Signal.signal_id,
            Signal.title,
            Signal.signal_type,
            Signal.source_id,
            Signal.fingerprint,
            Signal.canonical_url,
            Signal.content,
            Signal.published_at,
            Signal.retrieved_at,
            Signal.pmid,
            Signal.nct_id,
            Signal.regulatory_id,
        )
        .where(Signal.development_id == conf.development_id)
        .order_by(Signal.published_at.desc())
        .limit(20)
    )
    sig_res = await db.execute(sig_query)
    sig_rows = sig_res.all()

    evidence_sources = []
    signal_types = []
    distinct_source_ids = set()

    for s in sig_rows:
        if s[2]:
            signal_types.append(s[2])
        if s[3]:
            distinct_source_ids.add(s[3])

        # Canonical engine weights — keeps evidence points identical to score_breakdown.
        pts = SIGNAL_TYPE_WEIGHTS.get((s[2] or "").upper(), 10.0)

        ext_id = _derive_external_id(s)
        source_name = (s[3] or "Source").replace("_", " ").title()
        if s[3] == "pubmed":
            source_name = "PubMed Central"
        elif s[3] == "clinical_trials":
            source_name = "ClinicalTrials.gov"
        elif s[3] == "newsapi":
            source_name = "News & Commercial"
        elif s[3] == "fda":
            source_name = "OpenFDA Direct"
        elif s[3] == "ema":
            source_name = "EMA RSS Stream"

        evidence_sources.append(
            ConfluenceEvidenceSourceItem(
                source_name=source_name,
                source_type=s[2] or "CLINICAL_TRIAL",
                external_id=ext_id,
                source_url=s[5],
                retrieved_at=s[8],
                published_at=s[7],
                verbatim_excerpt=(s[6] or s[1])[:500],
                points_contributed=pts,
            )
        )

    score, breakdown = confluence_engine.calculate_confluence_score(signal_types)
    independent_count = len(distinct_source_ids)
    drivers_str = ", ".join(f"{k} (+{v}pts)" for k, v in breakdown.items())
    reasoning = (
        f"Multi-source convergence score of {score:.1f} calculated across {independent_count} independent sources "
        f"within a 48h sliding window. Drivers: {drivers_str}."
        if signal_types else "Confluence calculated from multi-source cross-referencing."
    )

    return ConfluenceInspectResponse(
        confluence_id=conf.confluence_id,
        development_id=conf.development_id,
        development_title=dev_title or "Unassigned Development",
        score=score if signal_types else 0.0,
        label=f"{conf.confluence_type.capitalize()} Confluence ({independent_count} Independent Sources)",
        confluence_type=conf.confluence_type,
        window_hours=48,
        distinct_sources_count=independent_count,
        score_breakdown=breakdown,
        reasoning=reasoning,
        sources=evidence_sources,
        detected_at=conf.created_at,
    )


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
        bucket = status.strip().upper()
        if bucket in ("SATISFIED", "SUPPRESSED"):
            # Stored lifecycle values are lowercase.
            query = query.where(WatchItem.status == bucket.lower())
        elif bucket in ("OVERDUE", "DUE", "WITHIN_WINDOW"):
            # Computed buckets never exist as stored status values; translate them
            # into date-window comparisons mirroring the per-row computation below:
            #   overdue_days = max(0, age_days - window), window defaults to 90,
            #   OVERDUE when overdue_days > 30, DUE when 0 < overdue_days <= 30.
            age_days = func.extract("epoch", func.now() - WatchItem.created_at) / 86400.0
            window_days = func.coalesce(WatchItem.monitoring_window_days, 90)
            overdue_days = func.greatest(age_days - window_days, 0.0)
            query = query.where(WatchItem.status.notin_(("satisfied", "suppressed")))
            if bucket == "OVERDUE":
                query = query.where(overdue_days > 30)
            elif bucket == "DUE":
                query = query.where(overdue_days > 0, overdue_days <= 30)
            else:  # WITHIN_WINDOW
                query = query.where(overdue_days <= 0)
        else:
            # Unknown value: fall back to exact stored-status match so garbage
            # input still returns an empty result set instead of everything.
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


async def _compute_review_time_metrics(db: AsyncSession, fn: str):
    """Computes real dual review-time metrics from Signal and AuditLog records."""
    signals_res = await db.execute(
        select(Signal).where(
            Signal.relevant_function == fn,
            Signal.review_status.in_(["REVIEWED", "ACTION_REQUIRED", "ACTIONED", "DISMISSED"])
        )
    )
    signals = signals_res.scalars().all()
    if not signals:
        return None, None

    first_review_deltas = []
    final_decision_deltas = []

    for s in signals:
        if s.reviewed_at and s.published_at:
            delta_h = max(0.1, (s.reviewed_at - s.published_at).total_seconds() / 3600.0)
            first_review_deltas.append(delta_h)
            if s.review_status in ("ACTIONED", "DISMISSED"):
                final_decision_deltas.append(delta_h)

    avg_first = round(sum(first_review_deltas) / len(first_review_deltas), 1) if first_review_deltas else None
    avg_final = round(sum(final_decision_deltas) / len(final_decision_deltas), 1) if final_decision_deltas else None
    return avg_first, avg_final


@router.get("/function-stats/{function_id}", response_model=FunctionStatsResponse)
async def get_function_stats(function_id: str, db: AsyncSession = Depends(get_db)):
    """Computes comprehensive operational metrics, dual review-time metrics, and recent decisions for a function workspace."""
    from app.api.v1.endpoints.signals import _serialize_signal

    fn = function_id.upper().strip()

    unreviewed = (await db.execute(
        select(func.count(Signal.signal_id)).where(Signal.relevant_function == fn, Signal.review_status == "UNREVIEWED")
    )).scalar() or 0

    in_review = (await db.execute(
        select(func.count(Signal.signal_id)).where(Signal.relevant_function == fn, Signal.review_status == "IN_REVIEW")
    )).scalar() or 0

    escalations = (await db.execute(
        select(func.count(Signal.signal_id)).where(
            Signal.relevant_function == fn,
            Signal.is_escalated == True,
            Signal.review_status.notin_(["ACTIONED", "DISMISSED"])
        )
    )).scalar() or 0

    t_first_review, t_final_decision = await _compute_review_time_metrics(db, fn)

    recent_signals = (await db.execute(
        select(Signal)
        .where(Signal.relevant_function == fn, Signal.review_status.in_(["ACTIONED", "DISMISSED", "REVIEWED"]))
        .order_by(Signal.reviewed_at.desc())
        .limit(10)
    )).scalars().all()

    return FunctionStatsResponse(
        function_id=fn,
        unreviewed_count=unreviewed,
        in_review_count=in_review,
        escalation_count=escalations,
        total_decisions=len(recent_signals),
        time_to_first_review_hours=t_first_review,
        time_to_final_decision_hours=t_final_decision,
        recent_decisions=[_serialize_signal(s) for s in recent_signals],
    )


@router.get("/calibration/status", response_model=CalibrationStatusResponse)
async def get_calibration_status(db: AsyncSession = Depends(get_db)):
    """Returns structured per-function calibration state across all 6 stakeholder functions."""
    canonical_functions = [
        ("MEDICAL_AFFAIRS", "calibrated"),
        ("REGULATORY", "calibrated"),
        ("SAFETY", "calibrated"),
        ("MARKET_ACCESS", "insufficient_data"),
        ("COMMUNICATIONS", "insufficient_data"),
        ("LEADERSHIP", "not_applicable"),
    ]

    profiles = []
    total_samples = 0

    for fn_name, default_status in canonical_functions:
        # Check actual database feedback count
        db_count_res = await db.execute(
            select(func.count(CalibrationFeedback.feedback_id)).where(
                CalibrationFeedback.stakeholder_function == fn_name
            )
        )
        real_count = db_count_res.scalar() or 0
        effective_count = int(real_count)
        total_samples += effective_count

        status = default_status
        if fn_name == "LEADERSHIP":
            status = "not_applicable"
        elif effective_count >= 20:
            status = "calibrated"
        else:
            status = "insufficient_data"

        profiles.append(
            FunctionCalibrationProfile(
                function_name=fn_name,
                status=status,
                feedback_sample_count=effective_count,
                min_required_samples=20,
                brier_score=None,
                ece_score=None,
                reliability_curve=[],
            )
        )

    return CalibrationStatusResponse(
        profiles=profiles,
        total_feedback_samples=total_samples,
        last_calibration_timestamp=None,
    )


@router.get("/leadership/summary", response_model=LeadershipSummaryResponse)
async def get_leadership_summary(
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Provides executive leadership overview with cross-functional backlogs, pending escalations, and critical unreviewed signals."""
    from app.api.v1.endpoints.signals import _serialize_signal

    if current_user and current_user.role not in {"LEADERSHIP", "ADMIN"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Leadership view restricted to Executive and Admin roles.",
        )

    escalated = (await db.execute(
        select(Signal).where(Signal.is_escalated == True, Signal.review_status.notin_(["ACTIONED", "DISMISSED"]))
    )).scalars().all()

    critical_unreviewed = (await db.execute(
        select(Signal).where(Signal.priority == "CRITICAL", Signal.review_status == "UNREVIEWED")
    )).scalars().all()

    # Per-function backlog counts
    all_fns = ["MEDICAL_AFFAIRS", "REGULATORY", "SAFETY", "MARKET_ACCESS", "COMMUNICATIONS", "LEADERSHIP"]
    per_fn_counts: Dict[str, Dict[str, int]] = {}

    for fn in all_fns:
        unrev = (await db.execute(
            select(func.count(Signal.signal_id)).where(Signal.relevant_function == fn, Signal.review_status == "UNREVIEWED")
        )).scalar() or 0
        in_rev = (await db.execute(
            select(func.count(Signal.signal_id)).where(Signal.relevant_function == fn, Signal.review_status == "IN_REVIEW")
        )).scalar() or 0
        esc = (await db.execute(
            select(func.count(Signal.signal_id)).where(
                Signal.relevant_function == fn,
                Signal.is_escalated == True,
                Signal.review_status.notin_(["ACTIONED", "DISMISSED"])
            )
        )).scalar() or 0
        per_fn_counts[fn] = {
            "unreviewed": unrev,
            "in_review": in_rev,
            "escalated": esc,
        }

    total_open = sum(c["unreviewed"] + c["in_review"] for c in per_fn_counts.values())

    return LeadershipSummaryResponse(
        pending_escalations=[_serialize_signal(s) for s in escalated],
        critical_unreviewed=[_serialize_signal(s) for s in critical_unreviewed],
        per_function_counts=per_fn_counts,
        total_open_signals=total_open,
    )

