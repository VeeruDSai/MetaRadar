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
    from app.db.session import AsyncSessionLocal
    from app.models import Signal
    from sqlalchemy import delete, or_
    try:
        async with AsyncSessionLocal() as session:
            test_patterns = [
                '%Test Signal%',
                'S1 Pending',
                'S2 In Review',
                'S3 Actioned',
                'FSM Lifecycle%',
                'Terminal State%',
                'Invalid Transition%',
                'Escalation Lifecycle%',
                'Deterministic E2E Acceptance%',
                'Test Signal Title',
                'MedAffairs Test Trial Signal',
                'Safety Test Advisory Signal',
                'Actioned Permission Test Signal',
                'Approval Workflow Pipeline Signal%',
            ]
            conditions = [Signal.title.ilike(p) for p in test_patterns]
            conditions.append(Signal.fingerprint.ilike('approval-fp-%'))
            await session.execute(delete(Signal).where(or_(*conditions)))
            await session.commit()
    except Exception:
        pass
    await engine.dispose()
