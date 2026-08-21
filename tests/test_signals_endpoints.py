import pytest
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.db.session import get_db


@pytest.mark.asyncio
async def test_signals_list_empty_database():
    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    
    mock_result_signals = MagicMock()
    mock_result_signals.scalars.return_value = mock_scalars
    
    mock_result_count = MagicMock()
    mock_result_count.scalar.return_value = 0
    
    # Return count on second execute
    mock_db.execute.side_effect = [mock_result_signals, mock_result_count]

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/signals?limit=10&offset=0")
            assert res.status_code == 200
            data = res.json()
            assert data["signals"] == []
            assert data["total"] == 0
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_overview_empty_database():
    mock_db = AsyncMock()
    
    # 1. signals count = 0
    res_signals_count = MagicMock()
    res_signals_count.scalar.return_value = 0
    
    # 2. assets count = 0
    res_assets_count = MagicMock()
    res_assets_count.scalar.return_value = 0
    
    # 3. confluences count = 0
    res_conf_count = MagicMock()
    res_conf_count.scalar.return_value = 0

    # 4. contradictions count = 0
    res_contra_count = MagicMock()
    res_contra_count.scalar.return_value = 0

    # 5. sources count = 0
    res_sources_count = MagicMock()
    res_sources_count.scalar.return_value = 0

    # 6. recent signals count = 0
    res_recent_count = MagicMock()
    res_recent_count.scalar.return_value = 0
    
    # 7. latest confluence = None
    res_latest_conf = MagicMock()
    res_latest_conf.scalar_one_or_none.return_value = None

    # 8. developments = []
    mock_dev_scalars = MagicMock()
    mock_dev_scalars.all.return_value = []
    res_devs = MagicMock()
    res_devs.scalars.return_value = mock_dev_scalars
    
    mock_db.execute.side_effect = [
        res_signals_count,
        res_assets_count,
        res_conf_count,
        res_contra_count,
        res_sources_count,
        res_recent_count,
        res_devs,
        res_latest_conf
    ]

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/overview")
            assert res.status_code == 200
            data = res.json()
            assert data["active_signals"] == 0
            assert data["monitored_assets"] == 0
            assert data["confluences_detected"] == 0
            assert data["contradictions_flagged"] == 0
            assert "confluence" in data
            assert data["confluence"]["score"] == 0.0
            assert data["confluence"]["drivers"] == []
            assert data["lifecycle"] == []
            assert data["trends"] == []
            assert data["health"]["api"] == "healthy"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_athena_endpoint_valid_and_invalid():
    mock_db = AsyncMock()
    mock_res = MagicMock()
    mock_res.scalars.return_value.all.return_value = []
    mock_res.fetchall.return_value = []
    mock_db.execute.return_value = mock_res

    async def override_get_db():
        yield mock_db

    app.dependency_overrides[get_db] = override_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            # Valid prompt
            res = await ac.post("/api/v1/athena", json={"prompt": "How does concizumab compare to mim8?"})
            assert res.status_code == 200
            data = res.json()
            assert "answer" in data
            assert data["confidence"] >= 0
            assert "mode" in data

            # Empty prompt -> 422
            res_empty = await ac.post("/api/v1/athena", json={"prompt": ""})
            assert res_empty.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)
