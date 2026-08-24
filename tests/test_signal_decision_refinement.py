"""Test suite for Signal Decision Object refinement, Source Authority, Deterministic Routing, and Review Lifecycle.
"""

import pytest
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.db.session import get_db
from app.models import Signal, AuditLog
from app.services.authority import (
    SourceAuthorityTier,
    ValidationStatus,
    get_source_authority_tier,
    resolve_validation_status,
    get_source_credibility_breakdown,
)
from app.services.routing import (
    StakeholderFunction,
    resolve_signal_function,
    resolve_signal_routing,
    formulate_suggested_action,
)


def test_source_authority_hierarchy():
    """Verify machine-readable source authority classification."""
    assert get_source_authority_tier("fda") == SourceAuthorityTier.AUTHORITATIVE
    assert get_source_authority_tier("ema") == SourceAuthorityTier.AUTHORITATIVE
    assert get_source_authority_tier("clinical_trials") == SourceAuthorityTier.AUTHORITATIVE
    assert get_source_authority_tier("pubmed") == SourceAuthorityTier.AUTHORITATIVE
    assert get_source_authority_tier("ash") == SourceAuthorityTier.SECONDARY
    assert get_source_authority_tier("company_press") == SourceAuthorityTier.SECONDARY
    assert get_source_authority_tier("newsapi") == SourceAuthorityTier.DISCOVERY
    assert get_source_authority_tier("fierce_pharma") == SourceAuthorityTier.DISCOVERY


def test_discovery_source_validation_states():
    """Verify discovery sources do not automatically become authoritative evidence."""
    # Authoritative is naturally validated
    assert resolve_validation_status("fda") == ValidationStatus.VALIDATED
    assert resolve_validation_status("pubmed") == ValidationStatus.VALIDATED

    # Discovery source without corroboration is PENDING_VALIDATION
    assert resolve_validation_status("newsapi", is_corroborated=False) == ValidationStatus.PENDING_VALIDATION

    # Discovery source with authoritative corroboration is VALIDATED
    assert resolve_validation_status("newsapi", is_corroborated=True) == ValidationStatus.VALIDATED

    # Contradicted is CONTRADICTED
    assert resolve_validation_status("newsapi", is_contradicted=True) == ValidationStatus.CONTRADICTED


def test_source_credibility_breakdown():
    """Verify honest source diversity counts."""
    sources = ["fda", "pubmed", "newsapi"]
    breakdown = get_source_credibility_breakdown(sources)
    assert breakdown["total_sources"] == 3
    assert breakdown["authoritative_count"] == 2
    assert breakdown["discovery_count"] == 1
    assert breakdown["has_authoritative_anchor"] is True


def test_deterministic_function_routing():
    """Verify function mapping based on domain classification."""
    assert resolve_signal_function("CLINICAL_TRIAL") == StakeholderFunction.MEDICAL_AFFAIRS
    assert resolve_signal_function("PUBLICATIONS") == StakeholderFunction.MEDICAL_AFFAIRS
    assert resolve_signal_function("CONGRESS") == StakeholderFunction.MEDICAL_AFFAIRS
    assert resolve_signal_function("REGULATORY") == StakeholderFunction.REGULATORY
    assert resolve_signal_function("SAFETY") == StakeholderFunction.SAFETY
    assert resolve_signal_function("ACCESS") == StakeholderFunction.MARKET_ACCESS
    assert resolve_signal_function("COMMERCIAL_PATENT") == StakeholderFunction.LEADERSHIP
    assert resolve_signal_function("COMMUNICATIONS") == StakeholderFunction.COMMUNICATIONS


def test_leadership_escalation_policy():
    """Verify CRITICAL signals and high-impact approvals escalate to Leadership."""
    # 1. Standard High priority clinical signal -> Medical Affairs (Not escalated)
    routing_med = resolve_signal_routing(
        signal_type="CLINICAL_TRIAL",
        priority="HIGH",
        priority_score=75.0,
        title="Phase 2 trial interim results",
    )
    assert routing_med["relevant_function"] == "MEDICAL_AFFAIRS"
    assert routing_med["route_destination"] == "MEDICAL_AFFAIRS"
    assert routing_med["is_escalated"] is False
    assert routing_med["route_role"] == "FUNCTION"

    # 2. CRITICAL priority signal -> Leadership (Escalated)
    routing_crit = resolve_signal_routing(
        signal_type="CLINICAL_TRIAL",
        priority="CRITICAL",
        priority_score=92.0,
        title="Pivotal Phase 3 FRONTIER-2 Met All Endpoints",
    )
    assert routing_crit["is_escalated"] is True
    assert routing_crit["route_destination"] == "LEADERSHIP"
    assert routing_crit["route_role"] == "LEADERSHIP"
    assert "Escalated to Executive Leadership" in routing_crit["routing_reason"]


def _create_mock_signal(sig_id: uuid.UUID = None) -> Signal:
    """Helper to construct a mock Signal SQLAlchemy model instance."""
    now = datetime.now(timezone.utc)
    s = Signal(
        signal_id=sig_id or uuid.uuid4(),
        source_id="clinical_trials",
        source_name="ClinicalTrials.gov",
        source_tier=1,
        external_id="NCT04869267",
        nct_id="NCT04869267",
        fingerprint="fp_test_decision_01",
        canonical_url="https://clinicaltrials.gov/study/NCT04869267",
        signal_type="CLINICAL_TRIAL",
        disease="haemophilia_a",
        title="Phase 3 FRONTIER-2 Trial Evaluates Subcutaneous Mim8 in Haemophilia A",
        content="Primary outcome measures achieved zero-bleed status in treated cohorts.",
        published_at=now - timedelta(days=2),
        retrieved_at=now,
        ingested_at=now,
        data_mode="live",
        is_synthetic=False,
        provenance_status="available",
        evidence_text="Primary outcome measures achieved zero-bleed status in treated cohorts.",
        what_changed="Pivotal Phase 3 FRONTIER-2 met primary and secondary endpoints.",
        why_it_matters="Demonstrates best-in-class zero-bleed rate in Haemophilia A.",
        relevant_function="LEADERSHIP",
        route_destination="LEADERSHIP",
        route_role="LEADERSHIP",
        is_escalated=True,
        routing_reason="Escalated to Executive Leadership due to CRITICAL priority impact.",
        routing_timestamp=now,
        source_authority_tier="AUTHORITATIVE",
        validation_status="VALIDATED",
        suggested_action="Convene Executive Steering Committee to finalize global BLA submission.",
        action_rationale="Pivotal milestone represents key growth asset.",
        review_status="UNREVIEWED",
        facts=["Met primary endpoint with zero bleeds."],
        interpretation="High-potency Factor VIIIa-mimetic efficacy.",
        priority="CRITICAL",
        score_breakdown={
            "novelty": 23.5,
            "clinical": 28.5,
            "regulatory": 23.0,
            "recency": 15.0,
            "total": 90.0,
            "priority_level": "CRITICAL",
            "version": "haemophilia_v2.0",
        },
        scoring_model_version="haemophilia_v2.0",
        scoring_config_version="haemophilia_v1",
        embedding_model_version="v1",
        prompt_version="v1.0.0",
        created_at=now,
    )
    return s


@pytest.mark.asyncio
async def test_signal_decision_object_endpoint():
    """Verify /signals/{id} returns the complete decoupled decision object."""
    mock_signal = _create_mock_signal()
    mock_db = AsyncMock()

    mock_res_signals = MagicMock()
    mock_res_signals.scalars.return_value.all.return_value = [mock_signal]

    mock_res_count = MagicMock()
    mock_res_count.scalar.return_value = 1

    mock_res_single = MagicMock()
    mock_res_single.scalars.return_value.first.return_value = mock_signal

    mock_db.execute.side_effect = [mock_res_signals, mock_res_count, mock_res_single]

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/signals?limit=5")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["signals"]) == 1

            sig = data["signals"][0]
            assert sig["what_changed"] is not None
            assert sig["why_it_matters"] is not None
            assert sig["relevant_function"] == "LEADERSHIP"
            assert sig["is_escalated"] is True
            assert sig["source_authority_tier"] == "AUTHORITATIVE"
            assert sig["validation_status"] == "VALIDATED"
            assert sig["review_status"] == "UNREVIEWED"

            # Fetch detail by id
            detail_resp = await client.get(f"/api/v1/signals/{mock_signal.signal_id}")
            assert detail_resp.status_code == 200
            detail = detail_resp.json()

            # Verify trust boundary sub-objects
            assert "evidence" in detail
            assert len(detail["evidence"]) > 0
            assert detail["evidence"][0]["authority_tier"] == "AUTHORITATIVE"
            assert detail["interpretation_details"]["why_it_matters"] is not None
            assert detail["action_details"]["text"] is not None
            assert detail["review_details"]["status"] == "UNREVIEWED"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_signal_review_submission_and_audit_history():
    """Verify submitting a review persists review state and records an immutable audit log."""
    mock_signal = _create_mock_signal()
    mock_db = AsyncMock()

    mock_res_single = MagicMock()
    mock_res_single.scalars.return_value.first.return_value = mock_signal

    mock_audit = AuditLog(
        audit_id=uuid.uuid4(),
        entity_name="Signal",
        entity_id=str(mock_signal.signal_id),
        action="SIGNAL_REVIEWED",
        performed_by="Senior Medical Director",
        timestamp=datetime.now(timezone.utc),
        details={
            "previous_status": "UNREVIEWED",
            "new_status": "REVIEWED",
            "decision": "Approved for inclusion in clinical benchmark matrix",
            "notes": "Verified against peer-reviewed durability data.",
            "resulting_action": "Briefed rare disease commercial team.",
        }
    )

    mock_res_audit = MagicMock()
    mock_res_audit.scalars.return_value.all.return_value = [mock_audit]

    # 1. find signal for review POST
    # 2. find signal for audit GET
    # 3. find audit logs
    mock_db.execute.side_effect = [mock_res_single, mock_res_single, mock_res_audit]

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            review_payload = {
                "status": "REVIEWED",
                "reviewer": "Senior Medical Director",
                "decision": "Approved for inclusion in clinical benchmark matrix",
                "notes": "Verified against peer-reviewed durability data.",
                "resulting_action": "Briefed rare disease commercial team."
            }
            review_resp = await client.post(f"/api/v1/signals/{mock_signal.signal_id}/review", json=review_payload)
            assert review_resp.status_code == 200
            updated = review_resp.json()

            assert updated["review_status"] == "REVIEWED"
            assert updated["reviewed_by"] == "Senior Medical Director"

            # Fetch audit history
            audit_resp = await client.get(f"/api/v1/signals/{mock_signal.signal_id}/audit-history")
            assert audit_resp.status_code == 200
            audit_trail = audit_resp.json()
            assert len(audit_trail) == 1
            assert audit_trail[0]["action"] == "SIGNAL_REVIEWED"
            assert audit_trail[0]["performed_by"] == "Senior Medical Director"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_signal_decision_object_unified_endpoint():
    """Verify /signals/{id}/decision-object returns full structure with drill-downs."""
    mock_signal = _create_mock_signal()
    mock_db = AsyncMock()

    # 1. find signal
    mock_res_sig = MagicMock()
    mock_res_sig.scalars.return_value.first.return_value = mock_signal

    # 2. contradictions
    mock_res_contra = MagicMock()
    mock_res_contra.scalars.return_value.all.return_value = []

    # 3. confluence
    mock_res_conf = MagicMock()
    mock_res_conf.scalars.return_value.first.return_value = None

    mock_db.execute.side_effect = [mock_res_sig, mock_res_contra, mock_res_conf]

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            obj_resp = await client.get(f"/api/v1/signals/{mock_signal.signal_id}/decision-object")
            assert obj_resp.status_code == 200
            decision_obj = obj_resp.json()

            assert decision_obj["id"] == str(mock_signal.signal_id)
            assert decision_obj["what_changed"] is not None
            assert decision_obj["why_it_matters"] is not None
            assert decision_obj["priority"]["level"] == "CRITICAL"
            assert decision_obj["function"]["name"] == "LEADERSHIP"
            assert decision_obj["routing"]["is_escalated"] is True
            assert len(decision_obj["evidence"]) > 0
            assert decision_obj["interpretation"]["summary"] is not None
            assert decision_obj["suggested_action"]["text"] is not None
            assert decision_obj["review"]["status"] == "UNREVIEWED"
    finally:
        app.dependency_overrides.pop(get_db, None)
