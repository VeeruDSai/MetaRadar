---
doc_type: codebase-map
focus: tech
analysis_date: 2026-08-22
---

# External Integrations

**Analysis Date:** 2026-08-22

## Data Source Connectors

All connectors implement the shared `SourceConnector` contract (`backend/app/connectors/base.py`): isolated, idempotent, incremental (per-connector `ConnectorState` cursor, D-11), quota-aware, retrying (`max_retries=3`, base delay 1.5s, timeout 30s), and observable. Connectors persist immutable bronze rows only — never intelligence.

| Connector | File | Status | Auth | Notes |
|---|---|---|---|---|
| NCBI PubMed (E-utilities) | `backend/app/connectors/pubmed.py` | LIVE | none (public E-utilities) | Literature/trial readouts |
| ClinicalTrials.gov v2 | `backend/app/connectors/clinical_trials.py` | LIVE | keyless public API | Trial registrations/status |
| NewsAPI | `backend/app/connectors/newsapi.py` | LIVE (quota-aware) | `NEWSAPI_KEY` env var | Degrades to cache/synthetic; config error surfaced via `configuration_error_for()` in `app/core/config.py:61` |
| openFDA | `backend/app/connectors/fda.py` | ADAPTER-READY | none | Scaffold + rate limits |
| EMA RSS | `backend/app/connectors/ema.py` | ADAPTER-READY | none | Regulatory feed |

Synthetic fallback: `data/synthetic_signals.json` (500 curated signals, `is_synthetic=true`, never presented as live). Seeded via `backend/app/db/seed.py`.

## Databases & Cache

- **PostgreSQL 16 + pgvector** — primary datastore. URL from `DATABASE_URL` (asyncpg driver). Schema managed by Alembic (`backend/alembic/versions/001…006`). 20 tables in `backend/app/models/__init__.py`: `pipeline_runs`, `sources`, `source_health_logs`, `companies`, `assets`, `trials`, `developments`, `events`, `lifecycle_events`, `confluences`, `raw_signals_bronze`, `connector_state`, `evidence`, `signals` (with `Vector(384)` embedding + HNSW similarity), `contradictions`, `calibration_runs/history`, `scoring_weights`, `signal_routing`, `calibration_feedback`, `watch_items`, `audit_log`.
- **Redis 7** — cache + rate limiting via `REDIS_URL` (db 0); endpoints in `backend/app/api/v1/endpoints/cache.py`.
- **Postgres advisory locks** — single-execution scheduler protection (`try_advisory_lock` in `backend/app/db/session.py:43`).

## AI Providers

- **Ollama sidecar** (`http://ollama:11434`, model `gemma3:4b`) — local reasoning LLM host. Client logic in `backend/app/providers/gemma.py`.
- **xAI Grok API** — optional hosted fallback (`XAI_API_KEY`, `ENABLE_GROK_FALLBACK`). Privacy gate in `backend/app/providers/grok.py` (`validate_privacy_gate(classification)`) blocks any non-public data from leaving the machine.
- **Degraded BART provider** — local summarization-only fallback when no reasoning provider is available.

## Internal Contract (Backend ⇄ Frontend)

- REST under `/api/v1` (routers registered in `backend/app/main.py`): health, signals, intelligence, registry, observability, cache, pipeline, ingestion, search, feedback (+ root `/`).
- **Canonical contract sync**: OpenAPI 3.1 spec at `contracts/openapi.json`; `scripts/export_openapi.py` regenerates the typed client source of truth `frontend/types/api.ts` (518 lines). `tests/test_contract_drift.py` fails on drift.
- Frontend typed fetch layer: `frontend/lib/api.ts` (wraps all endpoints, `ApiError` in `frontend/lib/errors.ts`, DTO mappers in `frontend/lib/mappers.ts`). Base URL `NEXT_PUBLIC_API_BASE_URL`.

## No Other External Services

No auth provider (prototype), no email/webhook/S3 integrations. CORS restricted to `CORS_ORIGINS` (default `http://localhost:3000`).

---

*Mapped as part of full-repo codebase analysis: 2026-08-22*
