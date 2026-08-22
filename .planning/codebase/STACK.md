---
doc_type: codebase-map
focus: tech
analysis_date: 2026-08-22
---

# Technology Stack

**Analysis Date:** 2026-08-22

MetaRadar v5.1.0 — AI-powered competitive-intelligence radar for Haemophilia (Novo Nordisk GBS Hackathon 2026). Two-service application: FastAPI backend + Next.js frontend, backed by PostgreSQL 16 (pgvector) and Redis 7.

## Languages & Runtimes

| Layer | Language | Runtime / Version |
|---|---|---|
| Backend | Python 3.11+ | asyncio throughout (`asyncpg`, async SQLAlchemy) |
| Frontend | TypeScript 5.7.3 | Node.js >=20.9.0, Next.js 16.3.0 (Turbopack) |
| Orchestration scripts | Python 3 (`start.py`, `setup.py`) | stdlib + urllib |
| Tooling script | JavaScript ESM (`scripts/check-banned-classes.mjs`) | Node |

## Core Frameworks

### Backend (`backend/`)
| Concern | Library | Pinned in `backend/requirements.txt` |
|---|---|---|
| Web framework | FastAPI | >=0.110.0 |
| ASGI server | Uvicorn | >=0.28.0 |
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

Test deps live in the same requirements.txt: pytest, pytest-asyncio (auto mode), pytest-cov, pytest-httpx.

### Frontend (`frontend/`)
| Concern | Library |
|---|---|
| Framework | Next.js **16.3.0** (App Router, Turbopack build) — note README still says "Next.js 15" |
| UI runtime | React 19 + react-dom 19 |
| Styling | Tailwind CSS v4 (`@tailwindcss/postcss` 4.3.3) + tw-animate-css |
| Components | shadcn 4.8.0 + `@base-ui/react` 1.5.0, class-variance-authority, clsx, tailwind-merge |
| Charts | recharts 3.10.1 |
| Animation | framer-motion 13.1.0 |
| Icons | lucide-react 1.16.0 |
| Lint | ESLint 10 + eslint-config-next 16.3.0 |
| Package manager | pnpm 9.15.5 (`packageManager` field) |

## AI / Model Allocation (canonical — Master Plan §13.8)

Provider chain implemented in `backend/app/providers/factory.py`:
1. **Local Gemma 3 4B Instruct** (`google/gemma-3-4b-it`, Q4/int4, GPU-first via Ollama sidecar `gemma3:4b` at `OLLAMA_HOST`) — reasoning, Four-Question briefs, Ask Athena.
2. **xAI Grok hosted fallback** (`ENABLE_GROK_FALLBACK=false` by default; privacy-gated by `DataClassification`).
3. **Degraded BART factual summary** (`DegradedProvider`, summarize-only; no reasoning/actions).

Supporting models: embeddings `all-MiniLM-L6-v2` rev `e4bb823e...` (384-dim), spaCy-style NER via domain config, NLI heuristics in `app/services/redteam.py`.

## Infrastructure

- **Docker Compose** (`docker-compose.yml`): 5 services — postgres (`pgvector/pgvector:pg16`), redis (`redis:7-alpine`), backend (CPU profile), backend-gpu (`gpu` profile, CUDA), frontend, ollama (GPU device reservation). Healthchecks on all core services.
- **Local orchestration**: `setup.py` (deps, docker, migrations, seed, model pull) → `start.py` (process launcher with telemetry, graceful shutdown, auto-applies Alembic migrations).
- Ports: frontend 3000, backend 8000, postgres 5432, redis 6379, ollama 11434.

## Configuration

- `backend/app/core/config.py` — single `Settings(BaseSettings)` instance; env-file `.env`, `extra="ignore"`. Keys: `DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER` (local|xai|auto), `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS=2048`, `MAX_OUTPUT_TOKENS=512`, `EMBEDDING_*`, `RAW_SIGNAL_RETENTION_DAYS=30`, `NEWSAPI_KEY`, `ENABLE_GROK_FALLBACK`, `XAI_API_KEY`, `OLLAMA_HOST/MODEL`, `CORS_ORIGINS`.
- `.env.example` mirrors all keys with empty secrets. `.env` exists locally (never commit).
- Domain config: `config/haemophilia.yaml` loaded by `backend/app/core/domain_config.py` (assets, confluence thresholds, disease area).

## Build & Verification Commands

| Gate | Command |
|---|---|
| Frontend lint | `npm --prefix frontend run lint` (ESLint 10, zero-warning policy) |
| Frontend build/TSC | `npm --prefix frontend run build` (Next 16 Turbopack; strict TS) |
| Banned-class gate | `node scripts/check-banned-classes.mjs` (Tailwind slate/arbitrary-hex classes banned outside `metaradar.tsx`) |
| Backend tests | `pytest tests/ -x -q` (pytest.ini: `pythonpath = backend .`, asyncio auto) |
| Contract sync | `python scripts/export_openapi.py` → regenerates `frontend/types/api.ts` from OpenAPI 3.1 (`contracts/openapi.json`) |

---

*Mapped as part of full-repo codebase analysis: 2026-08-22*
