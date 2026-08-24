from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field, field_validator

from app.schemas.intelligence import (
    DataMode,
    ConfidenceType,
    ConfluenceAlertItem,
    ConfluenceInspectResponse,
    ConfluenceEvidenceSourceItem,
    LifecycleTimelineItem,
    ContradictionItem,
    MissingSignalWatchItem,
)
from app.schemas.registry import (
    DevelopmentSummary,
    SourceRegistryItem,
    SourceHealthLogItem,
)


def utc_now():
    return datetime.now(timezone.utc)


class CacheClearResponse(BaseModel):
    status: str
    flushed_at: datetime = Field(default_factory=utc_now)
    keys_cleared: int = 0


class ModelMetadataSchema(BaseModel):
    provider: str
    mode: str  # reasoning | degraded_factual
    model: str
    fallback_used: bool = False
    fallback_reason: Optional[str] = None
    reasoning_available: bool = True
    actions_available: bool = True
    latency_ms: Optional[int] = None


class FactInterpretationSpeculationSchema(BaseModel):
    facts: List[str] = Field(default_factory=list)
    interpretation: Optional[str] = None
    speculation: Optional[str] = None


class AthenaSuggestedQuestionsResponse(BaseModel):
    questions: List[str] = Field(default_factory=list)
    signals_count: int = 0
    generated_by: str = "gemma_3_4b"
    landscape: str = "haemophilia"


class ScoreBreakdownSchema(BaseModel):
    novelty: float = 0.0
    clinical: float = 0.0
    regulatory: float = 0.0
    recency: float = 0.0
    total: float = 0.0
    version: str = "haemophilia_v2.0"
    reason: Optional[str] = None

    # Legacy fields supported for backwards compatibility
    impact: Optional[float] = None
    urgency: Optional[float] = None
    evidence_strength: Optional[float] = None
    strategic_relevance: Optional[float] = None
    routing_relevance: Optional[float] = None
    total_score: Optional[float] = None


class SourceSchema(BaseModel):
    source_id: str
    name: str
    freshness_class: str
    syndication_group: Optional[str] = None
    status: str
    quota_remaining: Optional[int] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None
    connector_status: str = "NEVER_CONNECTED"
    latency_ms: Optional[int] = None
    records_fetched: int = 0


class EvidenceSchema(BaseModel):
    evidence_id: UUID
    raw_signal_id: UUID
    evidence_excerpt: str
    content_hash: str
    created_at: datetime


class SignalSchema(BaseModel):
    signal_id: UUID
    source_id: str
    source_name: Optional[str] = None
    external_id: Optional[str] = None
    development_id: Optional[UUID] = None
    pipeline_run_id: Optional[UUID] = None
    pmid: Optional[str] = None
    nct_id: Optional[str] = None
    regulatory_id: Optional[str] = None
    fingerprint: str
    canonical_url: Optional[str] = None
    signal_type: str
    disease: str
    title: str
    content: str
    published_at: datetime
    retrieved_at: datetime
    ingested_at: Optional[datetime] = None

    # Truthfulness, DataMode & Provenance
    data_mode: str = "live"
    is_synthetic: bool = False
    confidence: Optional[float] = None
    confidence_type: Optional[str] = None
    confidence_rationale: Optional[str] = None
    provenance_status: str = "available"
    evidence_text: Optional[str] = None
    raw_record_reference: Optional[str] = None
    scoring_status: str = "computed"

    facts: List[str] = Field(default_factory=list)
    interpretation: Optional[str] = None
    speculation: Optional[str] = None
    priority: str = "MEDIUM"
    score_breakdown: Optional[ScoreBreakdownSchema] = None
    model_metadata: Optional[ModelMetadataSchema] = None
    scoring_model_version: str = "haemophilia_v2.0"
    scoring_config_version: str = "haemophilia_v1"
    embedding_model_version: str = "v1"
    prompt_version: str = "v1.0.0"
    created_at: datetime


class DevelopmentSchema(BaseModel):
    development_id: UUID
    title: str
    disease: str
    asset_id: Optional[str] = None
    company_id: Optional[str] = None
    current_stage: str
    created_at: datetime
    updated_at: datetime


class PipelineRunSchema(BaseModel):
    pipeline_run_id: UUID
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    trigger: str
    signals_fetched: int
    signals_created: int
    signals_updated: int
    duplicates_removed: int
    errors_count: int
    error_summary: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "MetaRadar API"
    version: str = "5.1.0"
    timestamp: datetime = Field(default_factory=utc_now)


class HealthReadyResponse(BaseModel):
    status: str  # ready | degraded
    database: bool
    redis: bool
    redis_warning: Optional[str] = None
    timestamp: datetime = Field(default_factory=utc_now)


class HealthModelsResponse(BaseModel):
    llm_provider: str
    ollama_host: str
    gemma_available: bool
    grok_configured: bool
    grok_fallback_enabled: bool
    bart_degraded_available: bool
    embedding_model: str
    embedding_revision: str
    embedding_dimension: int


class ConnectorHealthStatus(BaseModel):
    source_id: str
    name: str
    status: str
    freshness_class: str
    tier: int = 1
    quota_remaining: Optional[int] = None
    last_success: Optional[datetime] = None
    last_attempted: Optional[datetime] = None
    last_error: Optional[str] = None
    connector_status: str = "NEVER_CONNECTED"
    latency_ms: Optional[int] = None
    records_fetched: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    records_new: int = 0
    records_updated: int = 0
    records_duplicate: int = 0
    upstream_data_timestamp: Optional[str] = None
    last_data_update: Optional[datetime] = None
    next_scheduled_run: Optional[datetime] = None
    consecutive_failures: int = 0
    backoff_minutes: Optional[int] = None
    http_status: Optional[int] = None
    configuration_error_message: Optional[str] = None


class HealthConnectorsResponse(BaseModel):
    connectors: List[ConnectorHealthStatus]
    timestamp: datetime = Field(default_factory=utc_now)


class SchedulerJobStatus(BaseModel):
    connector_id: str
    interval_minutes: int
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_status: str = "IDLE"
    consecutive_failures: int = 0
    current_backoff_minutes: int = 0
    records_fetched_last_run: int = 0
    records_new_last_run: int = 0
    last_error: Optional[str] = None


class SchedulerStatusResponse(BaseModel):
    scheduler_enabled: bool
    scheduler_running: bool
    scheduler_started_at: Optional[datetime] = None
    total_jobs: int = 0
    active_jobs: List[SchedulerJobStatus] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utc_now)


class PipelineRunRequestSchema(BaseModel):
    batch_size: int = Field(default=50, ge=1, le=500, description="Max bronze signals to process")
    calibration_weights: Optional[Dict[str, float]] = Field(default=None, description="Optional runtime role weight overrides")


class PipelineRunResponseSchema(BaseModel):
    pipeline_run_id: str
    status: str
    signals_processed: int
    role_briefs_count: int
    developments_count: int
    confluence_stories_count: int
    contradictions_count: int
    missing_signals_count: int
    node_statuses: Dict[str, str]
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=utc_now)


class TrendPointSchema(BaseModel):
    label: str
    value: int
    baseline: Optional[int] = None


class ConfluenceSummarySchema(BaseModel):
    score: float
    label: str
    drivers: List[str] = Field(default_factory=list)
    updated_at: str


class LifecycleSummarySchema(BaseModel):
    id: str
    name: str
    stage: str
    momentum: Optional[float] = None
    confidence: Optional[float] = None
    last_changed: Optional[str] = None
    signals: int = 0


class OverviewHealthSchema(BaseModel):
    api: str = "healthy"
    latency_ms: int = 0
    source_count: int = 0


class OverviewResponse(BaseModel):
    active_signals: int
    monitored_assets: int
    confluences_detected: int
    contradictions_flagged: int = 0
    weekly_change: Optional[str] = None
    last_sync: str
    confluence: ConfluenceSummarySchema
    lifecycle: List[LifecycleSummarySchema] = Field(default_factory=list)
    trends: List[TrendPointSchema] = Field(default_factory=list)
    health: OverviewHealthSchema


class SignalListResponse(BaseModel):
    signals: List[SignalSchema]
    total: int


class AthenaQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=500)


class AthenaEvidenceCitation(BaseModel):
    signal_id: str
    title: str
    source_id: str
    canonical_url: Optional[str] = None
    published_at: Optional[str] = None
    excerpt: str
    distance: float


class AthenaQueryResponse(BaseModel):
    answer: str
    confidence: float
    confidence_type: str = "model_reasoning"
    evidence_count: int
    mode: str = "reasoning"
    model_metadata: Optional[ModelMetadataSchema] = None
    evidence: List[AthenaEvidenceCitation] = Field(default_factory=list)
    response_type: str = "grounded_synthesis"


class FeedbackSubmissionRequest(BaseModel):
    signal_id: UUID
    stakeholder_function: str = Field(..., description="Canonical function (e.g., REGULATORY, MEDICAL_AFFAIRS)")
    relevance_rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    urgency_rating: int = Field(..., ge=1, le=5, description="1 to 5 urgency rating")
    action_appropriate: bool = Field(..., description="Whether proposed action is appropriate")
    comments: Optional[str] = Field(None, max_length=1000)
    user_id: Optional[str] = Field("demo_user", max_length=100)

    @field_validator("stakeholder_function")
    @classmethod
    def validate_stakeholder_function(cls, v: str) -> str:
        v_upper = v.strip().upper()
        allowed = {
            "MEDICAL_AFFAIRS",
            "REGULATORY",
            "SAFETY",
            "MARKET_ACCESS",
            "COMMUNICATIONS",
            "LEADERSHIP",
        }
        if v_upper not in allowed:
            raise ValueError(f"Invalid stakeholder_function '{v}'. Allowed: {sorted(allowed)}")
        return v_upper


class FeedbackSubmissionResponse(BaseModel):
    feedback_id: UUID
    signal_id: UUID
    stakeholder_function: str
    status: str = "recorded"
    unapplied_count: int
    recalibration_triggered: bool


class RoleWeightSchema(BaseModel):
    stakeholder_function: str
    impact_weight: float
    urgency_weight: float
    novelty_weight: float
    updated_at: datetime


class CalibrationRunSchema(BaseModel):
    run_id: UUID
    triggered_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    feedback_count: int
    previous_weights: Optional[Dict[str, Any]] = None
    new_weights: Optional[Dict[str, Any]] = None
    affected_functions: Optional[List[str]] = None
    reason: Optional[str] = None
    scoring_version: str


class CalibrationWeightsResponse(BaseModel):
    version: str
    weights: List[RoleWeightSchema]
    run_history: List[CalibrationRunSchema] = Field(default_factory=list)
    pending_feedback_count: int = 0


class WatchRuleSuggestionSchema(BaseModel):
    suggestion_id: str
    development_id: Optional[UUID] = None
    trigger_event: str
    expected_event: str
    monitoring_window_days: int
    responsible_function: str
    rationale: str


class BeforeAfterComparisonSchema(BaseModel):
    signal_id: UUID
    stakeholder_function: str
    baseline_priority: str
    calibrated_priority: str
    baseline_relevance_score: float
    calibrated_relevance_score: float
    baseline_suggested_action: str
    calibrated_suggested_action: str
    confidence_uplift_pct: float


class RecalibrateResponse(BaseModel):
    status: str
    calibration_version: str
    stakeholder_function: Optional[str] = None
    applied_feedback_count: int
    run_id: Optional[UUID] = None
    updated_weights: List[RoleWeightSchema] = Field(default_factory=list)
    comparisons: List[BeforeAfterComparisonSchema] = Field(default_factory=list)
    watch_rule_suggestions: List[WatchRuleSuggestionSchema] = Field(default_factory=list)


class FeedbackRoleSummarySchema(BaseModel):
    stakeholder_function: str
    total_feedback_count: int
    average_relevance: float
    average_urgency: float
    action_approval_rate: float


class FeedbackSummaryResponse(BaseModel):
    total_feedback: int
    roles: List[FeedbackRoleSummarySchema] = Field(default_factory=list)


class ConfirmWatchItemRequest(BaseModel):
    development_id: UUID
    trigger_event: str
    expected_event: str
    monitoring_window_days: int = 90
    responsible_function: str


class ConfirmWatchItemResponse(BaseModel):
    watch_id: UUID
    status: str
    responsible_function: str
    monitoring_window_days: int


class ActivityLogItem(BaseModel):
    id: UUID
    timestamp: datetime
    level: str
    service: str
    component: str
    event: str
    status: str
    duration_ms: Optional[float] = None
    request_id: Optional[str] = None
    pipeline_run_id: Optional[str] = None
    message: str
    details: Optional[Dict[str, Any]] = None
