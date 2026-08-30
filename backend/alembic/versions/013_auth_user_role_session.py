"""Add users and sessions tables for authentication and RBAC

Revision ID: 013_auth_user_role_session
Revises: 012_decision_fields
Create Date: 2026-08-27 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '013_auth_user_role_session'
down_revision = '012_decision_fields'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            email VARCHAR(255) NOT NULL UNIQUE,
            display_name VARCHAR(100) NOT NULL,
            hashed_password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_users_role ON users (role)")

    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            token_hash VARCHAR(64) NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_activity_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            expires_at TIMESTAMPTZ NOT NULL,
            is_revoked BOOLEAN NOT NULL DEFAULT false
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_sessions_token_hash ON sessions (token_hash)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sessions_user_id ON sessions (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sessions_expires_at ON sessions (expires_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_sessions_last_activity_at ON sessions (last_activity_at)")


def downgrade():
    op.execute("DROP TABLE IF EXISTS sessions")
    op.execute("DROP TABLE IF EXISTS users")
