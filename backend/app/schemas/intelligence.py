from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class ConfluenceAlertItem(BaseModel):
    confluence_id: UUID
    development_id: UUID
    development_title: Optional[str] = None
    signal_count: int
    confluence_type: str
    created_at: datetime
    signals: List[Dict[str, Any]] = Field(default_factory=list)


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
    description: str
    detected_at: datetime
    claim_a_excerpt: Optional[str] = None
    claim_b_excerpt: Optional[str] = None


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
    days_overdue: int = 0
    created_at: datetime
