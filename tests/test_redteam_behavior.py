import pytest
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.services.redteam import RedTeamNLIService, REDTEAM_RULES


@pytest.mark.asyncio
async def test_redteam_priority_gating():
    service = RedTeamNLIService(candidate_cap=5)
    claims = [
        {"claim_id": "c1", "priority": "LOW", "asset": "Hemgenix", "signal_type": "TRIAL"},
        {"claim_id": "c2", "priority": "HIGH", "asset": "Hemgenix", "signal_type": "REGULATORY"},
        {"claim_id": "c3", "priority": "CRITICAL", "asset": "Hemgenix", "signal_type": "REGULATORY"}
    ]
    candidates = service.filter_candidates(claims)
    # Priority gating filters out LOW priority
    assert len(candidates) == 2
    assert all(c["priority"] in ["HIGH", "CRITICAL"] for c in candidates)


@pytest.mark.asyncio
async def test_redteam_candidate_cap():
    service = RedTeamNLIService(candidate_cap=3)
    claims = [{"claim_id": f"c_{i}", "priority": "HIGH", "asset": "Asset"} for i in range(10)]
    candidates = service.filter_candidates(claims)
    assert len(candidates) == 3


@pytest.mark.asyncio
async def test_redteam_contradiction_eval_and_caching():
    service = RedTeamNLIService()
    claims = [
        {"claim_id": "c1", "asset": "Hemgenix", "signal_type": "CLINICAL_TRIAL", "priority": "HIGH", "source": "PubMed"},
        {"claim_id": "c2", "asset": "Hemgenix", "signal_type": "REGULATORY", "priority": "HIGH", "source": "FDA"}
    ]
    # First execution -> Evaluates and caches
    flags1 = await service.evaluate_contradictions(claims)
    assert len(flags1) == 1
    assert flags1[0]["rule_id"] == "RULE_A_DOSING_CONTRADICTION"

    # Second execution -> Served from cache
    flags2 = await service.evaluate_contradictions(claims)
    assert len(flags2) == 1
    assert flags2[0] == flags1[0]
