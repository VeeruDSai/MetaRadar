import pytest
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_root_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION


@pytest.mark.asyncio
async def test_health_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # /api/v1/health
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

        # /api/v1/health/models
        res_models = await ac.get("/api/v1/health/models")
        assert res_models.status_code == 200
        models_data = res_models.json()
        assert "gemma_available" in models_data
        assert "embedding_dimension" in models_data
        assert models_data["embedding_dimension"] == 384

        # /api/v1/health/connectors
        res_conn = await ac.get("/api/v1/health/connectors")
        assert res_conn.status_code == 200
        connectors_data = res_conn.json()["connectors"]
        assert len(connectors_data) >= 5
        pubmed_conn = next(c for c in connectors_data if c["source_id"] == "pubmed")
        assert pubmed_conn["freshness_class"] in ["batch", "delayed", "near_real_time"]


@pytest.mark.asyncio
async def test_business_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # /api/v1/overview
        res_overview = await ac.get("/api/v1/overview")
        assert res_overview.status_code == 200
        assert "active_signals" in res_overview.json()

        # /api/v1/signals
        res_signals = await ac.get("/api/v1/signals")
        assert res_signals.status_code == 200
        assert "signals" in res_signals.json()

        # /api/v1/athena
        res_athena = await ac.post("/api/v1/athena", json={"prompt": "What changed in durability?"})
        assert res_athena.status_code == 200
        athena_data = res_athena.json()
        assert "answer" in athena_data
        assert athena_data["confidence"] > 0
