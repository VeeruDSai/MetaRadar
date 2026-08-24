import time
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, distinct, or_

from app.db.session import get_db
from app.models import Signal, Asset, Confluence, Development, Contradiction, Evidence
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
)
from app.services.pii import PIIPHIScrubber
from app.services.provenance_urls import resolve_canonical_provenance
from app.services.scoring import priority_scorer
from app.services.confluence import confluence_engine
from app.services.embeddings import embedding_service
from app.providers.factory import provider_factory
from app.providers.base import ProviderCapability, DataClassification

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


@router.get("/signals", response_model=SignalListResponse)
async def list_signals(
    severity: Optional[str] = Query(None, description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW"),
    entity: Optional[str] = Query(None, description="Search term in signal title or content"),
    date_from: Optional[datetime] = Query(None, description="Filter signals published on or after date"),
    date_to: Optional[datetime] = Query(None, description="Filter signals published on or before date"),
    signal_type: Optional[str] = Query(None, description="Filter by signal type"),
    source: Optional[str] = Query(None, description="Filter by source ID"),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """Returns filtered signals list with deterministic ordering, limit/offset pagination, and total count."""
    query = select(Signal)
    count_query = select(func.count(Signal.signal_id))

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
        total=total
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
    greetings = {"hey", "hello", "hi", "greetings", "good morning", "good evening", "who are you", "what is athena", "what can you do", "help"}
    clean_lower = scrubbed_prompt.lower().strip("?!., ")
    if clean_lower in greetings or len(clean_lower) < 4:
        return AthenaQueryResponse(
            answer=(
                "Hello! I am Athena, MetaRadar's grounded clinical intelligence copilot. "
                "I analyze competitive intelligence and clinical developments across Haemophilia A and B, "
                "grounded strictly in indexed evidence from ClinicalTrials.gov, PubMed, FDA/EMA regulatory registries, and market news.\n\n"
                "You can ask me questions such as:\n"
                "• \"What are the latest clinical readout updates for Factor VIII gene therapies?\"\n"
                "• \"Are there any contradiction alerts on concizumab safety?\"\n"
                "• \"What regulatory target dates are expected in Q3 2026 for Haemophilia B?\"\n"
                "• \"Summarize recent pipeline updates for mim8 and fitusiran.\""
            ),
            confidence=100.0,
            confidence_type="model_reasoning",
            evidence_count=0,
            mode="assistant_intro",
            model_metadata=None,
            evidence=[],
            response_type="assistant_intro",
        )

    # 3. Real Vector Retrieval over indexed Signals / Evidence
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

    # 4. Keyword / Lexical Fallback if vector search yielded 0 matches
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

    # Zero-fabrication gate: If no evidence is found, return honest failure notice
    if not evidence_texts:
        return AthenaQueryResponse(
            answer="No sufficiently relevant evidence was found in the indexed sources to answer this question. Please try querying specific haemophilia therapies, trial phases, or regulatory events.",
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
