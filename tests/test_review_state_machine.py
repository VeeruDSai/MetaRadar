import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.db.session import AsyncSessionLocal
from app.models import Signal, AuditLog


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
async def test_fsm_valid_lifecycle_transitions():
    sig_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        sig = make_test_signal(
            signal_id=sig_id,
            source_id="fda",
            title="FSM Lifecycle Forward Test",
            relevant_function="SAFETY",
            review_status="UNREVIEWED",
            priority="HIGH",
        )
        db.add(sig)
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        await ac.post("/api/v1/auth/demo-login", json={"role": "SAFETY"})

        # Step 1: UNREVIEWED -> IN_REVIEW
        r1 = await ac.post(f"/api/v1/signals/{sig_id}/review", json={"status": "IN_REVIEW", "notes": "Under safety triage"})
        assert r1.status_code == 200
        assert r1.json()["review_status"] == "IN_REVIEW"

        # Step 2: IN_REVIEW -> REVIEWED
        r2 = await ac.post(f"/api/v1/signals/{sig_id}/review", json={"status": "REVIEWED", "decision": "CONFIRMED_SIGNAL"})
        assert r2.status_code == 200
        assert r2.json()["review_status"] == "REVIEWED"

        # Step 3: REVIEWED -> ACTIONED (Terminal)
        r3 = await ac.post(f"/api/v1/signals/{sig_id}/review", json={"status": "ACTIONED", "resulting_action": "Updated REMS filing"})
        assert r3.status_code == 200
        assert r3.json()["review_status"] == "ACTIONED"


@pytest.mark.asyncio
async def test_fsm_terminal_state_lock():
    sig_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        sig = make_test_signal(
            signal_id=sig_id,
            source_id="fda",
            title="Terminal State Lock Test",
            relevant_function="SAFETY",
            review_status="ACTIONED",
            priority="CRITICAL",
        )
        db.add(sig)
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        await ac.post("/api/v1/auth/demo-login", json={"role": "SAFETY"})

        # Attempting any modification on ACTIONED must return 409 Conflict
        res = await ac.post(
            f"/api/v1/signals/{sig_id}/review",
            json={"status": "IN_REVIEW", "notes": "Attempting to reopen"}
        )
        assert res.status_code == 409
        assert "terminal state 'ACTIONED'" in res.json()["detail"]


@pytest.mark.asyncio
async def test_fsm_invalid_transition_conflict():
    sig_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        sig = make_test_signal(
            signal_id=sig_id,
            source_id="pubmed",
            title="Invalid Transition Test",
            relevant_function="SAFETY",
            review_status="UNREVIEWED",
            priority="MEDIUM",
        )
        db.add(sig)
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        await ac.post("/api/v1/auth/demo-login", json={"role": "SAFETY"})

        # Direct UNREVIEWED -> ACTIONED is illegal -> 409 Conflict
        res = await ac.post(
            f"/api/v1/signals/{sig_id}/review",
            json={"status": "ACTIONED"}
        )
        assert res.status_code == 409


@pytest.mark.asyncio
async def test_fsm_escalation_and_resolution_lifecycle():
    sig_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        sig = make_test_signal(
            signal_id=sig_id,
            source_id="pubmed",
            title="Escalation Lifecycle Test",
            relevant_function="MEDICAL_AFFAIRS",
            review_status="IN_REVIEW",
            priority="HIGH",
        )
        db.add(sig)
        await db.commit()

    # 1. MedAffairs reviewer escalates to Leadership
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_med:
        await ac_med.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        res_esc = await ac_med.post(
            f"/api/v1/signals/{sig_id}/review",
            json={
                "status": "REVIEWED",
                "escalate": True,
                "escalation_reason": "Cross-indication trial conflict requires VP decision"
            }
        )
        assert res_esc.status_code == 200
        assert res_esc.json()["is_escalated"] is True

    # 2. Leadership resolves escalation and directs action
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_lead:
        await ac_lead.post("/api/v1/auth/demo-login", json={"role": "LEADERSHIP"})
        res_res = await ac_lead.post(
            f"/api/v1/signals/{sig_id}/review",
            json={
                "status": "ACTION_REQUIRED",
                "resolve_escalation": True,
                "resulting_action": "Proceed with advisory committee consultation"
            }
        )
        assert res_res.status_code == 200
        assert res_res.json()["is_escalated"] is False

    # 3. Verify chronological audit trail
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_audit:
        res_audit = await ac_audit.get(f"/api/v1/signals/{sig_id}/audit-history")
        assert res_audit.status_code == 200
        actions = [a["action"] for a in res_audit.json()]
        assert "SIGNAL_ESCALATED" in actions
        assert "ESCALATION_RESOLVED" in actions


@pytest.mark.asyncio
async def test_audit_log_immutability_enforcement():
    audit_id = uuid.uuid4()
    async with AsyncSessionLocal() as db:
        log_entry = AuditLog(
            audit_id=audit_id,
            entity_name="Signal",
            entity_id="test-signal-uuid",
            action="SECURITY_AUDIT_PROBE",
            performed_by="Automated Auditor",
            details={"test": True}
        )
        db.add(log_entry)
        await db.commit()

    # 1. ORM Level Update Block
    async with AsyncSessionLocal() as db:
        fetched = await db.get(AuditLog, audit_id)
        assert fetched is not None
        fetched.performed_by = "Malicious Actor"
        with pytest.raises(PermissionError, match="Security Invariant Violation: AuditLog records are append-only"):
            await db.commit()

    # 2. Database Trigger Level Update Block (via raw SQL)
    async with AsyncSessionLocal() as db:
        with pytest.raises(Exception, match="Security Invariant Violation"):
            await db.execute(
                text("UPDATE audit_log SET performed_by = 'Tampered' WHERE audit_id = :aid"),
                {"aid": audit_id}
            )
            await db.commit()

    # 3. Database Trigger Level Delete Block (via raw SQL)
    async with AsyncSessionLocal() as db:
        with pytest.raises(Exception, match="Security Invariant Violation"):
            await db.execute(
                text("DELETE FROM audit_log WHERE audit_id = :aid"),
                {"aid": audit_id}
            )
            await db.commit()
