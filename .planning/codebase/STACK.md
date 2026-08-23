# Technology Stack

**Analysis Date:** 2026-08-23

## Languages

**Primary:**
- Python (3.11 target) - FastAPI backend in `backend/app/`, run with `python:3.11-slim` in `backend/Dockerfile` and CI (`.github/workflows/ci.yml` uses Python 3.11). Local dev artifacts show CPython 3.13 (`__pycache__/*.cpython-313.pyc`) — treat 3.11 as canonical.
- TypeScript 5.7.3 - Next.js frontend in `frontend/` (App Router), strict typecheck via `pnpm exec tsc --noEmit`.

**Secondary:**
- SQL - Alembic migrations in `backend/alembic/versions/` (11 migrations, PostgreSQL dialect)
- YAML - domain config `config/haemophilia.yaml`
- CSS/Tailwind - styling via `frontend/app/globals.css`

## Runtime

**Environment:**
- Python 3.11+ (backend, uvicorn ASGI server)
- Node.js >= 20.9.0 (frontend engines field; CI uses Node 22)

**Package Manager:**
- Frontend: pnpm 9.15.5 (pinned via `packageManager` in `frontend/package.json`)
  - Lockfile: present — `frontend/pnpm-lock.yaml`
- Backend: pip with `>=` range constraints in `backend/requirements.txt`
  - Lockfile: missing (no pinned hashes; versions are minimums only)

## Frameworks

**Core:**
- FastAPI >= 0.110.0 - REST API under `/api/v1`, app factory in `backend/app/main.py`
- Uvicorn >= 0.28.0 - ASGI server (`CMD ["uvicorn", "app.main:app", ...]` in `backend/Dockerfile`)
- LangGraph >= 0.2.0 - canonical 11-node intelligence pipeline, `backend/app/workflows/graph.py` (`StateGraph`)
- Next.js 16.3.0 + React 19 - frontend App Router (`frontend/app/`)
- Tailwind CSS >= 4.3.3 via `@tailwindcss/postcss` (`frontend/postcss.config.mjs`)
- shadcn/ui (style "base-nova" on @base-ui/react) - component system per `frontend/components.json`

**Testing:**
- pytest >= 8.0.0 + pytest-asyncio + pytest-cov + pytest-httpx - backend suite in `tests/` (25 test files), config at `pytest.ini`
- Frontend: no test runner detected — gates are `tsc --noEmit`, ESLint, banned-class check, `next build` (CI steps)

**Build/Dev:**
- Docker Compose - full local stack: Postgres 16+pgvector, Redis 7, Ollama sidecar, backend (+ optional `gpu` profile), frontend (`docker-compose.yml`)
- `start.py` (repo root) - unified host-mode launcher: starts Docker backing services, uvicorn backend, Next.js dev/prod frontend with live telemetry
- Alembic >= 1.13.1 - schema migrations (`backend/alembic/`, config `backend/alembic.ini`)
- scripts/export_openapi.py - contract sync generator producing canonical `frontend/types/api.ts` from OpenAPI
- ESLint 10 + eslint-config-next 16.3.0 (`frontend/eslint.config.mjs`) + custom gate `scripts/check-banned-classes.mjs`

## Key Dependencies

**Critical:**
- SQLAlchemy >= 2.0.28 + asyncpg >= 0.29.0 - async ORM/data layer, engine in `backend/app/db/session.py` (`create_async_engine`, pool_size=10, max_overflow=20)
- pgvector >= 0.2.5 - vector column support (`from pgvector.sqlalchemy import Vector` in `backend/app/models/__init__.py`)
- redis >= 5.0.3 - cache + health checks (`redis.asyncio` in `backend/app/api/v1/endpoints/cache.py`)
- fastembed >= 0.4.0 - ONNX CPU embeddings (all-MiniLM-L6-v2, 384-dim) in `backend/app/services/embeddings.py`; deliberately no torch/sentence-transformers
- pydantic >= 2.6.0 + pydantic-settings >= 2.2.0 - schemas and typed settings (`backend/app/core/config.py`)
- httpx >= 0.27.0 - all outbound HTTP (connectors, LLM providers)

**Infrastructure:**
- structlog >= 24.1.0 - JSON structured logging (`backend/app/core/logging.py`)
- asgi-correlation-id >= 4.3.0 - request correlation middleware (`backend/app/core/middleware.py`)
- python-dotenv >= 1.0.1 - env loading for settings
- pyyaml >= 6.0.1 - domain config parsing (`backend/app/core/domain_config.py`)
- langgraph - workflow orchestration (see above)
- Frontend UI: framer-motion ^13, recharts ^3.10, lucide-react, class-variance-authority, clsx, tailwind-merge

## Configuration

**Environment:**
- Typed settings singleton in `backend/app/core/config.py` (`pydantic_settings.BaseSettings`, reads `.env`, `extra="ignore"`)
- `.env` file present at repo root (secrets — never commit); `.env.example` documents expected variables
- Key backend variables: `DATABASE_URL`, `REDIS_URL`, `CORS_ORIGINS`, `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`, `ENABLE_GROK_FALLBACK`, `XAI_API_KEY`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `EMBEDDING_MODEL*`, `NEWSAPI_KEY`, `NCBI_API_KEY|NCBI_TOOL|NCBI_EMAIL`, `OPENFDA_API_KEY`, `ENABLE_BACKGROUND_SCHEDULER`, `SCHEDULER_*_INTERVAL_MINUTES`
- Frontend variable: `NEXT_PUBLIC_API_URL` read in `frontend/lib/api.ts:142`. Note: `docker-compose.yml:102` sets `NEXT_PUBLIC_API_BASE_URL`, which the code does NOT read — set `NEXT_PUBLIC_API_URL` when running via Compose.

**Build:**
- `backend/Dockerfile` - python:3.11-slim, non-root user, port 8000
- `frontend/Dockerfile` - Next.js standalone build, port 3000
- `frontend/tsconfig.json` - path alias `@/*` → repo-relative frontend root
- `pytest.ini` - root test discovery config
- `contracts/openapi.json` - committed API contract snapshot (drift-checked in CI by `tests/test_contract_drift.py`)

## Platform Requirements

**Development:**
- Windows/macOS/Linux hosts supported; `start.py` orchestrates Docker Desktop + local processes on Windows (see `.planning/WINDOWS.md`)
- Docker required for Postgres/Redis/Ollama unless running services natively
- GPU optional: `docker compose --profile gpu up` uses `LLM_DEVICE=cuda:0` (~4 GB VRAM budget documented in docker-compose.yml comments); default is CPU (`gemma3:4b` Q4 int4)

**Production:**
- Deployment target: local/on-prem Docker Compose stack ("Local Gemma" privacy-first architecture; hosted LLM fallback disabled by default)
- Health probes: `GET /api/v1/health` (compose healthchecks hit this endpoint)

---

*Stack analysis: 2026-08-23*
