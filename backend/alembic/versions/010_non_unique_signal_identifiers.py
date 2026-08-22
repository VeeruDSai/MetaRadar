"""Drop unique constraints on pmid, nct_id, regulatory_id, canonical_url

Signals represent discrete intelligence events (deduplicated by fingerprint).
Multiple events/updates frequently share the same clinical trial (nct_id),
publication (pmid), or regulatory source URL (canonical_url). Unique constraints
on these fields caused UniqueViolationError on subsequent signals for the same
trial/source, causing InFailedSQLTransactionError and total signal loss during
pipeline execution.

Revision ID: 010_signal_indexes
Revises: 009_final_schema_sync
Create Date: 2026-08-23 00:00:00.000000
"""
from alembic import op

revision = '010_signal_indexes'
down_revision = '009_final_schema_sync'
branch_labels = None
depends_on = None


def upgrade():
    # Drop unique indexes that block multi-event signals for same trial/source
    op.execute("DROP INDEX IF EXISTS uix_signals_pmid")
    op.execute("DROP INDEX IF EXISTS uix_signals_nct_id")
    op.execute("DROP INDEX IF EXISTS uix_signals_regulatory_id")
    op.execute("DROP INDEX IF EXISTS uix_signals_canonical_url")

    # Create regular (non-unique) performance lookup indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_pmid ON signals (pmid) WHERE pmid IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_nct_id ON signals (nct_id) WHERE nct_id IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_regulatory_id ON signals (regulatory_id) WHERE regulatory_id IS NOT NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_canonical_url ON signals (canonical_url) WHERE canonical_url IS NOT NULL")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_signals_canonical_url")
    op.execute("DROP INDEX IF EXISTS ix_signals_regulatory_id")
    op.execute("DROP INDEX IF EXISTS ix_signals_nct_id")
    op.execute("DROP INDEX IF EXISTS ix_signals_pmid")

    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uix_signals_pmid ON signals (pmid) WHERE pmid IS NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uix_signals_nct_id ON signals (nct_id) WHERE nct_id IS NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uix_signals_regulatory_id ON signals (regulatory_id) WHERE regulatory_id IS NOT NULL")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uix_signals_canonical_url ON signals (canonical_url) WHERE canonical_url IS NOT NULL")
