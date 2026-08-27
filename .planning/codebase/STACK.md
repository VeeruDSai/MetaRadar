# Technology Stack

**Analysis Date:** 2026-08-28

## Languages

**Primary:**
- Python 3.11+ (CPython) - Backend core API, data connectors, LangGraph intelligence pipeline, background scheduler, Alembic migrations, database models, ML/inference
- TypeScript 5.7.3 - Frontend Next.js 16 application, React 19 client/server components, API client, type definitions, UI shaders

**Secondary:**
- SQL / PostgreSQL DDL & PL/pgSQL - Schema definitions, pgvector embeddings, triggers, index definitions
- Shell / PowerShell / Python scripts - Automation, environment bootstrap (`setup.py`), unified process launcher (`start.py`), schema export (`scripts/export_openapi.py`)

## Runtime

**Environment:**
- Backend: Python 3.11+ via virtual environment or Docker (`backend/Dockerfile`)
- Frontend: Node.js >=20.9.0 (`frontend/.nvmrc`)
- Backing Services: Docker Compose (`docker-compose.yml`) hosting PostgreSQL 16 (pgvector) and Redis 7 Alpine

**Package Manager:**
- Python: `pip` with `backend/requirements.txt`
- Frontend: `pnpm` 9.15.5 (`frontend/pnpm-lock.yaml`, `frontend/package.json`), compatible with `npm`

## Frameworks

**Core:**
- FastAPI >=0.110.0 (`backend/app/main.py`) - High-performance async REST API with automatic OpenAPI documentation
- Next.js 16.3.0 (`frontend/app/`) - React 19 App Router framework with SSR, dynamic routing (`app/[section]`, `app/signals/[signalId]`), and standalone output
- LangGraph >=0.2.0 (`backend/app/workflows/graph.py`) - 11-node stateful workflow engine orchestrating ingestion, extraction, validation, synthesis, and calibration

**Database & ORM:**
- SQLAlchemy >=2.0.28 (`backend/app/db/session.py`) - Async ORM with `asyncpg` driver
- Alembic >=1.13.1 (`backend/alembic/`) - Database migration framework
- pgvector >=0.2.5 (`backend/app/models/__init__.py`) - Vector similarity search engine in PostgreSQL for 384-dimensional dense embeddings

**Testing:**
- Pytest >=8.0.0 (`pytest.ini`, `tests/`) - Python unit, integration, and contract tests with `pytest-asyncio`, `pytest-cov`, `pytest-httpx`
- ESLint 10.8.1 & Next.js ESLint (`frontend/eslint.config.mjs`) - Frontend linting and type checking

**Build/Dev:**
- Uvicorn >=0.28.0 (`backend/app/main.py`, `start.py`) - ASGI web server with async event loop
- Tailwind CSS 4.3.3 (`frontend/app/globals.css`, `frontend/postcss.config.mjs`) - Modern CSS utility framework with `@theme` directives
- PostCSS 8.5 (`frontend/postcss.config.mjs`) - CSS processing pipeline

## Key Dependencies

**Critical:**
- `pydantic` >=2.6.0 & `pydantic-settings` >=2.2.0 (`backend/app/core/config.py`, `backend/app/schemas/`) - Strict data validation and schema definitions
- `fastembed` >=0.4.0 (`backend/app/services/embeddings.py`) - Local, high-throughput text embeddings using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions)
- `llama-cpp-python` / Ollama (`backend/app/providers/gemma.py`) - Local hardware-accelerated LLM inference for `google/gemma-3-4b-it` (GGUF Q4_K_M)
- `httpx` >=0.27.0 (`backend/app/connectors/`, `backend/app/providers/grok.py`) - Async HTTP client for external biomedical APIs and hosted LLM reasoning
- `structlog` >=24.1.0 & `asgi-correlation-id` >=4.3.0 (`backend/app/core/logging.py`, `backend/app/core/middleware.py`) - Structured JSON logging with end-to-end request tracing

**UI & Visualization:**
- `lucide-react` ^1.16.0 (`frontend/components/`) - Comprehensive iconography
- `framer-motion` ^13.1.0 (`frontend/components/common/ScrollReveal.tsx`, `frontend/components/effects/`) - Physics-based animations and transitions
- `recharts` ^3.10.1 (`frontend/components/observability/`, `frontend/components/calibration/`) - Charting and data visualization
- `clsx` & `tailwind-merge` (`frontend/lib/utils.ts`) - Conditional class utility merging
- `@base-ui/react` & `shadcn` (`frontend/components/ui/`) - Accessible component primitives

## Configuration

**Environment:**
- Root `.env` file (`.env.example`) parsed by `backend/app/core/config.py` and `start.py`
- Required configurations:
  - `DATABASE_URL`: PostgreSQL connection string (`postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar`)
  - `REDIS_URL`: Redis caching string (`redis://localhost:6379/0`)
  - `LLM_PROVIDER`: `local` (Gemma GGUF/Ollama), `xai` (Grok), or `auto`
  - `SECRET_KEY`: Cryptographic signing secret for user sessions and cookies
  - Optional API keys: `XAI_API_KEY`, `NEWSAPI_KEY`, `NCBI_API_KEY`, `OPENFDA_API_KEY`

**Build:**
- Frontend: `frontend/next.config.mjs`, `frontend/tsconfig.json`, `frontend/components.json`
- Backend: `backend/alembic.ini`, `pytest.ini`
- Domain: `config/haemophilia.yaml` (Rare disease ontology, competitive assets, patient segments, and scoring weights)

## Platform Requirements

**Development:**
- Python 3.11+, Node.js 20+, Docker & Docker Compose
- Optional: NVIDIA GPU (RTX 3050+ or CUDA 12.4 compatible) for local real-time Gemma-3-4B inference (falls back to CPU or hosted Grok API)

**Production:**
- Containerized Linux deployment via Docker Compose or Kubernetes
- PostgreSQL 16 with pgvector extension
- Redis 7 cache and session store

---

*Stack analysis: 2026-08-28*
