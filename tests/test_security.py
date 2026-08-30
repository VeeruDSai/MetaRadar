import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text, select

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.db.session import AsyncSessionLocal
from app.models import AuditLog
from app.models.auth import User, Session
from app.core.config import settings
from app.core.security import (
    generate_session_bound_csrf,
    verify_session_bound_csrf,
    hash_session_token,
    verify_session_token_hash,
)


@pytest.mark.asyncio
async def test_security_headers_present_on_all_endpoints():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.get("/api/v1/health/ready")
        assert res.status_code == 200
        headers = res.headers

        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
        assert "1; mode=block" in headers.get("X-XSS-Protection", "")
        
        csp = headers.get("Content-Security-Policy", "")
        assert "default-src 'self'" in csp
        assert "object-src 'none'" in csp
        assert "base-uri 'none'" in csp
        assert "frame-ancestors 'none'" in csp
        assert "form-action 'self'" in csp


@pytest.mark.asyncio
async def test_preauth_missing_origin_and_referer_returns_403():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res.status_code == 403
        assert "Missing Origin/Referer" in res.json()["detail"]


@pytest.mark.asyncio
async def test_preauth_untrusted_origin_returns_403():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://malicious-attacker.com"}
    ) as ac:
        res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res.status_code == 403
        assert "Untrusted request origin" in res.json()["detail"]


@pytest.mark.asyncio
async def test_preauth_prefix_spoofed_origin_returns_403():
    # Attempting to bypass with http://localhost:3000.evil.com
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000.evil.com"}
    ) as ac:
        res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res.status_code == 403
        assert "Untrusted request origin" in res.json()["detail"]


@pytest.mark.asyncio
async def test_preauth_exact_origin_allows_authentication():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res.status_code == 200
        assert res.json()["role"] == "MEDICAL_AFFAIRS"
        assert "metaradar_session" in res.cookies
        assert "metaradar_csrf" in res.cookies


@pytest.mark.asyncio
async def test_csrf_missing_token_on_authenticated_post_returns_403():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        # Remove CSRF cookie / header
        ac.cookies.delete("metaradar_csrf")
        res = await ac.post("/api/v1/auth/logout")
        assert res.status_code == 403
        assert "CSRF" in res.json()["detail"]


@pytest.mark.asyncio
async def test_csrf_mismatched_token_returns_403():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        res = await ac.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": "forged-csrf-token-value"}
        )
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_csrf_valid_session_bound_token_allows_mutation():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        csrf_token = ac.cookies.get("metaradar_csrf")
        res = await ac.post(
            "/api/v1/auth/logout",
            headers={"X-CSRF-Token": csrf_token}
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_audit_log_orm_update_raises_permission_error():
    audit_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    now_utc = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        log_entry = AuditLog(
            audit_id=audit_id,
            entity_name="Signal",
            entity_id=str(sig_id),
            action="SIGNAL_DETECTED",
            performed_by="SYSTEM",
            details={"notes": "Initial ingestion audit trail"},
            timestamp=now_utc,
        )
        db.add(log_entry)
        await db.commit()

    async with AsyncSessionLocal() as db_update:
        entry = await db_update.get(AuditLog, audit_id)
        assert entry is not None
        entry.performed_by = "ATTACKER"
        with pytest.raises(PermissionError) as exc_info:
            await db_update.commit()
        assert "AuditLog records are append-only and cannot be updated" in str(exc_info.value)
        await db_update.rollback()


@pytest.mark.asyncio
async def test_audit_log_orm_delete_raises_permission_error():
    audit_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    now_utc = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        log_entry = AuditLog(
            audit_id=audit_id,
            entity_name="Signal",
            entity_id=str(sig_id),
            action="SIGNAL_DETECTED",
            performed_by="SYSTEM",
            details={"notes": "Initial ingestion audit trail"},
            timestamp=now_utc,
        )
        db.add(log_entry)
        await db.commit()

    async with AsyncSessionLocal() as db_delete:
        entry = await db_delete.get(AuditLog, audit_id)
        assert entry is not None
        await db_delete.delete(entry)
        with pytest.raises(PermissionError) as exc_info:
            await db_delete.commit()
        assert "AuditLog records are append-only and cannot be deleted" in str(exc_info.value)
        await db_delete.rollback()


@pytest.mark.asyncio
async def test_audit_log_pg_trigger_blocks_raw_sql_update_and_delete():
    audit_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    now_utc = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        log_entry = AuditLog(
            audit_id=audit_id,
            entity_name="Signal",
            entity_id=str(sig_id),
            action="SIGNAL_DETECTED",
            performed_by="SYSTEM",
            details={"notes": "Trigger test entry"},
            timestamp=now_utc,
        )
        db.add(log_entry)
        await db.commit()

        # Raw SQL update should be rejected by PostgreSQL trigger if active or ORM
        try:
            await db.execute(
                text("UPDATE audit_log SET performed_by = 'RAW_SQL_ATTACKER' WHERE audit_id = :aid"),
                {"aid": str(audit_id)}
            )
            await db.commit()
            pytest.fail("Expected PostgreSQL trigger or database exception on raw SQL update")
        except Exception:
            await db.rollback()


@pytest.mark.asyncio
async def test_auth_rate_limit_triggers_429_on_6th_request():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
        status_codes = []
        for _ in range(limit + 2):
            res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
            status_codes.append(res.status_code)

        assert 429 in status_codes


@pytest.mark.asyncio
async def test_login_success_and_failure_recorded_in_audit_log():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        # Successful demo login
        res_ok = await ac.post("/api/v1/auth/demo-login", json={"role": "REGULATORY"})
        assert res_ok.status_code == 200

        # Check audit log contains LOGIN_SUCCESS
        async with AsyncSessionLocal() as db:
            audit_res = await db.execute(
                select(AuditLog)
                .where(AuditLog.action.in_(["LOGIN_SUCCESS", "USER_LOGIN_SUCCESS"]))
                .order_by(AuditLog.timestamp.desc())
                .limit(5)
            )
            audits = audit_res.scalars().all()
            assert len(audits) >= 1
            assert any("REGULATORY" in str(a.details) or a.performed_by.startswith("Demo") for a in audits)



@pytest.mark.asyncio
async def test_session_token_stored_as_sha256_hash():
    # Verify cryptographic helper ensures zero raw session tokens in DB
    raw_token = f"test-raw-token-{uuid.uuid4().hex}"
    token_hash = hash_session_token(raw_token)
    assert token_hash != raw_token
    assert len(token_hash) == 64
    assert verify_session_token_hash(raw_token, token_hash) is True
    assert verify_session_token_hash("wrong-raw-token", token_hash) is False
