import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.db.session import AsyncSessionLocal
from app.models import Signal


def make_signal(
    signal_id: uuid.UUID,
    source_id: str,
    title: str,
    relevant_function: str,
    review_status: str = "UNREVIEWED",
    priority: str = "HIGH",
    is_escalated: bool = False,
    reviewed_at: datetime = None,
) -> Signal:
    now_utc = datetime.now(timezone.utc)
    return Signal(
        signal_id=signal_id,
        source_id=source_id,
        fingerprint=f"fp-{uuid.uuid4().hex[:16]}",
        signal_type="CLINICAL_TRIAL",
        disease="Haemophilia A",
        title=title,
        content=f"Content for {title}",
        published_at=now_utc - timedelta(hours=4),
        retrieved_at=now_utc,
        ingested_at=now_utc,
        relevant_function=relevant_function,
        review_status=review_status,
        priority=priority,
        is_escalated=is_escalated,
        reviewed_at=reviewed_at or (now_utc if review_status != "UNREVIEWED" else None),
    )


@pytest.mark.asyncio
async def test_function_operational_stats_and_dual_metrics():
    sig1_id = uuid.uuid4()
    sig2_id = uuid.uuid4()
    sig3_id = uuid.uuid4()

    async with AsyncSessionLocal() as db:
        s1 = make_signal(sig1_id, "fda", "S1 Pending", "SAFETY", "UNREVIEWED", "CRITICAL")
        s2 = make_signal(sig2_id, "fda", "S2 In Review", "SAFETY", "IN_REVIEW", "HIGH", is_escalated=True)
        s3 = make_signal(sig3_id, "fda", "S3 Actioned", "SAFETY", "ACTIONED", "CRITICAL")
        db.add_all([s1, s2, s3])
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.get("/api/v1/function-stats/SAFETY")
        assert res.status_code == 200
        data = res.json()
        assert data["function_id"] == "SAFETY"
        assert data["unreviewed_count"] >= 1
        assert data["in_review_count"] >= 1
        assert data["escalation_count"] >= 1
        assert data["time_to_first_review_hours"] is not None
        assert data["time_to_final_decision_hours"] is not None
        assert len(data["recent_decisions"]) >= 1


@pytest.mark.asyncio
async def test_per_function_calibration_status_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.get("/api/v1/calibration/status")
        assert res.status_code == 200
        data = res.json()
        assert "profiles" in data
        assert len(data["profiles"]) == 6

        profiles_by_fn = {p["function_name"]: p for p in data["profiles"]}
        
        # Calibration status is derived from real feedback, never seeded with
        # fabricated sample counts or reliability metrics.
        for function_name in ("MEDICAL_AFFAIRS", "REGULATORY", "SAFETY"):
            profile = profiles_by_fn[function_name]
            expected_status = "calibrated" if profile["feedback_sample_count"] >= 20 else "insufficient_data"
            assert profile["status"] == expected_status
            assert profile["brier_score"] is None
            assert profile["ece_score"] is None
            assert profile["reliability_curve"] == []

        # Verify insufficient data profiles
        assert profiles_by_fn["MARKET_ACCESS"]["status"] == "insufficient_data"
        assert profiles_by_fn["COMMUNICATIONS"]["status"] == "insufficient_data"

        # Verify leadership aggregate profile
        assert profiles_by_fn["LEADERSHIP"]["status"] == "not_applicable"


@pytest.mark.asyncio
async def test_leadership_summary_authorization_and_aggregation():
    # 1. Non-leadership role -> 403 Forbidden
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_med:
        await ac_med.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        res_med = await ac_med.get("/api/v1/leadership/summary")
        assert res_med.status_code == 403

    # 2. Leadership role -> 200 OK with cross-functional summary
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_lead:
        await ac_lead.post("/api/v1/auth/demo-login", json={"role": "LEADERSHIP"})
        res_lead = await ac_lead.get("/api/v1/leadership/summary")
        assert res_lead.status_code == 200
        data = res_lead.json()
        assert "pending_escalations" in data
        assert "critical_unreviewed" in data
        assert "per_function_counts" in data
        assert "MEDICAL_AFFAIRS" in data["per_function_counts"]
        assert "SAFETY" in data["per_function_counts"]
        assert data["total_open_signals"] >= 0
