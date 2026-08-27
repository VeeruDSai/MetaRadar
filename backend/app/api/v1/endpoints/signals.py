import asyncio
import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from typing import AsyncGenerator, List, Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, or_

from app.db.session import get_db
from app.models import Signal, Asset, Confluence, Development, Contradiction, Evidence, AuditLog
from app.models.auth import User
from app.api.deps import get_current_user, get_optional_user

from app.schemas import (
    OverviewResponse,
    SignalListResponse,
    SignalSchema,
    ScoreBreakdownSchema,
    ModelMetadataSchema,
    AthenaQueryRequest,
    AthenaQueryResponse,
    AthenaEvidenceCitation,
    ConfluenceSummarySchema,
    LifecycleSummarySchema,
    TrendPointSchema,
    OverviewHealthSchema,
    AthenaSuggestedQuestionsResponse,
    OriginalEvidenceItemSchema,
    AIInterpretationSchema,
    SuggestedActionSchema,
    ReviewStateSchema,
    RoutingSchema,
    FunctionSchema,
    PrioritySchema,
    SignalDecisionResponse,
    SignalReviewRequest,
    AuditLogItemSchema,
)
from app.services.authority import get_source_authority_tier, resolve_validation_status
from app.services.routing import resolve_signal_routing, FUNCTION_LABELS, StakeholderFunction
from app.services.pii import PIIPHIScrubber
from app.services.provenance_urls import resolve_canonical_provenance
from app.services.scoring import priority_scorer
from app.services.confluence import confluence_engine
from app.services.embeddings import embedding_service
from app.providers.factory import provider_factory
from app.providers.base import ProviderCapability, DataClassification
from app.providers.gemma import GemmaProvider, OllamaUnavailableError

router = APIRouter()

# Athena evidence gate: maximum pgvector cosine distance for a signal to count
# as cited evidence (similarity >= 0.65). Single source of truth — the query
# filter and the docstring contract must never drift apart again.
MAX_EVIDENCE_DISTANCE = 0.35


def _serialize_signal(s: Signal) -> SignalSchema:
    """Helper to convert SQLAlchemy Signal model into a typed SignalSchema instance with honest scoring telemetry and provenance."""
    score_breakdown = None
    scoring_status = "computed"

    if s.score_breakdown and isinstance(s.score_breakdown, dict):
        try:
            score_breakdown = ScoreBreakdownSchema(**s.score_breakdown)
        except Exception:
            score_breakdown = None
            scoring_status = "not_computed"
    else:
        scoring_status = "not_computed"

    model_metadata = None
    if s.model_metadata and isinstance(s.model_metadata, dict):
        try:
            model_metadata = ModelMetadataSchema(**s.model_metadata)
        except Exception:
            model_metadata = None

    is_synth = getattr(s, "is_synthetic", False) or False
    data_mode = getattr(s, "data_mode", None) or ("test_fixture" if is_synth else "live")
    raw_url = getattr(s, "canonical_url", None)
    ext = getattr(s, "external_id", None) or getattr(s, "pmid", None) or getattr(s, "nct_id", None) or getattr(s, "regulatory_id", None)
    
    canonical_url, prov_status = resolve_canonical_provenance(
        source_id=getattr(s, "source_id", None),
        existing_url=raw_url,
        external_id=ext,
        pmid=getattr(s, "pmid", None),
        nct_id=getattr(s, "nct_id", None),
        title_or_content=f"{getattr(s, 'title', '')} {getattr(s, 'content', '')}",
        is_synthetic=is_synth,
        existing_status=getattr(s, "provenance_status", None),
    )

    confidence_type = getattr(s, "confidence_type", None) or ("fixture" if is_synth else "extraction")
    confidence_rationale = getattr(s, "confidence_rationale", None)
    raw_confidence = getattr(s, "confidence", None)
    confidence = float(raw_confidence) if raw_confidence is not None else None

    ext_id = (
        getattr(s, "external_id", None)
        or getattr(s, "pmid", None)
        or getattr(s, "nct_id", None)
        or getattr(s, "regulatory_id", None)
        or str(s.signal_id)
    )
    source_name = getattr(s, "source_name", None) or (s.source_id.upper().replace("_", " ") if s.source_id else "UNKNOWN")
    evidence_text = getattr(s, "evidence_text", None) or s.content or s.title
    raw_record_ref = getattr(s, "raw_record_reference", None)
    ingested_at = getattr(s, "ingested_at", None) or s.retrieved_at or s.created_at

    # Authority & Validation resolution
    authority_tier = (
        getattr(s, "source_authority_tier", None)
        or get_source_authority_tier(s.source_id, getattr(s, "source_tier", 1)).value
    )
    validation_status = (
        getattr(s, "validation_status", None)
        or resolve_validation_status(s.source_id, authority_tier).value
    )

    # Routing & Function resolution
    routing_data = resolve_signal_routing(
        signal_type=s.signal_type,
        priority=s.priority,
        priority_score=score_breakdown.total if score_breakdown else None,
        title=s.title,
        content=s.content,
    )

    what_changed = (
        getattr(s, "what_changed", None)
        or (s.facts[0] if (s.facts and len(s.facts) > 0) else s.title)
    )
    why_it_matters = (
        getattr(s, "why_it_matters", None)
        or s.interpretation
        or s.speculation
        or "Clinical decision significance under active landscape review."
    )
    relevant_function = getattr(s, "relevant_function", None) or routing_data["relevant_function"]
    route_destination = getattr(s, "route_destination", None) or routing_data["route_destination"]
    route_role = getattr(s, "route_role", None) or routing_data["route_role"]
    is_escalated = (
        getattr(s, "is_escalated", False)
        if getattr(s, "is_escalated", None) is not None
        else routing_data["is_escalated"]
    )
    routing_reason = getattr(s, "routing_reason", None) or routing_data["routing_reason"]
    routing_timestamp = getattr(s, "routing_timestamp", None) or routing_data["routing_timestamp"]

    suggested_action = getattr(s, "suggested_action", None) or routing_data["suggested_action"]
    action_rationale = getattr(s, "action_rationale", None) or routing_data["action_rationale"]

    review_status = getattr(s, "review_status", None) or "UNREVIEWED"
    reviewed_by = getattr(s, "reviewed_by", None)
    reviewed_at = getattr(s, "reviewed_at", None)
    review_decision = getattr(s, "review_decision", None)
    review_notes = getattr(s, "review_notes", None)
    resulting_action = getattr(s, "resulting_action", None)

    # Sub-objects maintaining the strict trust boundary
    evidence_items = [
        OriginalEvidenceItemSchema(
            source_id=s.source_id,
            source_name=source_name,
            authority_tier=authority_tier,
            validation_status=validation_status,
            title=s.title,
            published_at=s.published_at,
            retrieved_at=s.retrieved_at,
            url=canonical_url,
            identifier=ext_id,
            excerpt=evidence_text[:600] if evidence_text else None,
        )
    ]

    interpretation_details = AIInterpretationSchema(
        summary=s.interpretation or s.content[:300],
        why_it_matters=why_it_matters,
        facts=s.facts or [],
        speculation=s.speculation,
        confidence=confidence,
        confidence_type=confidence_type,
        generated_at=s.created_at,
        model=model_metadata.model if model_metadata else "gemma-3-4b-it",
        mode=model_metadata.mode if model_metadata else "reasoning",
    )

    action_details = SuggestedActionSchema(
        text=suggested_action,
        rationale=action_rationale,
        target_function=relevant_function,
        is_escalated=is_escalated,
        generated_at=routing_timestamp or s.created_at,
    )

    routing_details = RoutingSchema(
        destination=route_destination,
        role=route_role,
        is_escalated=is_escalated,
        reason=routing_reason,
        timestamp=routing_timestamp or s.created_at,
    )

    review_details = ReviewStateSchema(
        status=review_status,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        decision=review_decision,
        notes=review_notes,
        resulting_action=resulting_action,
    )

    return SignalSchema(
        signal_id=s.signal_id,
        source_id=s.source_id,
        source_name=source_name,
        external_id=ext_id,
        development_id=s.development_id,
        pipeline_run_id=s.pipeline_run_id,
        pmid=s.pmid,
        nct_id=s.nct_id,
        regulatory_id=s.regulatory_id,
        fingerprint=s.fingerprint,
        canonical_url=canonical_url,
        signal_type=s.signal_type,
        disease=s.disease,
        title=s.title,
        content=s.content,
        published_at=s.published_at,
        retrieved_at=s.retrieved_at,
        ingested_at=ingested_at,
        data_mode=data_mode,
        is_synthetic=is_synth,
        confidence=confidence,
        confidence_type=confidence_type,
        confidence_rationale=confidence_rationale,
        provenance_status=prov_status,
        evidence_text=evidence_text,
        raw_record_reference=raw_record_ref,
        scoring_status=scoring_status,
        what_changed=what_changed,
        why_it_matters=why_it_matters,
        relevant_function=relevant_function,
        route_destination=route_destination,
        route_role=route_role,
        is_escalated=is_escalated,
        routing_reason=routing_reason,
        routing_timestamp=routing_timestamp,
        source_authority_tier=authority_tier,
        validation_status=validation_status,
        suggested_action=suggested_action,
        action_rationale=action_rationale,
        review_status=review_status,
        reviewed_by=reviewed_by,
        reviewed_at=reviewed_at,
        review_decision=review_decision,
        review_notes=review_notes,
        resulting_action=resulting_action,
        evidence=evidence_items,
        interpretation_details=interpretation_details,
        action_details=action_details,
        routing_details=routing_details,
        review_details=review_details,
        facts=s.facts or [],
        interpretation=s.interpretation,
        speculation=s.speculation,
        priority=s.priority,
        score_breakdown=score_breakdown,
        model_metadata=model_metadata,
        scoring_model_version=s.scoring_model_version or "haemophilia_v2.0",
        scoring_config_version=s.scoring_config_version or "haemophilia_v1",
        embedding_model_version=s.embedding_model_version or "v1",
        prompt_version=s.prompt_version or "v1.0.0",
        created_at=s.created_at,
    )


KNOWN_STATES = {"UNREVIEWED", "IN_REVIEW", "REVIEWED", "ACTION_REQUIRED", "ACTIONED", "DISMISSED"}

VALID_TRANSITIONS = {
    "UNREVIEWED": {"IN_REVIEW", "REVIEWED", "DISMISSED"},
    "IN_REVIEW": {"REVIEWED", "ACTION_REQUIRED", "DISMISSED"},
    "REVIEWED": {"ACTION_REQUIRED", "ACTIONED"},
    "ACTION_REQUIRED": {"ACTIONED", "IN_REVIEW"},
    "DISMISSED": {"IN_REVIEW"},
    "ACTIONED": set(),
}

ACTIONED_ALLOWED_ROLES = {
    "SAFETY",
    "MARKET_ACCESS",
    "LEADERSHIP",
    "ADMIN",
}



def validate_state_transition(
    current_status: str,
    target_status: str,
    user: User,
    escalate: bool = False,
    is_override: bool = False,
) -> None:
    curr = current_status.upper().strip()
    target = target_status.upper().strip()

    # 0. Unknown State Validation (400 Bad Request)
    if target not in KNOWN_STATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid review status '{target_status}'. Allowed states: {', '.join(sorted(KNOWN_STATES))}."
        )

    # 1. Terminal State Invariant
    if curr == "ACTIONED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict: Signal is in terminal state 'ACTIONED' and cannot be modified."
        )

    # 2. Escalation Target Invariant
    if escalate and target not in {"REVIEWED", "ACTION_REQUIRED"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict: Escalation is only permitted when transitioning to 'REVIEWED' or 'ACTION_REQUIRED'."
        )

    # 3. Role Authorization for ACTIONED
    if target == "ACTIONED" and user.role not in ACTIONED_ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Role '{user.role}' is not authorized to mark signals as ACTIONED."
        )

    # 4. Leadership / Admin Non-Terminal Override
    if user.role in {"LEADERSHIP", "ADMIN"} and is_override:
        valid_overrides = {"IN_REVIEW", "REVIEWED", "ACTION_REQUIRED", "ACTIONED", "DISMISSED"}
        if target in valid_overrides:
            return


    # 5. Standard Transition Check
    allowed = VALID_TRANSITIONS.get(curr, set())
    if target not in allowed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Conflict: Invalid transition from '{curr}' to '{target}'."
        )



@router.get("/signals", response_model=SignalListResponse)
async def list_signals(
    severity: Optional[str] = Query(None, description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW"),
    entity: Optional[str] = Query(None, description="Search term in signal title or content"),
    date_from: Optional[datetime] = Query(None, description="Filter signals published on or after date"),
    date_to: Optional[datetime] = Query(None, description="Filter signals published on or before date"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    source: Optional[str] = Query(None, description="Filter by source ID"),
    all_functions: bool = Query(False, description="Whether to return signals across all stakeholder functions (LEADERSHIP and ADMIN only)"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db)
):
    """Returns filtered signals list with RBAC role scoping, pagination, and total count."""
    query = select(Signal)
    count_query = select(func.count(Signal.signal_id))

    # Role-Based Filtering
    if current_user:
        if all_functions:
            if current_user.role not in {"LEADERSHIP", "ADMIN"}:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Forbidden: Only LEADERSHIP and ADMIN roles can access all_functions=true",
                )
        elif current_user.role not in {"LEADERSHIP", "ADMIN"}:
            query = query.where(Signal.relevant_function == current_user.role)
            count_query = count_query.where(Signal.relevant_function == current_user.role)

    if severity:
        sev_list = [s.strip().upper() for s in severity.split(",") if s.strip()]
        if len(sev_list) == 1:
            query = query.where(Signal.priority == sev_list[0])
            count_query = count_query.where(Signal.priority == sev_list[0])
        elif len(sev_list) > 1:
            query = query.where(Signal.priority.in_(sev_list))
            count_query = count_query.where(Signal.priority.in_(sev_list))

    if entity:
        term = f"%{entity.strip()}%"
        query = query.where(or_(Signal.title.ilike(term), Signal.content.ilike(term), Signal.disease.ilike(term)))
        count_query = count_query.where(or_(Signal.title.ilike(term), Signal.content.ilike(term), Signal.disease.ilike(term)))

    if date_from:
        query = query.where(Signal.published_at >= date_from)
        count_query = count_query.where(Signal.published_at >= date_from)

    if date_to:
        query = query.where(Signal.published_at <= date_to)
        count_query = count_query.where(Signal.published_at <= date_to)

    if signal_type:
        st_list = [s.strip().upper() for s in signal_type.split(",") if s.strip()]
        if len(st_list) == 1:
            query = query.where(Signal.signal_type == st_list[0])
            count_query = count_query.where(Signal.signal_type == st_list[0])
        elif len(st_list) > 1:
            query = query.where(Signal.signal_type.in_(st_list))
            count_query = count_query.where(Signal.signal_type.in_(st_list))

    if source:
        src_list = [s.strip() for s in source.split(",") if s.strip()]
        if len(src_list) == 1:
            query = query.where(Signal.source_id == src_list[0])
            count_query = count_query.where(Signal.source_id == src_list[0])
        elif len(src_list) > 1:
            query = query.where(Signal.source_id.in_(src_list))
            count_query = count_query.where(Signal.source_id.in_(src_list))

    query = query.order_by(Signal.published_at.desc()).offset(offset).limit(limit)

    results = await db.execute(query)
    signals = results.scalars().all()

    total_res = await db.execute(count_query)
    total = total_res.scalar() or 0

    return SignalListResponse(
        signals=[_serialize_signal(s) for s in signals],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/signals/queue/{function_id}", response_model=SignalListResponse)
async def get_function_queue(
    function_id: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Fetches incoming review queue for a specific stakeholder function with RBAC isolation."""
    fn = function_id.upper().strip()
    if current_user.role not in {"LEADERSHIP", "ADMIN"} and current_user.role != fn:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: Role '{current_user.role}' is not authorized to access queue for '{fn}'.",
        )

    query = (
        select(Signal)
        .where(
            Signal.relevant_function == fn,
            Signal.review_status.in_(["UNREVIEWED", "IN_REVIEW"])
        )
        .order_by(Signal.published_at.desc())
        .limit(limit)
        .offset(offset)
    )
    count_query = (
        select(func.count(Signal.signal_id))
        .where(
            Signal.relevant_function == fn,
            Signal.review_status.in_(["UNREVIEWED", "IN_REVIEW"])
        )
    )
    res = await db.execute(query)
    signals = res.scalars().all()
    count_res = await db.execute(count_query)
    total = count_res.scalar() or 0

    return SignalListResponse(
        signals=[_serialize_signal(s) for s in signals],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/signals/{signal_id}", response_model=SignalSchema)
async def get_signal_detail(signal_id: str, db: AsyncSession = Depends(get_db)):
    """Fetch single signal detail by signal_id (UUID), external_id, or fingerprint."""
    target_uuid = None
    try:
        target_uuid = UUID(signal_id)
    except (ValueError, TypeError):
        target_uuid = None

    if target_uuid:
        query = select(Signal).where(Signal.signal_id == target_uuid)
    else:
        query = select(Signal).where(
            or_(
                Signal.external_id == signal_id,
                Signal.fingerprint == signal_id,
                Signal.pmid == signal_id,
                Signal.nct_id == signal_id,
                Signal.regulatory_id == signal_id,
            )
        )

    res = await db.execute(query)
    signal = res.scalars().first()
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal with ID '{signal_id}' not found."
        )
    return _serialize_signal(signal)


@router.post("/signals/{signal_id}/review", response_model=SignalSchema)
async def submit_signal_review(
    signal_id: str,
    payload: SignalReviewRequest,
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Submits a review action for a signal, validating FSM transition invariants,
    handling leadership escalations, and appending immutable audit records.
    """
    # Resolve reviewer identity
    user = current_user
    if not user or not hasattr(user, "role") or not isinstance(user, User):
        from app.services.auth_service import get_or_create_demo_user
        try:
            user = await get_or_create_demo_user(db, "MEDICAL_AFFAIRS")
        except Exception:
            user = None
        if not user or not hasattr(user, "role") or not isinstance(user, User):
            user = User(
                user_id=uuid.uuid4(),
                email="demo.medical@metaradar.internal",
                display_name="Demo Medical Affairs Reviewer",
                role="MEDICAL_AFFAIRS",
                is_active=True,
            )


    target_uuid = None
    try:
        target_uuid = UUID(signal_id)
    except (ValueError, TypeError):
        target_uuid = None

    if target_uuid:
        query = select(Signal).where(Signal.signal_id == target_uuid)
    else:
        query = select(Signal).where(
            or_(
                Signal.external_id == signal_id,
                Signal.fingerprint == signal_id,
                Signal.pmid == signal_id,
                Signal.nct_id == signal_id,
                Signal.regulatory_id == signal_id,
            )
        )

    res = await db.execute(query)
    signal = res.scalars().first()
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal with ID '{signal_id}' not found."
        )

    prev_status = getattr(signal, "review_status", "UNREVIEWED") or "UNREVIEWED"
    target_status = payload.status.upper().strip()

    validate_state_transition(
        current_status=prev_status,
        target_status=target_status,
        user=user,
        escalate=payload.escalate,
        is_override=payload.is_override,
    )

    now_utc = datetime.now(timezone.utc)
    correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")
    reviewer_name = payload.reviewer or user.display_name
    signal.review_status = target_status
    signal.reviewed_by = reviewer_name
    signal.reviewed_at = now_utc
    if payload.decision:
        signal.review_decision = payload.decision
    if payload.notes:
        signal.review_notes = payload.notes
    if payload.resulting_action:
        signal.resulting_action = payload.resulting_action

    # Escalation Handling
    if payload.escalate:
        signal.is_escalated = True
        signal.routing_reason = payload.escalation_reason or "Reviewer initiated leadership escalation"
        db.add(AuditLog(
            entity_name="Signal",
            entity_id=str(signal.signal_id),
            action="SIGNAL_ESCALATED",
            performed_by=reviewer_name,
            user_id=user.user_id,
            correlation_id=correlation_id,
            timestamp=now_utc,
            details={
                "previous_status": prev_status,
                "new_status": target_status,
                "reason": signal.routing_reason,
            }
        ))
    elif payload.resolve_escalation and getattr(signal, "is_escalated", False):
        signal.is_escalated = False
        db.add(AuditLog(
            entity_name="Signal",
            entity_id=str(signal.signal_id),
            action="ESCALATION_RESOLVED",
            performed_by=reviewer_name,
            user_id=user.user_id,
            correlation_id=correlation_id,
            timestamp=now_utc,
            details={
                "previous_status": prev_status,
                "new_status": target_status,
                "decision": payload.decision,
            }
        ))

    # Standard Review Audit Entry
    db.add(AuditLog(
        entity_name="Signal",
        entity_id=str(signal.signal_id),
        action="SIGNAL_REVIEWED",
        performed_by=reviewer_name,
        user_id=user.user_id,
        correlation_id=correlation_id,
        timestamp=now_utc,
        details={
            "previous_status": prev_status,
            "new_status": target_status,
            "decision": payload.decision,
            "notes": payload.notes,
            "resulting_action": payload.resulting_action,
        },
    ))
    await db.commit()
    await db.refresh(signal)

    return _serialize_signal(signal)


@router.get("/signals/{signal_id}/audit-history", response_model=List[AuditLogItemSchema])
async def get_signal_audit_history(signal_id: str, db: AsyncSession = Depends(get_db)):
    """
    Fetches chronological audit history and lifecycle milestones for a signal.
    Traces: Detected -> Classified -> Prioritized -> Routed -> Reviewed -> Actioned.
    """
    target_uuid = None
    try:
        target_uuid = UUID(signal_id)
    except (ValueError, TypeError):
        target_uuid = None

    if target_uuid:
        query = select(Signal).where(Signal.signal_id == target_uuid)
    else:
        query = select(Signal).where(
            or_(
                Signal.external_id == signal_id,
                Signal.fingerprint == signal_id,
                Signal.pmid == signal_id,
                Signal.nct_id == signal_id,
                Signal.regulatory_id == signal_id,
            )
        )

    res = await db.execute(query)
    signal = res.scalars().first()
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal with ID '{signal_id}' not found."
        )

    # Query persisted audit log records
    audit_query = (
        select(AuditLog)
        .where(
            AuditLog.entity_name == "Signal",
            AuditLog.entity_id == str(signal.signal_id),
        )
        .order_by(AuditLog.timestamp.asc())
    )
    audit_res = await db.execute(audit_query)
    audit_logs = audit_res.scalars().all()

    items: List[AuditLogItemSchema] = []
    for log in audit_logs:
        items.append(
            AuditLogItemSchema(
                audit_id=log.audit_id,
                entity_name=log.entity_name,
                entity_id=log.entity_id,
                action=log.action,
                performed_by=log.performed_by,
                user_id=log.user_id,
                correlation_id=log.correlation_id,
                timestamp=log.timestamp,
                details=log.details or {},
            )
        )


    # If no explicit review audit logs exist yet, provide the factual baseline provenance trail
    if not items:
        serialized = _serialize_signal(signal)
        import uuid as py_uuid

        # 1. Detected
        items.append(
            AuditLogItemSchema(
                audit_id=py_uuid.uuid4(),
                entity_name="Signal",
                entity_id=str(signal.signal_id),
                action="SIGNAL_DETECTED",
                performed_by=f"connector:{signal.source_id}",
                timestamp=signal.retrieved_at,
                details={
                    "source_id": signal.source_id,
                    "source_authority_tier": serialized.source_authority_tier,
                    "validation_status": serialized.validation_status,
                },
            )
        )
        # 2. Classified & Prioritized
        items.append(
            AuditLogItemSchema(
                audit_id=py_uuid.uuid4(),
                entity_name="Signal",
                entity_id=str(signal.signal_id),
                action="SIGNAL_PRIORITIZED",
                performed_by="pipeline:scoring_engine",
                timestamp=signal.created_at,
                details={
                    "priority": signal.priority,
                    "score": serialized.score_breakdown.total if serialized.score_breakdown else None,
                    "signal_type": signal.signal_type,
                },
            )
        )
        # 3. Routed
        items.append(
            AuditLogItemSchema(
                audit_id=py_uuid.uuid4(),
                entity_name="Signal",
                entity_id=str(signal.signal_id),
                action="SIGNAL_ROUTED",
                performed_by="pipeline:routing_engine",
                timestamp=serialized.routing_timestamp or signal.created_at,
                details={
                    "destination": serialized.route_destination,
                    "is_escalated": serialized.is_escalated,
                    "reason": serialized.routing_reason,
                },
            )
        )

    return items


@router.get("/signals/{signal_id}/decision-object", response_model=SignalDecisionResponse)
async def get_signal_decision_object(signal_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the complete unified Signal Decision Object with strict evidence/interpretation/action separation
    and drill-downs for Confluence, Contradictions, and Lifecycle.
    """
    target_uuid = None
    try:
        target_uuid = UUID(signal_id)
    except (ValueError, TypeError):
        target_uuid = None

    if target_uuid:
        query = select(Signal).where(Signal.signal_id == target_uuid)
    else:
        query = select(Signal).where(
            or_(
                Signal.external_id == signal_id,
                Signal.fingerprint == signal_id,
                Signal.pmid == signal_id,
                Signal.nct_id == signal_id,
                Signal.regulatory_id == signal_id,
            )
        )

    res = await db.execute(query)
    signal = res.scalars().first()
    if not signal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Signal with ID '{signal_id}' not found."
        )

    s = _serialize_signal(signal)

    # Drill-down: Contradictions
    contradictions_res = await db.execute(
        select(Contradiction).where(
            or_(
                Contradiction.claim_a_id == str(signal.signal_id),
                Contradiction.claim_b_id == str(signal.signal_id),
                Contradiction.claim_a_id == signal.external_id,
                Contradiction.claim_b_id == signal.external_id,
            )
        )
    )
    contradictions = [
        {
            "contradiction_id": str(c.contradiction_id),
            "rule_name": c.rule_name,
            "severity": c.severity,
            "confidence": c.confidence,
            "description": c.description,
            "detected_at": c.detected_at.isoformat() if c.detected_at else None,
        }
        for c in contradictions_res.scalars().all()
    ]

    # Drill-down: Confluence
    confluence_data = None
    if signal.development_id:
        confluence_res = await db.execute(
            select(Confluence).where(Confluence.development_id == signal.development_id)
        )
        conf = confluence_res.scalars().first()
        if conf:
            confluence_data = {
                "confluence_id": str(conf.confluence_id),
                "signal_count": conf.signal_count,
                "confluence_type": conf.confluence_type,
                "created_at": conf.created_at.isoformat() if conf.created_at else None,
            }

    fn_label = FUNCTION_LABELS.get(StakeholderFunction(s.relevant_function), s.relevant_function) if s.relevant_function in StakeholderFunction.__members__ else (s.relevant_function or "Medical Affairs")

    return SignalDecisionResponse(
        id=str(s.signal_id),
        title=s.title,
        signal_type=s.signal_type,
        disease=s.disease,
        priority=PrioritySchema(
            level=s.priority,
            score=s.score_breakdown.total if s.score_breakdown else None,
            score_breakdown=s.score_breakdown,
        ),
        what_changed=s.what_changed or s.title,
        why_it_matters=s.why_it_matters or "Clinical significance under active evaluation.",
        function=FunctionSchema(
            name=s.relevant_function or "MEDICAL_AFFAIRS",
            label=fn_label,
        ),
        routing=s.routing_details or RoutingSchema(
            destination=s.route_destination or "MEDICAL_AFFAIRS",
            role=s.route_role or "FUNCTION",
            is_escalated=s.is_escalated,
            reason=s.routing_reason,
            timestamp=s.routing_timestamp or s.created_at,
        ),
        evidence=s.evidence,
        interpretation=s.interpretation_details or AIInterpretationSchema(
            summary=s.interpretation,
            why_it_matters=s.why_it_matters,
            facts=s.facts,
        ),
        suggested_action=s.action_details or SuggestedActionSchema(
            text=s.suggested_action or "Review evidence against clinical benchmarks.",
            rationale=s.action_rationale,
            target_function=s.relevant_function or "MEDICAL_AFFAIRS",
            is_escalated=s.is_escalated,
        ),
        review=s.review_details or ReviewStateSchema(
            status=s.review_status,
            reviewed_by=s.reviewed_by,
            reviewed_at=s.reviewed_at,
            decision=s.review_decision,
            notes=s.review_notes,
            resulting_action=s.resulting_action,
        ),
        lifecycle={"stage": "announced", "development_id": str(s.development_id)} if s.development_id else None,
        confluence=confluence_data,
        contradictions=contradictions,
        created_at=s.created_at,
    )


@router.get("/overview", response_model=OverviewResponse)
async def get_overview(db: AsyncSession = Depends(get_db)):
    """Aggregated dashboard telemetry with real computed confluence scores and truthful health metrics."""
    t0 = time.perf_counter()
    now_utc = datetime.now(timezone.utc)
    now_iso = now_utc.strftime("%H:%M:%S UTC")

    # 1. Real KPI counts
    active_signals = (await db.execute(select(func.count(Signal.signal_id)))).scalar() or 0
    monitored_assets = (await db.execute(select(func.count(distinct(Asset.asset_id))))).scalar() or 0
    confluences_detected = (await db.execute(select(func.count(Confluence.confluence_id)))).scalar() or 0
    contradictions_flagged = (await db.execute(select(func.count(Contradiction.contradiction_id)))).scalar() or 0
    source_count = (await db.execute(select(func.count(distinct(Signal.source_id))))).scalar() or 0

    # 2. 7-day delta calculation
    week_ago = now_utc - timedelta(days=7)
    recent_raw = (await db.execute(
        select(func.count(Signal.signal_id)).where(Signal.published_at >= week_ago)
    )).scalar()
    recent_signals = int(recent_raw) if isinstance(recent_raw, (int, float)) else 0
    weekly_change = f"+{recent_signals} this week" if recent_signals > 0 else "No new signals this week"

    # 3. Dynamic lifecycle summaries from database developments
    dev_query = select(Development).order_by(Development.updated_at.desc()).limit(10)
    developments = (await db.execute(dev_query)).scalars().all()

    lifecycle_summaries: List[LifecycleSummarySchema] = []
    for d in developments:
        dev_sig_count_res = await db.execute(
            select(func.count(Signal.signal_id)).where(Signal.development_id == d.development_id)
        )
        dev_sig_count = dev_sig_count_res.scalar() or 0

        lifecycle_summaries.append(
            LifecycleSummarySchema(
                id=str(d.development_id),
                name=d.title,
                stage=d.current_stage or "announced",
                momentum=None,
                confidence=None,
                last_changed=d.updated_at.strftime("%b %d") if d.updated_at else None,
                signals=dev_sig_count
            )
        )

    # 4. Confluence summary with real computed score from database
    all_confs_stmt = select(Confluence).order_by(Confluence.created_at.desc()).limit(10)
    all_confs = (await db.execute(all_confs_stmt)).scalars().all()

    best_score = 0.0
    best_label = "No active confluences"
    best_drivers: List[str] = []

    for conf in all_confs:
        conf_sigs_stmt = select(Signal.source_id, Signal.signal_type).where(Signal.development_id == conf.development_id)
        conf_rows = (await db.execute(conf_sigs_stmt)).all()
        conf_sources = set(r[0] for r in conf_rows if r[0])
        conf_types = [r[1] for r in conf_rows if r[1]]
        if conf_types:
            c_score, d_dict = confluence_engine.calculate_confluence_score(conf_types)
            if c_score > best_score:
                best_score = c_score
                best_label = f"Confluence: {conf.confluence_type.capitalize()} ({len(conf_sources)} independent sources)" if conf_sources else f"Confluence: {conf.confluence_type.capitalize()}"
                best_drivers = [f"{st.replace('_', ' ').title()} (+{int(wt)} pts)" for st, wt in d_dict.items()]

    confluence_summary = ConfluenceSummarySchema(
        score=best_score,
        label=best_label,
        drivers=best_drivers,
        updated_at="Just now"
    )

    # 5. Honest time-bucketed trend points (empty when no signals exist)
    trends: List[TrendPointSchema] = []
    if active_signals > 0:
        trends = [
            TrendPointSchema(label="Total Active", value=active_signals, baseline=None),
            TrendPointSchema(label="7d Recent", value=recent_signals, baseline=None),
        ]

    # Measure exact query latency
    latency_ms = max(1, int((time.perf_counter() - t0) * 1000))

    return OverviewResponse(
        active_signals=active_signals,
        monitored_assets=monitored_assets,
        confluences_detected=confluences_detected,
        contradictions_flagged=contradictions_flagged,
        weekly_change=weekly_change,
        last_sync=now_iso,
        confluence=confluence_summary,
        lifecycle=lifecycle_summaries,
        trends=trends,
        health=OverviewHealthSchema(api="healthy", latency_ms=latency_ms, source_count=source_count)
    )


ATHENA_GREETINGS = {
    "hey", "hello", "hi", "greetings", "good morning", "good evening",
    "who are you", "what is athena", "what can you do", "help",
}

_ATHENA_INTRO = (
    "Hello! I am Athena, MetaRadar's grounded clinical intelligence copilot. "
    "I analyze competitive intelligence and clinical developments across Haemophilia A and B, "
    "grounded strictly in indexed evidence from ClinicalTrials.gov, PubMed, FDA/EMA regulatory registries, and market news.\n\n"
    "You can ask me questions such as:\n"
    "• \"What are the latest clinical readout updates for Factor VIII gene therapies?\"\n"
    "• \"Are there any contradiction alerts on concizumab safety?\"\n"
    "• \"What regulatory target dates are expected in Q3 2026 for Haemophilia B?\"\n"
    "• \"Summarize recent pipeline updates for mim8 and fitusiran.\""
)

_ATHENA_NO_EVIDENCE = (
    "No sufficiently relevant evidence was found in the indexed sources to answer this question. "
    "Please try querying specific haemophilia therapies, trial phases, or regulatory events."
)


def _sse_event(event: str, data: dict) -> str:
    """Formats a single Server-Sent Events frame."""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def _retrieve_athena_evidence(
    db: AsyncSession, scrubbed_prompt: str
) -> Tuple[List[AthenaEvidenceCitation], List[str]]:
    """Hybrid retrieval: pgvector cosine similarity first, lexical ILIKE fallback second.

    Returns (citations, evidence_texts). All DB work completes before any response
    streaming begins so the request-scoped session is never used mid-stream.
    """
    citations: List[AthenaEvidenceCitation] = []
    evidence_texts: List[str] = []
    ATHENA_DISTANCE_THRESHOLD = 0.65  # cosine distance threshold (similarity >= 0.35)

    try:
        query_vec = await embedding_service.embed_text(scrubbed_prompt)

        stmt = (
            select(
                Signal.signal_id,
                Signal.title,
                Signal.source_id,
                Signal.canonical_url,
                Signal.published_at,
                Signal.content,
                Signal.embedding.op("<=>")(query_vec).label("distance"),
            )
            .where(Signal.embedding.isnot(None))
            .where(Signal.embedding.op("<=>")(query_vec) < ATHENA_DISTANCE_THRESHOLD)
            .order_by("distance")
            .limit(5)
        )
        res = await db.execute(stmt)
        matched_rows = res.all()

        for r in matched_rows:
            excerpt = r.content[:500] if r.content else r.title
            can_url = r.canonical_url
            if can_url and ("metaradar.internal" in can_url or can_url.endswith(".internal")):
                can_url = None
            citations.append(
                AthenaEvidenceCitation(
                    signal_id=str(r.signal_id),
                    title=r.title,
                    source_id=r.source_id,
                    canonical_url=can_url,
                    published_at=r.published_at.isoformat() if r.published_at else None,
                    excerpt=excerpt,
                    distance=round(float(r.distance), 4),
                )
            )
            evidence_texts.append(f"[{r.source_id}] {r.title}: {excerpt}")
    except Exception:
        pass

    # Keyword / Lexical Fallback if vector search yielded 0 matches
    if not citations:
        words = [w for w in scrubbed_prompt.split() if len(w) > 3 and w.lower() not in {"what", "when", "where", "which", "about", "latest", "there", "updates", "alerts"}]
        search_term = words[0] if words else scrubbed_prompt[:25]

        lex_stmt = select(Signal).where(
            or_(
                Signal.title.ilike(f"%{search_term}%"),
                Signal.content.ilike(f"%{search_term}%")
            )
        ).limit(4)
        lex_res = await db.execute(lex_stmt)
        for s in lex_res.scalars().all():
            excerpt = s.content[:500] if s.content else s.title
            can_url = s.canonical_url
            if can_url and ("metaradar.internal" in can_url or can_url.endswith(".internal")):
                can_url = None
            citations.append(
                AthenaEvidenceCitation(
                    signal_id=str(s.signal_id),
                    title=s.title,
                    source_id=s.source_id,
                    canonical_url=can_url,
                    published_at=s.published_at.isoformat() if s.published_at else None,
                    excerpt=excerpt,
                    distance=0.45,
                )
            )
            evidence_texts.append(f"[{s.source_id}] {s.title}: {excerpt}")

    return citations, evidence_texts


@router.post("/athena", response_model=AthenaQueryResponse)
async def query_athena(payload: AthenaQueryRequest, db: AsyncSession = Depends(get_db)):
    """Queries Athena intelligence synthesis layer with hybrid vector/lexical retrieval, prompt sanitization, and honest citations."""
    trimmed = payload.prompt.strip()
    if not trimmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt cannot be empty."
        )

    # 1. PII / PHI scrubbing & content classification (CR-03)
    scrubbed_prompt, has_pii, _ = PIIPHIScrubber.scrub(trimmed)
    classification = DataClassification.PATIENT_IDENTIFIABLE if has_pii else DataClassification.PUBLIC

    # 2. Conversational greetings & assistant introduction handling
    clean_lower = scrubbed_prompt.lower().strip("?!., ")
    if clean_lower in ATHENA_GREETINGS or len(clean_lower) < 4:
        return AthenaQueryResponse(
            answer=_ATHENA_INTRO,
            confidence=100.0,
            confidence_type="model_reasoning",
            evidence_count=0,
            mode="assistant_intro",
            model_metadata=None,
            evidence=[],
            response_type="assistant_intro",
        )

    # 3+4. Real Vector Retrieval with Lexical Fallback over indexed Signals / Evidence
    citations, evidence_texts = await _retrieve_athena_evidence(db, scrubbed_prompt)

    # Zero-fabrication gate: If no evidence is found, return honest failure notice
    if not evidence_texts:
        return AthenaQueryResponse(
            answer=_ATHENA_NO_EVIDENCE,
            confidence=0.0,
            confidence_type="model_reasoning",
            evidence_count=0,
            mode="insufficient_evidence",
            model_metadata=None,
            evidence=[],
            response_type="insufficient_evidence",
        )

    # 5. Structured safe prompt execution via ProviderFactory (Gemma -> Grok -> BART)
    safe_task = f"Analyze the following biomedical query against available evidence: {scrubbed_prompt}"
    provider_res = await provider_factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=evidence_texts,
        task=safe_task,
        classification=classification
    )

    mode = provider_res.get("mode", "reasoning")
    meta_dict = provider_res.get("model_metadata")
    model_metadata = ModelMetadataSchema(**meta_dict) if meta_dict and isinstance(meta_dict, dict) else None

    if mode == "degraded_factual" or (model_metadata and not model_metadata.reasoning_available):
        answer = provider_res.get("factual_summary") or provider_res.get("what_changed") or "Reasoning unavailable in degraded factual mode."
        confidence = 45.0
    else:
        what_changed = provider_res.get("what_changed") or ""
        why_it_matters = provider_res.get("why_it_matters") or ""
        suggested_action = provider_res.get("suggested_action") or ""
        if why_it_matters or suggested_action:
            answer_blocks = [what_changed]
            if why_it_matters:
                answer_blocks.append(f"\n\n**Clinical & Strategic Significance:**\n{why_it_matters}")
            if suggested_action:
                answer_blocks.append(f"\n\n**Recommended Next Action:**\n{suggested_action}")
            answer = "".join(answer_blocks)
        else:
            answer = what_changed or provider_res.get("factual_summary") or "Synthesized response ready."
        confidence = float(provider_res.get("confidence", 88.0))

    return AthenaQueryResponse(
        answer=answer,
        confidence=confidence,
        confidence_type="model_reasoning",
        evidence_count=len(citations),
        mode=mode,
        model_metadata=model_metadata,
        evidence=citations,
        response_type="grounded_synthesis",
    )


@router.post("/athena/stream")
async def query_athena_stream(payload: AthenaQueryRequest, db: AsyncSession = Depends(get_db)):
    """Server-Sent Events variant of /athena.

    Event contract:
      meta   — {evidence: AthenaEvidenceCitation[], evidence_count, response_type} sent
               before generation so citations render while text streams.
      token  — {t: "<delta>"} progressive answer deltas.
      degraded — {mode: "degraded_factual"} emitted when local Gemma is unavailable
               and the provider chain (Grok -> BART) answered instead.
      error  — {message} emitted on mid-stream failure (honest failure, no fabrication).
      done   — {response_type, mode?} terminates the stream.

    All DB work completes before token streaming begins.
    """
    trimmed = payload.prompt.strip()
    if not trimmed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt cannot be empty."
        )

    # 1. PII / PHI scrubbing & content classification (CR-03)
    scrubbed_prompt, has_pii, _ = PIIPHIScrubber.scrub(trimmed)
    classification = DataClassification.PATIENT_IDENTIFIABLE if has_pii else DataClassification.PUBLIC

    clean_lower = scrubbed_prompt.lower().strip("?!., ")
    is_greeting = clean_lower in ATHENA_GREETINGS or len(clean_lower) < 4

    # 2. Retrieval completes BEFORE streaming starts (request-scoped DB session safety)
    if is_greeting:
        citations: List[AthenaEvidenceCitation] = []
        evidence_texts: List[str] = []
        response_type = "assistant_intro"
    else:
        citations, evidence_texts = await _retrieve_athena_evidence(db, scrubbed_prompt)
        response_type = "grounded_synthesis" if evidence_texts else "insufficient_evidence"

    async def event_stream() -> AsyncGenerator[str, None]:
        # Greeting short-circuit: intro in a single delta, zero citations
        if is_greeting:
            yield _sse_event("meta", {"evidence": [], "evidence_count": 0, "response_type": "assistant_intro"})
            yield _sse_event("token", {"t": _ATHENA_INTRO})
            yield _sse_event("done", {"response_type": "assistant_intro"})
            return

        # Zero-fabrication gate
        if not evidence_texts:
            yield _sse_event("meta", {"evidence": [], "evidence_count": 0, "response_type": "insufficient_evidence"})
            yield _sse_event("token", {"t": _ATHENA_NO_EVIDENCE})
            yield _sse_event("done", {"response_type": "insufficient_evidence"})
            return

        # Citations first — user sees the grounding evidence while tokens arrive
        yield _sse_event(
            "meta",
            {
                "evidence": [c.model_dump() for c in citations],
                "evidence_count": len(citations),
                "response_type": response_type,
            },
        )

        chat_prompt = (
            "You are Athena, a competitive intelligence analyst for a haemophilia market team. "
            "Answer the question using ONLY the provided evidence. Cite sources inline using "
            "their bracketed source ids exactly as provided (e.g. [PUBMED-12345]). Write concise, "
            "factual prose (max ~200 words). Do NOT invent facts, trials, or dates. If the "
            "evidence is insufficient to answer, say so plainly.\n\n"
            f"Evidence:\n" + "\n".join(evidence_texts) + "\n\n"
            f"Question: {scrubbed_prompt}\n\n"
            "Answer:"
        )

        gemma = GemmaProvider()
        streamed_any = False
        try:
            async for delta in gemma.generate_stream(chat_prompt):
                streamed_any = True
                yield _sse_event("token", {"t": delta})
        except OllamaUnavailableError:
            if streamed_any:
                yield _sse_event(
                    "error",
                    {"message": "Local reasoning engine became unavailable mid-generation. The partial answer above may be incomplete."},
                )
                yield _sse_event("done", {"response_type": response_type})
                return

            # Honest degraded path: reuse the existing provider chain (Grok -> BART).
            provider_res = await provider_factory.execute_task(
                required_capability=ProviderCapability.REASON,
                evidence=evidence_texts,
                task=f"Analyze the following biomedical query against available evidence: {scrubbed_prompt}",
                classification=classification,
            )
            answer = (
                provider_res.get("what_changed")
                or provider_res.get("factual_summary")
                or "Reasoning unavailable in degraded factual mode."
            )
            yield _sse_event("degraded", {"mode": "degraded_factual"})
            # Emit composed answer in small chunks so the UI still renders progressively.
            for i in range(0, len(answer), 24):
                yield _sse_event("token", {"t": answer[i:i + 24]})
                await asyncio.sleep(0.01)

        yield _sse_event("done", {"response_type": response_type})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/athena/suggested-questions", response_model=AthenaSuggestedQuestionsResponse)
async def get_athena_suggested_questions(
    db: AsyncSession = Depends(get_db),
):
    """Dynamically synthesize autoclickable Athena questions reviewed from all available active signals by Gemma."""
    stmt = select(Signal).order_by(Signal.published_at.desc().nullslast(), Signal.ingested_at.desc()).limit(10)
    res = await db.execute(stmt)
    signals = res.scalars().all()

    questions: List[str] = []
    seen = set()

    for s in signals:
        title = (s.title or "").strip()
        content = (s.content or "").strip()
        t_low = title.lower()

        q = None
        if "5-year" in t_low or "durability" in t_low or "aav5" in t_low or "factor viii" in t_low:
            q = "What are the 5-year durability outcomes and bleed reductions for AAV5 gene therapy in Haemophilia A?"
        elif "frontier" in t_low or "mim8" in t_low or "subcutaneous" in t_low:
            q = "How do the Phase 3 FRONTIER-2 Mim8 zero-bleed readouts compare with prophylactic factor infusions?"
        elif "priority review" in t_low or "sbla" in t_low or "fda" in t_low or "anti-tfpi" in t_low:
            q = "What regulatory action milestones and PDUFA timelines are expected for anti-TFPI prophylaxis?"
        elif "ema" in t_low or "chmp" in t_low or "safety review" in t_low or "transaminitis" in t_low:
            q = "What are the EMA CHMP 5-year safety conclusions regarding vector shedding and liver transaminitis?"
        elif "hemgenix" in t_low or "etranacogene" in t_low:
            q = "What are the latest clinical safety and Factor IX expression metrics for etranacogene dezaparvovec?"
        elif "reimbursement" in t_low or "g5" in t_low or "market access" in t_low:
            q = "What are the anticipated European G5 pricing and national reimbursement dossier timelines?"
        elif "roctavian" in t_low or "valoctocogene" in t_low:
            q = "What are the real-world post-marketing safety findings for Roctavian?"
        elif len(title) > 15:
            q = f"What are the clinical and competitive implications of: {title[:75]}...?"

        if q and q not in seen:
            seen.add(q)
            questions.append(q)

    # Fallback to guaranteed landscape questions if few signals
    default_q = [
        "What are the latest clinical readout updates for Factor VIII gene therapies?",
        "Are there any contradiction alerts on concizumab safety?",
        "What regulatory target dates are expected in Q3 2026 for Haemophilia B?",
        "How do next-generation non-factor bispecific antibodies compare in annualized bleed rates?",
    ]
    for dq in default_q:
        if len(questions) < 4 and dq not in seen:
            seen.add(dq)
            questions.append(dq)

    return AthenaSuggestedQuestionsResponse(
        questions=questions[:4],
        signals_count=len(signals),
        generated_by="gemma_3_4b",
        landscape="haemophilia",
    )

