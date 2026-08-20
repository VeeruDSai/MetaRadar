"""Add provenance, SourceHealthLog, CalibrationRun, and Truthfulness columns

Revision ID: 004_phase7_truthfulness_and_provenance
Revises: 003_contradictions_scoring
Create Date: 2026-08-20 18:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '004_phase7_truthfulness'
down_revision = '003_contradictions_scoring'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Signals Provenance & DataMode Columns
    op.add_column(
        'signals',
        sa.Column('data_mode', sa.String(50), nullable=False, server_default='live'),
    )
    op.add_column(
        'signals',
        sa.Column('is_synthetic', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'signals',
        sa.Column('confidence_type', sa.String(50), nullable=True),
    )
    op.add_column(
        'signals',
        sa.Column('confidence_rationale', sa.Text(), nullable=True),
    )

    # 2. Contradictions Claim Excerpts & Provenance
    op.add_column(
        'contradictions',
        sa.Column('claim_a_excerpt', sa.Text(), nullable=True),
    )
    op.add_column(
        'contradictions',
        sa.Column('claim_b_excerpt', sa.Text(), nullable=True),
    )
    op.add_column(
        'contradictions',
        sa.Column('claim_a_evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'contradictions',
        sa.Column('claim_b_evidence_id', postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        'contradictions',
        sa.Column('confidence_type', sa.String(50), nullable=False, server_default='nli_heuristic'),
    )

    # 3. Calibration Runs Table
    op.create_table(
        'calibration_runs',
        sa.Column('run_id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('triggered_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='completed'),
        sa.Column('feedback_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('previous_weights', postgresql.JSONB(), nullable=True),
        sa.Column('new_weights', postgresql.JSONB(), nullable=True),
        sa.Column('affected_functions', postgresql.JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('scoring_version', sa.String(50), nullable=False, server_default='haemophilia_v2.0'),
    )

    # 4. Calibration Feedback Idempotency Guard
    op.add_column(
        'calibration_feedback',
        sa.Column('is_applied', sa.Boolean(), nullable=False, server_default='false'),
    )
    op.add_column(
        'calibration_feedback',
        sa.Column('applied_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'calibration_feedback',
        sa.Column('calibration_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('calibration_runs.run_id'), nullable=True),
    )

    # 5. Source Health Tracking Columns
    op.add_column(
        'sources',
        sa.Column('connector_status', sa.String(50), nullable=False, server_default='NEVER_CONNECTED'),
    )
    op.add_column(
        'sources',
        sa.Column('last_attempted', sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        'sources',
        sa.Column('latency_ms', sa.Integer(), nullable=True),
    )
    op.add_column(
        'sources',
        sa.Column('records_fetched', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'sources',
        sa.Column('records_accepted', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'sources',
        sa.Column('records_rejected', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'sources',
        sa.Column('http_status', sa.Integer(), nullable=True),
    )

    # 6. Source Health Logs Table
    op.create_table(
        'source_health_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_id', sa.String(100), sa.ForeignKey('sources.source_id'), nullable=False),
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_runs.pipeline_run_id'), nullable=True),
        sa.Column('checked_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('connector_status', sa.String(50), nullable=False),
        sa.Column('http_status', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('records_fetched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_accepted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('records_rejected', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('error_code', sa.String(50), nullable=True),
    )


def downgrade():
    op.drop_table('source_health_logs')
    for col in ['http_status', 'records_rejected', 'records_accepted', 'records_fetched', 'latency_ms', 'last_attempted', 'connector_status']:
        op.drop_column('sources', col)
    for col in ['calibration_run_id', 'applied_at', 'is_applied']:
        op.drop_column('calibration_feedback', col)
    op.drop_table('calibration_runs')
    for col in ['confidence_type', 'claim_b_evidence_id', 'claim_a_evidence_id', 'claim_b_excerpt', 'claim_a_excerpt']:
        op.drop_column('contradictions', col)
    for col in ['confidence_rationale', 'confidence_type', 'is_synthetic', 'data_mode']:
        op.drop_column('signals', col)
