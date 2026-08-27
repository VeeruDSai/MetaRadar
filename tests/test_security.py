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
from app.models import AuditLog
from app.core.config import settings
from app.core.security import generate_session_bound_csrf


@pytest.mark.asyncio
async def test_security_headers_middleware():
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
async def test_preauth_exact_origin_validation():
    # 1. Missing Origin and Referer -> 403 Forbidden
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac_no_origin:
        res1 = await ac_no_origin.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res1.status_code == 403
        assert "Missing Origin/Referer" in res1.json()["detail"]

    # 2. Untrusted Origin -> 403 Forbidden
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://evil-pharma-hacker.com"}
    ) as ac_evil:
        res2 = await ac_evil.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res2.status_code == 403
        assert "Untrusted request origin" in res2.json()["detail"]

    # 3. Allowed Origin -> 200 OK
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_valid:
        res3 = await ac_valid.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res3.status_code == 200
        assert res3.json()["role"] == "MEDICAL_AFFAIRS"


@pytest.mark.asyncio
async def test_session_bound_csrf_validation_logic():
    # Test valid and forged CSRF HMAC generation
    session_id = "test-session-12345"
    valid_csrf = generate_session_bound_csrf(session_id, settings.SECRET_KEY)
    
    # 1. Verify valid token matches
    from app.core.security import verify_session_bound_csrf
    assert verify_session_bound_csrf(valid_csrf, session_id, settings.SECRET_KEY) is True

    # 2. Forged token fails
    assert verify_session_bound_csrf("forged-csrf-token", session_id, settings.SECRET_KEY) is False

    # 3. Different session ID fails
    assert verify_session_bound_csrf(valid_csrf, "other-session-67890", settings.SECRET_KEY) is False


@pytest.mark.asyncio
async def test_audit_log_database_and_orm_immutability():
    audit_id = uuid.uuid4()
    sig_id = uuid.uuid4()
    now_utc = datetime.now(timezone.utc)

    # 1. Append valid audit record
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

    # 2. Verify ORM blocks UPDATE with PermissionError
    async with AsyncSessionLocal() as db_update:
        entry_to_update = await db_update.get(AuditLog, audit_id)
        assert entry_to_update is not None
        entry_to_update.performed_by = "ATTACKER"
        with pytest.raises(PermissionError) as exc_info:
            await db_update.commit()
        assert "AuditLog records are append-only and cannot be updated" in str(exc_info.value)
        await db_update.rollback()


    # 3. Verify ORM blocks DELETE with PermissionError
    async with AsyncSessionLocal() as db_delete:
        entry_to_delete = await db_delete.get(AuditLog, audit_id)
        assert entry_to_delete is not None
        await db_delete.delete(entry_to_delete)
        with pytest.raises(PermissionError) as exc_info:
            await db_delete.commit()
        assert "AuditLog records are append-only and cannot be deleted" in str(exc_info.value)
        await db_delete.rollback()


@pytest.mark.asyncio
async def test_auth_rate_limiting_gate():
    # Hit login endpoint with multiple requests to test rate limit gate
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
        # Make limit requests
        responses = []
        for i in range(limit + 2):
            res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
            responses.append(res.status_code)

        # The last requests should be rate limited (429)
        assert 429 in responses
