# Technology Stack

**Analysis Date:** 2026-08-24

## Languages

**Primary:**
- Python 3.11+ - Backend API, connectors, LLM pipeline (`backend/`); enforced by `setup.py` (exits if < 3.11), Dockerfile uses `python:3.11-slim`, CI pins 3.11
- TypeScript 5.7.3 - Frontend UI (`frontend/`); pinned exactly via `frontend/package.json` devDependencies

**Secondary:**
- YAML - Domain configuration (`config/haemophilia.yaml`), CI workflow definitions
- CSS / Tailwind v4 utility classes - Styling (`frontend/app/globals.css`, `frontend/components/`)
- MJS (ES modules) - Build/lint config (`frontend/next.config.mjs`, `frontend/eslint.config.mjs`, `frontend/postcss.config.mjs`, `scripts/check-banned-classes.mjs`)

## Runtime

**Environment:**
- Backend: Python 3.11 on uvicorn ASGI server (`backend/app/main.py`, `CMD ["uvicorn", "app.main:app", ...]` in `backend/Dockerfile`)
- Frontend: Node.js >= 20.9.0 (`engines` field in `frontend/package.json`); `.nvmrc` pins major version 20; CI uses Node 22
- Local LLM inference: Ollama sidecar container (`ollama/ollama:latest`) hosting `gemma3:4b`, OR in-process llama-cpp-python executing GGUF files from root `models/` directory

**Package Manager:**
- Frontend: pnpm 9.15.5 (declared via `packageManager` field in `frontend/package.json`; CI installs pnpm 9)
- Backend: pip + `backend/requirements.txt` (no pyproject.toml; root `setup.py` is an environment-setup launcher script, NOT package metadata)
- Lockfiles: `frontend/pnpm-lock.yaml` present; **also** a legacy `frontend/package-lock.json` exists alongside it — use pnpm, ignore the npm lockfile
- No backend lockfile (requirements are range-pinned with `>=`)

## Frameworks

**Core:**
- FastAPI >= 0.110.0 - REST API under `/api/v1` (`backend/app/main.py` registers 10 routers: health, signals, intelligence, registry, observability, cache, pipeline, ingestion, search, feedback)
- Next.js 16.3.0 (App Router) - Frontend framework (`frontend/app/layout.tsx`, `frontend/app/page.tsx`, route dirs `frontend/app/signals/`, `frontend/app/[section]/`) — **breaking-change version**: consult `node_modules/next/dist/docs/` before writing frontend code
- React 19 + react-dom 19 - UI runtime
- LangGraph >= 0.2.0 - 11-node intelligence StateGraph (`backend/app/workflows/graph.py`: ingest → validate → embed → nlp_extract → ontology_enrich → confluence → lifecycle → redteam → missing_signal → synthesize → calibrate → END)

**UI/Styling:**
- Tailwind CSS 4.3.3 via `@tailwindcss/postcss` + PostCSS 8.5 (`frontend/postcss.config.mjs`)
- shadcn v4.8.0 ("base-nova" style, RSC enabled — `frontend/components.json`) + Base UI (`@base-ui/react`)
- framer-motion ^13.1.0 - Animations
- recharts ^3.10.1 - Charts/dashboards
- lucide-react - Icons
- class-variance-authority + clsx + tailwind-merge - Variant/class utilities (`frontend/lib/utils.ts`)
- tw-animate-css, @designcodeio/threeui - Visual effects components (`frontend/components/effects/`)

**Data/ORM:**
- SQLAlchemy >= 2.0.28 (async mode) + asyncpg >= 0.29.0 - PostgreSQL access (`backend/app/db/session.py`, pool_size=10, max_overflow=20)
- pgvector >= 0.2.5 - Vector column type, 384-dim embeddings (`backend/app/models/__init__.py` line 291: `Column(Vector(settings.EMBEDDING_DIMENSION))`)
- Alembic >= 1.13.1 - Migrations (`backend/alembic/versions/001_*` through `012_*`)
- pydantic >= 2.6.0 + pydantic-settings >= 2.2.0 - Schemas and typed settings (`backend/app/core/config.py`)

**AI/ML:**
- fastembed >= 0.4.0 - ONNX CPU embeddings, model `sentence-transformers/all-MiniLM-L6-v2` pinned to revision `e4bb823e...` (`backend/app/services/embeddings.py`) — deliberately no torch/sentence-transformers stack
- llama-cpp-python - Optional local GGUF inference engine, installed by `setup.py` with CUDA 12.4 prebuilt wheels when NVIDIA GPU detected (`setup.py` `setup_llama_cpp()`)

**Testing:**
- pytest >= 8.0.0 + pytest-asyncio (auto mode) + pytest-cov + pytest-httpx - Backend suite (`pytest.ini`, `tests/test_*.py`)
- ESLint 10 + eslint-config-next 16.3.0 - Frontend linting (`frontend/eslint.config.mjs`)
- Custom gate: `pnpm run check:banned-classes` (`scripts/check-banned-classes.mjs`)

**Build/Dev:**
- Docker Compose - Full local stack (`docker-compose.yml`: postgres, redis, backend, backend-gpu profile, frontend, ollama)
- `setup.py` - Zero-config environment bootstrap (deps, docker, migrations, seed, model download)
- `start.py` - Unified process launcher (backing services + uvicorn + next dev) with Windows-aware cleanup
- GitHub Actions - CI (`ci.yml`: pytest, contract-sync check, tsc, banned-class gate, lint, build)

## Key Dependencies

**Critical (backend):**
- `langgraph` - The entire intelligence engine is a LangGraph StateGraph; removing breaks `backend/app/workflows/`
- `sqlalchemy[asyncpg]` + `pgvector` - All persistence and vector search (`backend/app/services/vector_query.py`)
- `fastapi` + `uvicorn` - Sole API surface consumed by the frontend
- `fastembed` - Every signal embedding flows through it (`backend/app/workflows/nodes/embed.py`)
- `httpx` - All external HTTP (5 data connectors + Ollama + xAI Grok)
- `structlog` + `asgi-correlation-id` - Structured JSON logging & request tracing (`backend/app/core/logging.py`, `backend/app/core/middleware.py`)

**Critical (frontend):**
- `next@16.3.0` - Breaking-changes release; do not assume older Next.js APIs
- `react@19` - Pairs with Next 16 App Router/RSC

**Infrastructure:**
- Redis client `redis >= 5.0.3` (asyncio API) - Cache management endpoint + health checks (`backend/app/api/v1/endpoints/cache.py`, `backend/app/api/v1/endpoints/health.py`)
- `pyyaml` - Domain config loading (`backend/app/core/domain_config.py`)
- `python-dotenv` - .env support for settings

## Configuration

**Environment:**
- Central typed settings via pydantic-settings `Settings` class in `backend/app/core/config.py`; loads `.env` from repo root first, then `backend/.env` (both exist; contents never committed — `.env.example` template also present at root)
- Domain/thematic configuration is YAML-driven: `config/haemophilia.yaml` parsed by `backend/app/core/domain_config.py` (disease, assets, connector query profiles, confluence thresholds); mounted read-only into containers (`./config:/app/config:ro` in `docker-compose.yml`)
- Frontend API base URL env var: `NEXT_PUBLIC_API_URL` (`frontend/lib/api.ts` line 149) — note `docker-compose.yml` sets `NEXT_PUBLIC_API_BASE_URL`, which nothing reads (dead variable; fallback `http://localhost:8000/api/v1` applies)
- Key required configs: `DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER` (`local|xai|auto`), `OLLAMA_HOST`, `NEWSAPI_KEY` (required for NewsAPI connector or it reports CONFIGURATION_ERROR), optional `XAI_API_KEY`/`GROK_API_KEY`, `METARADAR_API_KEY`, scheduler intervals (`SCHEDULER_*`)

**Build:**
- `backend/Dockerfile` (python:3.11-slim, non-root appuser, port 8000)
- `frontend/Dockerfile` (node:20-alpine multi-stage, pnpm build, port 3000)
- `frontend/next.config.mjs` (images unoptimized), `frontend/tsconfig.json` (strict, path alias `@/*` → frontend root)
- `pytest.ini` (asyncio_mode=auto, testpaths=tests, pythonpath=`backend .`, `live` marker for tests needing real services)
- `backend/alembic.ini` (asyncpg URL, script_location=alembic)

## Platform Requirements

**Development:**
- Python 3.11+, Node 20+ with pnpm 9, Docker Desktop (Postgres 16/pgvector + Redis 7 + optionally Ollama)
- Optional NVIDIA GPU: CUDA-accelerated llama-cpp-python auto-selected by `setup.py` via `nvidia-smi` detection; `LLM_GPU_LAYERS` env tunes offload (default -1 = all layers)
- Windows host supported explicitly (`start.py` uses `taskkill /F /T` on win32)

**Production:**
- Deployment target is the local Docker Compose stack (`docker-compose.yml`); no cloud/deployment manifests detected
- GPU profile available: `docker compose --profile gpu up` runs `backend-gpu` with `LLM_DEVICE=cuda:0` and reserves an NVIDIA device for the ollama container
- Health gates: backend container healthcheck hits `/api/v1/health`; postgres/redis use native readiness probes; ollama probes `/api/tags`

---

*Stack analysis: 2026-08-24*
