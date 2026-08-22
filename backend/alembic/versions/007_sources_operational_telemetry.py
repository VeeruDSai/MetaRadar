"""Add operational telemetry columns to sources table

The Source model was extended with 17 new columns for:
- Source tier classification (tier)
- Hierarchical source grouping (syndication_group, parent_source_id)
- Granular bronze record telemetry (records_new, records_updated, records_duplicate)
- Upstream data staleness tracking (upstream_data_timestamp, last_data_update)
- Scheduler state (next_scheduled_run, consecutive_failures, backoff_minutes)
- HTTP-level diagnostics (http_status, configuration_error_message)

None of these were in the database — causing UndefinedColumnError at runtime
for every connector execution and health-check SELECT query.

Revision ID: 007_sources_telemetry
Revises: 006_widen_signals_external_id
Create Date: 2026-08-22 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '007_sources_telemetry'
down_revision = '006_widen_signals_external_id'
branch_labels = None
depends_on = None


def upgrade():
    # Use raw SQL with IF NOT EXISTS for idempotency.
    # The alembic_version stamping failed on first attempt (VARCHAR(32) overflow),
    # so DDL may or may not already be applied. IF NOT EXISTS is safe either way.
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS tier INTEGER NOT NULL DEFAULT 1")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS records_new INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS records_updated INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS records_duplicate INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS upstream_data_timestamp VARCHAR(100)")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS last_data_update TIMESTAMPTZ")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS next_scheduled_run TIMESTAMPTZ")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS consecutive_failures INTEGER NOT NULL DEFAULT 0")
    op.execute("ALTER TABLE sources ADD COLUMN IF NOT EXISTS backoff_minutes INTEGER NOT NULL DEFAULT 0")


def downgrade():
    op.drop_column('sources', 'backoff_minutes')
    op.drop_column('sources', 'consecutive_failures')
    op.drop_column('sources', 'next_scheduled_run')
    op.drop_column('sources', 'last_data_update')
    op.drop_column('sources', 'upstream_data_timestamp')
    op.drop_column('sources', 'records_duplicate')
    op.drop_column('sources', 'records_updated')
    op.drop_column('sources', 'records_new')
    op.drop_column('sources', 'tier')
