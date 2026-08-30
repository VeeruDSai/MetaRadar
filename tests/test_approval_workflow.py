import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select

from app.main import app
from app.db.session import AsyncSessionLocal
from app.models import Signal, AuditLog, ApprovalRequest
from app.core.security import SESSION_COOKIE_NAME, CSRF_COOKIE_NAME


async def create_test_signal(db) -> Signal:
    """Helper to create a test signal for approval testing."""
    signal = Signal(
        source_id="clinical_trials",
        signal_type="TRIAL_UPDATE",
        disease="Haemophilia A",
        title=f"Approval Workflow Pipeline Signal {uuid.uuid4().hex[:8]}",
        content="Phase III evaluation of NXT007 shows significant reduction in annualized bleeding rate.",
        fingerprint=f"approval-fp-{uuid.uuid4().hex[:12]}",
        priority="CRITICAL",
        relevant_function="MEDICAL_AFFAIRS",
        published_at=datetime.now(timezone.utc),
        retrieved_at=datetime.now(timezone.utc),
    )
    db.add(signal)
    await db.commit()
    await db.refresh(signal)
    return signal


@pytest.mark.asyncio
async def test_medical_affairs_requests_approval():
    async with AsyncSessionLocal() as db:
        sig = await create_test_signal(db)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"},
    ) as client:
        # Login as Medical Affairs
        login_res = await client.post(
            "/api/v1/auth/demo-login",
            json={"role": "MEDICAL_AFFAIRS"},
        )
        assert login_res.status_code == 200
        csrf_token = client.cookies.get(CSRF_COOKIE_NAME)

        # Request Approval
        res = await client.post(
            f"/api/v1/signals/{sig.signal_id}/request-approval",
            json={
                "request_note": "Immediate executive steer needed on competitor Phase III readout",
                "urgency": "CRITICAL",
            },
            headers={"X-CSRF-Token": csrf_token},
        )
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["status"] == "PENDING"
        assert data["requested_by_role"] == "MEDICAL_AFFAIRS"
        assert data["signal_id"] == str(sig.signal_id)
        assert "Immediate executive steer" in data["request_note"]

        # Verify Signal detail shows approval_status = PENDING
        detail_res = await client.get(f"/api/v1/signals/{sig.signal_id}")
        assert detail_res.status_code == 200
        detail_data = detail_res.json()
        assert detail_data["approval_status"] == "PENDING"
        assert detail_data["latest_approval_request"] is not None
        assert detail_data["latest_approval_request"]["status"] == "PENDING"


@pytest.mark.asyncio
async def test_pending_approvals_rbac_guard():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"},
    ) as client:
        # 1. Non-leadership (Safety) -> 403 Forbidden
        await client.post("/api/v1/auth/demo-login", json={"role": "SAFETY"})
        res_forbidden = await client.get("/api/v1/signals/pending-approvals")
        assert res_forbidden.status_code == 403

        # 2. Leadership -> 200 OK
        await client.post("/api/v1/auth/demo-login", json={"role": "LEADERSHIP"})
        res_ok = await client.get("/api/v1/signals/pending-approvals")
        assert res_ok.status_code == 200
        assert isinstance(res_ok.json(), list)


@pytest.mark.asyncio
async def test_leadership_resolves_approval_workflow():
    async with AsyncSessionLocal() as db:
        sig = await create_test_signal(db)

    # Step 1: Medical Affairs requests approval
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"},
    ) as client:
        await client.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        csrf = client.cookies.get(CSRF_COOKIE_NAME)
        req_res = await client.post(
            f"/api/v1/signals/{sig.signal_id}/request-approval",
            json={"request_note": "Requesting go-ahead for advisory board preparation."},
            headers={"X-CSRF-Token": csrf},
        )
        assert req_res.status_code == 200

        # Step 2: Medical Affairs cannot resolve -> 403 Forbidden
        resolve_fail = await client.post(
            f"/api/v1/signals/{sig.signal_id}/resolve-approval",
            json={"status": "APPROVED", "resolution_note": "Unauthorized approval"},
            headers={"X-CSRF-Token": csrf},
        )
        assert resolve_fail.status_code == 403

        # Step 3: Leadership logs in and approves
        await client.post("/api/v1/auth/demo-login", json={"role": "LEADERSHIP"})
        csrf_leader = client.cookies.get(CSRF_COOKIE_NAME)

        # Check pending approvals contains this item
        pending_list = await client.get("/api/v1/signals/pending-approvals")
        assert pending_list.status_code == 200
        items = pending_list.json()
        assert any(item["signal_id"] == str(sig.signal_id) for item in items)

        # Resolve as APPROVED
        resolve_ok = await client.post(
            f"/api/v1/signals/{sig.signal_id}/resolve-approval",
            json={
                "status": "APPROVED",
                "resolution_note": "Authorized. Proceed with scientific communication briefing.",
            },
            headers={"X-CSRF-Token": csrf_leader},
        )
        assert resolve_ok.status_code == 200
        res_data = resolve_ok.json()
        assert res_data["status"] == "APPROVED"
        assert res_data["resolved_by_role"] == "LEADERSHIP"
        assert "Authorized" in res_data["resolution_note"]

        # Step 4: Medical Affairs checks signal and sees APPROVED badge
        await client.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        signal_view = await client.get(f"/api/v1/signals/{sig.signal_id}")
        assert signal_view.status_code == 200
        view_data = signal_view.json()
        assert view_data["approval_status"] == "APPROVED"
        assert view_data["latest_approval_request"]["resolution_note"] == "Authorized. Proceed with scientific communication briefing."


@pytest.mark.asyncio
async def test_immutable_audit_log_for_approval_actions():
    async with AsyncSessionLocal() as db:
        sig = await create_test_signal(db)

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"},
    ) as client:
        # Request
        await client.post("/api/v1/auth/demo-login", json={"role": "REGULATORY"})
        csrf = client.cookies.get(CSRF_COOKIE_NAME)
        await client.post(
            f"/api/v1/signals/{sig.signal_id}/request-approval",
            json={"request_note": "Urgent EMA filing variance assessment"},
            headers={"X-CSRF-Token": csrf},
        )

        # Resolve
        await client.post("/api/v1/auth/demo-login", json={"role": "LEADERSHIP"})
        csrf_leader = client.cookies.get(CSRF_COOKIE_NAME)
        await client.post(
            f"/api/v1/signals/{sig.signal_id}/resolve-approval",
            json={"status": "REJECTED", "resolution_note": "Need additional validation first"},
            headers={"X-CSRF-Token": csrf_leader},
        )

    # Verify AuditLog in DB
    async with AsyncSessionLocal() as db:
        audit_stmt = select(AuditLog).where(
            AuditLog.entity_name == "ApprovalRequest",
            AuditLog.entity_id == str(sig.signal_id)
        ).order_by(AuditLog.timestamp.asc())
        records = (await db.execute(audit_stmt)).scalars().all()
        assert len(records) >= 2
        actions = [r.action for r in records]
        assert "APPROVAL_REQUESTED" in actions
        assert "APPROVAL_RESOLVED" in actions
