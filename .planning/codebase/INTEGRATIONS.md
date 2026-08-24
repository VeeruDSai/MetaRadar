# External Integrations

**Analysis Date:** 2026-08-24

## APIs & External Services

**Life-Science Data Connectors** (all under `backend/app/connectors/`, sharing the abstract contract in `backend/app/connectors/base.py` — bounded retry/backoff, bronze-only persistence, per-source state in `connector_states` table):

- **PubMed (NCBI E-utilities)** - Biomedical publication signals
  - Files: `backend/app/connectors/pubmed.py` (esearch + efetch: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi`, `.../efetch.fcgi`)
  - Client: raw `httpx.AsyncClient` via `SourceConnector._fetch_with_retry`
  - Auth: `NCBI_API_KEY` (optional, higher rate limits) + `NCBI_TOOL` ("MetaRadar") + `NCBI_EMAIL` (`backend/app/core/config.py` lines 86-88)

- **ClinicalTrials.gov API v2** - Trial registry signals
  - File: `backend/app/connectors/clinical_trials.py` (`https://clinicaltrials.gov/api/v2/studies`)
  - Auth: none

- **OpenFDA (drugsfda endpoint)** - Drug approval/safety signals
  - File: `backend/app/connectors/fda.py` (`https://api.fda.gov/drug/drugsfda.json`)
  - Auth: `OPENFDA_API_KEY` (optional)

- **EMA (European Medicines Agency)** - Regulatory news via RSS
  - File: `backend/app/connectors/ema.py` (default RSS `https://www.ema.europa.eu/en/medicines/rss`; per-profile override via domain config `rss_url`)
  - Auth: none

- **NewsAPI** - News signals
  - File: `backend/app/connectors/newsapi.py` (`https://newsapi.org/v2/everything`)
  - Auth: `NEWSAPI_KEY` or `NEWS_API_KEY` (**required**; missing key surfaces as `CONFIGURATION_ERROR` run status via `configuration_error_for()` in `backend/app/core/config.py` lines 109-120)

Connector queries are config-driven from `config/haemophilia.yaml` (parsed into `ConnectorQueryProfile` models in `backend/app/core/domain_config.py`) — connectors execute config, never invent queries.

**LLM Providers** (fallback chain orchestrated by `ProviderFactory` in `backend/app/providers/factory.py`: Local Gemma → xAI Grok → Degraded factual mode):

- **Ollama sidecar (primary local reasoning)** - Hosts Gemma 3 4B
  - SDK/Client: plain `httpx.AsyncClient` with `base_url=settings.OLLAMA_HOST` (default `http://localhost:11434`), model `gemma3:4b`
  - Implementation: `backend/app/providers/gemma.py` (`GemmaProvider`)
  - Container: `ollama/ollama:latest` in `docker-compose.yml` with NVIDIA device reservation; first run needs `docker exec metaradar-ollama ollama pull gemma3:4b`

- **Local GGUF engine (alternative local path)** - llama-cpp-python executing `.gguf` files discovered in root `models/` directory
  - Implementation: `backend/app/providers/gemma.py` (`find_local_gguf_model()` + `_generate_with_local_gguf()`); default download is Gemma 3 4B Instruct Q4_K_M from Hugging Face (`setup.py` line 326)
  - Hardware env: `LLM_DEVICE` (`auto|cpu|cuda`), `LLM_GPU_LAYERS` read directly from os.environ in `backend/app/providers/gemma.py`

- **xAI Grok (hosted fallback)** - Optional cloud reasoning behind a privacy gate
  - Endpoint: `https://api.x.ai/v1/chat/completions`, model `grok-beta` (`backend/app/providers/grok.py` lines 22-23)
  - Auth: `XAI_API_KEY` (or legacy alias `GROK_API_KEY`); only activated when `ENABLE_GROK_FALLBACK=true` / `LLM_PROVIDER=xai|auto`
  - Privacy gate: `validate_privacy_gate()` blocks all payloads except `PUBLIC`/`SYNTHETIC` classification before transmission (`backend/app/providers/grok.py` lines 56-67)

- **Degraded provider (terminal fallback)** - No external calls
  - Implementation: `backend/app/providers/degraded.py` — truncation-based factual bullet summary labeled `bart_degraded`/`facebook/bart-large-cnn` metadata but loads no actual model; guarantees "never-crash" behavior when both LLM paths fail

**Embeddings:**
- **fastembed (ONNX, CPU, fully local)** - Model `sentence-transformers/all-MiniLM-L6-v2` pinned to revision `e4bb823e5956b6277b069d276b978c48a73507c7`, 384-dim, max seq 256
  - File: `backend/app/services/embeddings.py` (lazy in-process singleton; inference offloaded to executor); backfill tooling in `backend/app/services/embeddings_backfill.py`

## Data Storage

**Databases:**
- **PostgreSQL 16 + pgvector** (image `pgvector/pgvector:pg16`, container `metaradar-postgres`)
  - Connection: `DATABASE_URL` (asyncpg driver; default `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar` in `backend/app/core/config.py` line 30)
  - Client: SQLAlchemy 2.0 async engine/session factory in `backend/app/db/session.py` (pool_size=10, max_overflow=20, pool_pre_ping); PostgreSQL advisory locks for scheduler single-execution (`try_advisory_lock`/`release_advisory_lock`, same file)
  - Migrations: Alembic, `backend/alembic/versions/001_*` … `012_*`; vector column on signals (`Vector(384)` in `backend/app/models/__init__.py` line 291), queried via `backend/app/services/vector_query.py`
  - Raw payload retention policy: `RAW_SIGNAL_RETENTION_DAYS` (default 30)

**File Storage:**
- Local filesystem only — GGUF model files in root `models/` dir (`MODELS_DIR` setting); no object storage service

**Caching:**
- **Redis 7** (`redis:7-alpine`, container `metaradar-redis`)
  - Connection: `REDIS_URL` (default `redis://localhost:6379/0`)
  - Client: `redis.asyncio` — cache-clear endpoint `backend/app/api/v1/endpoints/cache.py`, health probe `backend/app/api/v1/endpoints/health.py`
  - Note: Redis usage is currently thin (cache management/health); primary state lives in PostgreSQL

## Authentication & Identity

**Auth Provider:**
- None (no user identity system, no OAuth/JWT)
- Optional service-level API key gate: mutations require `X-API-Key` header matching `METARADAR_API_KEY` **when set** — local dev stays open when unset (`require_mutation_auth` in `backend/app/api/deps.py` lines 16-27)
- In-memory mutation rate limiting: `mutation_rate_limit` dependency, default 60/min (`MUTATION_RATE_LIMIT_PER_MINUTE`, same file)
- CORS restricted to `CORS_ORIGINS` (default `http://localhost:3000`) in `backend/app/main.py` lines 66-73

## Monitoring & Observability

**Error Tracking:**
- None (no Sentry/equivalent)

**Logs:**
- structlog JSON logging configured at import time (`backend/app/core/logging.py`, called from `backend/app/main.py` line 25); ISO UTC timestamps, INFO bound level
- Custom ASGI correlation middleware binding `X-Request-ID`/`X-Correlation-ID` contextvars (`backend/app/core/middleware.py`)
- Secret scrubbing log filter applied to stdlib records too (`SecretScrubFilter` in `backend/app/core/redact.py`); connector error strings passed through `redact_text()` before persistence/logging

**Telemetry:**
- Connector run telemetry persisted to `source_health_logs` table and live `sources` rows (`_persist_health_log` in `backend/app/connectors/base.py` lines 366-433): http_status, latency_ms, records fetched/accepted/rejected, upstream timestamps — honest-status contract (D-22), never fabricates values
- Health endpoints: `/api/v1/health`, `/health/ready`, `/health/models`, `/health/connectors` (`backend/app/api/v1/endpoints/health.py`); scheduler status via `/api/v1/observability/*`

## Background Scheduling

- Autonomous asyncio scheduler singleton started in FastAPI lifespan (`backend/app/main.py` lines 43-52 → `SourceScheduler` in `backend/app/services/scheduler.py`)
- Per-source worker tasks with intervals from settings (`SCHEDULER_CT_INTERVAL_MINUTES`=60, PUBMED=60, EMA=30, FDA=30, NEWS=15), jitter ±10%, exponential backoff capped at 120 min, failure threshold 3, PostgreSQL advisory locks prevent duplicate runs across processes

## CI/CD & Deployment

**Hosting:**
- Local Docker Compose stack only (`docker-compose.yml`); no cloud deployment manifests detected. Process-mode alternative: `start.py` launches uvicorn + Next dev directly on host.

**CI Pipeline:**
- GitHub Actions: `.github/workflows/ci.yml` — pytest suite, OpenAPI→TypeScript contract-sync gate (`scripts/export_openapi.py` vs `frontend/types/api.ts` must be unchanged), then pnpm install, `tsc --noEmit`, banned-class gate, lint, build
- Canonical API contract committed at `contracts/openapi.json`

## Environment Configuration

**Required env vars:**
- `DATABASE_URL`, `REDIS_URL` (have local-dev defaults; override for any shared environment)
- `NEWSAPI_KEY` — required for the NewsAPI connector to leave CONFIGURATION_ERROR state
- `LLM_PROVIDER` (`local|xai|auto`), `OLLAMA_HOST`, `OLLAMA_MODEL` for reasoning path
- `ENABLE_GROK_FALLBACK` + `XAI_API_KEY`/`GROK_API_KEY` for hosted fallback
- Frontend: `NEXT_PUBLIC_API_URL` (read in `frontend/lib/api.ts` line 149 and `frontend/components/metaradar.tsx` line 897). ⚠️ `docker-compose.yml` passes `NEXT_PUBLIC_API_BASE_URL` to the frontend container, which nothing reads — dead variable; Docker frontend silently falls back to `http://localhost:8000/api/v1`.

**Optional env vars:** `METARADAR_API_KEY`, `CORS_ORIGINS`, `OPENFDA_API_KEY`, `NCBI_API_KEY`, `NCBI_TOOL`, `NCBI_EMAIL`, `EMBEDDING_MODEL*`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`, `LLM_DEVICE`, `LLM_DTYPE`, `LLM_GPU_LAYERS`, `LOCAL_GGUF_MODEL`, `LOCAL_GGUF_PATH`, `MODELS_DIR`, `RAW_SIGNAL_RETENTION_DAYS`, `SCHEDULER_*` family

**Secrets location:**
- Root `.env` (present, gitignored — contents not inspected) with `.env.example` template; loaded by pydantic-settings (`backend/app/core/config.py` `_ENV_FILES`) and by `start.py`'s own parser. Never commit real keys; CI runs green without any key (Grok fallback disabled by default).

## Webhooks & Callbacks

**Incoming:**
- None (all data enters via scheduled polling connectors)

**Outgoing:**
- None (only request/response calls to the APIs listed above; Grok calls are gated by privacy classification)

---

*Integration audit: 2026-08-24*
