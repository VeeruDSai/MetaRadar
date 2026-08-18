import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.core.config import settings
from app.db.session import get_db


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
    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    
    mock_res_scalars = MagicMock()
    mock_res_scalars.scalars.return_value = mock_scalars
    
    mock_res_count = MagicMock()
    mock_res_count.scalar.return_value = 0
    
    mock_db.execute.side_effect = [
        mock_res_count, mock_res_count, mock_res_count, mock_res_count, mock_res_count, mock_res_count, mock_res_scalars, # overview
        mock_res_scalars, mock_res_count # signals
    ]

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # /api/v1/overview
            res_overview = await ac.get("/api/v1/overview")
            assert res_overview.status_code == 200
            assert "active_signals" in res_overview.json()

            # /api/v1/signals
            res_signals = await ac.get("/api/v1/signals?severity=HIGH&entity=Hemgenix")
            assert res_signals.status_code == 200
            assert "signals" in res_signals.json()

            # /api/v1/athena
            res_athena = await ac.post("/api/v1/athena", json={"prompt": "What changed in durability?"})
            assert res_athena.status_code == 200
            athena_data = res_athena.json()
            assert "answer" in athena_data
            assert athena_data["confidence"] > 0
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_intelligence_and_registry_reads():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.all.return_value = []
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_res.scalars.return_value = mock_scalars

    mock_db.execute.return_value = mock_res

    async def mock_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = mock_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # /confluence
            res_conf = await ac.get("/api/v1/confluence")
            assert res_conf.status_code == 200
            assert isinstance(res_conf.json(), list)

            # /lifecycles
            res_life = await ac.get("/api/v1/lifecycles?disease=haemophilia")
            assert res_life.status_code == 200
            assert isinstance(res_life.json(), list)

            # /red-team
            res_red = await ac.get("/api/v1/red-team?severity=HIGH")
            assert res_red.status_code == 200
            assert isinstance(res_red.json(), list)

            # /missing-signals
            res_miss = await ac.get("/api/v1/missing-signals")
            assert res_miss.status_code == 200
            assert isinstance(res_miss.json(), list)

            # /developments
            res_devs = await ac.get("/api/v1/developments")
            assert res_devs.status_code == 200
            assert isinstance(res_devs.json(), list)

            # /sources
            res_sources = await ac.get("/api/v1/sources")
            assert res_sources.status_code == 200
            assert isinstance(res_sources.json(), list)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_cache_clear_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.post("/api/v1/cache/clear")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] in ["cleared", "cache_unavailable"]
        assert "flushed_at" in data
