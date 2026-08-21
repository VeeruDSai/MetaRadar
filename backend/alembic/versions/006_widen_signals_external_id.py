"""Widen signals.external_id from String(100) to String(255)

Bronze stores external_id as String(255) and connectors such as NewsAPI write
full article URLs into it. Silver previously truncated at 100 chars, causing
StringDataRightTruncationError and silent signal loss on every pipeline run.

Revision ID: 006_widen_signals_external_id
Revises: 005_provenance_traceability
Create Date: 2026-08-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '006_widen_signals_external_id'
down_revision = '005_provenance_traceability'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'signals',
        'external_id',
        existing_type=sa.String(100),
        type_=sa.String(255),
    )


def downgrade():
    op.alter_column(
        'signals',
        'external_id',
        existing_type=sa.String(255),
        type_=sa.String(100),
    )
