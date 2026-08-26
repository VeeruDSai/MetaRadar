# Technology Stack

**Analysis Date:** 2026-08-27

## Languages

**Primary:**
- **Python 3.11+ (CPython 3.13.5)** - Backend services, FastAPI REST API, LangGraph 11-node intelligence pipeline, 8 ingestion connectors, SQLAlchemy 2.0 async ORM, background scheduler with NewsAPI quota governor
- **TypeScript 5.7.3** - Next.js 16.3.0 App Router frontend, 9 specialized intelligence workspaces, REST API client, strictly typed DTOs

**Secondary:**
- **SQL (PostgreSQL 16 Dialect)** - Relational schemas for Signals, Raw Bronze data, Audit Logs, Sources, Feedback, and pgvector cosine distance queries
- **CSS / Tailwind CSS v4** - CSS-first design token system (`@theme inline`), CSS custom properties in `frontend/app/globals.css`
- **Shell / Python Tooling** - Orchestration and verification scripts (`setup.py`, `start.py`, `scripts/export_openapi.py`, `scripts/check-banned-classes.mjs`, `scripts/test_demo_scenarios_e2e.py`)

## Runtime

**Environment:**
- **Node.js**: `>= 20.9.0` (Frontend execution & Next.js production build)
- **Python**: `3.11+` / `3.13.5` (Backend async event loop & pipeline execution)

**Package Manager:**
- **Frontend**: `pnpm@9.15.5` (configured via `pnpm-workspace.yaml`, `pnpm-lock.yaml`, and `.pnpmrc`) / `npm`
- **Backend**: `pip` with `backend/requirements.txt`
- **Lockfile**: `frontend/pnpm-lock.yaml` and `frontend/package-lock.json` present

## Frameworks

**Core:**
- **Next.js 16.3.0 (App Router, Turbopack)** - Server/client components, nested routing, streaming layouts, error boundaries
- **FastAPI >=0.110.0** - Asynchronous REST API, Server-Sent Events (SSE), automated OpenAPI 3.1 documentation, lifespan management
- **LangGraph >=0.2.0** - 11-node stateful graph pipeline for biomedical competitive intelligence processing
- **SQLAlchemy 2.0.28+ (Async) & asyncpg 0.29.0+** - Async PostgreSQL ORM, connection pooling, PostgreSQL advisory locks (`try_advisory_lock`)
- **Pydantic v2 >=2.6.0 & pydantic-settings >=2.2.0** - Strict DTO schemas, domain configuration validation (`config/haemophilia.yaml`)

**Testing:**
- **Pytest 8.0.0+ with pytest-asyncio 0.23.0+ & pytest-httpx 0.30.0+** - Comprehensive backend test suites (141 executable unit & integration tests)
- **ESLint 10.8.1 with `@next/eslint-plugin-next`** - Frontend linting and strict code quality rules
- **Custom Linting Tooling**: `scripts/check-banned-classes.mjs` (banned Tailwind utility and hex color enforcement)

**Build/Dev:**
- **Turbopack (Next.js 16)** - Fast frontend bundler and compiler
- **PostCSS 8.5 with `@tailwindcss/postcss` 4.3.3** - CSS-first token parsing
- **Alembic 1.13.1+** - Async database schema migrations

## Key Dependencies

**Critical:**
- `fastembed` >=0.4.0 / `sentence-transformers/all-MiniLM-L6-v2` - 384-dimensional dense semantic vector embeddings
- `pgvector` >=0.2.5 - HNSW cosine similarity indexing and hybrid vector search in PostgreSQL
- `framer-motion` ^13.1.0 & `recharts` ^3.10.1 - Smooth micro-animations, counters, and radar visualization
- `@base-ui/react` ^1.5.0 & `lucide-react` ^1.16.0 - Accessible headless UI primitives and semantic icons
- `structlog` >=24.1.0 & `asgi-correlation-id` >=4.3.0 - Structured JSON logging with correlation tracing and PII redaction

**Infrastructure:**
- `httpx` >=0.27.0 - Asynchronous HTTP client for external connector ingestion
- `redis` >=5.0.3 - Distributed caching, health checks, and rate limiting
- `pyyaml` >=6.0.1 - Disease area domain configuration parser (`config/haemophilia.yaml`)

## Configuration

**Environment:**
- Managed through `.env` and `backend/app/core/config.py` using `pydantic-settings`
- Critical keys: `DATABASE_URL`, `REDIS_URL`, `NEWSAPI_KEY`, `NCBI_API_KEY`, `OPENFDA_API_KEY`, `LLM_PROVIDER`, `OLLAMA_HOST`, `XAI_API_KEY`
- Pure validator: `configuration_error_for(source_id)` for side-effect-free connector configuration status validation

**Build:**
- `frontend/next.config.mjs` - Turbopack, strict type and lint gating (`ignoreBuildErrors: false`)
- `frontend/tsconfig.json` - Strict TypeScript configuration with `@/*` path alias mapping
- `frontend/eslint.config.mjs` - ESLint 10 flat configuration
- `pytest.ini` - Asyncio mode auto, test path configuration

## Platform Requirements

**Development:**
- Windows / macOS / Linux with Python 3.11+, Node.js >= 20.9.0, PostgreSQL 16 with `pgvector`
- Optional local GPU (e.g. RTX 3050 4GB VRAM) for Ollama Gemma 3 4B local inference

**Production:**
- Containerized deployment via Docker (`backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml`)
- Single-command zero-config onboarding (`setup.py`) and development runner (`start.py`)

---

*Stack analysis: 2026-08-27*
