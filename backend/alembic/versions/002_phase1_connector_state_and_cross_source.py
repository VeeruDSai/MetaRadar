"""Phase 1: connector_state table + cross_source_group_id column

Revision ID: 002_phase1_connector_state_and_cross_source
Revises: 001_initial_v51_schema
Create Date: 2026-08-13 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '002_phase1_connector_state_and_cross_source'
down_revision = '001_initial_v51_schema'
branch_labels = None
depends_on = None


def upgrade():
    # Per-connector per-profile incremental run state (D-11).
    op.create_table(
        'connector_state',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', sa.String(100), nullable=False),
        sa.Column('profile_id', sa.String(100), nullable=False),
        sa.Column('last_success', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cursor', sa.Text(), nullable=True),
        sa.Column('next_run_after', sa.DateTime(timezone=True), nullable=True),
        sa.Column('first_run_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.UniqueConstraint('source_id', 'profile_id', name='uq_connector_state_source_profile'),
    )

    # Cross-source group assignment on bronze rows (D-17), consumed by Phase 2.
    op.add_column(
        'raw_signals_bronze',
        sa.Column('cross_source_group_id', postgresql.UUID(as_uuid=True), nullable=True),
    )


def downgrade():
    op.drop_column('raw_signals_bronze', 'cross_source_group_id')
    op.drop_table('connector_state')
