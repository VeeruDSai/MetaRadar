# External Integrations

**Analysis Date:** 2026-08-23

## APIs & External Services

**Data Connectors (polling ingestion, `backend/app/connectors/`):**

All connectors extend the shared async base with retry/backoff, dedup, and state tracking in `backend/app/connectors/base.py` (`ConnectorFetchError`, `RawSignalPayload`, `ConnectorStatus`).

- ClinicalTrials.gov API v2 - clinical study signals
  - SDK/Client: raw `httpx` calls in `backend/app/connectors/clinical_trials.py` (`BASE_URL = https://clinicaltrials.gov/api/v2/studies`)
  - Auth: none (public API)

- PubMed E-utilities (NCBI) - biomedical literature
  - Client: `backend/app/connectors/pubmed.py` (`BASE_ESEARCH = https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`, `BASE_EFETCH = .../efetch.fcgi`)
  - Auth: optional `NCBI_API_KEY` (query param); identifies as `NCBI_TOOL` / `NCBI_EMAIL` (defaults in `backend/app/core/config.py`)

- openFDA Drugs (drugsfda) + FDA MedWatch safety
  - Client: `backend/app/connectors/fda.py` (`BASE_URL = https://api.fda.gov/drug/drugsfda.json`)
  - Auth: optional `OPENFDA_API_KEY` (higher rate limits only)

- EMA medicines RSS feed - EU regulatory updates
  - Client: `backend/app/connectors/ema.py` (`DEFAULT_RSS_URL = https://www.ema.europa.eu/en/medicines/rss`, XML parsing)
  - Auth: none

- NewsAPI - pharma news
  - Client: `backend/app/connectors/newsapi.py` (`BASE_URL = https://newsapi.org/v2/everything`)
  - Auth: **required** `NEWSAPI_KEY` sent as `X-Api-Key` header; missing key yields `CONFIGURATION_ERROR` surfaced via `configuration_error_for()` in `backend/app/core/config.py`

**LLM Providers (fallback chain, `backend/app/providers/factory.py`):**

Execution order: Local Gemma → xAI Grok (privacy-gated) → Degraded BART summary.

- Ollama sidecar (local Gemma 3 4B) - primary inference
  - Client: `backend/app/providers/gemma.py` — httpx `POST {OLLAMA_HOST}/api/generate`, availability probe `GET /api/tags`; model `gemma3:4b`
  - Never-crash contract: raises `OllamaUnavailableError`, factory falls through
- xAI Grok API - hosted fallback (disabled by default)
  - Client: `backend/app/providers/grok.py` — `POST https://api.x.ai/v1/chat/completions`, model `grok-beta`
  - Auth: `XAI_API_KEY` bearer token; gated by `ENABLE_GROK_FALLBACK=true` AND mandatory privacy gate `validate_privacy_gate()` — only PUBLIC/SYNTHETIC-classified payloads may leave the host
- BART degraded mode - offline last resort
  - `backend/app/providers/degraded.py` — deterministic truncate-to-300-char factual summary; no network

**Embeddings:**
- fastembed (ONNX, CPU) in-process — NOT a remote API. Model `sentence-transformers/all-MiniLM-L6-v2`, pinned revision `e4bb823e...`, 384-dim, loaded lazily in `backend/app/services/embeddings.py`

## Data Storage

**Databases:**
- PostgreSQL 16 with pgvector extension
  - Image: `pgvector/pgvector:pg16` (`docker-compose.yml:3`)
  - Connection: `DATABASE_URL` (default `postgresql+asyncpg://metaradar:...@localhost:5432/metaradar`)
  - Client: SQLAlchemy 2.x async engine + session factory in `backend/app/db/session.py`; PostgreSQL advisory locks (`pg_try_advisory_lock`) guard scheduler single-execution
  - Migrations: Alembic, 11 versions in `backend/alembic/versions/` (`001_initial_v51_schema.py` … `011_widen_signals_fingerprint.py`)
  - Vector search: pgvector `Vector(384)` columns queried via `backend/app/services/vector_query.py`

**File Storage:**
- Local filesystem only — raw payload JSON retained per `RAW_SIGNAL_RETENTION_DAYS=30` policy; domain config at `config/haemophilia.yaml` (mounted read-only into backend container)

**Caching:**
- Redis 7-alpine (`docker-compose.yml:20`)
  - Connection: `REDIS_URL` (default `redis://localhost:6379/0`)
  - Client: `redis.asyncio` in `backend/app/api/v1/endpoints/cache.py` (cache management endpoints) and health checks in `backend/app/api/v1/endpoints/health.py`

## Authentication & Identity

**Auth Provider:**
- None (no user auth/OAuth/JWT detected anywhere in `backend/app/api/`)
  - Access control is CORS-based only: `CORS_ORIGINS` (default `http://localhost:3000`) enforced by FastAPI CORSMiddleware in `backend/app/main.py:66-73`
  - LLM-side "identity" is data classification, not user identity: `DataClassification` enum in `backend/app/providers/base.py` drives the Grok privacy gate

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Datadog detected)

**Logs:**
- structlog JSON logging configured in `backend/app/core/logging.py` (`configure_structlog(json_logs=True)`)
- Request correlation via `CorrelationIdMiddleware` (asgi-correlation-id) in `backend/app/core/middleware.py`
- In-app observability endpoints under `/api/v1/observability` (`backend/app/api/v1/endpoints/observability.py`) and source health telemetry (`backend/app/connectors/base.py` state persisted to DB)
- Process logs written to `logs/backend.log` / `logs/frontend.log` by `start.py`

## CI/CD & Deployment

**Hosting:**
- Local/on-prem Docker Compose only (no cloud deploy config detected). Services: postgres, redis, ollama, backend (+`gpu` profile), frontend

**CI Pipeline:**
- GitHub Actions — `.github/workflows/ci.yml` ("MetaRadar v5.1 CI"): pytest suite → OpenAPI contract-sync check (`python scripts/export_openapi.py` + git diff gate on `frontend/types/api.ts`) → pnpm install → `tsc --noEmit` → banned-classes gate → ESLint → `next build`

## Environment Configuration

**Required env vars (backend — see `backend/app/core/config.py`):**
- `DATABASE_URL`, `REDIS_URL` (have local defaults)
- `NEWSAPI_KEY` (required for NewsAPI connector to be operational)
- Optional keys: `NCBI_API_KEY`, `OPENFDA_API_KEY` (rate limits), `XAI_API_KEY` + `ENABLE_GROK_FALLBACK=true` (hosted LLM fallback)
- LLM tuning: `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`
- Scheduler: `ENABLE_BACKGROUND_SCHEDULER`, `SCHEDULER_{CT,PUBMED,EMA,FDA,NEWS}_INTERVAL_MINUTES`, `SCHEDULER_JITTER_PERCENT`, `SCHEDULER_MAX_BACKOFF_MINUTES`, `SCHEDULER_FAILURE_THRESHOLD`, `SCHEDULER_STALE_MULTIPLIER`

**Frontend env vars:**
- `NEXT_PUBLIC_API_URL` — backend base URL, read at `frontend/lib/api.ts:142`. Discrepancy: `docker-compose.yml:102` exports `NEXT_PUBLIC_API_BASE_URL` instead, which is ignored by code.

**Secrets location:**
- `.env` at repo root (loaded by pydantic-settings; present but contents never committed). `.env.example` documents variables. Compose file contains only local dev credentials for Postgres.

## Webhooks & Callbacks

**Incoming:**
- None — all external data arrives via scheduled polling (asyncio workers with jitter/backoff in `backend/app/services/scheduler.py`, started from app lifespan in `backend/app/main.py:44-46`)

**Outgoing:**
- None — no outbound webhooks/callback notifications; all outbound traffic is request/response HTTP (connectors + LLM providers listed above)

---

*Integration audit: 2026-08-23*
