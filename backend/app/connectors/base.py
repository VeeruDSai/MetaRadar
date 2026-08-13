from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class RawSignalPayload(BaseModel):
    source_id: str
    source_type: str
    external_id: str
    title: str
    content: str
    url: Optional[str] = None
    published_at: datetime
    retrieved_at: datetime = Field(default_factory=datetime.utcnow)
    publisher: Optional[str] = None
    raw_hash: str


class ConnectorStatus(BaseModel):
    source_id: str
    status: str  # active | degraded | error | idle
    quota_remaining: Optional[int] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None


class SourceConnector:
    source_id: str = "base"
    freshness_class: str = "batch"  # real_time | near_real_time | delayed | batch | adapter_ready | synthetic

    def __init__(self):
        self.status = "idle"
        self.quota_remaining: Optional[int] = None
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None

    async def fetch_latest(self, limit: int = 50) -> List[RawSignalPayload]:
        raise NotImplementedError

    def get_status(self) -> ConnectorStatus:
        return ConnectorStatus(
            source_id=self.source_id,
            status=self.status,
            quota_remaining=self.quota_remaining,
            last_success=self.last_success,
            last_error=self.last_error
        )
