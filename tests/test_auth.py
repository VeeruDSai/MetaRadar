import asyncio
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pytest
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    hash_token,
    sign_session_token,
    unsign_session_token,
    generate_session_bound_csrf,
    verify_session_bound_csrf,
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
)
from app.db.session import AsyncSessionLocal
from app.models.auth import User, Session
from app.services.auth_service import (
    authenticate_user,
    create_session,
    get_session_user,
    invalidate_session,
    get_or_create_demo_user,
    get_demo_password,
)


@pytest.mark.asyncio
async def test_password_hashing_and_verification():
    plain = "SuperSecretPassword123!"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.asyncio
async def test_session_token_hashing_and_signing():
    session_id = "550e8400-e29b-41d4-a716-446655440000"
    signed = sign_session_token(session_id, settings.SECRET_KEY)
    assert signed != session_id
    
    t_hash1 = hash_token(signed)
    t_hash2 = hash_token(signed)
    assert t_hash1 == t_hash2
    assert len(t_hash1) == 64

    recovered = unsign_session_token(signed, settings.SECRET_KEY, 3600)
    assert recovered == session_id


@pytest.mark.asyncio
async def test_session_bound_csrf_token_lifecycle():
    session_id = "550e8400-e29b-41d4-a716-446655440000"
    csrf = generate_session_bound_csrf(session_id, settings.SECRET_KEY)
    assert ":" in csrf
    assert verify_session_bound_csrf(csrf, session_id, settings.SECRET_KEY) is True
    assert verify_session_bound_csrf(csrf, "wrong-session-id", settings.SECRET_KEY) is False
    assert verify_session_bound_csrf("invalid:nonce", session_id, settings.SECRET_KEY) is False


@pytest.mark.asyncio
async def test_auth_demo_login_and_me_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert res.status_code == 200, f"Demo login failed: {res.text}"
        data = res.json()
        assert data["role"] == "MEDICAL_AFFAIRS"
        assert "user_id" in data
        assert SESSION_COOKIE_NAME in ac.cookies
        assert CSRF_COOKIE_NAME in ac.cookies

        me_res = await ac.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        me_data = me_res.json()
        assert me_data["role"] == "MEDICAL_AFFAIRS"
        assert me_data["email"] == "medical.affairs@metaradar.internal"


@pytest.mark.asyncio
async def test_auth_standard_credential_login():
    from app.services.auth_service import get_role_password
    admin_pw = get_role_password("ADMIN")
    async with AsyncSessionLocal() as db:
        user = await get_or_create_demo_user(db, "ADMIN")
        assert user is not None

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        # Invalid password
        bad_res = await ac.post("/api/v1/auth/login", json={"email": "admin@metaradar.internal", "password": "WrongPassword!"})
        assert bad_res.status_code == 401

        # Valid password
        good_res = await ac.post("/api/v1/auth/login", json={"email": "admin@metaradar.internal", "password": admin_pw})
        assert good_res.status_code == 200
        data = good_res.json()
        assert data["role"] == "ADMIN"
        assert SESSION_COOKIE_NAME in ac.cookies



@pytest.mark.asyncio
async def test_auth_logout_revokes_session():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        login_res = await ac.post("/api/v1/auth/demo-login", json={"role": "REGULATORY"})
        assert login_res.status_code == 200
        csrf_token = ac.cookies[CSRF_COOKIE_NAME]
        session_token = ac.cookies[SESSION_COOKIE_NAME]

        # Verify authenticated
        me_before = await ac.get("/api/v1/auth/me")
        assert me_before.status_code == 200

        # Logout
        logout_res = await ac.post("/api/v1/auth/logout", headers={"X-CSRF-Token": csrf_token})
        assert logout_res.status_code == 200
        assert logout_res.json()["status"] == "logged_out"

        # Attempt to access /auth/me with explicit revoked session cookie
        ac.cookies.set(SESSION_COOKIE_NAME, session_token)
        me_after = await ac.get("/api/v1/auth/me")
        assert me_after.status_code == 401


@pytest.mark.asyncio
async def test_dual_timeout_enforcement():
    async with AsyncSessionLocal() as db:
        user = await get_or_create_demo_user(db, "SAFETY")
        assert user is not None

        sess, token = await create_session(db, user.user_id, settings.SECRET_KEY, 3600)
        res = await get_session_user(db, token, settings.SECRET_KEY, 3600, 1800)
        assert res is not None
        u, s = res
        assert u.user_id == user.user_id

        # Idle timeout expiration (last_activity_at 2h ago)
        s.last_activity_at = datetime.now(timezone.utc) - timedelta(hours=2)
        await db.commit()
        idle_res = await get_session_user(db, token, settings.SECRET_KEY, 28800, 3600)
        assert idle_res is None, "Expected idle session to expire after 1h inactivity"

        # Absolute timeout expiration (expires_at in past)
        s.last_activity_at = datetime.now(timezone.utc)
        s.expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)
        await db.commit()
        abs_res = await get_session_user(db, token, settings.SECRET_KEY, 28800, 3600)
        assert abs_res is None, "Expected session past absolute expires_at to be rejected"


@pytest.mark.asyncio
async def test_csrf_bootstrap_endpoint():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.get("/api/v1/auth/csrf")
        assert res.status_code == 200
        data = res.json()
        assert "csrf_token" in data
        assert len(data["csrf_token"]) > 20
        assert CSRF_COOKIE_NAME in ac.cookies
