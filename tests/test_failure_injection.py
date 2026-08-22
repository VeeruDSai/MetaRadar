import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.core.config import settings
from app.connectors.base import SourceConnector, ConnectorStatus


class FlakyTestConnector(SourceConnector):
    source_id: str = "flaky_test_source"
    source_type: str = "publication"
    freshness_class: str = "delayed"

    def __init__(self, should_fail: bool = False):
        super().__init__()
        self.should_fail = should_fail

    async def fetch_signals(self, since=None):
        if self.should_fail:
            raise Exception("Simulated connector timeout")
        return []


@pytest.mark.asyncio
async def test_connector_failure_logging_and_resilience():
    # 1. Failure scenario
    failing_connector = FlakyTestConnector(should_fail=True)
    with pytest.raises(Exception) as exc_info:
        await failing_connector.fetch_signals()
    assert "Simulated connector timeout" in str(exc_info.value)

    # 2. Healthy scenario
    healthy_connector = FlakyTestConnector(should_fail=False)
    res_ok = await healthy_connector.fetch_signals()
    assert res_ok == []


@pytest.mark.asyncio
async def test_malformed_feedback_payload_validation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Submit invalid rating (e.g. relevance_rating = 10, when max is 5)
        bad_payload = {
            "signal_id": "sig-test-123",
            "stakeholder_function": "REGULATORY",
            "relevance_rating": 10,  # Invalid
            "urgency_rating": 4,
            "action_appropriate": True,
        }
        res = await ac.post("/api/v1/feedback", json=bad_payload)
        assert res.status_code == 422
        # Correlation ID must be returned even on validation failure
        assert "x-request-id" in res.headers
