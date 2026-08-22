---
doc_type: codebase-map
focus: tech
analysis_date: 2026-08-22
---

# External Integrations

**Analysis Date:** 2026-08-22

## Data Source Connectors

All connectors implement the shared `SourceConnector` contract (`backend/app/connectors/base.py`): isolated, idempotent, incremental (per-connector `ConnectorState` cursor), quota-aware, retrying (`max_retries=3`, base delay 1.5s, timeout 30s), and observable. Connectors persist immutable bronze rows only — never intelligence.

| Connector | File | Profiles & Feeds | Auth / Credentials | Capabilities & Notes |
|---|---|---|---|---|
| NCBI PubMed | `backend/app/connectors/pubmed.py` | `haemophilia_clinical`, `haemophilia_safety`, `competitive_news` | Keyless public E-utilities + `NCBI_API_KEY`, `NCBI_TOOL`, `NCBI_EMAIL` | Tier 1 Authoritative. PII-scrubbed abstracts, verbatim XML persisted. |
| ClinicalTrials.gov v2 | `backend/app/connectors/clinical_trials.py` | `haemophilia_trials`, `novo_pipeline` | Keyless API v2 | Tier 1 Authoritative. `dataTimestamp` tracking to avoid redundant fetches; diff change event detection (`NEW_TRIAL`, `STATUS_CHANGED`, `RECRUITMENT_UPDATE`, `RESULTS_POSTED`, `STUDY_COMPLETED`, etc.). |
| openFDA Drugs & Safety | `backend/app/connectors/fda.py` | `haemophilia_approvals`, `fda_medwatch_safety`, `fda_drug_safety_comms` | Keyless public + `OPENFDA_API_KEY` | Tier 1 Authoritative. Multi-feed adapter: Drugs@FDA API + FDA MedWatch RSS + Drug Safety Communications RSS. |
| European Medicines Agency (EMA) | `backend/app/connectors/ema.py` | `haemophilia_ema`, `ema_epars`, `ema_orphan_designations` | Keyless public RSS feeds | Tier 1 Authoritative. Multi-feed RSS adapter: Medicines RSS, EPAR updates RSS, and Orphan Designations RSS. |
| NewsAPI | `backend/app/connectors/newsapi.py` | `haemophilia_market`, `gene_therapy_news` | `NEWSAPI_KEY` (tracked daily quota) | Tier 3 Discovery. Daily 100 req/day quota gate; graceful fallback and `CONFIGURATION_ERROR` diagnostics. |

Synthetic fallback: `data/synthetic_signals.json` (500 curated signals, `is_synthetic=true`, never presented as live). Seeded via `backend/app/db/seed.py`.

## Autonomous Background Scheduler (`backend/app/services/scheduler.py`)

- **Autonomous Persistent Workers**: Independent `asyncio` background tasks per connector (`ClinicalTrials`: 60m, `PubMed`: 60m, `EMA`: 30m, `FDA`: 30m, `NewsAPI`: 15m).
- **Jitter & Backoff**: ±10% random jitter on intervals; exponential backoff on connector errors up to `SCHEDULER_MAX_BACKOFF_MINUTES` (240m).
- **Concurrency Protection**: PostgreSQL 31-bit advisory locks (`try_advisory_lock` / `release_advisory_lock` in `backend/app/db/session.py`) prevent overlapping runs across multiple server instances.
- **Ingestion vs. Intelligence Separation**: LangGraph pipeline is triggered *only* when new/changed records are found (`records_new > 0`).
- **Telemetry**: Exposed via `GET /api/v1/observability/scheduler` (`SchedulerStatusResponse`).

## Deterministic Relevance Gate (`backend/app/services/relevance.py`)

- First-stage filter classifying bronze records into `DIRECTLY_RELEVANT`, `POTENTIALLY_RELEVANT`, and `IRRELEVANT`.
- Records explicit rationale (`relevance_reason`) and relevance scores.
- Rejects irrelevant records before promoting them to expensive NLP and embedding pipeline nodes.

## Databases & Cache

- **PostgreSQL 16 + pgvector** — primary datastore (`DATABASE_URL`, asyncpg). Schema managed by Alembic (`backend/alembic/versions/001…006`). 20 tables in `backend/app/models/__init__.py`.
- **Redis 7** — cache + rate limiting via `REDIS_URL` (db 0); endpoints in `backend/app/api/v1/endpoints/cache.py`.
- **Postgres advisory locks** — distributed single-execution scheduler protection.

## AI Providers

- **Ollama sidecar** (`http://ollama:11434`, model `gemma3:4b`) — local reasoning LLM host (`backend/app/providers/gemma.py`).
- **xAI Grok API** — optional hosted fallback (`XAI_API_KEY`, `ENABLE_GROK_FALLBACK`). Privacy gate in `backend/app/providers/grok.py` blocks non-public data.
- **Degraded BART provider** — local summarization-only fallback when no reasoning provider is available.

## Internal Contract (Backend ⇄ Frontend)

- REST under `/api/v1` (routers in `backend/app/api/v1/endpoints/`): health, signals, intelligence, registry, observability, cache, pipeline, ingestion, search, feedback.
- **Canonical contract sync**: OpenAPI 3.1 spec at `contracts/openapi.json`; `scripts/export_openapi.py` generates `frontend/types/api.ts`.
- Frontend typed fetch layer: `frontend/lib/api.ts` wrapping endpoints with `ApiError` (`frontend/lib/errors.ts`) and DTO mappers (`frontend/lib/mappers.ts`). Base URL `NEXT_PUBLIC_API_BASE_URL`.
