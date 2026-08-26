import pytest
import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.models import Signal, AuditLog, Source
from app.db.session import get_db


def _create_test_signal(sig_id: uuid.UUID) -> Signal:
    now_dt = datetime.now(timezone.utc)
    return Signal(
        signal_id=sig_id,
        source_id="clinical_trials",
        source_name="ClinicalTrials.gov",
        nct_id="NCT09999999",
        external_id="NCT09999999",
        fingerprint=f"sig:ct:NCT09999999:{sig_id}",
        canonical_url="https://clinicaltrials.gov/study/NCT09999999",
        signal_type="CLINICAL_TRIAL",
        disease="haemophilia_a",
        title="Phase 3 Study of Next-Generation FVIIIa Mimetic Prophylaxis",
        content="Demonstrated substantial reduction in annualized bleed rates compared to standard of care.",
        evidence_text="Demonstrated substantial reduction in annualized bleed rates compared to standard of care.",
        provenance_status="available",
        data_mode="test_fixture",
        is_synthetic=False,
        priority="HIGH",
        review_status="UNREVIEWED",
        relevant_function="MEDICAL_AFFAIRS",
        route_destination="MEDICAL_AFFAIRS",
        route_role="FUNCTION",
        is_escalated=False,
        published_at=now_dt,
        retrieved_at=now_dt,
        ingested_at=now_dt,
        created_at=now_dt,
    )


@pytest.mark.asyncio
async def test_signal_review_lifecycle_state_machine():
    """
    Tests the complete end-to-end review lifecycle:
    1. UNREVIEWED (initial state)
    2. Acknowledge -> IN_REVIEW + AuditLog created
    3. Review & Approve -> REVIEWED with decision & reviewer persisted
    4. Action -> ACTIONED with resulting_action recorded
    5. Verify chronological AuditLog history via GET /signals/{id}/audit-history
    """
    sig_id = uuid.uuid4()
    signal = _create_test_signal(sig_id)

    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    audit_logs = []

    def mock_add(instance):
        if isinstance(instance, AuditLog):
            if not getattr(instance, "audit_id", None):
                instance.audit_id = uuid.uuid4()
            audit_logs.append(instance)

    mock_db.add.side_effect = mock_add

    # Mock execute handling
    async def mock_execute(query):
        mock_res = MagicMock()
        q_str = str(query)
        if "FROM audit_log" in q_str:
            mock_res.scalars.return_value.all.return_value = list(audit_logs)
        else:
            mock_res.scalars.return_value.first.return_value = signal
        return mock_res

    mock_db.execute.side_effect = mock_execute
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Step 1: Verify Initial State
            resp = await client.get(f"/api/v1/signals/{sig_id}")
            assert resp.status_code == 200
            data = resp.json()
            assert data["review_status"] == "UNREVIEWED"
            assert data["reviewed_by"] is None

            # Step 2: Transition UNREVIEWED -> IN_REVIEW (Acknowledge)
            ack_payload = {
                "status": "IN_REVIEW",
                "reviewer": "Demo Regulatory Affairs Reviewer",
                "notes": "Acknowledged by Regulatory Affairs for label assessment.",
            }
            resp = await client.post(f"/api/v1/signals/{sig_id}/review", json=ack_payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["review_status"] == "IN_REVIEW"
            assert data["reviewed_by"] == "Demo Regulatory Affairs Reviewer"

            # Step 3: Transition IN_REVIEW -> REVIEWED (Approve)
            approve_payload = {
                "status": "REVIEWED",
                "reviewer": "Demo Regulatory Affairs Reviewer",
                "decision": "APPROVED",
                "notes": "Trial readout verified against baseline parameters.",
            }
            resp = await client.post(f"/api/v1/signals/{sig_id}/review", json=approve_payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["review_status"] == "REVIEWED"
            assert data["review_decision"] == "APPROVED"
            assert data["reviewed_by"] == "Demo Regulatory Affairs Reviewer"

            # Step 4: Transition REVIEWED -> ACTIONED (Record Resulting Action)
            action_payload = {
                "status": "ACTIONED",
                "reviewer": "Demo Regulatory Affairs Reviewer",
                "resulting_action": "Briefed cross-functional team and initiated label comparison matrix update.",
            }
            resp = await client.post(f"/api/v1/signals/{sig_id}/review", json=action_payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["review_status"] == "ACTIONED"
            assert data["resulting_action"] == "Briefed cross-functional team and initiated label comparison matrix update."

            # Step 5: Verify Audit History via GET /signals/{id}/audit-history
            audit_resp = await client.get(f"/api/v1/signals/{sig_id}/audit-history")
            assert audit_resp.status_code == 200
            history = audit_resp.json()
            assert len(history) == 3
            actions = [item["action"] for item in history]
            assert all(a == "SIGNAL_REVIEWED" for a in actions)
            assert history[0]["performed_by"] == "Demo Regulatory Affairs Reviewer"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_signal_review_invalid_status():
    """Asserts that submitting an invalid review status raises HTTP 400 Bad Request."""
    sig_id = uuid.uuid4()
    signal = _create_test_signal(sig_id)

    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = signal
    mock_db.execute.return_value = mock_res

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            invalid_payload = {
                "status": "INVALID_STATE_NAME",
                "reviewer": "Test Reviewer",
            }
            resp = await client.post(f"/api/v1/signals/{sig_id}/review", json=invalid_payload)
            assert resp.status_code == 400
            assert "Invalid review status" in resp.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_signal_review_nonexistent_signal():
    """Asserts that reviewing a non-existent signal returns HTTP 404 Not Found."""
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.first.return_value = None
    mock_db.execute.return_value = mock_res

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            fake_uuid = str(uuid.uuid4())
            resp = await client.post(
                f"/api/v1/signals/{fake_uuid}/review",
                json={"status": "IN_REVIEW", "reviewer": "Test Reviewer"}
            )
            assert resp.status_code == 404
            assert "not found" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)
