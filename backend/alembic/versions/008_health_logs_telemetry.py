"""Add telemetry columns to source_health_logs table

The SourceHealthLog model was extended with 6 new columns:
- profile_id: per-profile health log tracking
- duration_ms: actual wall-clock time of connector run
- records_new / records_updated / records_duplicate: granular bronze telemetry
- upstream_data_timestamp: upstream freshness tracking

These were missing from the DB causing UndefinedColumnError on every
connector execution when the health log INSERT was attempted.

Revision ID: 008_health_logs_telemetry
Revises: 007_sources_telemetry
Create Date: 2026-08-22 00:00:00.000000
"""
from alembic import op

revision = '008_health_logs_telemetry'
down_revision = '007_sources_telemetry'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE source_health_logs ADD COLUMN IF NOT EXISTS profile_id VARCHAR(100)")
    op.execute("ALTER TABLE source_health_logs ADD COLUMN IF NOT EXISTS duration_ms FLOAT")
    op.execute("ALTER TABLE source_health_logs ADD COLUMN IF NOT EXISTS records_new INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE source_health_logs ADD COLUMN IF NOT EXISTS records_updated INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE source_health_logs ADD COLUMN IF NOT EXISTS records_duplicate INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE source_health_logs ADD COLUMN IF NOT EXISTS upstream_data_timestamp VARCHAR(100)")


def downgrade():
    op.execute("ALTER TABLE source_health_logs DROP COLUMN IF EXISTS upstream_data_timestamp")
    op.execute("ALTER TABLE source_health_logs DROP COLUMN IF EXISTS records_duplicate")
    op.execute("ALTER TABLE source_health_logs DROP COLUMN IF EXISTS records_updated")
    op.execute("ALTER TABLE source_health_logs DROP COLUMN IF EXISTS records_new")
    op.execute("ALTER TABLE source_health_logs DROP COLUMN IF EXISTS duration_ms")
    op.execute("ALTER TABLE source_health_logs DROP COLUMN IF EXISTS profile_id")
