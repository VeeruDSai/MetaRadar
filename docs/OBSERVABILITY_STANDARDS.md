# MetaRadar Observability Standards

1. Health endpoints (`/api/v1/health/*`) report actual database, cache, model load, and connector status.
2. Pipeline execution records metrics in `pipeline_runs` table (`pipeline_run_id`, `started_at`, `completed_at`, `status`, `signals_fetched`, `signals_created`, `errors_count`).
3. Audit logging persists system actions in `audit_log` table.
