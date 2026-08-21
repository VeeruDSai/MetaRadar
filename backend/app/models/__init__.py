import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import (
    Column, String, Text, DateTime, Integer, Boolean, Float, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from app.db.session import Base
from app.core.config import settings


def utc_now():
    return datetime.now(timezone.utc)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    pipeline_run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="queued", nullable=False)
    trigger = Column(String(50), default="scheduled", nullable=False)
    signals_fetched = Column(Integer, default=0, nullable=False)
    signals_created = Column(Integer, default=0, nullable=False)
    signals_updated = Column(Integer, default=0, nullable=False)
    duplicates_removed = Column(Integer, default=0, nullable=False)
    errors_count = Column(Integer, default=0, nullable=False)
    error_summary = Column(JSONB, nullable=True)


class Source(Base):
    __tablename__ = "sources"

    source_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    freshness_class = Column(String(50), nullable=False)
    syndication_group = Column(String(100), nullable=True)
    parent_source_id = Column(String(100), nullable=True)
    status = Column(String(50), default="active", nullable=False)
    quota_remaining = Column(Integer, nullable=True)
    last_success = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)

    # Health & Operational Telemetry
    connector_status = Column(String(50), default="NEVER_CONNECTED", nullable=False)
    last_attempted = Column(DateTime(timezone=True), nullable=True)
    latency_ms = Column(Integer, nullable=True)
    records_fetched = Column(Integer, default=0, nullable=False)
    records_accepted = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    http_status = Column(Integer, nullable=True)
    configuration_error_message = Column(Text, nullable=True)


class SourceHealthLog(Base):
    __tablename__ = "source_health_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), ForeignKey("sources.source_id"), nullable=False)
    pipeline_run_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_runs.pipeline_run_id"), nullable=True)
    checked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    connector_status = Column(String(50), nullable=False)
    http_status = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    records_fetched = Column(Integer, default=0, nullable=False)
    records_accepted = Column(Integer, default=0, nullable=False)
    records_rejected = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    error_code = Column(String(50), nullable=True)


class Company(Base):
    __tablename__ = "companies"

    company_id = Column(String(100), primary_key=True)
    name = Column(String(255), nullable=False)
    is_novo_nordisk = Column(Boolean, default=False, nullable=False)


class Asset(Base):
    __tablename__ = "assets"

    asset_id = Column(String(100), primary_key=True)
    brand_name = Column(String(255), nullable=False)
    generic_name = Column(String(255), nullable=False)
    company_id = Column(String(100), ForeignKey("companies.company_id"), nullable=False)
    mechanism = Column(Text, nullable=False)
    modality = Column(String(100), nullable=False)
    indication = Column(Text, nullable=False)
    approval_status = Column(String(50), nullable=False)
    approval_date = Column(String(20), nullable=True)
    jurisdiction = Column(String(100), nullable=True)
    last_verified = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ClinicalTrial(Base):
    __tablename__ = "trials"

    trial_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nct_id = Column(String(50), nullable=True)
    title = Column(Text, nullable=False)
    phase = Column(String(50), nullable=True)
    status = Column(String(100), nullable=True)
    sponsor = Column(String(255), nullable=True)

    __table_args__ = (
        Index("uix_trials_nct_id", "nct_id", unique=True, postgresql_where=(nct_id.isnot(None))),
    )


class Development(Base):
    __tablename__ = "developments"

    development_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(Text, nullable=False)
    disease = Column(String(100), nullable=False)
    asset_id = Column(String(100), ForeignKey("assets.asset_id"), nullable=True)
    company_id = Column(String(100), ForeignKey("companies.company_id"), nullable=True)
    current_stage = Column(String(50), nullable=False, default="announced")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Event(Base):
    __tablename__ = "events"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    development_id = Column(UUID(as_uuid=True), ForeignKey("developments.development_id"), nullable=False)
    source_id = Column(String(100), ForeignKey("sources.source_id"), nullable=True)
    event_type = Column(String(100), nullable=False)
    event_date = Column(DateTime(timezone=True), nullable=False)
    summary = Column(Text, nullable=False)


class LifecycleEvent(Base):
    __tablename__ = "lifecycle_events"

    lifecycle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    development_id = Column(UUID(as_uuid=True), ForeignKey("developments.development_id"), nullable=False)
    source_id = Column(String(100), ForeignKey("sources.source_id"), nullable=True)
    stage = Column(String(100), nullable=False)
    event_date = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    notes = Column(Text, nullable=True)


class Confluence(Base):
    __tablename__ = "confluences"

    confluence_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    development_id = Column(UUID(as_uuid=True), ForeignKey("developments.development_id"), nullable=False)
    signal_count = Column(Integer, nullable=False, default=1)
    confluence_type = Column(String(50), nullable=False, default="emerging")
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class RawSignalBronze(Base):
    __tablename__ = "raw_signals_bronze"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), ForeignKey("sources.source_id"), nullable=False)
    external_id = Column(String(255), nullable=False)
    pipeline_run_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_runs.pipeline_run_id"), nullable=True)
    retrieved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    raw_payload = Column(JSONB, nullable=False)
    content_hash = Column(String(64), nullable=False)
    connector_version = Column(String(50), default="1.0.0", nullable=False)
    cross_source_group_id = Column(UUID(as_uuid=True), nullable=True)

    __table_args__ = (
        UniqueConstraint("source_id", "external_id", name="uq_raw_source_external"),
    )


class ConnectorState(Base):
    """Per-connector per-profile incremental run state (D-11)."""

    __tablename__ = "connector_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), nullable=False)
    profile_id = Column(String(100), nullable=False)
    last_success = Column(DateTime(timezone=True), nullable=True)
    cursor = Column(Text, nullable=True)
    next_run_after = Column(DateTime(timezone=True), nullable=True)
    first_run_completed = Column(Boolean, nullable=False, default=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    __table_args__ = (
        UniqueConstraint("source_id", "profile_id", name="uq_connector_state_source_profile"),
    )


class Evidence(Base):
    __tablename__ = "evidence"

    evidence_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    raw_signal_id = Column(UUID(as_uuid=True), ForeignKey("raw_signals_bronze.id"), nullable=False)
    evidence_excerpt = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class Signal(Base):
    __tablename__ = "signals"

    signal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_id = Column(String(100), ForeignKey("sources.source_id"), nullable=False)
    source_name = Column(String(255), nullable=True)
    external_id = Column(String(255), nullable=True)
    development_id = Column(UUID(as_uuid=True), ForeignKey("developments.development_id"), nullable=True)
    pipeline_run_id = Column(UUID(as_uuid=True), ForeignKey("pipeline_runs.pipeline_run_id"), nullable=True)

    pmid = Column(String(50), nullable=True)
    nct_id = Column(String(50), nullable=True)
    regulatory_id = Column(String(100), nullable=True)
    fingerprint = Column(String(64), nullable=False)
    canonical_url = Column(Text, nullable=True)

    signal_type = Column(String(50), nullable=False)
    disease = Column(String(100), nullable=False)
    title = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=False)
    retrieved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    ingested_at = Column(DateTime(timezone=True), default=utc_now, nullable=True)

    # Truthfulness, DataMode & Provenance
    data_mode = Column(String(50), default="live", nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    confidence_type = Column(String(50), nullable=True)
    confidence_rationale = Column(Text, nullable=True)
    provenance_status = Column(String(50), default="available", nullable=False)
    evidence_text = Column(Text, nullable=True)
    raw_record_reference = Column(String(255), nullable=True)

    facts = Column(JSONB, nullable=True)
    interpretation = Column(Text, nullable=True)
    speculation = Column(Text, nullable=True)

    priority = Column(String(50), default="MEDIUM", nullable=False)
    score_breakdown = Column(JSONB, nullable=True)
    model_metadata = Column(JSONB, nullable=True)

    embedding = Column(Vector(settings.EMBEDDING_DIMENSION), nullable=True)

    scoring_model_version = Column(String(50), default="v1", nullable=False)
    scoring_config_version = Column(String(50), default="haemophilia_v1", nullable=False)
    embedding_model_version = Column(String(100), default=settings.EMBEDDING_MODEL_REVISION, nullable=False)
    prompt_version = Column(String(50), default="v1.0.0", nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    __table_args__ = (
        Index("uix_signals_pmid", "pmid", unique=True, postgresql_where=(pmid.isnot(None))),
        Index("uix_signals_nct_id", "nct_id", unique=True, postgresql_where=(nct_id.isnot(None))),
        Index("uix_signals_regulatory_id", "regulatory_id", unique=True, postgresql_where=(regulatory_id.isnot(None))),
        Index("uix_signals_fingerprint", "fingerprint", unique=True),
        Index("uix_signals_canonical_url", "canonical_url", unique=True, postgresql_where=(canonical_url.isnot(None))),
        Index("ix_signals_source_name", "source_name"),
        Index("ix_signals_external_id", "external_id"),
        Index("ix_signals_provenance_status", "provenance_status"),
    )


class Contradiction(Base):
    __tablename__ = "contradictions"

    contradiction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    claim_a_id = Column(String(100), nullable=False)
    claim_b_id = Column(String(100), nullable=False)
    rule_id = Column(String(100), nullable=False)
    rule_name = Column(String(255), nullable=False)
    severity = Column(String(50), nullable=False)
    confidence = Column(Float, nullable=False)
    description = Column(Text, nullable=False)
    detected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Excerpts & Provenance
    claim_a_excerpt = Column(Text, nullable=True)
    claim_b_excerpt = Column(Text, nullable=True)
    claim_a_evidence_id = Column(UUID(as_uuid=True), nullable=True)
    claim_b_evidence_id = Column(UUID(as_uuid=True), nullable=True)
    confidence_type = Column(String(50), default="nli_heuristic", nullable=False)


class CalibrationRun(Base):
    __tablename__ = "calibration_runs"

    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    triggered_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="completed", nullable=False)
    feedback_count = Column(Integer, default=0, nullable=False)
    previous_weights = Column(JSONB, nullable=True)
    new_weights = Column(JSONB, nullable=True)
    affected_functions = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    scoring_version = Column(String(50), default="haemophilia_v2.0", nullable=False)


class CalibrationHistory(Base):
    __tablename__ = "calibration_history"

    history_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    version = Column(String(50), nullable=False)
    weights = Column(JSONB, nullable=False)
    applied_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class ScoringWeights(Base):
    __tablename__ = "scoring_weights"

    weight_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stakeholder_function = Column(String(100), primary_key=True)
    impact_weight = Column(Float, nullable=False, default=1.0)
    urgency_weight = Column(Float, nullable=False, default=1.0)
    novelty_weight = Column(Float, nullable=False, default=1.0)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class SignalRouting(Base):
    __tablename__ = "signal_routing"

    routing_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.signal_id"), nullable=False)

    baseline_primary_function = Column(String(100), nullable=False)
    baseline_relevance_scores = Column(JSONB, nullable=False)
    baseline_suggested_action = Column(Text, nullable=False)

    calibrated_primary_function = Column(String(100), nullable=True)
    calibrated_relevance_scores = Column(JSONB, nullable=True)
    calibrated_suggested_action = Column(Text, nullable=True)

    calibration_version = Column(String(50), default="v1.0.0", nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class CalibrationFeedback(Base):
    __tablename__ = "calibration_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    signal_id = Column(UUID(as_uuid=True), ForeignKey("signals.signal_id"), nullable=False)
    stakeholder_function = Column(String(100), nullable=False)
    relevance_rating = Column(Integer, nullable=False)
    urgency_rating = Column(Integer, nullable=False)
    action_appropriate = Column(Boolean, nullable=False)
    comments = Column(Text, nullable=True)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Idempotency Tracking
    is_applied = Column(Boolean, default=False, nullable=False)
    applied_at = Column(DateTime(timezone=True), nullable=True)
    calibration_run_id = Column(UUID(as_uuid=True), ForeignKey("calibration_runs.run_id"), nullable=True)


class WatchItem(Base):
    __tablename__ = "watch_items"

    watch_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    development_id = Column(UUID(as_uuid=True), ForeignKey("developments.development_id"), nullable=False)
    trigger_event = Column(Text, nullable=False)
    expected_event = Column(Text, nullable=False)
    monitoring_window_days = Column(Integer, default=90, nullable=False)
    responsible_function = Column(String(100), nullable=False)
    status = Column(String(50), default="watching", nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_log"

    audit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_name = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=False)
    action = Column(String(50), nullable=False)
    performed_by = Column(String(100), default="system", nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    details = Column(JSONB, nullable=True)
