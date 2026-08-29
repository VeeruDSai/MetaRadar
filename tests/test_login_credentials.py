import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.auth_service import (
    authenticate_user,
    get_role_password,
    seed_demo_users_if_needed,
)


@pytest.mark.asyncio
async def test_all_role_passwords_authenticate_via_service():
    """Verify that every single demo persona authenticates with its dedicated fixed password."""
    roles = [
        ("MEDICAL_AFFAIRS", "medical.affairs@metaradar.internal", settings.DEMO_PASSWORD_MEDICAL_AFFAIRS),
        ("REGULATORY", "regulatory@metaradar.internal", settings.DEMO_PASSWORD_REGULATORY),
        ("SAFETY", "safety@metaradar.internal", settings.DEMO_PASSWORD_SAFETY),
        ("MARKET_ACCESS", "market.access@metaradar.internal", settings.DEMO_PASSWORD_MARKET_ACCESS),
        ("COMMUNICATIONS", "comms@metaradar.internal", settings.DEMO_PASSWORD_COMMUNICATIONS),
        ("LEADERSHIP", "leadership@metaradar.internal", settings.DEMO_PASSWORD_LEADERSHIP),
        ("ADMIN", "admin@metaradar.internal", settings.DEMO_PASSWORD_ADMIN),
    ]

    async with AsyncSessionLocal() as db:
        await seed_demo_users_if_needed(db)
        for role, email, password in roles:
            # Test with .internal
            user = await authenticate_user(db, email, password)
            assert user is not None, f"Failed authentication for {role} with {email}"
            assert user.role == role

            # Test with .demo alias
            demo_alias = email.replace("@metaradar.internal", "@metaradar.demo")
            user_alias = await authenticate_user(db, demo_alias, password)
            assert user_alias is not None, f"Failed alias authentication for {role} with {demo_alias}"
            assert user_alias.role == role


@pytest.mark.asyncio
async def test_invalid_password_rejected():
    """Verify wrong password is rejected."""
    async with AsyncSessionLocal() as db:
        user = await authenticate_user(db, "medical.affairs@metaradar.internal", "WrongPassword123!")
        assert user is None


@pytest.mark.asyncio
async def test_http_login_endpoint_medical_affairs():
    """Verify HTTP endpoint handles login with origin header."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"},
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "medical.affairs@metaradar.demo",
                "password": settings.DEMO_PASSWORD_MEDICAL_AFFAIRS,
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["role"] == "MEDICAL_AFFAIRS"
        assert data["email"] == "medical.affairs@metaradar.internal"
        assert "user_id" in data


@pytest.mark.asyncio
async def test_http_login_endpoint_leadership():
    """Verify HTTP endpoint handles leadership login with origin header."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"},
    ) as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "leadership@metaradar.demo",
                "password": settings.DEMO_PASSWORD_LEADERSHIP,
            },
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert data["role"] == "LEADERSHIP"
