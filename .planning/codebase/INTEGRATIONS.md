# External Integrations

**Analysis Date:** 2026-09-01

## APIs & External Services

**Biomedical Literature & Clinical Registries:**
- **NCBI PubMed** (`backend/app/connectors/pubmed.py` - `PubMedConnector`)
  - Endpoints: E-utilities ESearch (`esearch.fcgi`) & EFetch (`efetch.fcgi`)
  - Ingestion Model: Batch freshness, 180-day backfill window, XML abstracts PII-scrubbed before persistence
  - SDK/Client: `httpx.AsyncClient` with exponential backoff
  - Auth: `NCBI_API_KEY` (optional, for higher rate limit), `NCBI_TOOL`, `NCBI_EMAIL`
- **ClinicalTrials.gov** (`backend/app/connectors/clinical_trials.py` - `ClinicalTrialsConnector`)
  - Endpoints: REST API v2 (`clinicaltrials.gov/api/v2/studies`)
  - Ingestion Model: Near-real-time freshness, paginated cursor (`nextPageToken`), NCT-fingerprinted, 365-day backfill
  - SDK/Client: `httpx.AsyncClient`
  - Auth: Public API (no credentials required)

**Regulatory Portals & Feeds:**
- **OpenFDA** (`backend/app/connectors/fda.py` - `OpenFDAConnector`)
  - Endpoints: Drugs@FDA endpoint (`api.fda.gov/drug/drugsfda.json`), MedWatch & Drug Safety RSS feeds
  - Ingestion Model: Regulatory decision tracking, approval events, label changes
  - SDK/Client: `httpx.AsyncClient`
  - Auth: `OPENFDA_API_KEY` (optional, increases request ceiling)
- **EMA** (`backend/app/connectors/ema.py` - `EMARSSConnector`)
  - Endpoints: European Medicines Agency medicines RSS, human medicines news, orphan designations
  - Ingestion Model: Keyword-filtered XML feeds mapped to development lifecycle events
  - SDK/Client: `httpx.AsyncClient` + `xml.etree.ElementTree`
  - Auth: Public RSS feeds

**News & Industry Media:**
- **NewsAPI** (`backend/app/connectors/newsapi.py` - `NewsAPIConnector`)
  - Endpoints: NewsAPI.org v2 `/everything` endpoint
  - Ingestion Model: Quota-aware governor (monitors `X-RateLimit-Remaining`, pauses when `< 15` calls remain)
  - SDK/Client: `httpx.AsyncClient`
  - Auth: `NEWSAPI_KEY` or `NEWS_API_KEY`
- **BioPharma Dive** (`backend/app/connectors/biopharma_dive.py` - `BioPharmaDiveRSSConnector`)
  - Endpoints: `biopharmadive.com/feeds/news/`
  - Ingestion Model: Haemophilia and gene therapy news ingestion with domain keyword gating
  - SDK/Client: `httpx.AsyncClient` + XML parsing
  - Auth: Public RSS
- **FiercePharma** (`backend/app/connectors/fierce_pharma.py` - `FiercePharmaRSSConnector`)
  - Endpoints: `fiercepharma.com/rss/xml`
  - Ingestion Model: Commercial, regulatory, and pricing news tracking
  - SDK/Client: `httpx.AsyncClient` + XML parsing
  - Auth: Public RSS
- **ET Pharma** (`backend/app/connectors/et_pharma.py` - `ETPharmaRSSConnector`)
  - Endpoints: Economic Times Pharma RSS (`pharma.economictimes.indiatimes.com/rss/topstories`, drug approvals)
  - Ingestion Model: Regional APAC market signals and global biopharma manufacturing developments
  - SDK/Client: `httpx.AsyncClient` + XML parsing
  - Auth: Public RSS

**LLM & AI Reasoning Providers:**
- **Local Gemma 3 4B (llama-cpp-python)** (`backend/app/providers/gemma.py` - `GemmaProvider`)
  - Model: Gemma 3 4B Instruct (`gemma-3-4b-it-Q4_K_M.gguf`) in `models/`
  - Acceleration: Native CUDA 12.4 with GPU layer offloading or AVX2 CPU execution
  - Mode: Primary reasoning engine for intelligence synthesis and Athena chat
  - SDK/Client: `llama-cpp-python`
  - Auth: None (local offline inference)
- **Local Gemma (Ollama Sidecar)** (`backend/app/providers/gemma.py` - `GemmaProvider`)
  - Daemon: Ollama at `OLLAMA_HOST` (default `http://localhost:11434` or Docker service `ollama`)
  - Model: `gemma3:4b`
  - Capabilities: Full NDJSON token streaming via `/api/generate`
  - SDK/Client: `httpx.AsyncClient`
  - Auth: None (local daemon)
- **Hosted xAI Grok API** (`backend/app/providers/grok.py` - `GrokProvider`)
  - Endpoints: `api.x.ai/v1/chat/completions`
  - Model: `grok-beta`
  - Privacy Gate: Hard constraint blocking any payload classified as `CONFIDENTIAL` or `PATIENT_IDENTIFIABLE`. Transmits only `PUBLIC` and `SYNTHETIC` data.
  - SDK/Client: `httpx.AsyncClient` with `Bearer` token
  - Auth: `XAI_API_KEY` or `GROK_API_KEY`
- **Degraded Factual Mode** (`backend/app/providers/degraded.py` - `DegradedProvider`)
  - Approach: Deterministic heuristic summarization when LLMs are offline; explicitly marks reasoning & action items as ungrounded
  - SDK/Client: Built-in Python string algorithms

**Embeddings Engine:**
- **FastEmbed** (`backend/app/services/embeddings.py` - `EmbeddingService`)
  - Model: `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
  - Execution: Local CPU/ONNX runtime; zero cloud dependency
  - Client: `fastembed` Python package

## Data Storage

**Databases:**
- **PostgreSQL 16 + pgvector** (`pgvector/pgvector:pg16`)
  - Connection: `DATABASE_URL=postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`
  - Client: SQLAlchemy 2.0 async engine with `asyncpg` driver
  - Migrations: Alembic (`backend/alembic.ini`, `backend/alembic/versions/` with 14 version files)
  - Tables: Medallion architecture — `raw_signals_bronze`, `evidence`, `developments`, `signals`, `calibration_runs`, `scoring_weights`, `audit_log`, `users`, `sessions`
- **Redis 7** (`redis:7-alpine`)
  - Connection: `REDIS_URL=redis://localhost:6379/0`
  - Client: `redis.asyncio` Python client
  - Role: Rate limiting counters, connector health cache, deduplication buffers, session caching

**File Storage:**
- Local model weights in `models/` directory (GGUF quant files)
- Docker persistent volumes: `pgdata`, `redisdata`, `models_cache`, `ollama_models`
- Runtime logs in `logs/backend.log` and `logs/frontend.log`
- Domain configuration in `config/haemophilia.yaml`

**Caching:**
- Redis for dynamic state caching and rate limiting
- In-memory thread-safe dictionary cache for parsed domain YAML in `backend/app/core/domain_config.py`

## Authentication & Identity

**Auth Provider:**
- Custom enterprise session-based authentication with bcrypt password hashing
- Token Signing: Timestamped cryptographic tokens signed via `itsdangerous.TimestampSigner`
- CSRF Protection: Session-bound HMAC-SHA256 tokens validated on all mutating requests (`POST`, `PUT`, `PATCH`, `DELETE`)
- Demo Mode (`DEMO_MODE=true`): 7 pre-seeded stakeholder personas (Medical Affairs, Regulatory, Commercial, Pipeline Strategy, Drug Safety, Market Access, Clinical Dev)

**Session Policies:**
- Absolute Session Lifetime: 28,800 seconds (8 hours)
- Idle Session Timeout: 3,600 seconds (1 hour)
- Cookie Security: `HttpOnly`, `SameSite="lax"`, dynamic `Secure` enforcement in production

## Monitoring & Observability

**Error Tracking & Health:**
- `GET /api/v1/health` — Application health, database liveness, and model availability
- `GET /api/v1/health/connectors` — Detailed health telemetry and quota remaining per connector
- `GET /api/v1/observability/activity` — Real-time event log and pipeline audit trail
- Docker health checks on all backing containers (`pg_isready`, `redis-cli ping`, Ollama ping)

**Structured Logging:**
- `structlog` with JSON output in production and colored console in development
- Automatic secret and credential scrubbing (`SecretScrubFilter`)
- Correlation ID propagation via `asgi-correlation-id` (`X-Request-ID`, `X-Correlation-ID`)

## CI/CD & Deployment

**CI Pipeline (GitHub Actions):**
- Workflow: `.github/workflows/ci.yml`
- Triggers: Push and PR to `main`, `develop`, and `feature/*` branches
- Execution Matrix:
  1. Backend Pytest: 186 unit/integration tests with `pytest`
  2. Contract Verification: `export_openapi.py` diff check against `frontend/types/api.ts`
  3. Frontend Static Analysis: `tsc --noEmit`
  4. Banned Class Verification: `scripts/check-banned-classes.mjs`
  5. ESLint: `pnpm lint` with Next.js 16 rules
  6. Next.js Production Build: `pnpm build`

**Deployment Orchestration:**
- `docker-compose.yml` orchestrates `postgres`, `redis`, `backend`/`backend-gpu`, `frontend`, and `ollama`
- `setup.py` provides zero-config environment initialization
- `start.py` launches services with port conflict resolution and unified log streaming

## Environment Configuration

**Required Environment Variables:**
- `DATABASE_URL` — PostgreSQL connection URI
- `REDIS_URL` — Redis connection URI
- `LLM_PROVIDER` — Provider selection (`local`, `xai`, `auto`)
- `CORS_ORIGINS` — Allowed CORS origins (e.g. `http://localhost:3000`)
- `SECRET_KEY` — Cryptographic signing key for sessions and CSRF

**Optional Environment Variables:**
- `XAI_API_KEY` / `GROK_API_KEY` — xAI hosted model API key
- `ENABLE_GROK_FALLBACK` — Enable/disable fallback to Grok (`true`/`false`)
- `NEWSAPI_KEY` / `NEWS_API_KEY` — NewsAPI key
- `NCBI_API_KEY` — NCBI E-utilities API key
- `OPENFDA_API_KEY` — OpenFDA API key
- `OLLAMA_HOST` — Ollama daemon URI (default `http://localhost:11434`)
- `LLM_DEVICE` — Device target (`auto`, `cuda`, `cpu`)
- `LLM_GPU_LAYERS` — Number of layers to offload to GPU

## Webhooks & Callbacks

**Incoming:** None (system utilizes polite pull-based polling for external data freshness)
**Outgoing:** None (no unauthenticated webhook dispatches; client communication occurs over REST & SSE)

---

*Integration audit: 2026-09-01*
