# Technology Stack

**Analysis Date:** 2026-09-01

## Languages

**Primary:**
- Python 3.11+ — Backend API, connectors, LLM providers, data layer
- TypeScript 5.7.3 — Frontend Next.js 16 + React 19 application

**Secondary:**
- YAML — Domain configuration (`config/haemophilia.yaml`)
- JSON — Schema definitions, lockfiles, OpenAPI contract, npm metadata
- SQL (PostgreSQL 16 dialect) — Database schema and migrations (`backend/alembic/versions/`)

## Runtime

**Environment:**
- Python 3.11+ (backend runtime; verified in `setup.py`)
- Node.js >=20.9.0 (frontend runtime; defined in `frontend/package.json` engines field)
- Docker Engine & Docker Compose (for backing services: PostgreSQL 16 + pgvector, Redis 7, Ollama)

**Package Manager:**
- `pip` (Python) — Installs from `backend/requirements.txt`
- `pnpm` 9.15.5 (preferred frontend package manager, declared in `frontend/package.json` `packageManager` field)
- npm fallback available if pnpm is absent
- Lockfiles: `frontend/pnpm-lock.yaml`, `frontend/package-lock.json`

## Frameworks

**Core (Backend):**
- **FastAPI** >=0.110.0 — Async REST API framework (`backend/app/main.py`)
- **Uvicorn** >=0.28.0 — ASGI server (`start.py` launches `uvicorn app.main:app`)
- **Pydantic** >=2.6.0 + **pydantic-settings** >=2.2.0 — Schema validation & settings (`backend/app/core/config.py`, `backend/app/schemas/`)
- **SQLAlchemy** >=2.0.28 — Async ORM for PostgreSQL (`backend/app/models/`, `backend/app/db/session.py`)
- **Alembic** >=1.13.1 — Database migration tool (`backend/alembic.ini`, `backend/alembic/versions/`)
- **pgvector** >=0.2.5 — PostgreSQL vector extension for 384-dimensional embeddings
- **Redis** >=5.0.3 — Async caching and rate-limiting backend
- **LangGraph** >=0.2.0 — 11-node intelligence pipeline execution graph (`backend/app/workflows/graph.py`)

**Core (Frontend):**
- **Next.js** 16.3.0 — React framework with App Router (`frontend/next.config.mjs`)
- **React** ^19.0.0 + **ReactDOM** ^19.0.0 — UI library and DOM renderer
- **@base-ui/react** ^1.5.0 — Base UI component primitives (shadcn base-nova style)
- **Tailwind CSS** 4.3.3 + **PostCSS** 8.5 — Styling via `@tailwindcss/postcss` plugin (`frontend/app/globals.css`)
- **tailwind-merge** ^3.3.1 + **clsx** ^2.1.1 — Dynamic class name merging
- **tw-animate-css** ^1.4.0 — CSS animation utilities
- **Lucide React** ^1.16.0 — Icon library
- **Framer Motion** ^13.1.0 — Micro-interactions, slide animations, drawer transitions
- **Recharts** ^3.10.1 — Data visualization and trend charting
- **shadcn** ^4.8.0 — Component generation framework
- **class-variance-authority** ^0.7.1 — Component variant definitions (`cva`)
- **@designcodeio/threeui** ^1.0.0 — 3D UI components (ProfileCard interactive 3D physics)

**Testing:**
- **pytest** >=8.0.0 — Python test runner (`pytest.ini`)
- **pytest-asyncio** >=0.23.0 — Async test support
- **pytest-cov** >=4.1.0 — Test coverage analysis
- **pytest-httpx** >=0.30.0 — HTTP mocking for connector & provider unit tests

**Build/Dev:**
- **ESLint** ^10.8.1 — Flat config linting (`frontend/eslint.config.mjs`) with `@next/eslint-plugin-next`
- **TypeScript** 5.7.3 — Type checker (`frontend/tsconfig.json`)
- **Docker Compose** — Multi-container orchestration (`docker-compose.yml`)

## Key Dependencies

**Critical:**
- **llama-cpp-python** — Local GGUF quantized model inference engine (CPU or CUDA 12.4); automated wheel installation in `setup.py`
- **Ollama** — Sidecar daemon for Gemma 3 4B (Q4_K_M) local inference; docker image `ollama/ollama:latest`
- **FastEmbed** >=0.4.0 — Local sentence embedding engine (`sentence-transformers/all-MiniLM-L6-v2`, 384d)
- **httpx** >=0.27.0 — Async HTTP client for external APIs, connectors, and LLM endpoints
- **structlog** >=24.1.0 — Structured JSON logging with contextvars and secret scrubbing
- **asgi-correlation-id** >=4.3.0 — Trace request correlation ID middleware
- **bcrypt** >=4.1.0 — Secure password hashing
- **itsdangerous** >=2.1.0 — Session token signing and CSRF tokens

**Infrastructure:**
- **asyncpg** >=0.29.0 — High-performance async PostgreSQL driver
- **pyyaml** >=6.0.1 — Domain config parsing (`config/haemophilia.yaml`)
- **python-dotenv** >=1.0.1 — Environment variable management

## Configuration

**Environment:**
- Settings loaded via `pydantic-settings` from `.env`, `backend/.env`, `../.env` (`backend/app/core/config.py`)
- `settings` singleton instantiated at startup with automatic validation
- Domain configuration loaded from YAML (`backend/app/core/domain_config.py`), cached in-memory

**Key Config Files:**
- `backend/app/core/config.py` — Central application configuration & environment schemas
- `config/haemophilia.yaml` — Domain ontology, keyword weights, asset mapping, seed rules
- `frontend/next.config.mjs` — Next.js configuration (unoptimized images, React strict mode)
- `frontend/tsconfig.json` — Strict TypeScript compiler configuration
- `backend/alembic.ini` — Alembic database migration configuration
- `docker-compose.yml` — Container services definition (postgres, redis, backend, backend-gpu, frontend, ollama)
- `pytest.ini` — Test suite runner settings and markers

## Platform Requirements

**Development:**
- Python 3.11+ in PATH
- Node.js >=20.9.0 & pnpm 9.15.5+ (or npm)
- Docker Desktop / Docker Engine with Compose plugin
- NVIDIA GPU with CUDA 12.4 (optional; CPU fallback fully supported)
- ~2.8 GB VRAM budget for Gemma 3 4B Q4_K_M weights + KV cache

**Production:**
- Multi-container Docker Compose deployment
- Service Ports: 8000 (FastAPI), 3000 (Next.js), 5432 (PostgreSQL + pgvector), 6379 (Redis), 11434 (Ollama)
- Health checks enabled across all services with graceful degradation

---

*Stack analysis: 2026-09-01*
