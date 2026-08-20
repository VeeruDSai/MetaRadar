# External Integrations

**Analysis Date:** 2026-08-20

## APIs & External Services

**Data Source Connectors (Phase 1 ingestion):**
All five connectors extend `SourceConnector` in `backend/app/connectors/base.py` (bounded retry with exponential backoff + jitter via `_fetch_with_retry`, per-profile incremental state in the `connector_state` table, dedupe + PII scrub before bronze persistence). They are registered in `backend/app/connectors/__init__.py` (`ALL_CONNECTORS`). Query profiles come from `config/haemophilia.yaml`.

- **NCBI PubMed E-utilities** - Scientific publications
  - Endpoints: `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi` + `efetch.fcgi` (`backend/app/connectors/pubmed.py`)
  - Auth: none (quota-free); polite 0.35s delay between efetch batches
  - SDK/Client: httpx
  - Config: `queries` per profile in `config/haemophilia.yaml` (e.g. `haemophilia_clinical`)
- **ClinicalTrials.gov API v2** - Clinical trial updates
  - Endpoint: `https://clinicaltrials.gov/api/v2/studies` (`backend/app/connectors/clinical_trials.py`)
  - Auth: none; pagination via `nextPageToken`; NCT-fingerprinted
  - Config: `conditions`, `interventions`, `sponsor_keywords` per profile
- **NewsAPI** - Market news
  - Endpoint: `https://newsapi.org/v2/everything` (`backend/app/connectors/newsapi.py`)
  - Auth: API key via `X-Api-Key` header — env var `NEWSAPI_KEY`
  - Quota: ~100 req/day dev cap tracked from `X-RateLimit-Remaining` header, persisted to `ConnectorState.cursor` as JSON `{"quota_remaining": N, "quota_window_date": "YYYY-MM-DD"}`; connector returns DEGRADED when quota exhausted (D-20)
- **OpenFDA** - Regulatory approvals
  - Endpoint: `https://api.fda.gov/drug/drugsfda.json` (`backend/app/connectors/fda.py`)
  - Auth: none (public endpoint); application numbers carried as canonical `reg:` fingerprint
  - Config: `search_terms` per profile (`openfda.substance_name:{term}` search)
- **EMA RSS feed** - EU regulatory decisions
  - Endpoint: `https://www.ema.europa.eu/en/medicines/rss` (override via `rss_url`) (`backend/app/connectors/ema.py`)
  - Auth: none; stdlib `xml.etree` parsing; keyword-filtered items persisted with verbatim XML fragment

**LLM Providers (fallback chain: Local Gemma → Grok → BART degraded):**
- **Ollama sidecar (local)** - primary reasoning provider, serves `gemma3:4b`
  - Endpoints: `POST {OLLAMA_HOST}/api/generate`, `GET {OLLAMA_HOST}/api/tags` (`backend/app/providers/gemma.py`)
  - Env: `OLLAMA_HOST` (default `http://localhost:11434`), `OLLAMA_MODEL` (default `gemma3:4b`), `MAX_CONTEXT_TOKENS` (2048), `MAX_OUTPUT_TOKENS` (512)
  - Containerized in `docker-compose.yml` (`ollama` service, GPU-reserved); model pulled via `setup.py` (`ollama pull gemma3:4b`)
  - Failure raises `OllamaUnavailableError` → factory falls through (`backend/app/providers/factory.py`)
- **xAI Grok (hosted fallback)** - model `grok-beta`
  - Endpoint: `POST https://api.x.ai/v1/chat/completions` (`backend/app/providers/grok.py`)
  - Auth: `Authorization: Bearer {XAI_API_KEY}` — env var `XAI_API_KEY`
  - Gate: only used when `ENABLE_GROK_FALLBACK=true`; strict privacy gate `validate_privacy_gate` blocks any payload not classified PUBLIC/SYNTHETIC (`backend/app/providers/grok.py` lines 56-70)
  - Missing key raises `GrokUnavailableError` → falls to BART degraded (CI stays green without a key, D-16)
- **BART degraded mode** - last-resort factual summarizer (`facebook/bart-large-cnn` label, no real model call) (`backend/app/providers/degraded.py`)
  - Summarize-only capability; explicit `degraded_factual` mode metadata

**Embedding Model:**
- fastembed downloads `sentence-transformers/all-MiniLM-L6-v2` (384-dim) from HuggingFace, revision pinned `e4bb823e5956b6277b069d276b978c48a73507c7` (`backend/app/core/config.py`, `backend/app/services/embeddings.py`); CPU/ONNX, lazy-loaded singleton, offloaded to executor

## Data Storage

**Databases:**
- PostgreSQL 16 with pgvector extension — primary store
  - Image: `pgvector/pgvector:pg16` (`docker-compose.yml`); local default via Docker Compose
  - Connection: `DATABASE_URL` env (e.g. `postgresql+asyncpg://...`); also hardcoded default in `backend/app/core/config.py` and `backend/alembic.ini`
  - Client: SQLAlchemy 2.0 async + asyncpg (`backend/app/db/session.py`); pool size 10, max overflow 20
  - Migrations: Alembic (`backend/alembic/versions/001_initial_v51_schema.py`, `002_phase1_connector_state_and_cross_source.py`, `003_contradictions_scoring.py`)
  - Vector search: HNSW index `signals_embedding_hnsw`, adjustable `hnsw.ef_search` via `set_config` (`backend/app/services/vector_query.py`)
  - Tables: `pipeline_runs`, `sources`, `companies`, `assets`, `trials`, `developments`, `events`, `lifecycle_events`, `confluences`, `raw_signals_bronze`, `connector_state`, `evidence`, `signals` (incl. pgvector `embedding` column), `contradictions`, `calibration_history`, `scoring_weights`, `signal_routing`, `calibration_feedback`, `watch_items`, `audit_log` (`backend/app/models/__init__.py`)

**File Storage:**
- Local filesystem only: `logs/` (runtime logs via `start.py`), Docker volumes `pgdata`, `redisdata`, `models_cache` (mounted at `/app/models` for embeddings), `ollama_models`

**Caching:**
- Redis 7 (`redis:7-alpine` container, port 6379)
  - Connection: `REDIS_URL` env
  - Usage: `POST /api/v1/cache/clear` flushes keys (`backend/app/api/v1/endpoints/cache.py`); `GET /api/v1/health/ready` pings non-blocking (`backend/app/api/v1/endpoints/health.py`)
  - No application-level cache orchestration beyond this; no Celery/background queue (pipeline runs in-process via LangGraph)

## Authentication & Identity

**Auth Provider:**
- None. No OAuth, JWT, API-key middleware, or user identity system in `backend/app/api/` — only FastAPI `Depends(get_db)` for DB sessions
- API is open; CORS restricted to `CORS_ORIGINS` (default `http://localhost:3000`) via `CORSMiddleware` (`backend/app/main.py`)
- Data classification exists only as an internal privacy gate for the Grok fallback (`DataClassification` in `backend/app/providers/base.py`), not as access control

## Monitoring & Observability

**Error Tracking:**
- None external; stdlib `logging` throughout backend

**Logs:**
- Console via `logging.basicConfig` (`backend/app/main.py`)
- File logs: `logs/backend.log`, `logs/frontend.log` written by `start.py`; `start.py` also polls health endpoints and prints telemetry every ~9s

**Health endpoints** (`backend/app/api/v1/endpoints/health.py`):
- `GET /api/v1/health` — liveness
- `GET /api/v1/health/ready` — DB (mandatory) + Redis (non-blocking)
- `GET /api/v1/health/models` — Ollama availability (real HTTP probe to `/api/tags`), Grok configured/fallback enabled, embedding model info
- `GET /api/v1/health/connectors` — per-connector status incl. quota, last success/error from `connector_state` (D-22 honest health)

## CI/CD & Deployment

**Hosting:**
- Docker Compose stack (`docker-compose.yml`): `postgres`, `redis`, `backend` (:8000), `backend-gpu` (profile `gpu`, `LLM_DEVICE=cuda:0`), `frontend` (:3000), `ollama` (:11434, NVIDIA GPU reservation)
- Host launcher alternative: `python start.py` (uvicorn + next dev, port cleanup, graceful shutdown)

**CI Pipeline:**
- GitHub Actions `.github/workflows/ci.yml` — triggers on push to `main`/`develop`/`feature/*` and PRs
  - Backend: pip install + `pytest -v` (Python 3.11)
  - Contract sync: `python scripts/export_openapi.py` then `git diff --exit-code frontend/types/api.ts` (OpenAPI → TypeScript contract drift fails CI)
  - Frontend: pnpm 9 + Node 22, `tsc --noEmit`, `pnpm lint`, `pnpm build`

## Environment Configuration

**Required env vars** (see `.env.example`):
- `DATABASE_URL` — PostgreSQL asyncpg connection
- `REDIS_URL` — Redis connection
- `LLM_PROVIDER` — `local` | `xai` | `auto`
- `OLLAMA_HOST` — Ollama sidecar base URL (default `http://localhost:11434`)
- `CORS_ORIGINS` — comma-separated allowed origins

**Optional env vars:**
- `NEWSAPI_KEY` — required only for NewsAPI connector (degrades to DEGRADED status when unset)
- `XAI_API_KEY`, `ENABLE_GROK_FALLBACK` — required only for Grok hosted fallback
- `EMBEDDING_MODEL`, `EMBEDDING_MODEL_REVISION`, `EMBEDDING_DIMENSION`, `EMBEDDING_MAX_SEQ_LENGTH` — embedding model identity
- `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS` — local LLM tuning
- `RAW_SIGNAL_RETENTION_DAYS` — bronze retention window

**Secrets location:**
- `.env` at repo root (NOT committed; loaded by pydantic-settings from `backend/app/core/config.py`); template committed at `.env.example`
- `docker-compose.yml` uses inline local dev credentials for Postgres (dev-only defaults)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None (no webhook emissions; all external calls are synchronous HTTP fetches from connectors/providers)

---

*Integration audit: 2026-08-20*