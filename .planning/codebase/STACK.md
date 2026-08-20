# Technology Stack

**Analysis Date:** 2026-08-20

## Languages

**Primary:**
- Python 3.11+ - Backend API, intelligence pipeline, connectors (`backend/`, `start.py`, `setup.py`)
- TypeScript 5.7.3 - Frontend application (`frontend/`)

**Secondary:**
- HTML/CSS (Tailwind CSS 4) - Frontend styling (`frontend/app/globals.css`, `frontend/components/ui/`)
- YAML - Domain/connector configuration (`config/haemophilia.yaml`)
- SQL - PostgreSQL schema and pgvector queries (`backend/app/models/__init__.py`, `backend/app/services/vector_query.py`)
- Bash/PowerShell - Orchestration scripts (`setup.py`, `start.py`)

## Runtime

**Environment:**
- Python 3.11 (required by `setup.py` line 47; container base `python:3.11-slim` in `backend/Dockerfile`)
- Node.js >= 20.9.0 (`frontend/package.json` engines; `.nvmrc` pins 20; frontend Dockerfile uses `node:20-alpine`)

**Package Manager:**
- Backend: pip with `backend/requirements.txt` (unpinned lower bounds, e.g. `fastapi>=0.110.0`)
- Frontend: pnpm 9.15.5 (declared `packageManager` in `frontend/package.json`; `pnpm-lock.yaml` committed; `package-lock.json` also present but secondary)
- Lockfiles: `frontend/pnpm-lock.yaml` present; backend has no lockfile

## Frameworks

**Core:**
- Next.js 16.3.0 - React framework, App Router (`frontend/`); config in `frontend/next.config.mjs` (images unoptimized)
- React 19 - UI library (`react`, `react-dom` in `frontend/package.json`)
- FastAPI >=0.110.0 - Async REST API (`backend/app/main.py`, `backend/app/api/v1/`)
- SQLAlchemy 2.0 (async) + asyncpg - ORM and PostgreSQL driver (`backend/app/db/session.py`, `backend/app/models/__init__.py`)
- Pydantic v2 + pydantic-settings - Validation and settings (`backend/app/core/config.py`, `backend/app/schemas/`)

**AI/ML:**
**AI/ML & Ingestion:**
- LangGraph >=0.2.0 - 10-node intelligence pipeline graph (`backend/app/workflows/graph.py`, `backend/app/workflows/runner.py`)
- Live Biomedical Ingestion - Real public HTTP connectors (`PubMed`, `ClinicalTrials.gov`, `OpenFDA`, `EMA RSS`) in `backend/app/connectors/`
- Ollama - Local LLM sidecar serving `gemma3:4b` with deterministic fallback (`backend/app/providers/gemma.py`)
- fastembed >=0.4.0 - ONNX CPU embeddings, `sentence-transformers/all-MiniLM-L6-v2` (384-dim) (`backend/app/services/embeddings.py`)
- pgvector >=0.2.5 - Vector column type + HNSW index for hybrid search (`backend/app/models/__init__.py`, `backend/app/services/vector_query.py`)

**Testing:**
- pytest >=8.0.0, pytest-asyncio, pytest-cov - Backend test suite (`pytest.ini`, `tests/` - 91 passed tests)
- Frontend: `tsc --noEmit`, ESLint 10, Next.js build validation in `.github/workflows/ci.yml`

**Build/Dev:**
- uvicorn - ASGI server (`start.py`, `backend/Dockerfile`)
- Alembic - DB migrations (`backend/alembic/`, `backend/alembic.ini`)
- ESLint 10 + eslint-config-next - Frontend linting (`frontend/eslint.config.mjs`)
- Tailwind CSS 4 + PostCSS - Styling pipeline (`frontend/postcss.config.mjs`, `frontend/components.json`)
- shadcn/ui - Component system (`frontend/components.json`)

## Key Dependencies

**Critical:**
- `next` 16.3.0 + `react` 19 - Frontend runtime (`frontend/package.json`)
- `fastapi` + `uvicorn` - Backend API server (`backend/requirements.txt`)
- `sqlalchemy` 2.0 + `asyncpg` - Async DB access (`backend/app/db/session.py`)
- `pgvector` - Vector search capability (`backend/app/models/__init__.py`)
- `langgraph` - Pipeline orchestration (`backend/app/workflows/graph.py`)
- `fastembed` - Local CPU embeddings (`backend/app/services/embeddings.py`)
- `httpx` - Outbound HTTP for public biomedical APIs (PubMed, ClinicalTrials, FDA, EMA, NewsAPI) and LLM providers
- `redis` - Cache health/clear endpoints (`backend/app/api/v1/endpoints/cache.py`, `backend/app/api/v1/endpoints/health.py`)

**Infrastructure:**
- `pydantic` + `pydantic-settings` - Schema + env config (`backend/app/core/config.py`)
- `pyyaml` - Domain config loading (`backend/app/core/domain_config.py`)
- `alembic` - Schema migrations (`backend/alembic/versions/`)
- `python-dotenv` - Local env loading

**Frontend UI libs:**
- `framer-motion` 13 - Animations
- `recharts` 3 - Charts/trends (`frontend/lib/api.ts` trend mappers)
- `lucide-react` - Icons
- `class-variance-authority`, `clsx`, `tailwind-merge`, `tw-animate-css`, `@base-ui/react` - shadcn/ui styling stack

## Configuration

**Environment:**
- pydantic-settings reads `.env` (`backend/app/core/config.py`); `.env` template at `.env.example`
- Key configs: `DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`, `ENABLE_GROK_FALLBACK`, `XAI_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_MODEL_REVISION`, `EMBEDDING_DIMENSION`, `RAW_SIGNAL_RETENTION_DAYS`, `NEWSAPI_KEY`, `CORS_ORIGINS`
- Frontend env: `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1` in `frontend/lib/api.ts`)
- Domain config: `config/haemophilia.yaml` (disease area, assets, connector query profiles, routing matrix), path overridable via `DOMAIN_CONFIG_PATH`

**Build:**
- `frontend/next.config.mjs` — Next.js 16 App Router configuration
- `frontend/tsconfig.json` — strict mode, path alias `@/*` → `./*`
- `frontend/eslint.config.mjs` — ESLint 10 flat config
- `backend/alembic.ini` — migration location `alembic`, asyncpg URL
- `docker-compose.yml` — full service stack (postgres, redis, backend, backend-gpu profile, frontend, ollama)
- `pytest.ini` — `asyncio_mode = auto`, `testpaths = tests`, `pythonpath = backend .`
- Contract sync: `scripts/export_openapi.py` regenerates `contracts/openapi.json` and `frontend/types/api.ts`

## Platform Requirements

**Development:**
- Python 3.11+ (`setup.py` enforces, exits on <3.11)
- Node.js >= 20.9.0, pnpm 9
- Docker + Docker Compose for backing services (Postgres, Redis, Ollama) — `setup.py` bootstraps: pip install → npm install → `docker compose up -d postgres redis` → `alembic upgrade head` → seed `backend/app/db/seed.py` → `ollama pull gemma3:4b`
- GPU optional: `--profile gpu` compose service `backend-gpu` with `LLM_DEVICE=cuda:0`; Ollama container reserves 1 NVIDIA GPU

**Production:**
- Deployment via `docker-compose.yml` (postgres:5432, redis:6379, backend:8000, frontend:3000, ollama:11434)
- `start.py` launcher runs host processes (uvicorn + `next dev`/`next start`) with health polling and logs to `logs/`
- CI: GitHub Actions `.github/workflows/ci.yml` (Python 3.11, Node 22, pnpm 9; pytest + contract sync + `tsc --noEmit` + lint + build)

---

*Stack analysis: 2026-08-20*