# Technology Stack

**Analysis Date:** 2026-08-24

## Languages

**Primary:**
- Python 3.11+ (CPython 3.11 / 3.13) - FastAPI backend in `backend/app/`, run with `python:3.11-slim` in `backend/Dockerfile` and CI (`.github/workflows/ci.yml` uses Python 3.11).
- TypeScript 5.7.3 - Next.js frontend in `frontend/` (App Router), strict typecheck via `npm run build` and `tsc --noEmit`.

**Secondary:**
- SQL - Alembic migrations in `backend/alembic/versions/` (11 migrations, PostgreSQL 16 + pgvector dialect)
- YAML - domain config `config/haemophilia.yaml`
- CSS/Tailwind - styling via `frontend/app/globals.css` (Tailwind 4 + custom rectangular scrollbar tokens)

## Runtime

**Environment:**
- Python 3.11+ (backend, uvicorn ASGI server)
- Node.js >= 20.9.0 (frontend engines field; CI uses Node 22)

**Package Manager:**
- Frontend: npm (with Next.js 16.3.0, React 19)
- Backend: pip with `>=` range constraints in `backend/requirements.txt`

## Frameworks

**Core:**
- FastAPI >= 0.110.0 - REST API under `/api/v1`, app factory in `backend/app/main.py`
- Uvicorn >= 0.28.0 - ASGI server (`CMD ["uvicorn", "app.main:app", ...]` in `backend/Dockerfile`)
- LangGraph >= 0.2.0 - canonical 11-node intelligence pipeline, `backend/app/workflows/graph.py` (`StateGraph`)
- Next.js 16.3.0 + React 19 - frontend App Router (`frontend/app/`)
- Tailwind CSS >= 4.3.3 via `@tailwindcss/postcss` (`frontend/postcss.config.mjs`)
- shadcn/ui (style "base-nova" on @base-ui/react) - component system per `frontend/components.json`

**Reasoning & Inference Engine:**
- Local GGUF Engine - direct quantized weights loading from root `models/` directory (`models/gemma-3-4b-it-Q4_K_M.gguf`, ~2.4 GB) via `llama-cpp-python` (with dynamic GPU layer offloading `n_gpu_layers=-1` and multi-threaded CPU execution).
- Ollama Sidecar - local daemon at `http://localhost:11434` (`gemma3:4b`).
- Hosted Reasoning Fallback - xAI Grok API (`XAI_API_KEY` / `GROK_API_KEY`) behind mandatory external privacy gate.
- Degraded Factual Summarization - `facebook/bart-large-cnn` (1-sentence source-grounded summaries).

**Testing:**
- pytest >= 8.0.0 + pytest-asyncio + pytest-cov + pytest-httpx - backend suite in `tests/` (25 test files, **119 passing tests**), config at `pytest.ini`.
- Frontend Quality Gates: `check-banned-classes.mjs`, ESLint 10, Next.js 16 production build.

**Build & Tooling:**
- Docker Compose - full local stack: Postgres 16 + pgvector, Redis 7, Ollama sidecar, backend, frontend (`docker-compose.yml`).
- `setup.py` (repo root) - zero-config environment and reasoning model setup wizard (downloads local GGUF models into `models/` or configures hosted API keys).
- `start.py` (repo root) - unified host-mode launcher: starts Docker backing services, applies migrations, launches uvicorn backend and Next.js frontend with live telemetry.
- Alembic >= 1.13.1 - schema migrations (`backend/alembic/`, config `backend/alembic.ini`).
- `scripts/export_openapi.py` - contract sync generator producing canonical `frontend/types/api.ts` from OpenAPI.

## Key Dependencies

**Critical:**
- SQLAlchemy >= 2.0.28 + asyncpg >= 0.29.0 - async ORM/data layer (`backend/app/db/session.py`)
- pgvector >= 0.2.5 - vector column support (`from pgvector.sqlalchemy import Vector`)
- redis >= 5.0.3 - query cache + health checks (`backend/app/api/v1/endpoints/cache.py`)
- fastembed >= 0.4.0 - ONNX CPU embeddings (`sentence-transformers/all-MiniLM-L6-v2`, 384-dim) in `backend/app/services/embeddings.py`
- pydantic >= 2.6.0 + pydantic-settings >= 2.2.0 - schemas and typed settings (`backend/app/core/config.py`)
- httpx >= 0.27.0 - outbound HTTP (connectors, LLM providers)
- llama-cpp-python - local GGUF inference engine

**Infrastructure:**
- structlog >= 24.1.0 - structured logging (`backend/app/core/logging.py`)
- asgi-correlation-id >= 4.3.0 - request correlation middleware (`backend/app/core/middleware.py`)
- python-dotenv >= 1.0.1 - multi-path env loading
- pyyaml >= 6.0.1 - domain config parsing (`backend/app/core/domain_config.py`)
- Frontend UI: framer-motion ^13, recharts ^3.10, lucide-react, class-variance-authority, clsx, tailwind-merge

## Configuration

**Environment:**
- Multi-path `.env` resolution in `backend/app/core/config.py` (searches current dir, parent dir, repo root, and backend dir).
- Key backend variables: `DATABASE_URL`, `REDIS_URL`, `MODELS_DIR`, `LOCAL_GGUF_MODEL`, `LOCAL_GGUF_PATH`, `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`, `ENABLE_GROK_FALLBACK`, `XAI_API_KEY`, `GROK_API_KEY`, `OLLAMA_HOST`, `OLLAMA_MODEL`, `NEWSAPI_KEY`, `NEWS_API_KEY`, `NCBI_API_KEY`, `OPENFDA_API_KEY`.
- Frontend variable: `NEXT_PUBLIC_API_URL` read in `frontend/lib/api.ts`.

---

*Stack analysis: 2026-08-24*

