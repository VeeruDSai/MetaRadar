from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


def utc_now():
    return datetime.now(timezone.utc)


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


class ScoreBreakdownSchema(BaseModel):
    impact: float
    urgency: float
    evidence_strength: float
    strategic_relevance: float
    novelty: float
    routing_relevance: float
    total_score: float
    reason: Optional[str] = None


class SourceSchema(BaseModel):
    source_id: str
    name: str
    freshness_class: str
    syndication_group: Optional[str] = None
    status: str
    quota_remaining: Optional[int] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None


class EvidenceSchema(BaseModel):
    evidence_id: UUID
    raw_signal_id: UUID
    evidence_excerpt: str
    content_hash: str
    created_at: datetime


class SignalSchema(BaseModel):
    signal_id: UUID
    source_id: str
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
    facts: List[str] = Field(default_factory=list)
    interpretation: Optional[str] = None
    speculation: Optional[str] = None
    priority: str
    score_breakdown: Optional[ScoreBreakdownSchema] = None
    model_metadata: Optional[ModelMetadataSchema] = None
    scoring_model_version: str
    scoring_config_version: str
    embedding_model_version: str
    prompt_version: str
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
    quota_remaining: Optional[int] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None


class HealthConnectorsResponse(BaseModel):
    connectors: List[ConnectorHealthStatus]
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


class AthenaQueryResponse(BaseModel):
    answer: str
    confidence: float
    evidence_count: int
    mode: str = "reasoning"
    model_metadata: Optional[ModelMetadataSchema] = None


class FeedbackSubmissionRequest(BaseModel):
    signal_id: UUID
    stakeholder_function: str = Field(..., description="Canonical function (e.g., REGULATORY, MEDICAL_AFFAIRS)")
    relevance_rating: int = Field(..., ge=1, le=5, description="1 to 5 star rating")
    urgency_rating: int = Field(..., ge=1, le=5, description="1 to 5 urgency rating")
    action_appropriate: bool = Field(..., description="Whether proposed action is appropriate")
    comments: Optional[str] = Field(None, max_length=1000)
    user_id: Optional[str] = Field("demo_user", max_length=100)


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


class CalibrationWeightsResponse(BaseModel):
    version: str
    weights: List[RoleWeightSchema]


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


