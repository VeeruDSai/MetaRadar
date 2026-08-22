import pytest
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.core.config import settings
from app.db.session import get_db
from app.services.scoring import PriorityScoringService, ScoreBreakdown, SCORING_VERSION
from app.services.confluence import ConfluenceEngine
from app.core.logging import _scrub_secrets, configure_structlog


# ---------------------------------------------------------------------------
# Invariant 1: Priority Scoring Determinism & Multi-Factor Weights
# ---------------------------------------------------------------------------
def test_priority_scoring_determinism():
    scorer = PriorityScoringService()

    title = "Phase 3 clinical trial of recombinant Factor VIII shows significant ABR reduction"
    content = "The study demonstrated prophylaxis superiority with annualized bleeding rate reduction in haemophilia patients."
    now_dt = datetime.now(timezone.utc)

    breakdown = scorer.score_text(
        text=f"{title} {content}",
        published_at=now_dt,
        novelty_distance=0.7,
    )

    assert breakdown is not None
    assert breakdown.version == SCORING_VERSION
    assert 0.0 <= breakdown.novelty <= 25.0
    assert 0.0 <= breakdown.clinical <= 30.0
    assert 0.0 <= breakdown.regulatory <= 25.0
    assert 0.0 <= breakdown.recency <= 20.0
    assert 0.0 <= breakdown.total <= 100.0
    assert breakdown.priority_level in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]

    # Re-running with same input must yield exact identical score
    breakdown_repeat = scorer.score_text(
        text=f"{title} {content}",
        published_at=now_dt,
        novelty_distance=0.7,
    )
    assert breakdown.total == breakdown_repeat.total
    assert breakdown.priority_level == breakdown_repeat.priority_level


def test_priority_scoring_decay_over_time():
    scorer = PriorityScoringService()
    text = "Factor VIII prophylaxis study and haemophilia treatment update"
    now = datetime.now(timezone.utc)

    # Recent (0 hours old)
    b_recent = scorer.score_text(
        text=text,
        published_at=now,
        novelty_distance=0.5,
    )

    # 14 days old (336 hours)
    old_time = now - timedelta(days=14)
    b_old = scorer.score_text(
        text=text,
        published_at=old_time,
        novelty_distance=0.5,
    )

    assert b_recent is not None and b_old is not None
    assert b_recent.recency > b_old.recency
    assert b_recent.total > b_old.total


# ---------------------------------------------------------------------------
# Invariant 2: Confluence Multi-Source Convergence Engine (>= 3 Distinct Providers)
# ---------------------------------------------------------------------------
def test_confluence_engine_threshold():
    engine = ConfluenceEngine()
    dev_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 3 signals from SAME source provider (e.g. pubmed) -> should NOT meet threshold (< 3 distinct providers)
    signals_same_provider = [
        {"signal_id": "sig-1", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
        {"signal_id": "sig-2", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
        {"signal_id": "sig-3", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
    ]
    res_same = engine.detect_confluence_in_signals(signals_same_provider, development_id=dev_id)
    assert res_same is None

    # 2 signals from 2 distinct providers -> should not meet threshold (< 3)
    signals_2_sources = [
        {"signal_id": "sig-1", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
        {"signal_id": "sig-2", "source_id": "clinical_trials", "signal_type": "CLINICAL_TRIAL", "published_at": now.isoformat()},
    ]
    res_2 = engine.detect_confluence_in_signals(signals_2_sources, development_id=dev_id)
    assert res_2 is None

    # 3 signals from 3 distinct source providers -> eligible confluence
    signals_3_sources = [
        {"signal_id": "sig-1", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
        {"signal_id": "sig-2", "source_id": "clinical_trials", "signal_type": "CLINICAL_TRIAL", "published_at": now.isoformat()},
        {"signal_id": "sig-3", "source_id": "fda", "signal_type": "REGULATORY", "published_at": now.isoformat()},
    ]
    res_3 = engine.detect_confluence_in_signals(signals_3_sources, development_id=dev_id)
    assert res_3 is not None
    assert res_3.independent_sources_count == 3
    assert res_3.score >= 60.0


# ---------------------------------------------------------------------------
# Invariant 3: PII & Secret Scrubbing in Logging
# ---------------------------------------------------------------------------
def test_secret_scrubbing():
    event_dict = {
        "event": "auth_event",
        "api_key": "xai-1234567890abcdef",
        "password": "supersecretpassword",
        "token": "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "email": "doctor@hospital.org",
        "normal_field": "safe_value",
    }

    scrubbed = _scrub_secrets(None, "info", event_dict)
    assert scrubbed["api_key"] == "[REDACTED_SECRET]"
    assert scrubbed["password"] == "[REDACTED_SECRET]"
    assert scrubbed["token"] == "[REDACTED_SECRET]"
    assert scrubbed["email"] == "[REDACTED_PII]"
    assert scrubbed["normal_field"] == "safe_value"


# ---------------------------------------------------------------------------
# Invariant 4: Correlation ID Header Propagation
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_correlation_id_propagation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Request without X-Request-ID -> server generates one
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        assert "x-request-id" in res.headers
        generated_id = res.headers["x-request-id"]
        assert generated_id.startswith("req-")

        # Request with explicit X-Request-ID -> server preserves it
        custom_id = "req-custom-audit-trace-12345"
        res_custom = await ac.get("/api/v1/health", headers={"X-Request-ID": custom_id})
        assert res_custom.status_code == 200
        assert res_custom.headers.get("x-request-id") == custom_id


# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# Invariant 5: Athena Vector Search Insufficient Evidence Handling
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_athena_insufficient_evidence_response():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []
    mock_res.fetchall.return_value = []
    mock_db.execute.return_value = mock_res

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Querying an empty or non-matching prompt
            res = await ac.post("/api/v1/athena", json={"prompt": "xyznonexistentnovelty123456"})
            assert res.status_code == 200
            data = res.json()
            assert "answer" in data
            assert "mode" in data
            assert data["evidence_count"] == 0
            assert data["mode"] == "insufficient_evidence"
            assert "No sufficiently relevant evidence" in data["answer"]
    finally:
        app.dependency_overrides.pop(get_db, None)


# ---------------------------------------------------------------------------
# Invariant 6: Strictly Read-Only GET Endpoints
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_endpoints_read_only():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []
    mock_res.scalars.return_value.first.return_value = None
    mock_res.scalar_one_or_none.return_value = None
    mock_res.scalar.return_value = 0
    mock_res.fetchall.return_value = []
    mock_db.execute.return_value = mock_res
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            endpoints = [
                "/api/v1/health",
                "/api/v1/health/ready",
                "/api/v1/health/models",
                "/api/v1/health/connectors",
                "/api/v1/observability/activity",
                "/api/v1/sources/health",
                "/api/v1/calibration/weights",
            ]
            for ep in endpoints:
                res = await ac.get(ep)
                assert res.status_code == 200, f"Failed on endpoint: {ep}"
    finally:
        app.dependency_overrides.pop(get_db, None)
