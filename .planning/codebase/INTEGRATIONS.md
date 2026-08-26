# External Integrations

**Analysis Date:** 2026-08-27

## APIs & External Services

**Tier 1: Authoritative Public Biomedical Registries:**
- **ClinicalTrials.gov API v2:**
  - Purpose: Tracks clinical study protocols, recruitment status, interventions, and milestone updates
  - Client: `backend/app/connectors/clinical_trials.py` (`httpx.AsyncClient`)
  - Auth: None (public REST endpoint `https://clinicaltrials.gov/api/v2/studies`)
  - Canonical URL: `https://clinicaltrials.gov/study/{NCTId}`
- **NCBI PubMed E-Utilities:**
  - Purpose: Ingests peer-reviewed biomedical literature abstracts and MeSH indexed terms
  - Client: `backend/app/connectors/pubmed.py` (`httpx.AsyncClient`)
  - Auth: `NCBI_API_KEY` (optional, enhances rate limit from 3 to 10 req/s), `NCBI_TOOL`, `NCBI_EMAIL`
  - Canonical URL: `https://pubmed.ncbi.nlm.nih.gov/{PMID}/`
- **openFDA & FDA MedWatch:**
  - Purpose: Queries FDA drug approvals, labeling, BLA filings, and safety alerts
  - Client: `backend/app/connectors/fda.py` (`httpx.AsyncClient`)
  - Auth: `OPENFDA_API_KEY` (optional)
  - Canonical URL: Record-specific Drugs@FDA link
- **European Medicines Agency (EMA) Medicines RSS:**
  - Purpose: Ingests CHMP scientific opinions, EPAR product summaries, and orphan drug designations
  - Client: `backend/app/connectors/ema.py` (RSS XML parser with `xml.etree.ElementTree`)
  - Auth: None (public XML feed)
  - Canonical URL: Product-specific EPAR page (e.g. `https://www.ema.europa.eu/en/medicines/human/EPAR/{slug}`)

**Tier 3: Discovery & News Feeds:**
- **NewsAPI:**
  - Purpose: Monitors commercial trade press, industry coverage, and general biomedical news
  - Client: `backend/app/connectors/newsapi.py` (`httpx.AsyncClient`)
  - Auth: `NEWSAPI_KEY` or `NEWS_API_KEY` (100 req/day developer quota tracking)
  - Canonical URL: Direct article URL (`article.url`), blocking generic registration/landing pages
- **Fierce Pharma RSS:**
  - Purpose: Continuous monitoring of biopharma corporate developments, M&A, regulatory submissions, and commercial strategy
  - Client: `backend/app/connectors/fierce_pharma.py` (RSS XML parser)
  - Auth: None (public RSS feed `https://www.fiercepharma.com/rss/xml`)
  - Canonical URL: Direct article link
- **The Economic Times (ET) Pharma RSS:**
  - Purpose: Global and regional pharmaceutical top stories and drug approval alerts
  - Client: `backend/app/connectors/et_pharma.py` (RSS XML parser)
  - Auth: None (public RSS feeds `.../rss/topstories` & `.../rss/drug_approvals`)
  - Canonical URL: Direct article link
- **BioPharma Dive:**
  - Purpose: Biopharma business intelligence monitoring
  - Client: Registered in source catalog with `status: configured_no_feed` for honest administrative visibility

**LLM & Reasoning Providers:**
- **Local Gemma (Ollama):**
  - Purpose: Offline private LLM inference for signal synthesis, action recommendation, and Athena clinical Q&A
  - Client: `backend/app/providers/gemma.py` via `OLLAMA_HOST` (`http://localhost:11434`) and model `gemma3:4b`
- **Grok (xAI):**
  - Purpose: Optional high-capability cloud reasoning fallback
  - Client: `backend/app/providers/grok.py`
  - Auth: `XAI_API_KEY` / `GROK_API_KEY` (strictly gated behind `backend/app/services/pii.py` PII/PHI scrubber)
- **Degraded Factual Mode:**
  - Purpose: Guaranteed deterministic extraction when external LLMs are unavailable (`backend/app/providers/degraded.py`)

## Data Storage

**Databases:**
- **PostgreSQL 16 + pgvector:**
  - Connection: `DATABASE_URL` (`postgresql+asyncpg://...`)
  - Client: SQLAlchemy 2.0 Async (`backend/app/db/session.py`)
  - Tables: `signals`, `raw_signals_bronze`, `evidence`, `developments`, `events`, `lifecycle_events`, `confluences`, `contradictions`, `calibration_feedback`, `scoring_weights`, `watch_items`, `audit_log`, `sources`, `source_health_logs`, `pipeline_runs`
  - Vectors: `384-dimensional` vector column on `signals.embedding` indexed via HNSW cosine distance

**File Storage:**
- Local filesystem only (`data/`, `models/`, `logs/`, `.planning/`)

**Caching & Locking:**
- **PostgreSQL Advisory Locks:** `try_advisory_lock` in `backend/app/services/scheduler.py` to prevent overlapping background runs
- **Redis 7 (Optional):** Configured via `REDIS_URL` for distributed cache invalidation

## Authentication & Identity

**Auth Provider:**
- **Demo Operator Persona System:** Client-side non-auth role switcher (`frontend/components/common/DemoOperatorSelector.tsx`) stored in `sessionStorage`
- Supported Roles: `Medical Affairs`, `Regulatory`, `Safety`, `Market Access`, `Communications`, `Leadership`
- **Optional API Key:** `METARADAR_API_KEY` header for backend API endpoints

## Monitoring & Observability

**Error Tracking & Correlation:**
- Middleware: `asgi-correlation-id` (`CorrelationIdMiddleware` in `backend/app/core/middleware.py`)
- Propagation: `X-Correlation-ID` header returned with all HTTP responses and injected into structured logs

**Logs:**
- Framework: `structlog` (`backend/app/core/logging.py`) with JSON output formatting and automated PII/PHI redaction (`backend/app/core/redact.py`)

**Health & Diagnostics:**
- Endpoints:
  - `GET /api/v1/health/live` - Basic service liveness
  - `GET /api/v1/health/ready` - Readiness check (DB, Redis, models, connectors)
  - `GET /api/v1/health/models` - Ollama Gemma 3 & Grok status telemetry
  - `GET /api/v1/health/sources` - Real-time connector latency, status, and error breakdown

## CI/CD & Deployment

**Hosting:**
- Containerized Docker deployment (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`)

**CI Pipeline:**
- GitHub Actions (`.github/workflows/ci.yml`):
  - Job 1: Pytest backend verification with coverage gates
  - Job 2: OpenAPI & TypeScript contract synchronization check (`scripts/export_openapi.py`)
  - Job 3: Frontend banned Tailwind classes gate (`scripts/check-banned-classes.mjs`)
  - Job 4: Next.js 16 build (`npm run build`) & ESLint (`npm run lint`)

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` (e.g. `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`)
- `REDIS_URL` (e.g. `redis://localhost:6379/0`)
- `LLM_PROVIDER` (`local` | `xai` | `auto`)

**Optional / Provider env vars:**
- `NEWSAPI_KEY` (required for NewsAPI live sync)
- `XAI_API_KEY` (required when `ENABLE_GROK_FALLBACK=true`)
- `NCBI_API_KEY` (optional PubMed speedup)
- `OPENFDA_API_KEY` (optional openFDA speedup)
- `OLLAMA_HOST` (defaults to `http://localhost:11434`)

**Secrets location:**
- Stored exclusively in local `.env` (never committed to git)

## Webhooks & Callbacks

**Incoming:**
- None (pull/polling and background scheduled sync model)

**Outgoing:**
- Server-Sent Events (SSE) stream on `POST /api/v1/athena` for real-time token streaming to the frontend

---

*Integration audit: 2026-08-27*
