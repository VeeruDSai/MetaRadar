# External Integrations

**Analysis Date:** 2026-08-28

## APIs & External Services

### Biomedical Literature & Registries
- **NCBI PubMed / Entrez API:**
  - Client / Module: `backend/app/connectors/pubmed.py`
  - Purpose: Fetches peer-reviewed medical publications, abstracts, and clinical trial outcomes in haemophilia.
  - Auth / Identifiers: `NCBI_API_KEY`, `NCBI_TOOL` ("MetaRadar"), `NCBI_EMAIL` ("metaradar@example.com")
  - Rate Limits: 10 req/sec with key, 3 req/sec unauthenticated

- **ClinicalTrials.gov REST API v2:**
  - Client / Module: `backend/app/connectors/clinical_trials.py`
  - Purpose: Tracks Phase 1–4 clinical trial statuses, primary endpoints, enrollment changes, and trial completions.
  - Auth: Open public API (No key required)
  - Endpoint: `https://clinicaltrials.gov/api/v2/studies`

### Regulatory Agencies
- **OpenFDA Drug API:**
  - Client / Module: `backend/app/connectors/fda.py`
  - Purpose: Retrieves FDA drug approvals, label changes, black-box warnings, and regulatory notices.
  - Auth: `OPENFDA_API_KEY` (optional for higher rate quotas)
  - Endpoint: `https://api.fda.gov/drug/`

- **European Medicines Agency (EMA) Feeds:**
  - Client / Module: `backend/app/connectors/ema.py`
  - Purpose: Parses CHMP positive opinions, marketing authorizations, and European public assessment reports (EPAR).
  - Auth: Public RSS/Atom XML feeds

### Competitive & Industry Media
- **NewsAPI:**
  - Client / Module: `backend/app/connectors/newsapi.py`
  - Purpose: Ingests global pharmaceutical press and industry news.
  - Auth: `NEWSAPI_KEY` (or `NEWS_API_KEY`)

- **Specialized Industry Scrapers & RSS:**
  - `backend/app/connectors/biopharma_dive.py` (BioPharma Dive headlines & articles)
  - `backend/app/connectors/et_pharma.py` (ET HealthWorld / Pharma)
  - `backend/app/connectors/fierce_pharma.py` (FiercePharma industry updates)

### Reasoning & LLM Inference
- **Local Gemma Inference:**
  - Client / Module: `backend/app/providers/gemma.py`, `backend/app/providers/factory.py`
  - Engine: `llama-cpp-python` (direct CUDA/CPU GGUF) or Ollama HTTP REST API (`http://localhost:11434/api/generate`)
  - Default Model: `google/gemma-3-4b-it` / `gemma3:4b`
  - Zero external API egress; ensures complete data privacy for internal competitive intelligence.

- **Hosted xAI Grok API:**
  - Client / Module: `backend/app/providers/grok.py`
  - Purpose: Cloud-hosted fallback reasoning engine when local GPU is unavailable or Grok fallback is enabled.
  - Auth: `XAI_API_KEY` or `GROK_API_KEY`
  - Privacy Gate: Enforces PII/PHI scrubbing before payload transmission.

- **Factual Summarizer Fallback:**
  - Client / Module: `backend/app/providers/degraded.py`
  - Purpose: Deterministic extractive synthesis if both local LLM and cloud APIs are unreachable.

## Data Storage

**Databases:**
- PostgreSQL 16 with `pgvector` Extension:
  - Connection: `DATABASE_URL` (e.g., `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`)
  - Client: SQLAlchemy 2.0 Async Engine (`backend/app/db/session.py`)
  - Schema Management: Alembic (`backend/alembic/`)
  - Vector Embeddings: 384-dimensional dense vectors stored in `signals.embedding` via `pgvector.sqlalchemy.Vector`

**Caching & Fast Key-Value Storage:**
- Redis 7 (Alpine):
  - Connection: `REDIS_URL` (e.g., `redis://localhost:6379/0`)
  - Client: `redis.asyncio` (`backend/app/core/config.py`, `backend/app/api/v1/endpoints/cache.py`)
  - Purpose: Endpoint response caching, rate limiting counters, and background lock orchestration.

**File Storage:**
- Local filesystem for GGUF model binaries in `models/` (`models/gemma-3-4b-it-Q4_K_M.gguf`) and file logging in `logs/` (`logs/backend.log`, `logs/frontend.log`).

## Authentication & Identity

**Auth Provider:**
- Custom Secure Session-based Authentication (`backend/app/models/auth.py`, `backend/app/services/auth_service.py`):
  - Tokens: Cryptographically random 64-character session tokens hashed with SHA-256 in PostgreSQL
  - Security: HttpOnly, SameSite cookies with idle timeout (1 hr) and absolute session lifetime (8 hrs)
  - RBAC: 6 Persona roles (`Executive`, `CI Lead`, `Regulatory Lead`, `Medical Affairs`, `Commercial Lead`, `Admin`)
  - Demo Mode: Fast persona-switching enabled via `/api/v1/auth/demo-login` (`frontend/components/auth/PersonaSwitcher.tsx`)

## Monitoring & Observability

**Error Tracking & Diagnostics:**
- Health & Diagnostics Endpoint: `/api/v1/health` (`backend/app/api/v1/endpoints/health.py`)
- Source Health Telemetry: `/api/v1/observability/sources` (`backend/app/models/__init__.py:SourceHealthLog`)
- Activity Stream: Real-time event log for ingestion, pipeline runs, and review state changes (`backend/app/api/v1/endpoints/observability.py`)

**Logs:**
- Structured JSON logging with `structlog` (`backend/app/core/logging.py`)
- Correlation IDs propagated via `asgi-correlation-id` and `CorrelationIdMiddleware` (`backend/app/core/middleware.py`)

**Audit Trail:**
- Tamper-proof, append-only `audit_log` table (`backend/app/models/__init__.py`) with SQLAlchemy event listeners preventing any row updates or deletions.

## CI/CD & Deployment

**Hosting & Containers:**
- Multi-container architecture via `docker-compose.yml`:
  - `metaradar-postgres` (PostgreSQL 16 + pgvector)
  - `metaradar-redis` (Redis 7)
  - `metaradar-backend` (FastAPI CPU profile)
  - `metaradar-backend-gpu` (FastAPI CUDA GPU profile)
  - `metaradar-frontend` (Next.js 16)
  - `metaradar-ollama` (Ollama local inference sidecar)

## Environment Configuration

**Required env vars:**
- `DATABASE_URL`: PostgreSQL connection string with `asyncpg` driver
- `REDIS_URL`: Redis server URL
- `SECRET_KEY`: Secret string for cryptographic signing and session hashing
- `CORS_ORIGINS`: Comma-separated list of allowed frontend origins (e.g., `http://localhost:3000`)

**Optional external API credentials:**
- `XAI_API_KEY` / `GROK_API_KEY`: xAI Grok API key
- `NEWSAPI_KEY`: NewsAPI key
- `NCBI_API_KEY`: PubMed NCBI key
- `OPENFDA_API_KEY`: OpenFDA API key

**Secrets location:**
- Stored exclusively in `.env` (gitignored, never committed). See `.env.example` for reference keys.

---

*Integration audit: 2026-08-28*
