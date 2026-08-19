"""Add contradictions, calibration, scoring_weights, and missing columns

Revision ID: 003_contradictions_scoring
Revises: 002_phase1_connector_state_and_cross_source
Create Date: 2026-08-19 20:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_contradictions_scoring'
down_revision = '002_phase1_connector_state_and_cross_source'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Contradictions Table
    op.create_table(
        'contradictions',
        sa.Column('contradiction_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('claim_a_id', sa.String(100), nullable=False),
        sa.Column('claim_b_id', sa.String(100), nullable=False),
        sa.Column('rule_id', sa.String(100), nullable=False),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('detected_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 2. Calibration History Table
    op.create_table(
        'calibration_history',
        sa.Column('history_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('weights', postgresql.JSONB(), nullable=False),
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 3. Scoring Weights Table
    op.create_table(
        'scoring_weights',
        sa.Column('weight_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('stakeholder_function', sa.String(100), primary_key=True),
        sa.Column('impact_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('urgency_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('novelty_weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
    )

    # 4. Missing columns on existing tables
    op.add_column(
        'lifecycle_events',
        sa.Column('source_id', sa.String(100), sa.ForeignKey('sources.source_id'), nullable=True),
    )
    op.add_column(
        'signals',
        sa.Column('model_metadata', postgresql.JSONB(), nullable=True),
    )


def downgrade():
    op.drop_column('signals', 'model_metadata')
    op.drop_column('lifecycle_events', 'source_id')
    op.drop_table('scoring_weights')
    op.drop_table('calibration_history')
    op.drop_table('contradictions')
