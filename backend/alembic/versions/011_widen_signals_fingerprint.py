"""Widen signals.fingerprint from String(64) to String(255)

Fingerprints generated with prefix format 'hash:<sha256>' (69 chars) or
'sig:<source>:<external_id>' (up to 128+ chars) exceeded the VARCHAR(64) limit,
causing StringDataRightTruncationError and transaction abort on every signal insert.

Revision ID: 011_widen_fingerprint
Revises: 010_signal_indexes
Create Date: 2026-08-23 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = '011_widen_fingerprint'
down_revision = '010_signal_indexes'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE signals ALTER COLUMN fingerprint TYPE VARCHAR(255)")


def downgrade():
    op.execute("ALTER TABLE signals ALTER COLUMN fingerprint TYPE VARCHAR(64)")
