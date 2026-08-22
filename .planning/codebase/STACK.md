---
doc_type: codebase-map
focus: tech
analysis_date: 2026-08-22
---

# Technology Stack

**Analysis Date:** 2026-08-22

MetaRadar v5.1.0 — Continuously operating competitive intelligence radar for Haemophilia (Novo Nordisk GBS Hackathon 2026). Two-service application: FastAPI backend + Next.js frontend, backed by PostgreSQL 16 (pgvector), Redis 7, and an autonomous background scheduler.

## Languages & Runtimes

| Layer | Language | Runtime / Version |
|---|---|---|
| Backend | Python 3.11+ | asyncio throughout (`asyncpg`, async SQLAlchemy, background tasks) |
| Frontend | TypeScript 5.7.3 | Node.js >=20.9.0, Next.js 16.3.0 (Turbopack) |
| Orchestration scripts | Python 3 (`start.py`, `setup.py`, `export_openapi.py`) | stdlib + urllib |
| Tooling script | JavaScript ESM (`scripts/check-banned-classes.mjs`) | Node |

## Core Frameworks

### Backend (`backend/`)
| Concern | Library | Pinned in `backend/requirements.txt` |
|---|---|---|
| Web framework | FastAPI | >=0.110.0 |
| ASGI server | Uvicorn | >=0.28.0 |
| Background scheduler | Native asyncio + PostgreSQL advisory locks (`app/services/scheduler.py`) | stdlib / asyncpg |
| Validation/settings | Pydantic v2 + pydantic-settings | >=2.6.0 / >=2.2.0 |
| ORM | SQLAlchemy 2.x (async) | >=2.0.28 |
| Postgres driver | asyncpg | >=0.29.0 |
| Migrations | Alembic (6 revisions in `backend/alembic/versions/`) | >=1.13.1 |
| Vectors | pgvector (`pgvector.sqlalchemy.Vector`) | >=0.2.5 |
| Cache | redis-py | >=5.0.3 |
| Workflow engine | LangGraph StateGraph (11-node linear pipeline) | >=0.2.0 |
| Embeddings | fastembed (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim) | >=0.4.0 |
| HTTP client | httpx | >=0.27.0 |
| Logging | structlog + asgi-correlation-id | >=24.1.0 / >=4.3.0 |
| Config files | PyYAML (`config/haemophilia.yaml` domain config) | >=6.0.1 |

Test dependencies: pytest, pytest-asyncio (auto mode), pytest-cov, pytest-httpx.

### Frontend (`frontend/`)
| Concern | Library |
|---|---|
| Framework | Next.js **16.3.0** (App Router, Turbopack build) |
| UI runtime | React 19 + react-dom 19 |
| Styling | Tailwind CSS v4 (`@tailwindcss/postcss` 4.3.3) + tw-animate-css |
| Components | shadcn 4.8.0 + `@base-ui/react` 1.5.0, class-variance-authority, clsx, tailwind-merge |
| Charts | recharts 3.10.1 |
| Animation | framer-motion 13.1.0 |
| Icons | lucide-react 1.16.0 |
| Lint | ESLint 10 + eslint-config-next 16.3.0 |
| Package manager | pnpm 9.15.5 (canonical `pnpm-lock.yaml`) |

## AI / Model Allocation (canonical — Master Plan §13.8)

Provider chain implemented in `backend/app/providers/factory.py`:
1. **Local Gemma 3 4B Instruct** (`google/gemma-3-4b-it`, Q4/int4, GPU-first via Ollama sidecar `gemma3:4b` at `OLLAMA_HOST`) — reasoning, Four-Question briefs, Ask Athena.
2. **xAI Grok hosted fallback** (`ENABLE_GROK_FALLBACK=false` by default; privacy-gated by `DataClassification`).
3. **Degraded BART factual summary** (`DegradedProvider`, summarize-only; no reasoning/actions).

Supporting models: embeddings `all-MiniLM-L6-v2` rev `e4bb823e...` (384-dim), deterministic entity extraction via domain config, NLI heuristics in `app/services/redteam.py`.

## Infrastructure & Configuration

- **Docker Compose** (`docker-compose.yml`): 5 services — postgres (`pgvector/pgvector:pg16`), redis (`redis:7-alpine`), backend (CPU profile), backend-gpu (`gpu` profile, CUDA), frontend, ollama (GPU device reservation). Healthchecks on all core services.
- **Local orchestration**: `setup.py` (deps, docker, migrations, seed, model pull) → `start.py` (process launcher with telemetry, graceful shutdown, auto-applies Alembic migrations).
- Ports: frontend 3000, backend 8000, postgres 5432, redis 6379, ollama 11434.

### Configuration (`backend/app/core/config.py`)
- **Scheduler**: `ENABLE_BACKGROUND_SCHEDULER` (default `True`), `SCHEDULER_CT_INTERVAL_MINUTES` (60), `SCHEDULER_PUBMED_INTERVAL_MINUTES` (60), `SCHEDULER_EMA_INTERVAL_MINUTES` (30), `SCHEDULER_FDA_INTERVAL_MINUTES` (30), `SCHEDULER_NEWS_INTERVAL_MINUTES` (15), `SCHEDULER_JITTER_PERCENT` (10), `SCHEDULER_MAX_BACKOFF_MINUTES` (240).
- **Connector API Keys & Tools**: `NCBI_API_KEY`, `NCBI_TOOL`, `NCBI_EMAIL`, `OPENFDA_API_KEY`, `NEWSAPI_KEY`.
- **Database & Cache**: `DATABASE_URL`, `REDIS_URL`.
- **LLM & Embeddings**: `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `OLLAMA_HOST`, `XAI_API_KEY`, `ENABLE_GROK_FALLBACK`, `EMBEDDING_MODEL`.
- **Domain Config**: `config/haemophilia.yaml` loaded by `backend/app/core/domain_config.py`.

## Build & Verification Commands

| Gate | Command |
|---|---|
| Frontend lint | `npm --prefix frontend run lint` (ESLint 10, zero-warning policy) |
| Frontend build/TSC | `npm --prefix frontend run build` (Next 16 Turbopack; strict TS) |
| Banned-class gate | `node scripts/check-banned-classes.mjs` (0 banned Tailwind slate/arbitrary-hex violations) |
| Backend tests | `pytest tests/ -v -k "not test_database_connection"` (114 tests passing) |
| Contract sync | `python scripts/export_openapi.py` → regenerates `contracts/openapi.json` and canonical `frontend/types/api.ts` |
