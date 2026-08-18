import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

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
from app.workflows.nodes import node_calibrate, node_missing_signal
from app.workflows.runner import PipelineRunner
from app.workflows.state import create_initial_state


@pytest.mark.asyncio
async def test_e2e_hemgenix_durability_shift_scenario():
    """
    Scripted End-to-End Scenario Test (Master Plan §9 & SRS §2.8):
    1. Ingest 3 Hemgenix durability signals (PubMed + CSL Press Release + ASH Abstract).
    2. Execute full 10-node pipeline -> generate Confluence & Baseline Routing.
    3. Submit simulated Regulatory persona feedback (5-star relevance, comment with watch trigger).
    4. Execute batch recalibration via StakeholderCalibrationService.
    5. Assert BEFORE vs AFTER shift (score uplift e.g. 0.88 -> 0.97, priority CRITICAL).
    6. Confirm suggested watch rule (90-day congress window).
    7. Evaluate node_missing_signal with active watch rule.
    """
    # Step 1: Load Curated Synthetic Demo Dataset
    data_path = base_dir / "data" / "synthetic_signals.json"
    assert data_path.exists(), "data/synthetic_signals.json must exist"
    with open(data_path, "r", encoding="utf-8") as f:
        demo_signals = json.load(f)

    assert len(demo_signals) >= 3
    signal_types = {s["signal_type"] for s in demo_signals}
    assert "PUBLICATIONS" in signal_types
    assert "COMMERCIAL_PATENT" in signal_types
    assert "CONGRESS" in signal_types

    # Step 2: Run 10-Node Pipeline Batch
    runner = PipelineRunner()
    final_state = await runner.run(
        raw_signals=demo_signals,
        batch_size=10,
    )

    assert len(final_state["validated_signals"]) == 3
    assert len(final_state["developments"]) >= 1
    assert len(final_state["confluent_stories"]) >= 1
    assert len(final_state["role_briefs"]) >= 1

    # Verify Baseline Routing for Regulatory
    reg_brief = next(
        (b for b in final_state["role_briefs"] if "REGULATORY" in b.get("relevance_scores", {})),
        None,
    )
    assert reg_brief is not None
    base_reg_score = reg_brief["relevance_scores"]["REGULATORY"]
    assert base_reg_score > 0

    # Step 3: Mock Persistence Database Session for Calibration
    mock_db = AsyncMock()
    sig_uuid = uuid.uuid4()
    dev_uuid = uuid.uuid4()

    # Initial ScoringWeights: 1.0
    now = datetime.now(timezone.utc)
    reg_w_row = ScoringWeights(
        stakeholder_function="REGULATORY",
        impact_weight=1.0,
        urgency_weight=1.0,
        novelty_weight=1.0,
        updated_at=now,
    )
    res_weights = MagicMock()
    res_weights.scalars.return_value.all.return_value = [reg_w_row]
    res_hist = MagicMock()
    res_hist.scalar_one_or_none.return_value = CalibrationHistory(version="v1.0.0")

    # Step 4: Submit Simulated Regulatory Persona Feedback
    fb_row = CalibrationFeedback(
        feedback_id=uuid.uuid4(),
        signal_id=sig_uuid,
        stakeholder_function="REGULATORY",
        relevance_rating=5,
        urgency_rating=5,
        action_appropriate=True,
        comments="Critical 3-year durability data for Hemgenix; watch upcoming ASH 2026 congress abstracts for sustained Factor IX expression.",
        submitted_at=now,
    )
    res_fb = MagicMock()
    res_fb.scalars.return_value.all.return_value = [fb_row]

    res_db_w = MagicMock()
    res_db_w.scalar_one_or_none.return_value = reg_w_row

    # Baseline Routing Model
    routing_row = SignalRouting(
        routing_id=uuid.uuid4(),
        signal_id=sig_uuid,
        baseline_primary_function="REGULATORY",
        baseline_relevance_scores={"REGULATORY": 0.88, "MEDICAL_AFFAIRS": 0.65},
        baseline_suggested_action="Initial regulatory filing surveillance",
    )
    res_routing = MagicMock()
    res_routing.scalars.return_value.all.return_value = [routing_row]

    mock_db.execute.side_effect = [
        res_weights,
        res_hist,
        res_fb,
        res_db_w,
        res_routing,
    ]

    # Step 5: Execute Bounded Batch Recalibration
    service = StakeholderCalibrationService(mock_db)
    recal_result = await service.recalibrate_role("REGULATORY")

    assert recal_result.status == "recalibrated"
    assert recal_result.calibration_version == "v1.0.1"

    # Delta = 0.05 * (5.0 - 3.0) = +0.10 -> Impact Weight = 1.10
    updated_reg_w = next(w for w in recal_result.updated_weights if w.stakeholder_function == "REGULATORY")
    assert updated_reg_w.impact_weight == 1.10

    # Assert BEFORE vs AFTER Comparison
    assert len(recal_result.comparisons) == 1
    comp = recal_result.comparisons[0]
    expected_cal_score = round(min(1.0, 0.88 * 1.10), 2)
    assert comp.calibrated_relevance_score == expected_cal_score
    assert comp.calibrated_relevance_score > comp.baseline_relevance_score
    assert comp.calibrated_priority == "CRITICAL"
    assert comp.confidence_uplift_pct > 0.0

    # Step 6: Verify Keyword Watch Rule Extraction
    assert len(recal_result.watch_rule_suggestions) == 1
    sug = recal_result.watch_rule_suggestions[0]
    assert "ASH/ISTH Congress presentation" in sug.expected_event
    assert sug.monitoring_window_days == 90
    assert sug.responsible_function == "REGULATORY"

    # Step 7: Confirm Watch Item
    confirm_req = ConfirmWatchItemRequest(
        development_id=dev_uuid,
        trigger_event=sug.trigger_event,
        expected_event=sug.expected_event,
        monitoring_window_days=sug.monitoring_window_days,
        responsible_function=sug.responsible_function,
    )
    confirm_resp = await service.confirm_watch_item(confirm_req)
    assert confirm_resp.status == "watching"
    assert confirm_resp.monitoring_window_days == 90
    assert confirm_resp.responsible_function == "REGULATORY"

    # Step 8: Evaluate Watch Monitoring with node_missing_signal
    test_watch_state = {
        "developments": [
            {
                "development_id": str(dev_uuid),
                "asset_id": "Hemgenix (etranacogene dezaparvovec)",
                "current_stage": "post_market",
                "created_at": now.isoformat(),
            }
        ],
        "lifecycle_events": [
            {
                "development_id": str(dev_uuid),
                "event_date": now.isoformat(),
            }
        ],
        "redteam_flags": [],
        "scored_signals": [],
    }

    missing_out = await node_missing_signal(test_watch_state)
    assert missing_out["node_statuses"]["node_missing_signal"] == "SUCCESS"
