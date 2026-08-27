import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.db.session import AsyncSessionLocal
from app.models import Signal
from app.services.auth_service import get_or_create_demo_user


def make_test_signal(
    signal_id: uuid.UUID,
    source_id: str,
    title: str,
    relevant_function: str,
    review_status: str = "UNREVIEWED",
    priority: str = "HIGH",
    signal_type: str = "CLINICAL_TRIAL"
) -> Signal:
    now_utc = datetime.now(timezone.utc)
    return Signal(
        signal_id=signal_id,
        source_id=source_id,
        fingerprint=f"fp-{uuid.uuid4().hex[:16]}",
        signal_type=signal_type,
        disease="Haemophilia A",
        title=title,
        content=f"Content for {title}",
        published_at=now_utc,
        retrieved_at=now_utc,
        ingested_at=now_utc,
        relevant_function=relevant_function,
        review_status=review_status,
        priority=priority,
    )


@pytest.mark.asyncio
async def test_rbac_signals_list_scoping():
    async with AsyncSessionLocal() as db:
        sig_med = make_test_signal(
            signal_id=uuid.uuid4(),
            source_id="clinical_trials",
            title="MedAffairs Test Trial Signal",
            relevant_function="MEDICAL_AFFAIRS",
            review_status="UNREVIEWED",
            priority="HIGH",
        )
        sig_safe = make_test_signal(
            signal_id=uuid.uuid4(),
            source_id="fda",
            title="Safety Test Advisory Signal",
            relevant_function="SAFETY",
            review_status="UNREVIEWED",
            priority="CRITICAL",
            signal_type="SAFETY_ALERT",
        )
        db.add_all([sig_med, sig_safe])
        await db.commit()

    # Authenticate as MEDICAL_AFFAIRS -> list_signals should only return MEDICAL_AFFAIRS signals
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_med:
        await ac_med.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        res = await ac_med.get("/api/v1/signals")
        assert res.status_code == 200
        items = res.json()["signals"]
        assert len(items) >= 1
        assert all(s["relevant_function"] == "MEDICAL_AFFAIRS" for s in items)

        # Non-leadership role requesting all_functions=true must receive 403 Forbidden
        res_forbidden = await ac_med.get("/api/v1/signals?all_functions=true")
        assert res_forbidden.status_code == 403

    # Authenticate as LEADERSHIP -> can access all_functions=true
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_lead:
        await ac_lead.post("/api/v1/auth/demo-login", json={"role": "LEADERSHIP"})
        res_lead = await ac_lead.get("/api/v1/signals?all_functions=true")
        assert res_lead.status_code == 200
        assert res_lead.json()["total"] >= 2


@pytest.mark.asyncio
async def test_rbac_function_queue_isolation():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_reg:
        # Authenticate as REGULATORY
        await ac_reg.post("/api/v1/auth/demo-login", json={"role": "REGULATORY"})

        # Own queue -> Allowed (200)
        res_own = await ac_reg.get("/api/v1/signals/queue/REGULATORY")
        assert res_own.status_code == 200

        # Foreign queue -> Forbidden (403)
        res_foreign = await ac_reg.get("/api/v1/signals/queue/SAFETY")
        assert res_foreign.status_code == 403

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_admin:
        # ADMIN can inspect any function's queue
        await ac_admin.post("/api/v1/auth/demo-login", json={"role": "ADMIN"})
        res_admin_safety = await ac_admin.get("/api/v1/signals/queue/SAFETY")
        assert res_admin_safety.status_code == 200


@pytest.mark.asyncio
async def test_rbac_actioned_permission_gate():
    sig_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        sig = make_test_signal(
            signal_id=sig_id,
            source_id="fda",
            title="Actioned Permission Test Signal",
            relevant_function="MEDICAL_AFFAIRS",
            review_status="REVIEWED",
            priority="HIGH",
        )
        db.add(sig)
        await db.commit()

    # MEDICAL_AFFAIRS is not in ACTIONED_ALLOWED_ROLES -> 403 Forbidden
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_med:
        await ac_med.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        res_action = await ac_med.post(
            f"/api/v1/signals/{sig_id}/review",
            json={"status": "ACTIONED", "resulting_action": "Initiated medical memo"}
        )
        assert res_action.status_code == 403

    # SAFETY is in ACTIONED_ALLOWED_ROLES -> 200 OK
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_safe:
        await ac_safe.post("/api/v1/auth/demo-login", json={"role": "SAFETY"})
        res_safe = await ac_safe.post(
            f"/api/v1/signals/{sig_id}/review",
            json={"status": "ACTIONED", "resulting_action": "Safety protocol completed"}
        )
        assert res_safe.status_code == 200
        assert res_safe.json()["review_status"] == "ACTIONED"
