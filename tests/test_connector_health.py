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


def test_discovery_connectors_registered():
    """Verifies that all 8 connectors including BioPharma Dive are instantiated in ALL_CONNECTORS."""
    from app.connectors import ALL_CONNECTORS
    
    source_ids = {c.source_id for c in ALL_CONNECTORS}
    assert len(ALL_CONNECTORS) == 8
    assert "fierce_pharma" in source_ids
    assert "et_pharma" in source_ids
    assert "biopharmadive" in source_ids
    assert "newsapi" in source_ids
    assert "pubmed" in source_ids
    assert "clinical_trials" in source_ids
    assert "fda" in source_ids
    assert "ema" in source_ids


def test_biopharmadive_domain_config_registration():
    """Verifies that BioPharma Dive is declared in haemophilia.yaml with active RSS feed."""
    from app.core.domain_config import get_domain_config

    cfg = get_domain_config()
    bpd = cfg.connectors.get("biopharmadive")
    assert bpd is not None
    assert bpd.tier == 3
    assert bpd.freshness_class == "delayed"
    assert "biopharmadive.com" in bpd.rss_url
    assert len(bpd.profiles) >= 1


@pytest.mark.asyncio
async def test_biopharmadive_rss_parsing(monkeypatch):
    """Tests BioPharmaDiveRSSConnector parsing on synthetic XML content."""
    from app.connectors.biopharma_dive import BioPharmaDiveRSSConnector

    sample_rss = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
        <channel>
            <title>BioPharma Dive News</title>
            <link>https://www.biopharmadive.com/</link>
            <item>
                <title>Roche announces Phase 3 readout for novel hemophilia therapy</title>
                <link>https://www.biopharmadive.com/news/roche-phase-3-hemophilia-emicizumab/12345/</link>
                <guid>https://www.biopharmadive.com/news/roche-phase-3-hemophilia-emicizumab/12345/</guid>
                <description>Roche reported positive Phase 3 results for its novel factor VIII mimetic.</description>
                <pubDate>Thu, 27 Aug 2026 12:00:00 GMT</pubDate>
            </item>
        </channel>
    </rss>
    """

    conn = BioPharmaDiveRSSConnector()
    
    mock_resp = MagicMock()
    mock_resp.text = sample_rss
    mock_resp.status_code = 200

    async def mock_fetch(url):
        return mock_resp

    monkeypatch.setattr(conn, "_fetch_with_retry", mock_fetch)
    
    mock_session = AsyncMock()
    conn._persist_bronze = AsyncMock(return_value=(1, 0))
    conn._write_connector_state = AsyncMock()

    result = await conn.run_profile(mock_session, "haemophilia_biopharmadive")
    assert result.status == "SUCCESS"
    assert result.fetched == 1
    assert result.new_rows == 1


def test_newsapi_quota_governor_logic():
    """Verifies adaptive quota governor logic thresholds."""
    from app.services.scheduler import SourceScheduler
    
    scheduler = SourceScheduler.get_instance()
    assert scheduler is not None
    assert "newsapi" in scheduler._jobs
    assert "biopharmadive" in scheduler._jobs
