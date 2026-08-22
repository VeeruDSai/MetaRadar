"""Add provenance traceability columns to signals and configuration_error_message to sources

Revision ID: 005_provenance_traceability
Revises: 004_phase7_truthfulness
Create Date: 2026-08-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '005_provenance_traceability'
down_revision = '004_phase7_truthfulness'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Signals Provenance Columns
    op.add_column('signals', sa.Column('source_name', sa.String(255), nullable=True))
    op.add_column('signals', sa.Column('external_id', sa.String(100), nullable=True))
    op.add_column('signals', sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column(
        'signals',
        sa.Column('provenance_status', sa.String(50), nullable=False, server_default='available'),
    )
    op.add_column('signals', sa.Column('evidence_text', sa.Text(), nullable=True))
    op.add_column('signals', sa.Column('raw_record_reference', sa.String(255), nullable=True))

    op.create_index('ix_signals_source_name', 'signals', ['source_name'])
    op.create_index('ix_signals_external_id', 'signals', ['external_id'])
    op.create_index('ix_signals_provenance_status', 'signals', ['provenance_status'])

    # 2. Sources Configuration Error Column
    op.add_column('sources', sa.Column('configuration_error_message', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('sources', 'configuration_error_message')

    op.drop_index('ix_signals_provenance_status', table_name='signals')
    op.drop_index('ix_signals_external_id', table_name='signals')
    op.drop_index('ix_signals_source_name', table_name='signals')

    op.drop_column('signals', 'raw_record_reference')
    op.drop_column('signals', 'evidence_text')
    op.drop_column('signals', 'provenance_status')
    op.drop_column('signals', 'ingested_at')
    op.drop_column('signals', 'external_id')
    op.drop_column('signals', 'source_name')
