# External Integrations

**Analysis Date:** 2026-08-30

## APIs & External Services

**Biomedical Literature & Trials:**
- **NCBI PubMed** (`PubMedConnector`) — E-utilities ESearch + EFetch; quota-free (NCBI_API_KEY optional for higher limits); batch freshness; backfill 180 days; XML abstracts PII-scrubbed before persistence
  - SDK/Client: `httpx.AsyncClient` (no dedicated SDK)
  - Auth: `NCBI_API_KEY` env var, `NCBI_TOOL`, `NCBI_EMAIL`
- **ClinicalTrials.gov** (`ClinicalTrialsConnector`) — API v2 studies endpoint; near-real-time freshness; paginated via `nextPageToken`; NCT-fingerprinted; backfill 365 days
  - SDK/Client: `httpx.AsyncClient`
  - Auth: None (public API)

**Regulatory:**
- **OpenFDA** (`OpenFDAConnector`) — Drugs@FDA API (`api.fda.gov/drug/drugsfda.json`) with optional `OPENFDA_API_KEY` for higher rate limits; also FDA MedWatch/Drug Safety RSS feeds
  - SDK/Client: `httpx.AsyncClient`
  - Auth: `OPENFDA_API_KEY` env var (optional)
- **EMA** (`EMARSSConnector`) — EMA medicines RSS feed + news RSS + orphan designations; keyword-filtered
  - SDK/Client: `httpx.AsyncClient` + `xml.etree.ElementTree`
  - Auth: None (RSS feeds)

**News & Media:**
- **NewsAPI** (`NewsAPIConnector`) — NewsAPI.org v2 everything endpoint; quota-aware (100 req/day dev cap); tracks `X-RateLimit-Remaining` header persisted to ConnectorState; halts with DEGRADED on exhaustion
  - SDK/Client: `httpx.AsyncClient`
  - Auth: `NEWSAPI_KEY` or `NEWS_API_KEY` env var
- **BioPharma Dive** (`BioPharmaDiveRSSConnector`) — RSS feed (`biopharmadive.com/feeds/news/`); keyword-filtered
  - SDK/Client: `httpx.AsyncClient` + XML parsing
  - Auth: None (RSS)
- **FiercePharma** (`FiercePharmaRSSConnector`) — RSS feed (`fiercepharma.com/rss/xml`); keyword-filtered
  - SDK/Client: `httpx.AsyncClient` + XML parsing
  - Auth: None (RSS)
- **ET Pharma** (`ETPharmaRSSConnector`) — Economic Times India pharma RSS (`pharma.economictimes.indiatimes.com/rss/topstories`) + drug_approvals feed
  - SDK/Client: `httpx.AsyncClient` + XML parsing
  - Auth: None (RSS)

**LLM / AI Reasoning:**
- **Local Gemma (llama-cpp-python)** (`GemmaProvider`) — Loads `.gguf` files from `models/` directory via `llama-cpp-python` Llama class; GPU-accelerated with CUDA 12.4 (n_gpu_layers), CPU fallback with `n_gpu=0`
  - SDK/Client: `llama-cpp-python` package
  - Auth: None (local inference)
- **Local Gemma (Ollama sidecar)** (`GemmaProvider`) — Connects to Ollama daemon at `OLLAMA_HOST` (default `http://localhost:11434`); model `gemma3:4b`; supports streaming via `/api/generate` NDJSON
  - SDK/Client: `httpx.AsyncClient` to Ollama API
  - Auth: None (local daemon)
- **Hosted xAI Grok API** (`GrokProvider`) — Chat completions at `api.x.ai/v1/chat/completions` with `grok-beta` model; privacy gate enforces PUBLIC/SYNTHETIC classification only
  - SDK/Client: `httpx.AsyncClient`
  - Auth: `XAI_API_KEY` or `GROK_API_KEY` env var; Bearer token
- **BART Degraded Fallback** (`DegradedProvider`) — Truncation-based factual summarization when no LLM available; REASONING and ACTIONS explicitly disabled
  - SDK/Client: None (built-in text processing)

**Embeddings:**
- **FastEmbed** (`sentence-transformers/all-MiniLM-L6-v2`, revision `e4bb823e5956b6277b069d276b978c48a73507c7`) — 384-dimensional embeddings, max sequence length 256; used for vector search
  - SDK/Client: `fastembed` package
  - Auth: None (local model)

## Data Storage

**Databases:**
- **PostgreSQL 16** + **pgvector** (384-dimensional vectors)
  - Connection: `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`
  - Client: SQLAlchemy 2.0 async ORM with `asyncpg` driver
  - Migrations: Alembic (`backend/alembic.ini`, `backend/alembic/versions/` with 14 migration files)
  - Docker: `pgvector/pgvector:pg16` image; persistent volume `pgdata`
- **Redis 7** (async) — Caching, rate-limiting, connector state/quota tracking
  - Connection: `redis://localhost:6379/0`
  - Client: `redis` >=5.0.3 Python async client
  - Docker: `redis:7-alpine`; persistent volume `redisdata`

**File Storage:**
- **Local filesystem** for GGUF model files (`models/` directory, `.gguf` files)
- **Local filesystem** for application logs (`logs/backend.log`, `logs/frontend.log`)
- **Local filesystem** for domain config (`config/haemophilia.yaml`)
- Docker volumes: `models_cache` (appended to `/app/models`), `ollama_models` (Ollama model storage at `/root/.ollama`)

**Caching:**
- Redis for connector quota tracking, session state, and pipeline caching
- In-memory caching for domain config (`_domain_config_cache` in `domain_config.py`)

## Authentication & Identity

**Auth Provider:**
- Custom session-based authentication with bcrypt password hashing and itsdangerous timestamped token signing
- Implementation: `backend/app/core/security.py` (`hash_password`, `verify_password`, `sign_session_token`, `unsign_session_token`, `generate_session_bound_csrf`, `verify_session_bound_csrf`)
- Session cookie: `metaradar_session`; CSRF cookie: `metaradar_csrf`
- Demo mode enabled (`DEMO_MODE=true`) with `/auth/demo-login` endpoint; auto-seeds demo users

**Session Management:**
- Session lifetime: 28800s absolute, 3600s idle timeout (`SESSION_LIFETIME_SECONDS`, `SESSION_IDLE_TIMEOUT_SECONDS`)
- HMAC-SHA256 CSRF tokens cryptographically bound to session ID
- SHA-256 token hashing for persistent session indexing

**API Key Management:**
- `METARADAR_API_KEY` — Optional API key for service access
- `CORS_ORIGINS` — Allowed origins (default `http://localhost:3000`)

## Monitoring & Observability

**Error Tracking:**
- Not detected — no dedicated error tracking service (Sentry, etc.)
- `OllamaUnavailableError` and `GrokUnavailableError` propagate for graceful fallback
- `ConnectorFetchError` for HTTP failure detection

**Logs:**
- **structlog** structured JSON logging (`backend/app/core/logging.py`)
- Secret scrubbing via `SecretScrubFilter` and `_scrub_secrets` processor — redacts API keys, tokens, passwords, emails
- Correlation ID tracing via `CorrelationIdMiddleware` (`X-Request-ID`, `X-Correlation-ID`)
- Log output to `logs/backend.log` and `logs/frontend.log` via `start.py`
- `[ATHENA]`, `[INGESTION]`, `[PIPELINE]`, `[LLM]` markers surfaced in live telemetry

**Health Checks:**
- `backend/app/api/v1/endpoints/health.py` — Service health endpoint
- `backend/app/connectors/base.py` — `ConnectorStatus` and `SourceHealthLog` per connector
- Docker health checks on all compose services (`pg_isready`, `redis-cli ping`, `curl` to Ollama and backend)
- `start.py` heartbeat telemetry every ~15 seconds checking backend (200 OK) and frontend availability

**Observability Endpoint:**
- `backend/app/api/v1/endpoints/observability.py` — Observability & system health API
- `backend/app/api/v1/endpoints/cache.py` — Cache management API

## CI/CD & Deployment

**Hosting:**
- Docker Compose multi-service deployment (`docker-compose.yml`)
- Services: `postgres`, `redis`, `backend`/`backend-gpu` (GPU profile), `frontend`, `ollama`
- Backend exposed on port 8000, frontend on port 3000

**CI Pipeline:**
- **GitHub Actions** (`.github/workflows/ci.yml`) — MetaRadar v5.1 CI
  - Triggers: push to `main`, `develop`, `feature/*`; PRs to `main`, `develop`
  - Steps: Backend pytest (`pytest -v`), TypeScript contract sync (`scripts/export_openapi.py` → `frontend/types/api.ts` diff check), pnpm install, `tsc --noEmit`, banned class gate (`check-banned-classes`), `pnpm lint`, `pnpm build`
  - Python 3.11 via `actions/setup-python@v5`; Node.js 22 via `actions/setup-node@v4`; pnpm via `pnpm/action-setup@v4`

**Deployment:**
- Docker Compose production: `docker compose up -d`
- Backend launched via `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- Frontend launched via `pnpm run dev` or `npx next start -p 3000` (production)
- `start.py` orchestrates service startup with port cleanup, graceful shutdown on SIGINT/SIGTERM, and live log streaming
- `setup.py` automates prerequisite checks, dependency installation, Docker bootstrap, migrations, seeding, and model setup

**GPU Deployment:**
- `backend-gpu` service uses `profiles: ["gpu"]` with NVIDIA device reservation (1 GPU, all capabilities)
- CUDA 12.4 prebuilt wheel from `jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu124`
- `LLM_DEVICE=cuda:0` for GPU backend

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `LLM_PROVIDER` — `local` (default), `xai`, or `auto`
- `NEWSAPI_KEY` — NewsAPI key (required for NewsAPI connector; `configuration_error_for` validates)
- `CORS_ORIGINS` — Comma-separated allowed origins

**Optional env vars:**
- `XAI_API_KEY` / `GROK_API_KEY` — xAI Grok API key for hosted fallback
- `ENABLE_GROK_FALLBACK` — Toggle Grok fallback (`true`/`false`)
- `NCBI_API_KEY` — NCBI E-utilities API key
- `OPENFDA_API_KEY` — OpenFDA API key
- `LLM_DEVICE` — `cpu`, `cuda`, `auto`
- `LLM_GPU_LAYERS` — GPU layer count for CUDA
- `MAX_CONTEXT_TOKENS` (default 2048), `MAX_OUTPUT_TOKENS` (default 512)
- `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION` (default 384)
- `SECRET_KEY` — Session signing secret (default `dev-secret-change-in-production`)
- `DOMAIN_CONFIG_PATH` — Override domain config YAML path

**Secrets Location:**
- `.env` file at repository root (listed in `.gitignore` but present with development values)
- Per-service secrets in Docker Compose environment section (PostgreSQL password `metaradar_pass`)
- **WARNING:** `.env` contains actual API keys for development; these must not be committed to production repositories

**Webhooks & Callbacks:**
- None detected — all external integrations are pull-based (API polling/RSS feed ingestion)
- No incoming webhook endpoints configured
- Ollama daemon provides `/api/generate` and `/api/tags` endpoints for inference

---

*Integration audit: 2026-08-30*
