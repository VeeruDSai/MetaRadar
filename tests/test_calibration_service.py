import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.db.session import get_db
from app.main import app
from app.models import (
    CalibrationFeedback,
    CalibrationHistory,
    ScoringWeights,
    SignalRouting,
    WatchItem,
)
from app.schemas import (
    ConfirmWatchItemRequest,
    FeedbackSubmissionRequest,
)
from app.services.calibration import (
    HeuristicWatchParser,
    StakeholderCalibrationService,
)


def test_heuristic_watch_parser_matches_keywords():
    # Test congress match
    sug_congress = HeuristicWatchParser.parse(
        comment="Watch upcoming ASH 2026 congress abstracts for Hemgenix durability.",
        signal_id=uuid.uuid4(),
        responsible_function="REGULATORY",
    )
    assert sug_congress is not None
    assert "ASH/ISTH Congress presentation" in sug_congress.expected_event
    assert sug_congress.monitoring_window_days == 90
    assert sug_congress.responsible_function == "REGULATORY"

    # Test trial match
    sug_trial = HeuristicWatchParser.parse(
        comment="Phase 3 trial cohort analysis expected soon.",
        responsible_function="MEDICAL_AFFAIRS",
    )
    assert sug_trial is not None
    assert "Clinical trial" in sug_trial.expected_event
    assert sug_trial.monitoring_window_days == 180

    # Test safety match
    sug_safety = HeuristicWatchParser.parse(
        comment="Monitor safety inhibitor titers carefully.",
        responsible_function="SAFETY",
    )
    assert sug_safety is not None
    assert "Safety surveillance" in sug_safety.expected_event
    assert sug_safety.monitoring_window_days == 90

    # Test non-matching comment
    sug_none = HeuristicWatchParser.parse(
        comment="Looks reasonable, no action needed.",
        responsible_function="LEADERSHIP",
    )
    assert sug_none is None


@pytest.mark.asyncio
async def test_calibration_service_submit_feedback():
    mock_db = AsyncMock()
    
    # Mock unapplied count
    res_count = MagicMock()
    res_count.scalar_one.return_value = 3
    mock_db.execute.return_value = res_count

    service = StakeholderCalibrationService(mock_db)
    req = FeedbackSubmissionRequest(
        signal_id=uuid.uuid4(),
        stakeholder_function="REGULATORY",
        relevance_rating=5,
        urgency_rating=4,
        action_appropriate=True,
        comments="Watch upcoming ASH 2026 data",
    )

    resp = await service.submit_feedback(req)
    assert resp.status == "recorded"
    assert resp.stakeholder_function == "REGULATORY"
    assert resp.unapplied_count == 3
    assert resp.recalibration_triggered is True
    assert mock_db.add.called
    assert mock_db.commit.called


@pytest.mark.asyncio
async def test_calibration_service_get_weights_seeding():
    mock_db = AsyncMock()
    
    # 1. Scoring weights query (returns empty -> seeds 6 functions)
    res_weights = MagicMock()
    res_weights.scalars.return_value.all.return_value = []
    
    # 2. History query (returns empty -> version v1.0.0)
    res_hist = MagicMock()
    res_hist.scalar_one_or_none.return_value = None

    mock_db.execute.side_effect = [res_weights, res_hist]

    service = StakeholderCalibrationService(mock_db)
    resp = await service.get_weights()

    assert resp.version == "v1.0.0"
    assert len(resp.weights) == 6
    for w in resp.weights:
        assert w.impact_weight == 1.0
        assert w.urgency_weight == 1.0


@pytest.mark.asyncio
async def test_calibration_service_recalibrate_role_bounded_math():
    mock_db = AsyncMock()

    # 1. get_weights() execution: existing rows
    now = datetime.now(timezone.utc)
    w_row = ScoringWeights(
        stakeholder_function="REGULATORY",
        impact_weight=1.0,
        urgency_weight=1.0,
        novelty_weight=1.0,
        updated_at=now,
    )
    res_weights = MagicMock()
    res_weights.scalars.return_value.all.return_value = [w_row]
    res_hist = MagicMock()
    res_hist.scalar_one_or_none.return_value = CalibrationHistory(version="v1.0.0")

    # 2. Query feedback: 2 feedback entries (relevance 5 and 5 -> avg 5.0; delta = 0.05*(5-3)=+0.10)
    sig_id = uuid.uuid4()
    fb1 = CalibrationFeedback(
        feedback_id=uuid.uuid4(),
        signal_id=sig_id,
        stakeholder_function="REGULATORY",
        relevance_rating=5,
        urgency_rating=5,
        action_appropriate=True,
        comments="Watch upcoming ASH 2026 abstract",
    )
    fb2 = CalibrationFeedback(
        feedback_id=uuid.uuid4(),
        signal_id=sig_id,
        stakeholder_function="REGULATORY",
        relevance_rating=5,
        urgency_rating=5,
        action_appropriate=True,
        comments="Critical durability follow-up",
    )
    res_feedback = MagicMock()
    res_feedback.scalars.return_value.all.return_value = [fb1, fb2]

    # 3. DB select for weights update
    res_db_w = MagicMock()
    res_db_w.scalar_one_or_none.return_value = w_row

    # 4. Routing rows
    routing_row = SignalRouting(
        routing_id=uuid.uuid4(),
        signal_id=sig_id,
        baseline_primary_function="REGULATORY",
        baseline_relevance_scores={"REGULATORY": 0.88, "MEDICAL_AFFAIRS": 0.70},
        baseline_suggested_action="Initial baseline regulatory review",
    )
    res_routing = MagicMock()
    res_routing.scalars.return_value.all.return_value = [routing_row]

    mock_db.execute.side_effect = [
        res_weights,
        res_hist,
        res_feedback,
        res_db_w,
        res_routing,
    ]

    service = StakeholderCalibrationService(mock_db)
    resp = await service.recalibrate_role("REGULATORY")

    assert resp.status == "recalibrated"
    assert resp.applied_feedback_count == 2
    assert resp.calibration_version == "v1.0.1"

    # Verify updated weights: impact 1.0 + 0.10 = 1.10
    reg_weight = next(w for w in resp.updated_weights if w.stakeholder_function == "REGULATORY")
    assert reg_weight.impact_weight == 1.10
    assert reg_weight.urgency_weight == 1.10

    # Verify comparisons: calibrated score min(1.0, 0.88 * 1.10) = 0.97
    assert len(resp.comparisons) == 1
    comp = resp.comparisons[0]
    assert comp.calibrated_relevance_score == 0.97
    assert comp.baseline_relevance_score == 0.88
    assert comp.confidence_uplift_pct > 0

    # Verify watch rule suggestions
    assert len(resp.watch_rule_suggestions) >= 1
    assert "ASH/ISTH Congress presentation" in resp.watch_rule_suggestions[0].expected_event


@pytest.mark.asyncio
async def test_feedback_endpoints_api():
    mock_db = AsyncMock()

    # Feedback submit mock
    res_count = MagicMock()
    res_count.scalar_one.return_value = 1
    mock_db.execute.return_value = res_count

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # 1. POST /api/v1/feedback
            payload = {
                "signal_id": str(uuid.uuid4()),
                "stakeholder_function": "REGULATORY",
                "relevance_rating": 5,
                "urgency_rating": 4,
                "action_appropriate": True,
                "comments": "Watch upcoming congress abstract",
            }
            res = await ac.post("/api/v1/feedback", json=payload)
            assert res.status_code == 201
            data = res.json()
            assert data["status"] == "recorded"

            # 2. GET /api/v1/calibration/weights
            res_weights = MagicMock()
            res_weights.scalars.return_value.all.return_value = []
            res_hist = MagicMock()
            res_hist.scalar_one_or_none.return_value = None
            mock_db.execute.side_effect = [res_weights, res_hist]

            res_w = await ac.get("/api/v1/calibration/weights")
            assert res_w.status_code == 200
            data_w = res_w.json()
            assert "weights" in data_w

            # 3. POST /api/v1/watch-items/confirm
            confirm_payload = {
                "development_id": str(uuid.uuid4()),
                "trigger_event": "3-year durability follow-up",
                "expected_event": "ASH 2026 congress publication",
                "monitoring_window_days": 90,
                "responsible_function": "REGULATORY",
            }
            res_c = await ac.post("/api/v1/watch-items/confirm", json=confirm_payload)
            assert res_c.status_code == 201
            data_c = res_c.json()
            assert data_c["status"] == "watching"
            assert data_c["monitoring_window_days"] == 90

    finally:
        app.dependency_overrides.pop(get_db, None)
