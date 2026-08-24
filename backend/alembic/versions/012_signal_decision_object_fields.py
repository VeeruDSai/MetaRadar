"""Add decision object, authority, routing, and review fields to signals table

Revision ID: 012_decision_fields
Revises: 011_widen_fingerprint
Create Date: 2026-08-24 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '012_decision_fields'
down_revision = '011_widen_fingerprint'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        ALTER TABLE signals
            ADD COLUMN IF NOT EXISTS what_changed TEXT,
            ADD COLUMN IF NOT EXISTS why_it_matters TEXT,
            ADD COLUMN IF NOT EXISTS relevant_function VARCHAR(100),
            ADD COLUMN IF NOT EXISTS route_destination VARCHAR(100),
            ADD COLUMN IF NOT EXISTS route_role VARCHAR(50),
            ADD COLUMN IF NOT EXISTS is_escalated BOOLEAN NOT NULL DEFAULT FALSE,
            ADD COLUMN IF NOT EXISTS routing_reason TEXT,
            ADD COLUMN IF NOT EXISTS routing_timestamp TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS source_authority_tier VARCHAR(50),
            ADD COLUMN IF NOT EXISTS validation_status VARCHAR(50) NOT NULL DEFAULT 'VALIDATED',
            ADD COLUMN IF NOT EXISTS suggested_action TEXT,
            ADD COLUMN IF NOT EXISTS action_rationale TEXT,
            ADD COLUMN IF NOT EXISTS review_status VARCHAR(50) NOT NULL DEFAULT 'UNREVIEWED',
            ADD COLUMN IF NOT EXISTS reviewed_by VARCHAR(100),
            ADD COLUMN IF NOT EXISTS reviewed_at TIMESTAMPTZ,
            ADD COLUMN IF NOT EXISTS review_decision VARCHAR(100),
            ADD COLUMN IF NOT EXISTS review_notes TEXT,
            ADD COLUMN IF NOT EXISTS resulting_action TEXT
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_review_status ON signals(review_status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_relevant_function ON signals(relevant_function)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_is_escalated ON signals(is_escalated)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_signals_source_authority_tier ON signals(source_authority_tier)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_signals_source_authority_tier")
    op.execute("DROP INDEX IF EXISTS ix_signals_is_escalated")
    op.execute("DROP INDEX IF EXISTS ix_signals_relevant_function")
    op.execute("DROP INDEX IF EXISTS ix_signals_review_status")

    op.execute("""
        ALTER TABLE signals
            DROP COLUMN IF EXISTS resulting_action,
            DROP COLUMN IF EXISTS review_notes,
            DROP COLUMN IF EXISTS review_decision,
            DROP COLUMN IF EXISTS reviewed_at,
            DROP COLUMN IF EXISTS reviewed_by,
            DROP COLUMN IF EXISTS review_status,
            DROP COLUMN IF EXISTS action_rationale,
            DROP COLUMN IF EXISTS suggested_action,
            DROP COLUMN IF EXISTS validation_status,
            DROP COLUMN IF EXISTS source_authority_tier,
            DROP COLUMN IF EXISTS routing_timestamp,
            DROP COLUMN IF EXISTS routing_reason,
            DROP COLUMN IF EXISTS is_escalated,
            DROP COLUMN IF EXISTS route_role,
            DROP COLUMN IF EXISTS route_destination,
            DROP COLUMN IF EXISTS relevant_function,
            DROP COLUMN IF EXISTS why_it_matters,
            DROP COLUMN IF EXISTS what_changed
    """)
