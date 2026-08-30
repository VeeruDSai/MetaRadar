from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from enum import Enum
from pydantic import BaseModel, Field


class DataMode(str, Enum):
    LIVE = "live"
    RECORDED_DEMO = "recorded_demo"
    TEST_FIXTURE = "test_fixture"
    BENCHMARK = "benchmark"
    SYNTHETIC = "synthetic"


class ConfidenceType(str, Enum):
    EXTRACTION = "extraction"
    CLASSIFICATION = "classification"
    EVIDENCE = "evidence"
    CONTRADICTION = "nli_heuristic"
    OVERDUE_HEURISTIC = "overdue_heuristic"
    MODEL_REASONING = "model_reasoning"
    HUMAN_VALIDATION = "human_validation"


class ConfluenceEvidenceSourceItem(BaseModel):
    source_name: str
    source_type: str
    external_id: str
    source_url: Optional[str] = None
    retrieved_at: Optional[datetime] = None
    published_at: Optional[datetime] = None
    verbatim_excerpt: str
    points_contributed: float = 0.0


class ConfluenceInspectResponse(BaseModel):
    confluence_id: UUID
    development_id: Optional[UUID] = None
    development_title: Optional[str] = None
    score: float
    label: str
    confluence_type: str
    window_hours: int = 48
    distinct_sources_count: int
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    reasoning: str
    sources: List[ConfluenceEvidenceSourceItem] = Field(default_factory=list)
    detected_at: datetime


class ConfluenceAlertItem(BaseModel):
    confluence_id: UUID
    development_id: UUID
    development_title: Optional[str] = None
    signal_count: int
    confluence_type: str
    created_at: datetime
    signals: List[Dict[str, Any]] = Field(default_factory=list)
    score: Optional[float] = None
    calculation_version: Optional[str] = "confluence_v2.0"
    independent_sources_count: Optional[int] = None
    score_breakdown: Optional[Dict[str, float]] = None
    reasoning: Optional[str] = None
    evidence_sources: List[ConfluenceEvidenceSourceItem] = Field(default_factory=list)


class LifecycleTimelineItem(BaseModel):
    lifecycle_id: UUID
    development_id: UUID
    development_title: str
    disease: str
    asset_name: Optional[str] = None
    stage: str
    event_date: datetime
    notes: Optional[str] = None


class ContradictionItem(BaseModel):
    contradiction_id: UUID
    claim_a_id: str
    claim_b_id: str
    rule_id: str
    rule_name: str
    severity: str
    confidence: float
    confidence_type: str = "nli_heuristic"
    description: str
    detected_at: datetime
    claim_a_excerpt: Optional[str] = None
    claim_b_excerpt: Optional[str] = None
    claim_a_evidence_id: Optional[UUID] = None
    claim_b_evidence_id: Optional[UUID] = None
    detection_rule: Optional[str] = None
    resolution_status: Optional[str] = "unresolved"


class MissingSignalWatchItem(BaseModel):
    watch_id: UUID
    development_id: UUID
    development_title: Optional[str] = None
    trigger_event: str
    expected_event: str
    monitoring_window_days: int
    responsible_function: str
    status: str
    confidence: float = 0.5
    confidence_type: str = "overdue_heuristic"
    overdue_heuristic_score: Optional[float] = None
    days_overdue: int = 0
    created_at: datetime


class FunctionStatsResponse(BaseModel):
    function_id: str
    unreviewed_count: int
    in_review_count: int
    escalation_count: int
    total_decisions: int
    time_to_first_review_hours: Optional[float] = None
    time_to_final_decision_hours: Optional[float] = None
    recent_decisions: List[Any] = Field(default_factory=list)


class FunctionCalibrationProfile(BaseModel):
    function_name: str
    status: str
    feedback_sample_count: int
    min_required_samples: int = 20
    brier_score: Optional[float] = None
    ece_score: Optional[float] = None
    reliability_curve: List[Dict[str, float]] = Field(default_factory=list)


class CalibrationStatusResponse(BaseModel):
    profiles: List[FunctionCalibrationProfile] = Field(default_factory=list)
    total_feedback_samples: int = 0
    last_calibration_timestamp: Optional[datetime] = None


class LeadershipSummaryResponse(BaseModel):
    pending_escalations: List[Any] = Field(default_factory=list)
    critical_unreviewed: List[Any] = Field(default_factory=list)
    per_function_counts: Dict[str, Dict[str, int]] = Field(default_factory=dict)
    total_open_signals: int = 0
