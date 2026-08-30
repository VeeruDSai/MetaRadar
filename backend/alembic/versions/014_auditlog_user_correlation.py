"""Add user_id, correlation_id, and immutability trigger to audit_log

Revision ID: 014_auditlog_user_correlation
Revises: 013_auth_user_role_session
Create Date: 2026-08-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '014_auditlog_user_correlation'
down_revision = '013_auth_user_role_session'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS correlation_id VARCHAR(36) NULL")
    op.execute("ALTER TABLE audit_log ADD COLUMN IF NOT EXISTS user_id UUID NULL REFERENCES users(user_id) ON DELETE SET NULL")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_log_user_id ON audit_log (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_audit_log_correlation_id ON audit_log (correlation_id)")

    # DB-Level Append-Only Immutability Trigger
    op.execute("""
        CREATE OR REPLACE FUNCTION block_audit_log_mutation()
        RETURNS TRIGGER AS $$
        BEGIN
            RAISE EXCEPTION 'Security Invariant Violation: AuditLog records are append-only and cannot be updated or deleted.';
        END;
        $$ LANGUAGE plpgsql;
    """)
    op.execute("DROP TRIGGER IF EXISTS trg_block_audit_log_update_delete ON audit_log")
    op.execute("""
        CREATE TRIGGER trg_block_audit_log_update_delete
        BEFORE UPDATE OR DELETE ON audit_log
        FOR EACH ROW EXECUTE FUNCTION block_audit_log_mutation()
    """)


def downgrade():
    op.execute("DROP TRIGGER IF EXISTS trg_block_audit_log_update_delete ON audit_log")
    op.execute("DROP FUNCTION IF EXISTS block_audit_log_mutation()")
    op.execute("DROP INDEX IF EXISTS ix_audit_log_correlation_id")
    op.execute("DROP INDEX IF EXISTS ix_audit_log_user_id")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS user_id")
    op.execute("ALTER TABLE audit_log DROP COLUMN IF EXISTS correlation_id")
