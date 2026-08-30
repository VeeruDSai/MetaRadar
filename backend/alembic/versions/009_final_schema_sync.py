"""Fix all remaining schema drift across signals, raw_signals_bronze, and events tables.

Drift found after migrations 007 and 008:
  - signals: missing event_type
  - raw_signals_bronze: missing source_tier, event_type
  - events: missing source_id

All use IF NOT EXISTS for idempotency.

Revision ID: 009_final_schema_sync
Revises: 008_health_logs_telemetry
Create Date: 2026-08-22 00:00:00.000000
"""
from alembic import op

revision = '009_final_schema_sync'
down_revision = '008_health_logs_telemetry'
branch_labels = None
depends_on = None


def upgrade():
    # signals table: event_type and source_tier classification
    op.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS event_type VARCHAR(100)")
    op.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS source_tier INTEGER NOT NULL DEFAULT 1")

    # raw_signals_bronze: source tier and event type for provenance tracking
    op.execute("ALTER TABLE raw_signals_bronze ADD COLUMN IF NOT EXISTS source_tier INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE raw_signals_bronze ADD COLUMN IF NOT EXISTS event_type VARCHAR(100)")

    # events: source_id to link events back to their originating source
    op.execute("ALTER TABLE events ADD COLUMN IF NOT EXISTS source_id VARCHAR(100)")


def downgrade():
    op.execute("ALTER TABLE events DROP COLUMN IF EXISTS source_id")
    op.execute("ALTER TABLE raw_signals_bronze DROP COLUMN IF EXISTS event_type")
    op.execute("ALTER TABLE raw_signals_bronze DROP COLUMN IF EXISTS source_tier")
    op.execute("ALTER TABLE signals DROP COLUMN IF EXISTS event_type")
