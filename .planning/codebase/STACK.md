# Technology Stack

**Analysis Date:** 2026-08-30

## Languages

**Primary:**
- Python 3.11+ — Backend API, connectors, LLM providers, data layer
- TypeScript 5.7.3 — Frontend Next.js 16 + React 19 application

**Secondary:**
- YAML — Domain configuration (`config/haemophilia.yaml`)
- JSON — Schema definitions, lockfiles, npm metadata
- SQL (PostgreSQL dialect) — Database schema and migrations

## Runtime

**Environment:**
- Python 3.11+ (backend runtime; `setup.py` enforces >=3.11 check)
- Node.js >=20.9.0 (frontend runtime; `package.json` engines field)
- Docker Engine (for composing backing services and containerized deployment)

**Package Manager:**
- `pip` (Python) — Installs from `backend/requirements.txt`
- `pnpm` 9.15.5 (preferred frontend package manager, declared in `frontend/package.json` `packageManager` field)
- npm fallback available if pnpm is absent
- Lockfile: `frontend/package-lock.json` present; `pnpm-lock.yaml` referenced in Dockerfile

## Frameworks

**Core (Backend):**
- **FastAPI** >=0.110.0 — Async REST API framework; app created in `backend/app/main.py` with lifespan context manager
- **UVicorn** >=0.28.0 — ASGI server (`start.py` launches `uvicorn app.main:app`)
- **Pydantic** >=2.6.0 + **pydantic-settings** >=2.2.0 — Data validation and settings management (`backend/app/core/config.py`)
- **SQLAlchemy** >=2.0.28 — Async ORM for PostgreSQL (`asyncpg` driver)
- **Alembic** >=1.13.1 — Database migration tool (`backend/alembic.ini`, `backend/alembic/versions/`)
- **pgvector** >=0.2.5 — PostgreSQL vector extension for 384-dimensional embeddings
- **Redis** >=5.0.3 — Async caching and rate-limiting backend
- **LangGraph** >=0.2.0 — Agent/orchestration graph framework

**Core (Frontend):**
- **Next.js** 16.3.0 — React framework with App Router (`frontend/next.config.mjs`)
- **React** ^19 + **ReactDOM** ^19 — UI library and DOM renderer
- **@base-ui/react** ^1.5.0 — Base UI component primitives (shadcn base-nova style)
- **Tailwind CSS** 4.3.3 + **PostCSS** 8.5 — Styling via `@tailwindcss/postcss` plugin
- **Tailwind merge** ^3.3.1 + **tw-animate-css** ^1.4.0 — Utility class merging and CSS animations
- **Lucide React** ^1.16.0 — Icon library (configured in `components.json` as `lucide`)
- **Framer Motion** ^13.1.0 — Animation library
- **Recharts** ^3.10.1 — Charting library
- **shadcn** ^4.8.0 — Component generation framework
- **class-variance-authority** ^0.7.1 + **clsx** ^2.1.1 — Variant and class name utilities
- **@designcodeio/threeui** ^1.0.0 — 3D UI component library

**Testing:**
- **pytest** >=8.0.0 — Test runner (`pytest.ini`)
- **pytest-asyncio** >=0.23.0 — Async test support
- **pytest-cov** >=4.1.0 — Coverage reporting
- **pytest-httpx** >=0.30.0 — HTTP mocking for tests

**Build/Dev:**
- **ESLint** ^10.8.1 — Linting (`frontend/eslint.config.mjs` with `@next/eslint-plugin-next`)
- **Uvicorn** >=0.28.0 — ASGI dev/production server
- **Docker Compose** — Multi-service orchestration

## Key Dependencies

**Critical:**
- **llama-cpp-python** — Local GGUF model inference engine (CPU or CUDA 12.4); installed via `setup.py` with optional prebuilt wheel from `jllllll.github.io`
- **Ollama** — Sidecar for Gemma 3 4B (Q4 int4) local inference; image `ollama/ollama:latest`
- **FastEmbed** >=0.4.0 — Local embedding model (`sentence-transformers/all-MiniLM-L6-v2`, 384d)
- **httpx** >=0.27.0 — Async HTTP client for all external API calls (connectors, providers)
- **structlog** >=24.1.0 — Structured JSON logging
- **asgi-correlation-id** >=4.3.0 — Request correlation ID middleware
- **bcrypt** >=4.1.0 — Password hashing
- **itsdangerous** >=2.1.0 — Session token signing and CSRF
- **pydantic-settings** >=2.2.0 — Environment-driven settings

**Infrastructure:**
- **asyncpg** >=0.29.0 — Async PostgreSQL driver
- **pyyaml** >=6.0.1 — YAML config parsing
- **python-dotenv** >=1.0.1 — `.env` file loading

## Configuration

**Environment:**
- Settings loaded via `pydantic-settings` from `.env`, `backend/.env`, `../.env` (`backend/app/core/config.py`)
- `SETTINGS` singleton instantiated at module import time
- `DOMAIN_CONFIG_PATH` env var overrides default `config/haemophilia.yaml`
- Domain config loaded from YAML with Pydantic validation (`backend/app/core/domain_config.py`)

**Key Environment Variables:**
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `LLM_PROVIDER` — `local` | `xai` | `auto`
- `XAI_API_KEY` / `GROK_API_KEY` — Hosted Grok API key
- `NEWSAPI_KEY` / `NEWS_API_KEY` — NewsAPI key
- `NCBI_API_KEY` — NCBI E-utilities key
- `OPENFDA_API_KEY` — OpenFDA API key
- `OLLAMA_HOST` — Ollama daemon URL
- `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION` — Embedding configuration
- `CORS_ORIGINS`, `SECRET_KEY`, `SESSION_LIFETIME_SECONDS`

**Build Config Files:**
- `backend/requirements.txt` — Python dependencies
- `frontend/package.json` — Node.js dependencies with `pnpm@9.15.5` packageManager field
- `frontend/tsconfig.json` — TypeScript strict config with `@/*` path alias, `react-jsx` JSX
- `frontend/next.config.mjs` — Next.js config (unoptimized images)
- `frontend/eslint.config.mjs` — Flat config ESLint with Next.js plugin
- `frontend/postcss.config.mjs` — PostCSS with `@tailwindcss/postcss`
- `backend/alembic.ini` — Alembic migration config (file_template `%%(year)d%%(month).2d%%(day).2d_%%(rev)s_%%(slug)s`)
- `pytest.ini` — pytest config (`asyncio_mode = auto`, `pythonpath = backend .`, `live` marker)
- `docker-compose.yml` — Multi-service compose (postgres, redis, backend, backend-gpu, frontend, ollama)
- `backend/Dockerfile` — Python 3.11-slim, uvicorn entrypoint
- `frontend/Dockerfile` — Node 20-alpine multi-stage build with pnpm

## Platform Requirements

**Development:**
- Python 3.11+ installed and in PATH
- Node.js >=20.9.0 installed and in PATH
- pnpm 9.15.5 (preferred) or npm
- Docker Engine with Compose plugin
- NVIDIA GPU (optional, CUDA 12.4) for accelerated local Gemma inference
- ~2.8 GB VRAM budget for Gemma 3 4B Q4_K_M weights + KV cache (RTX 3050 4 GB with MAX_CONTEXT_TOKENS=2048)

**Production:**
- Docker Compose deployment: `postgres` (pgvector/pgvector:pg16), `redis` (redis:7-alpine), `backend`/`backend-gpu` (profiles), `frontend`, `ollama`
- Ports: 5432 (PostgreSQL), 6379 (Redis), 8000 (FastAPI), 3000 (Next.js), 11434 (Ollama)
- Health checks on all services; `backend-gpu` uses `profiles: ["gpu"]` with NVIDIA device reservation
- Models stored in volume `models_cache` and `ollama_models`; config mounted read-only from `./config`

---

*Stack analysis: 2026-08-30*
