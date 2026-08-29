"""Add approval_requests table for cross-functional leadership escalation

Revision ID: 015_approval_requests
Revises: 014_auditlog_user_correlation
Create Date: 2026-08-30 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = '015_approval_requests'
down_revision = '014_auditlog_user_correlation'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS approval_requests (
            request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            signal_id UUID NOT NULL REFERENCES signals(signal_id) ON DELETE CASCADE,
            requested_by_user_id UUID NOT NULL REFERENCES users(user_id),
            requested_by_role VARCHAR(50) NOT NULL,
            request_note TEXT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
            resolved_by_user_id UUID NULL REFERENCES users(user_id),
            resolved_by_role VARCHAR(50) NULL,
            resolution_note TEXT NULL,
            requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            resolved_at TIMESTAMPTZ NULL
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_approval_requests_signal_id ON approval_requests (signal_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_approval_requests_status ON approval_requests (status)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_approval_requests_requested_by_role ON approval_requests (requested_by_role)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_approval_requests_requested_by_role")
    op.execute("DROP INDEX IF EXISTS ix_approval_requests_status")
    op.execute("DROP INDEX IF EXISTS ix_approval_requests_signal_id")
    op.execute("DROP TABLE IF EXISTS approval_requests")
