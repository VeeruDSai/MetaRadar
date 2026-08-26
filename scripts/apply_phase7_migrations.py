import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.db.session import engine
from app.models import Base


async def apply_migrations():
    print("Applying database schema sync and Phase 07 tables/columns...")
    async with engine.begin() as conn:
        # Create extensions
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))

        # Create all tables defined in models if not exist
        await conn.run_sync(Base.metadata.create_all)

        # 1. Signals columns
        await conn.execute(text("ALTER TABLE signals ADD COLUMN IF NOT EXISTS data_mode VARCHAR(50) DEFAULT 'live';"))
        await conn.execute(text("ALTER TABLE signals ADD COLUMN IF NOT EXISTS is_synthetic BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE signals ADD COLUMN IF NOT EXISTS confidence_type VARCHAR(50);"))
        await conn.execute(text("ALTER TABLE signals ADD COLUMN IF NOT EXISTS confidence_rationale TEXT;"))

        # 2. Contradictions columns
        await conn.execute(text("ALTER TABLE contradictions ADD COLUMN IF NOT EXISTS claim_a_excerpt TEXT;"))
        await conn.execute(text("ALTER TABLE contradictions ADD COLUMN IF NOT EXISTS claim_b_excerpt TEXT;"))
        await conn.execute(text("ALTER TABLE contradictions ADD COLUMN IF NOT EXISTS claim_a_evidence_id UUID;"))
        await conn.execute(text("ALTER TABLE contradictions ADD COLUMN IF NOT EXISTS claim_b_evidence_id UUID;"))
        await conn.execute(text("ALTER TABLE contradictions ADD COLUMN IF NOT EXISTS confidence_type VARCHAR(50) DEFAULT 'nli_heuristic';"))

        # 3. Calibration feedback columns
        await conn.execute(text("ALTER TABLE calibration_feedback ADD COLUMN IF NOT EXISTS is_applied BOOLEAN DEFAULT FALSE;"))
        await conn.execute(text("ALTER TABLE calibration_feedback ADD COLUMN IF NOT EXISTS applied_at TIMESTAMPTZ;"))
        await conn.execute(text("ALTER TABLE calibration_feedback ADD COLUMN IF NOT EXISTS calibration_run_id UUID;"))

        # 4. Sources columns
        await conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS connector_status VARCHAR(50) DEFAULT 'NEVER_CONNECTED';"))
        await conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS last_attempted TIMESTAMPTZ;"))
        await conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS latency_ms INTEGER;"))
        await conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS records_fetched INTEGER DEFAULT 0;"))
        await conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS records_accepted INTEGER DEFAULT 0;"))
        await conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS records_rejected INTEGER DEFAULT 0;"))
        await conn.execute(text("ALTER TABLE sources ADD COLUMN IF NOT EXISTS http_status INTEGER;"))

        # 5. Alembic version
        await conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL, CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num));"))
        await conn.execute(text("DELETE FROM alembic_version;"))
        await conn.execute(text("INSERT INTO alembic_version (version_num) VALUES ('011_widen_fingerprint');"))

        print("Phase 07 database schema and all columns successfully applied!")


if __name__ == "__main__":
    asyncio.run(apply_migrations())
