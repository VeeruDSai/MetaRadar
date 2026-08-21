import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.ingestion import IngestionService
from app.connectors.base import ProfileRunResult
from app.core.config import settings


@pytest.mark.asyncio
async def test_ingestion_minimum_records_degraded_rule(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "dummy_key")

    # Mock session
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_src_res = MagicMock()
    mock_src_res.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_src_res

    # Create mock connector that returns 0 fetched records with SUCCESS status
    mock_conn = MagicMock()
    mock_conn.source_id = "pubmed"
    mock_conn.run_all_profiles = AsyncMock(return_value=[
        ProfileRunResult(
            profile_id="haemophilia_literature",
            status="SUCCESS",
            duration_s=0.5,
            fetched=0,
            new_rows=0,
            duplicates=0,
            errors=0,
        )
    ])
    mock_conn._resolve_run_status.return_value = "SUCCESS"

    monkeypatch.setattr("app.services.ingestion.ALL_CONNECTORS", [mock_conn])

    svc = IngestionService(mock_session)
    results = await svc.run_connectors(["pubmed"])

    pubmed_res = results["results"]["pubmed"]
    # Minimum-records rule: 0 records fetched must result in DEGRADED status
    assert pubmed_res["status"] == "DEGRADED"
    assert "0 records fetched" in (pubmed_res["error_detail"] or "")


@pytest.mark.asyncio
async def test_ingestion_all_duplicates_degraded_rule(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "dummy_key")

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_src_res = MagicMock()
    mock_src_res.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_src_res

    mock_conn = MagicMock()
    mock_conn.source_id = "clinical_trials"
    mock_conn.run_all_profiles = AsyncMock(return_value=[
        ProfileRunResult(
            profile_id="haemophilia_interventional",
            status="SUCCESS",
            duration_s=0.5,
            fetched=5,
            new_rows=0,
            duplicates=5,
            errors=0,
        )
    ])
    mock_conn._resolve_run_status.return_value = "SUCCESS"

    monkeypatch.setattr("app.services.ingestion.ALL_CONNECTORS", [mock_conn])

    svc = IngestionService(mock_session)
    results = await svc.run_connectors(["clinical_trials"])

    ct_res = results["results"]["clinical_trials"]
    # 0 new accepted records must result in DEGRADED status
    assert ct_res["status"] == "DEGRADED"
    assert "0 new records accepted" in (ct_res["error_detail"] or "")


@pytest.mark.asyncio
async def test_ingestion_healthy_when_records_accepted(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "dummy_key")

    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_src_res = MagicMock()
    mock_src_res.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_src_res

    mock_conn = MagicMock()
    mock_conn.source_id = "pubmed"
    mock_conn.run_all_profiles = AsyncMock(return_value=[
        ProfileRunResult(
            profile_id="haemophilia_literature",
            status="SUCCESS",
            duration_s=0.5,
            fetched=10,
            new_rows=8,
            duplicates=2,
            errors=0,
        )
    ])
    mock_conn._resolve_run_status.return_value = "SUCCESS"

    monkeypatch.setattr("app.services.ingestion.ALL_CONNECTORS", [mock_conn])

    svc = IngestionService(mock_session)
    results = await svc.run_connectors(["pubmed"])

    pubmed_res = results["results"]["pubmed"]
    assert pubmed_res["status"] == "HEALTHY"
    assert pubmed_res["fetched"] == 10
    assert pubmed_res["new_rows"] == 8
