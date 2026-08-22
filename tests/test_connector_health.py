import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from app.api.v1.endpoints.health import get_health_connectors
from app.models import Source, SourceHealthLog
from app.connectors.base import SourceConnector, ProfileRunResult
from app.core.config import settings


@pytest.mark.asyncio
async def test_connector_health_endpoint_configuration_error(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "")

    # Mock DB session returning real source rows
    mock_db = AsyncMock()
    mock_source = MagicMock(spec=Source)
    mock_source.source_id = "newsapi"
    mock_source.name = "NewsAPI Commercial Signals"
    mock_source.connector_status = "CONFIGURATION_ERROR"
    mock_source.configuration_error_message = "NEWSAPI_KEY missing"
    mock_source.latency_ms = None
    mock_source.http_status = None
    mock_source.records_fetched = 0
    mock_source.records_accepted = 0
    mock_source.records_rejected = 0
    mock_source.last_attempted = None
    mock_source.last_success = None
    mock_source.is_active = True

    mock_db_res = MagicMock()
    mock_db_res.scalars.return_value.all.return_value = [mock_source]
    mock_db.execute.return_value = mock_db_res

    res = await get_health_connectors(session=mock_db)
    assert len(res.connectors) >= 1
    newsapi_status = next(s for s in res.connectors if s.source_id == "newsapi")
    assert newsapi_status.connector_status == "CONFIGURATION_ERROR"
    assert newsapi_status.configuration_error_message is not None
    assert "NEWSAPI_KEY" in newsapi_status.configuration_error_message
    assert newsapi_status.http_status is None


@pytest.mark.asyncio
async def test_connector_base_health_mapping_precedence():
    class DummyConnector(SourceConnector):
        source_id = "dummy"
        name = "Dummy"
        base_url = "https://example.com"

        def _get_profiles(self):
            return {}

        async def fetch(self, profile, session, run_mode):
            return []

        def transform(self, raw_item, profile):
            return []

    conn = DummyConnector()
    assert conn._run_status_to_health_state("CONFIGURATION_ERROR") == "CONFIGURATION_ERROR"
    assert conn._run_status_to_health_state("FAILED") == "UNHEALTHY"
    assert conn._run_status_to_health_state("DEGRADED") == "DEGRADED"
    assert conn._run_status_to_health_state("PARTIAL") == "DEGRADED"
    assert conn._run_status_to_health_state("SUCCESS") == "HEALTHY"


@pytest.mark.asyncio
async def test_source_health_log_unprobed_http_status_none():
    class DummyConnector(SourceConnector):
        source_id = "dummy"
        name = "Dummy"
        base_url = "https://example.com"

        def _get_profiles(self):
            return {}

        async def fetch(self, profile, session, run_mode):
            return []

        def transform(self, raw_item, profile):
            return []

    conn = DummyConnector()
    mock_session = AsyncMock()
    result = ProfileRunResult(
        profile_id="test",
        status="CONFIGURATION_ERROR",
        duration_s=0.01,
        fetched=0,
        new_rows=0,
        duplicates=0,
        errors=0,
        error_detail="Missing credentials",
    )

    await conn._persist_health_log(mock_session, result, http_status=None)

    # Verify log entry added with http_status=None
    added_objs = [call[0][0] for call in mock_session.add.call_args_list]
    assert len(added_objs) == 1
    log = added_objs[0]
    assert isinstance(log, SourceHealthLog)
    assert log.connector_status == "CONFIGURATION_ERROR"
    assert log.http_status is None
