# Technology Stack

**Analysis Date:** 2026-08-24

## Languages

**Primary:**
- Python 3.11 - Backend API, connectors, LLM providers, pipeline (`backend/`). Docker image pins `python:3.11-slim` (`backend/Dockerfile`); CI uses Python 3.11 (`.github/workflows/ci.yml`). Local dev machine runs 3.13.5 successfully.
- TypeScript 5.7.3 - Frontend SPA (`frontend/`, pinned exact in `frontend/package.json`)

**Secondary:**
- SQL - Alembic migrations (`backend/alembic/versions/001_*.py` through `011_*.py`)
- YAML - Domain config (`config/haemophilia.yaml`), Docker Compose, GitHub Actions
- JSX/TSX - React components under `frontend/components/`

## Runtime

**Environment:**
- Backend: Python 3.11 (uvicorn ASGI server)
- Frontend: Node.js >=20.9.0 enforced via `engines` in `frontend/package.json`; Docker builds on `node:20-alpine`, CI on Node 22
- Local inference: Ollama daemon hosting Gemma 3 4B Q4 (`ollama/ollama:latest` sidecar, port 11434)

**Package Manager:**
- Frontend: pnpm@9.15.5 declared via `packageManager` field in `frontend/package.json`
  - Both `frontend/pnpm-lock.yaml` AND `frontend/package-lock.json` exist (npm lockfile is a legacy artifact — use pnpm)
- Backend: pip + `backend/requirements.txt` (range-pinned, e.g., `fastapi>=0.110.0`)
- Lockfile (backend): missing — no `requirements.lock` / pip-tools

## Frameworks

**Core:**
- FastAPI >=0.110.0 - REST API, app factory at `backend/app/main.py` (v5.1.0, prefix `/api/v1`)
- Next.js 16.3.0 - Frontend framework (`frontend/package.json`) — NOTE: breaking-change version; consult `node_modules/next/dist/docs/` before writing Next code (per `frontend/AGENTS.md`)
- React 19 + react-dom 19 - UI runtime
- Tailwind CSS 4.3.3 - Styling (`@tailwindcss/postcss` v4 pipeline, `frontend/postcss.config.mjs`)
- LangGraph >=0.2.0 - 11-node intelligence pipeline state machine (`backend/app/workflows/graph.py`)
- SQLAlchemy >=2.0.28 (async) + asyncpg - ORM/data access (`backend/app/db/session.py`)
- Pydantic v2 + pydantic-settings - Validation and typed configuration (`backend/app/core/config.py`)

**Testing:**
- pytest >=8.0.0 + pytest-asyncio (auto mode) + pytest-cov + pytest-httpx - Backend tests (`pytest.ini`, `tests/`)
- No frontend unit-test framework detected — frontend verification = `tsc --noEmit` + ESLint + banned-class gate + production build (CI steps)

**Build/Dev:**
- uvicorn >=0.28.0 - ASGI server (`backend/Dockerfile` CMD)
- Alembic >=1.13.1 - DB migrations (`backend/alembic/`)
- Docker Compose - Full stack orchestration (`docker-compose.yml`)
- ESLint 10 + eslint-config-next 16.3.0 - Frontend linting (`frontend/eslint.config.mjs`)
- Custom banned-class gate: `scripts/check-banned-classes.mjs` run via `pnpm run check:banned-classes`

## Key Dependencies

**Critical (backend):**
- `langgraph>=0.2.0` - Canonical pipeline: ingest → validate → embed → nlp_extract → ontology_enrich → confluence → lifecycle → redteam → missing_signal → synthesize → calibrate (`backend/app/workflows/graph.py`)
- `fastembed>=0.4.0` - ONNX/CPU embeddings, model `sentence-transformers/all-MiniLM-L6-v2` 384-dim (`backend/app/services/embeddings.py`). Deliberately NO torch/sentence-transformers stack.
- `pgvector>=0.2.5` - Vector column support in SQLAlchemy models (`backend/app/models/__init__.py`)
- `sqlalchemy[async]` + `asyncpg>=0.29.0` - Async engine pool (pool_size=10, max_overflow=20) with advisory-lock helpers (`backend/app/db/session.py`)
- `redis>=5.0.3` (aioredis interface) - Cache flush + health checks (`backend/app/api/v1/endpoints/cache.py`)
- `httpx>=0.27.0` - All outbound HTTP (connectors, Grok, Ollama); also `pytest-httpx` for test mocking
- `structlog>=24.1.0` + `asgi-correlation-id>=4.3.0` - Structured JSON logging with correlation-ID middleware (`backend/app/core/logging.py`, `backend/app/core/middleware.py`)

**Critical (frontend):**
- `next@16.3.0` / `react@19` - App Router structure (`frontend/app/layout.tsx`, `frontend/app/page.tsx`, dynamic routes `frontend/app/signals/[signalId]/page.tsx`, `frontend/app/[section]/page.tsx`)
- `recharts ^3.10.1` - Charts in workspaces
- `framer-motion ^13.1.0` - Animations
- `@base-ui/react ^1.5.0` + `shadcn ^4.8.0` - Component primitives (`frontend/components/ui/`)
- `lucide-react`, `clsx`, `tailwind-merge`, `class-variance-authority`, `tw-animate-css` - Styling utilities
- `@designcodeio/threeui` - WebGL/shader effects (`frontend/components/effects/star-portal/`)
- Path alias `@/*` → repo root of `frontend/` (`frontend/tsconfig.json`)

**Infrastructure:**
- PostgreSQL 16 with pgvector extension (`pgvector/pgvector:pg16` image, `docker-compose.yml`)
- Redis 7 (`redis:7-alpine`)
- Ollama sidecar with GPU reservation (nvidia), volume `ollama_models`

## Configuration

**Environment:**
- Typed settings singleton: `backend/app/core/config.py` (`Settings(BaseSettings)` from pydantic-settings, `extra="ignore"`)
- Env file search order: root `.env` → `backend/.env` → CWD `.env` → `../.env`
- `.env` and `.env.example` present at repo root — contents are secret-bearing; NEVER commit or quote
- Key settings groups: DATABASE_URL, REDIS_URL, CORS_ORIGINS, METARADAR_API_KEY, mutation rate limit; LLM block (`LLM_PROVIDER=local|xai|auto`, LOCAL_LLM_MODEL, LLM_DEVICE, LLM_DTYPE=int4, MAX_CONTEXT_TOKENS=2048); Grok fallback (`ENABLE_GROK_FALLBACK`, XAI_API_KEY/GROK_API_KEY); GGUF overrides (MODELS_DIR, LOCAL_GGUF_MODEL/PATH); Ollama (OLLAMA_HOST, OLLAMA_MODEL=gemma3:4b); embedding identity pinned to a specific HuggingFace revision; connector keys (NEWSAPI_KEY or NEWS_API_KEY, NCBI_API_KEY/NCBI_TOOL/NCBI_EMAIL, OPENFDA_API_KEY); scheduler intervals per source
- Domain config (non-secret): `config/haemophilia.yaml` loaded via `backend/app/core/domain_config.py`
- Contract sync: `contracts/openapi.json` ↔ generated `frontend/types/api.ts` via `scripts/export_openapi.py` (CI enforces zero drift)

**Build:**
- `backend/Dockerfile` - python:3.11-slim, non-root `appuser`, uvicorn CMD
- `frontend/Dockerfile` - Multi-stage node:20-alpine builder → runner, `next start -p 3000`
- `docker-compose.yml` - postgres, redis, ollama, backend (+ `backend-gpu` profile with cuda:0), frontend
- `pytest.ini` - asyncio_mode=auto, testpaths=`tests`, `live` marker for live-service tests
- `setup.py` (repo root) - Zero-config launcher: prerequisites check, Docker bootstrap, migrations, seed, model download (`python setup.py --help` for flags)
- `start.py` (repo root) - Dev startup orchestration

## Platform Requirements

**Development:**
- Python 3.11+, Node 20+, pnpm 9, Docker (for Postgres+Redis+Ollama)
- Optional NVIDIA GPU for `--profile gpu` backend / Ollama acceleration (RTX 3050 4GB class suffices at MAX_CONTEXT_TOKENS=2048)
- First-run: `docker exec metaradar-ollama ollama pull gemma3:4b` (or use `setup.py --download-model`; GGUF already present at `models/gemma-3-4b-it-Q4_K_M.gguf`)

**Production:**
- Deployment target: Docker Compose single-host stack (ports: frontend 3000, backend 8000, Postgres 5432, Redis 6379, Ollama 11434)
- Health gates: backend `/api/v1/health`, pg_isready, redis-cli ping, Ollama `/api/tags` (compose healthchecks)
- CI: GitHub Actions `.github/workflows/ci.yml` — pytest → OpenAPI contract drift check → pnpm tsc/lint/banned-class/build

---

*Stack analysis: 2026-08-24*
