"""Initial v5.1 Schema with vector extension, entity tables, partial unique indexes, and HNSW vector index

Revision ID: 001_initial_v51_schema
Revises: 
Create Date: 2026-08-13 14:35:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from pgvector.sqlalchemy import Vector
from app.core.config import settings

revision = '001_initial_v51_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 1. Enable Extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm;")

    # 2. Pipeline Runs Table
    op.create_table(
        'pipeline_runs',
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('trigger', sa.String(50), nullable=False),
        sa.Column('signals_fetched', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('signals_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('signals_updated', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('duplicates_removed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_summary', postgresql.JSONB(), nullable=True),
    )

    # 3. Sources Table
    op.create_table(
        'sources',
        sa.Column('source_id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('freshness_class', sa.String(50), nullable=False),
        sa.Column('syndication_group', sa.String(100), nullable=True),
        sa.Column('parent_source_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('quota_remaining', sa.Integer(), nullable=True),
        sa.Column('last_success', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
    )

    # 4. Companies Table
    op.create_table(
        'companies',
        sa.Column('company_id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('is_novo_nordisk', sa.Boolean(), nullable=False, server_default='false'),
    )

    # 5. Assets Table
    op.create_table(
        'assets',
        sa.Column('asset_id', sa.String(100), primary_key=True),
        sa.Column('brand_name', sa.String(255), nullable=False),
        sa.Column('generic_name', sa.String(255), nullable=False),
        sa.Column('company_id', sa.String(100), sa.ForeignKey('companies.company_id'), nullable=False),
        sa.Column('mechanism', sa.Text(), nullable=False),
        sa.Column('modality', sa.String(100), nullable=False),
        sa.Column('indication', sa.Text(), nullable=False),
        sa.Column('approval_status', sa.String(50), nullable=False),
        sa.Column('approval_date', sa.String(20), nullable=True),
        sa.Column('jurisdiction', sa.String(100), nullable=True),
        sa.Column('last_verified', sa.DateTime(timezone=True), nullable=False),
    )

    # 6. Clinical Trials Table
    op.create_table(
        'trials',
        sa.Column('trial_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('nct_id', sa.String(50), nullable=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('phase', sa.String(50), nullable=True),
        sa.Column('status', sa.String(100), nullable=True),
        sa.Column('sponsor', sa.String(255), nullable=True),
    )
    op.execute("CREATE UNIQUE INDEX uix_trials_nct_id ON trials (nct_id) WHERE nct_id IS NOT NULL;")

    # 7. Developments Table
    op.create_table(
        'developments',
        sa.Column('development_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('disease', sa.String(100), nullable=False),
        sa.Column('asset_id', sa.String(100), sa.ForeignKey('assets.asset_id'), nullable=True),
        sa.Column('company_id', sa.String(100), sa.ForeignKey('companies.company_id'), nullable=True),
        sa.Column('current_stage', sa.String(50), nullable=False, server_default='announced'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 8. Events Table
    op.create_table(
        'events',
        sa.Column('event_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('development_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('developments.development_id'), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
    )

    # 9. Lifecycle Events Table
    op.create_table(
        'lifecycle_events',
        sa.Column('lifecycle_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('development_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('developments.development_id'), nullable=False),
        sa.Column('stage', sa.String(100), nullable=False),
        sa.Column('event_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
    )

    # 10. Confluences Table
    op.create_table(
        'confluences',
        sa.Column('confluence_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('development_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('developments.development_id'), nullable=False),
        sa.Column('signal_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('confluence_type', sa.String(50), nullable=False, server_default='emerging'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 11. Raw Signals Bronze Table
    op.create_table(
        'raw_signals_bronze',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', sa.String(100), sa.ForeignKey('sources.source_id'), nullable=False),
        sa.Column('external_id', sa.String(255), nullable=False),
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_runs.pipeline_run_id'), nullable=True),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('raw_payload', postgresql.JSONB(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('connector_version', sa.String(50), nullable=False, server_default='1.0.0'),
        sa.UniqueConstraint('source_id', 'external_id', name='uq_raw_source_external')
    )

    # 12. Evidence Table
    op.create_table(
        'evidence',
        sa.Column('evidence_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('raw_signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('raw_signals_bronze.id'), nullable=False),
        sa.Column('evidence_excerpt', sa.Text(), nullable=False),
        sa.Column('content_hash', sa.String(64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 13. Signals Table
    op.create_table(
        'signals',
        sa.Column('signal_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', sa.String(100), sa.ForeignKey('sources.source_id'), nullable=False),
        sa.Column('source_tier', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('development_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('developments.development_id'), nullable=True),
        sa.Column('pipeline_run_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('pipeline_runs.pipeline_run_id'), nullable=True),
        sa.Column('pmid', sa.String(50), nullable=True),
        sa.Column('nct_id', sa.String(50), nullable=True),
        sa.Column('regulatory_id', sa.String(100), nullable=True),
        sa.Column('fingerprint', sa.String(64), nullable=False),
        sa.Column('canonical_url', sa.Text(), nullable=True),
        sa.Column('signal_type', sa.String(50), nullable=False),
        sa.Column('disease', sa.String(100), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('facts', postgresql.JSONB(), nullable=True),
        sa.Column('interpretation', sa.Text(), nullable=True),
        sa.Column('speculation', sa.Text(), nullable=True),
        sa.Column('priority', sa.String(50), nullable=False, server_default='MEDIUM'),
        sa.Column('score_breakdown', postgresql.JSONB(), nullable=True),
        sa.Column('embedding', Vector(settings.EMBEDDING_DIMENSION), nullable=True),
        sa.Column('scoring_model_version', sa.String(50), nullable=False, server_default='v1'),
        sa.Column('scoring_config_version', sa.String(50), nullable=False, server_default='haemophilia_v1'),
        sa.Column('embedding_model_version', sa.String(100), nullable=False, server_default=settings.EMBEDDING_MODEL_REVISION),
        sa.Column('prompt_version', sa.String(50), nullable=False, server_default='v1.0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("CREATE UNIQUE INDEX uix_signals_pmid ON signals (pmid) WHERE pmid IS NOT NULL;")
    op.execute("CREATE UNIQUE INDEX uix_signals_nct_id ON signals (nct_id) WHERE nct_id IS NOT NULL;")
    op.execute("CREATE UNIQUE INDEX uix_signals_regulatory_id ON signals (regulatory_id) WHERE regulatory_id IS NOT NULL;")
    op.execute("CREATE UNIQUE INDEX uix_signals_fingerprint ON signals (fingerprint);")
    op.execute("CREATE UNIQUE INDEX uix_signals_canonical_url ON signals (canonical_url) WHERE canonical_url IS NOT NULL;")

    # HNSW Vector Index
    op.execute("""
        CREATE INDEX signals_embedding_hnsw
        ON signals
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64);
    """)

    # 14. Signal Routing Table
    op.create_table(
        'signal_routing',
        sa.Column('routing_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('signals.signal_id'), nullable=False),
        sa.Column('baseline_primary_function', sa.String(100), nullable=False),
        sa.Column('baseline_relevance_scores', postgresql.JSONB(), nullable=False),
        sa.Column('baseline_suggested_action', sa.Text(), nullable=False),
        sa.Column('calibrated_primary_function', sa.String(100), nullable=True),
        sa.Column('calibrated_relevance_scores', postgresql.JSONB(), nullable=True),
        sa.Column('calibrated_suggested_action', sa.Text(), nullable=True),
        sa.Column('calibration_version', sa.String(50), nullable=False, server_default='v1.0.0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 15. Calibration Feedback Table
    op.create_table(
        'calibration_feedback',
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('signal_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('signals.signal_id'), nullable=False),
        sa.Column('stakeholder_function', sa.String(100), nullable=False),
        sa.Column('relevance_rating', sa.Integer(), nullable=False),
        sa.Column('urgency_rating', sa.Integer(), nullable=False),
        sa.Column('action_appropriate', sa.Boolean(), nullable=False),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 16. Watch Items Table
    op.create_table(
        'watch_items',
        sa.Column('watch_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('development_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('developments.development_id'), nullable=False),
        sa.Column('trigger_event', sa.Text(), nullable=False),
        sa.Column('expected_event', sa.Text(), nullable=False),
        sa.Column('monitoring_window_days', sa.Integer(), nullable=False, server_default='90'),
        sa.Column('responsible_function', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='watching'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    # 17. Audit Log Table
    op.create_table(
        'audit_log',
        sa.Column('audit_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entity_name', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('performed_by', sa.String(100), nullable=False, server_default='system'),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('details', postgresql.JSONB(), nullable=True),
    )


def downgrade():
    op.drop_table('audit_log')
    op.drop_table('watch_items')
    op.drop_table('calibration_feedback')
    op.drop_table('signal_routing')
    op.drop_table('signals')
    op.drop_table('evidence')
    op.drop_table('raw_signals_bronze')
    op.drop_table('confluences')
    op.drop_table('lifecycle_events')
    op.drop_table('events')
    op.drop_table('developments')
    op.drop_table('trials')
    op.drop_table('assets')
    op.drop_table('companies')
    op.drop_table('sources')
    op.drop_table('pipeline_runs')
