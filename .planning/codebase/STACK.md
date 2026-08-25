# Technology Stack

**Analysis Date:** 2026-08-25

## Languages

**Primary:**
- Python 3.11+ - Backend API, connectors, intelligence workflows, ML services (`backend/`); enforced by `setup.py` (checks >= 3.11), `backend/Dockerfile` (`python:3.11-slim`), and GitHub Actions CI matrix (`3.11`)
- TypeScript 5.7.3 - Frontend UI (`frontend/`); pinned via `frontend/package.json` devDependencies with `strict: true` in `tsconfig.json`

**Secondary:**
- YAML - Domain configuration (`config/haemophilia.yaml`), GitHub Actions CI workflows (`.github/workflows/ci.yml`)
- CSS / Tailwind CSS v4 utility classes - Modern design token styling (`frontend/app/globals.css`, `frontend/components/`)
- MJS (ES modules) - Build and lint tooling (`frontend/next.config.mjs`, `frontend/eslint.config.mjs`, `frontend/postcss.config.mjs`, `scripts/check-banned-classes.mjs`)
- JSON - Synthetic datasets (`data/synthetic_signals.json`), OpenAPI specifications (`contracts/openapi.json`), component config (`frontend/components.json`)

## Runtime & Environment

**Runtimes:**
- Backend: Python 3.11 on `uvicorn` ASGI server (`backend/app/main.py`, containerized via `backend/Dockerfile`)
- Frontend: Node.js >= 20.9.0 (engines declared in `frontend/package.json`; `.nvmrc` declares 20; CI runs Node 22)
- Local LLM inference: Ollama container (`ollama/ollama:latest`) serving `gemma3:4b`, or local `llama-cpp-python` executing quantized `.gguf` weights from `models/`

**Package Management:**
- Frontend: pnpm 9.15.5 (`packageManager` field in `frontend/package.json`; lockfile `frontend/pnpm-lock.yaml`)
- Backend: pip + `backend/requirements.txt` (range-pinned dependencies; root `setup.py` serves as environment bootstrap launcher)

## Frameworks & Core Libraries

**Backend (Python):**
- FastAPI >= 0.110.0 - REST API under `/api/v1` (`backend/app/main.py` registers 10 routers: `health`, `signals`, `intelligence`, `registry`, `observability`, `cache`, `pipeline`, `ingestion`, `search`, `feedback`)
- LangGraph >= 0.2.0 - 11-node intelligence pipeline StateGraph (`backend/app/workflows/graph.py` orchestrating `ingest` → `validate` → `embed` → `nlp_extract` → `ontology_enrich` → `confluence` → `lifecycle` → `redteam` → `missing_signal` → `synthesize` → `calibrate`)
- SQLAlchemy >= 2.0.28 (async engine) + asyncpg >= 0.29.0 - Async PostgreSQL access with connection pooling (`backend/app/db/session.py`)
- pgvector >= 0.2.5 - Vector data type for 384-dimensional dense semantic embeddings (`backend/app/models/__init__.py`)
- Alembic >= 1.13.1 - Database schema migrations (`backend/alembic/versions/001_*` through `012_*`)
- Pydantic >= 2.6.0 + pydantic-settings >= 2.2.0 - Data validation, schema serialization, and typed settings (`backend/app/core/config.py`, `backend/app/schemas/`)
- fastembed >= 0.4.0 - CPU ONNX embedding engine running `sentence-transformers/all-MiniLM-L6-v2` pinned to commit `e4bb823e5956b6277b069d276b978c48a73507c7` (`backend/app/services/embeddings.py`)
- structlog >= 24.1.0 - Structured JSON telemetry and correlation ID logging (`backend/app/core/logging.py`, `backend/app/core/middleware.py`)
- httpx >= 0.27.0 - Async HTTP client for external connector fetching and API dispatch

**Frontend (TypeScript / React):**
- Next.js 16.3.0 (App Router, Turbopack) - UI framework (`frontend/app/layout.tsx`, `frontend/app/[section]/page.tsx`, `frontend/app/signals/[signalId]/page.tsx`)
- React 19 + react-dom 19 - UI component runtime
- Tailwind CSS 4.3.3 via `@tailwindcss/postcss` + PostCSS 8.5 (`frontend/postcss.config.mjs`)
- shadcn UI (v4.8.0 base-nova style) + Base UI (`@base-ui/react`)
- Framer Motion ^13.1.0 - Micro-animations and page transitions
- Recharts ^3.10.1 - Data visualizations, radar charts, calibration timelines
- Lucide React - Standardized iconography
- class-variance-authority + clsx + tailwind-merge - Dynamic styling utilities (`frontend/lib/utils.ts`)
- tw-animate-css & @designcodeio/threeui - Ambient visual effects (`frontend/components/effects/`)

## Testing & Quality Infrastructure

- pytest >= 8.0.0 + pytest-asyncio (auto mode) + pytest-cov + pytest-httpx (`pytest.ini`, 25 test suites in `tests/`)
- ESLint 10 with Next.js 16 flat config (`frontend/eslint.config.mjs`)
- Custom design token guard: `node scripts/check-banned-classes.mjs` (enforces strict CSS variable usage)
- Contract sync guard: `python scripts/export_openapi.py` with `git diff --exit-code frontend/types/api.ts`

## Infrastructure & Containers

- Docker & Docker Compose v2 (`docker-compose.yml`)
  - `metaradar-postgres`: PostgreSQL 16 + pgvector (`pgvector/pgvector:pg16`)
  - `metaradar-redis`: Redis 7 (`redis:7-alpine`)
  - `metaradar-backend`: FastAPI app (`backend/Dockerfile`) with GPU/CPU support
  - `metaradar-frontend`: Next.js production build (`frontend/Dockerfile`)
  - `metaradar-ollama`: Ollama sidecar with GPU passthrough for local LLM inference
