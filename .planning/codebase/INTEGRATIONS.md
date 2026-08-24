# External Integrations

**Analysis Date:** 2026-08-24

## APIs & External Services

**Data Source Connectors** (all async httpx-based, subclass `SourceConnector` from `backend/app/connectors/base.py`; verbatim payloads persisted to bronze per D-23; PII/PHI scrubbed via `backend/app/services/pii.py`):

- NCBI PubMed E-utilities - Publication surveillance
  - Files: `backend/app/connectors/pubmed.py`
  - Endpoints: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` + `efetch.fcgi` (XML)
  - Auth: `NCBI_API_KEY` (optional, raises rate limit); `NCBI_TOOL=MetaRadar`, `NCBI_EMAIL` sent as UA etiquette
  - Pattern: batched (200/batch, 0.35s delay), incremental per profile via ConnectorState cursor

- ClinicalTrials.gov API v2 - Clinical trial signals
  - File: `backend/app/connectors/clinical_trials.py`
  - Endpoint: `https://clinicaltrials.gov/api/v2/studies` (JSON, nextPageToken pagination, PAGE_SIZE=100)
  - Auth: none

- EMA Medicines RSS - Regulatory feed
  - File: `backend/app/connectors/ema.py`
  - Endpoint: `https://www.ema.europa.eu/en/medicines/rss` (XML parsed with stdlib `xml.etree`)
  - Auth: none; keyword filtering by domain-config profiles

- openFDA / FDA - Drug & safety regulatory data
  - File: `backend/app/connectors/fda.py`
  - Endpoints: `https://api.fda.gov/drug/drugsfda.json` (JSON) + FDA MedWatch/Drug Safety RSS feeds
  - Auth: `OPENFDA_API_KEY` (optional, higher rate limits)

- NewsAPI - News monitoring
  - File: `backend/app/connectors/newsapi.py`
  - Endpoint: `https://newsapi.org/v2/everything`
  - Auth: `NEWSAPI_KEY` or `NEWS_API_KEY` (**required** — connector returns CONFIGURATION_ERROR without it; see `configuration_error_for()` in `backend/app/core/config.py`)
  - Quota-aware: ~100 req/day dev cap (D-20), tracks `X-RateLimit-Remaining` header into ConnectorState cursor JSON

**LLM Providers** (fallback chain orchestrated by `ProviderFactory.execute_task` in `backend/app/providers/factory.py`: Local Gemma → Grok (privacy-gated) → BART Degraded):

- Ollama (local Gemma 3 4B) - Primary reasoning engine
  - File: `backend/app/providers/gemma.py`
  - Client: raw `httpx.AsyncClient` against `OLLAMA_HOST` (default `http://localhost:11434`, compose: `http://ollama:11434`)
  - Model: `OLLAMA_MODEL=gemma3:4b` (Q4 int4); alternative GGUF path via llama-cpp-python scanning `models/*.gguf` (`models/gemma-3-4b-it-Q4_K_M.gguf` present)
  - Auth: none (local daemon); never-crash contract D-12 → raises `OllamaUnavailableError`

- xAI Grok API - Hosted fallback
  - File: `backend/app/providers/grok.py`
  - Endpoint: `POST https://api.x.ai/v1/chat/completions` (model `grok-beta`)
  - Auth: `XAI_API_KEY` or `GROK_API_KEY` (Bearer header); gated by `ENABLE_GROK_FALLBACK=true` AND `validate_privacy_gate()` — only PUBLIC/SYNTHETIC data classifications may leave the host (SECURITY_STANDARDS privacy gate)

- BART Degraded (offline fallback) - Summarize-only stub
  - File: `backend/app/providers/degraded.py` — no network call; deterministic truncation/bullet summary labeled as AI-reasoning-fallback output

## Data Storage

**Databases:**
- PostgreSQL 16 + pgvector extension
  - Image: `pgvector/pgvector:pg16` (`docker-compose.yml`)
  - Connection: `DATABASE_URL` (default `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`)
  - Client: SQLAlchemy 2.0 async engine (`backend/app/db/session.py`, pool_pre_ping, pool_size=10/max_overflow=20) + `asyncpg` driver
  - Migrations: Alembic (`backend/alembic/env.py`, versions `001`–`011` in `backend/alembic/versions/`)
  - Vectors: `pgvector.sqlalchemy.Vector(384)` column on signals table (`backend/app/models/__init__.py`)
  - Concurrency: PostgreSQL advisory locks for scheduler single-execution (`try_advisory_lock` in `backend/app/db/session.py`)
  - Seed: `backend/app/db/seed.py`

**File Storage:**
- Local filesystem only — GGUF models under `models/`; verbatim bronze payloads stored in Postgres JSON columns, not object storage

**Caching:**
- Redis 7 (`REDIS_URL`, default `redis://localhost:6379/0`)
  - Usage: server-side cache flush endpoint (`backend/app/api/v1/endpoints/cache.py`) and health diagnostics (`backend/app/api/v1/endpoints/health.py`)
  - Client: `redis.asyncio` (`aioredis.from_url`)

## Authentication & Identity

**Auth Provider:**
- Custom / minimal — no OAuth/SSO/JWT detected
- Optional shared API key: `METARADAR_API_KEY` (`backend/app/core/config.py`) enforced at middleware/deps layer (`backend/app/api/deps.py`)
- Mutation throttling: `MUTATION_RATE_LIMIT_PER_MINUTE=60`
- CORS allow-list: `CORS_ORIGINS` (default `http://localhost:3000`), configured in `backend/app/main.py`
- Frontend calls backend directly with fetch — no auth token flow in `frontend/lib/api.ts`

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/Datadog SDK)

**Logs:**
- structlog JSON logging (`configure_structlog(json_logs=True)` in `backend/app/main.py`, config in `backend/app/core/logging.py`)
- Request correlation: `CorrelationIdMiddleware` from `asgi-correlation-id` (`backend/app/core/middleware.py`)
- Health/diagnostics endpoints: `/api/v1/health/*` and `/api/v1` observability router (`backend/app/api/v1/endpoints/health.py`, `observability.py`); source health persisted to DB (`008_health_logs_telemetry` migration)

## CI/CD & Deployment

**Hosting:**
- Docker Compose single-host (services: postgres, redis, ollama, backend [+gpu profile], frontend) — `docker-compose.yml`

**CI Pipeline:**
- GitHub Actions: `.github/workflows/ci.yml` — pytest → OpenAPI contract drift check (`scripts/export_openapi.py` vs `frontend/types/api.ts`) → pnpm install → tsc --noEmit → banned-class gate → ESLint → next build

**Contract Sync:**
- Canonical OpenAPI: `contracts/openapi.json`; generated TS types: `frontend/types/api.ts`; regenerator: `scripts/export_openapi.py`

## Environment Configuration

**Required env vars:**
- `DATABASE_URL`, `REDIS_URL` (have local-dev defaults in `backend/app/core/config.py`; always override for shared/deployed envs)
- `NEWSAPI_KEY` (or `NEWS_API_KEY`) — required for the newsapi connector to leave CONFIGURATION_ERROR state

**Optional env vars:**
- `NCBI_API_KEY`, `OPENFDA_API_KEY` — rate-limit upgrades
- `XAI_API_KEY` / `GROK_API_KEY` + `ENABLE_GROK_FALLBACK=true` — hosted LLM fallback
- `METARADAR_API_KEY`, `CORS_ORIGINS`, `MUTATION_RATE_LIMIT_PER_MINUTE` — API security
- `LLM_PROVIDER`, `LLM_DEVICE`, `LLM_DTYPE`, `LOCAL_GGUF_MODEL`, `LOCAL_GGUF_PATH`, `MODELS_DIR`, `OLLAMA_HOST`, `OLLAMA_MODEL` — inference tuning
- `EMBEDDING_MODEL*` — pinned model identity (do not change revision casually; backfill script exists: `backend/app/services/embeddings_backfill.py`)
- `SCHEDULER_*_INTERVAL_MINUTES`, `SCHEDULER_JITTER_PERCENT`, `SCHEDULER_MAX_BACKOFF_MINUTES`, `ENABLE_BACKGROUND_SCHEDULER` — autonomous ingestion cadence (`backend/app/services/scheduler.py`)
- Frontend: `NEXT_PUBLIC_API_URL` (read in `frontend/lib/api.ts:149`; compose sets `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` — note the code reads `NEXT_PUBLIC_API_URL`, defaulting to `http://localhost:8000/api/v1`)

**Secrets location:**
- Root `.env` (gitignored; present on disk — never read/commit). Template: `.env.example`. CI has no secrets; Grok tests skip without key (D-16).

## Webhooks & Callbacks

**Incoming:**
- None — all external data pulled on schedule (`SourceScheduler` in `backend/app/services/scheduler.py`, started in app lifespan `backend/app/main.py`)

**Outgoing:**
- None — no outbound webhooks/notification services detected; all outbound traffic is the connector/provider HTTP calls listed above

---

*Integration audit: 2026-08-24*
