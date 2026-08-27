import asyncio
import os
import sys
from pathlib import Path
import pytest
import pytest_asyncio

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.db.session import engine
from app.api.deps import _auth_rate_buckets


@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_connections():
    _auth_rate_buckets.clear()
    yield
    await engine.dispose()
