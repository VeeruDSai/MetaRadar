from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel


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
    connector_status: str = "LIVE"
