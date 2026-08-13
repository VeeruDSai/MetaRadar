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
