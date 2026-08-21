from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class DevelopmentSummary(BaseModel):
    development_id: UUID
    title: str
    disease: str
    current_stage: str
    asset_name: Optional[str] = None
    company_name: Optional[str] = None
    signal_count: int = 0
    created_at: datetime
    updated_at: datetime


class SourceRegistryItem(BaseModel):
    source_id: str
    name: str
    freshness_class: str
    syndication_group: Optional[str] = None
    status: str
    quota_remaining: Optional[int] = None
    last_success: Optional[datetime] = None
    connector_status: str = "NEVER_CONNECTED"
    last_attempted: Optional[datetime] = None
    latency_ms: Optional[int] = None
    records_fetched: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    http_status: Optional[int] = None
    configuration_error_message: Optional[str] = None


class SourceHealthLogItem(BaseModel):
    id: UUID
    source_id: str
    pipeline_run_id: Optional[UUID] = None
    checked_at: datetime
    connector_status: str
    http_status: Optional[int] = None
    latency_ms: Optional[int] = None
    records_fetched: int = 0
    records_accepted: int = 0
    records_rejected: int = 0
    last_error: Optional[str] = None
    error_code: Optional[str] = None
