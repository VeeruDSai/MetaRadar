# External Integrations

**Analysis Date:** 2026-08-24

## APIs & External Services

**Data Connectors (polling ingestion, `backend/app/connectors/`):**

All connectors extend the shared async base with retry/backoff, dedup, and state tracking in `backend/app/connectors/base.py` (`ConnectorFetchError`, `RawSignalPayload`, `ConnectorStatus`).

- ClinicalTrials.gov API v2 - clinical study signals
  - Client: `backend/app/connectors/clinical_trials.py` (`BASE_URL = https://clinicaltrials.gov/api/v2/studies`)
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
  - Auth: **required** `NEWSAPI_KEY` / `NEWS_API_KEY` sent as `X-Api-Key` header; missing key yields `CONFIGURATION_ERROR` surfaced via `configuration_error_for()` in `backend/app/core/config.py`. Path-independent multi-env loader ensures key is detected across root, backend, and subdirectories.

**Reasoning & Inference Providers (`backend/app/providers/`):**

Execution chain: Local GGUF (`models/`) / Ollama sidecar → xAI Grok (privacy-gated) → Degraded BART factual summary.

- Local GGUF Engine (`backend/app/providers/gemma.py`)
  - Auto-discovers any `.gguf` reasoning model in the root `models/` directory (e.g. `models/gemma-3-4b-it-Q4_K_M.gguf`, 2.48 GB).
  - Executes hardware-optimized local inference via `llama-cpp-python` (`n_gpu_layers=-1`, `n_threads=os.cpu_count()`, `n_ctx=2048`, `n_batch=512`).
  - Formats turns with official Gemma template markers and robustly extracts JSON (with markdown code fence handling).
- Ollama Sidecar (local Gemma 3 4B)
  - Connects over HTTP to `http://localhost:11434` (`gemma3:4b`) if no GGUF file is found.
- xAI Grok API (hosted fallback)
  - Client: `backend/app/providers/grok.py` — `POST https://api.x.ai/v1/chat/completions`, model `grok-beta`.
  - Auth: `XAI_API_KEY` / `GROK_API_KEY` bearer token with 60s timeout; gated by `ENABLE_GROK_FALLBACK=true` AND mandatory privacy gate `validate_privacy_gate()` (only PUBLIC/SYNTHETIC-classified payloads permitted).
- BART Degraded Mode (`backend/app/providers/degraded.py`)
  - Deterministic source-grounded factual bulleted summary citing verified evidence; zero hallucinations.

**Embeddings:**
- fastembed (ONNX, CPU) in-process — model `sentence-transformers/all-MiniLM-L6-v2`, 384-dim, loaded lazily in `backend/app/services/embeddings.py`.

## Data Storage

**Databases:**
- PostgreSQL 16 with pgvector extension (`pgvector/pgvector:pg16`)
  - Connection: `DATABASE_URL` (default `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`)
  - Client: SQLAlchemy 2.x async engine + session factory in `backend/app/db/session.py` with PostgreSQL advisory locks.
  - Migrations: Alembic, 11 versions in `backend/alembic/versions/`.
  - Vector search: pgvector `Vector(384)` with HNSW cosine distance index.

**Caching:**
- Redis 7-alpine (`REDIS_URL` default `redis://localhost:6379/0`)
  - Client: `redis.asyncio` for query caching, health checks, and fast flush.

## CI/CD & Verification

**CI Pipeline (`.github/workflows/ci.yml`):**
- Pytest suite (119 test cases)
- Contract sync check (`python scripts/export_openapi.py` with git diff gate on `frontend/types/api.ts`)
- Frontend typecheck (`tsc --noEmit`)
- Banned-classes architectural gate (`node scripts/check-banned-classes.mjs`)
- ESLint 10 & Next.js 16 production build

---

*Integration audit: 2026-08-24*
