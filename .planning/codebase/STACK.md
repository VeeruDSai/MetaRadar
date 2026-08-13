# Technology Stack

**Analysis Date:** 2026-08-13 (Refreshed Post-Stabilization Baseline)

> **Current state:** Frontend architecture reconciled and type-safe (Next.js 16 + React 19 + Tailwind 4 + Framer Motion + Base UI/shadcn, strict TypeScript, ESLint 10 flat config, verified production build). Backend core (FastAPI 0.115, Pydantic v2, SQLAlchemy 2.0 async, Alembic async scaffold, PII/PHI scrubber, Red-Team 19-rule registry, provider capability matrix, unified OpenAPI contract) stabilized with an 18-point `pytest` suite. Infrastructure Dockerfiles authored (`backend/Dockerfile`, `frontend/Dockerfile`) with `docker compose config` zero-warning validation.

## Prescribed vs. Implemented Matrix

| Layer | Prescribed (Master Plan / CLAUDE.md) | Actually in code | Status |
|---|---|---|---|
| Backend API | FastAPI 0.110+ | FastAPI `>=0.110.0` (`backend/app/main.py`); health + business endpoints (`/signals`, `/overview`, `/athena`) | ✅ Operational |
| Workflow | LangGraph 10-node pipeline | Abstract connector base (`backend/app/connectors/base.py`) + pipeline runs schema | ⚠ Scaffold |
| Scheduler | APScheduler in-process | Deferred to Phase 1 polling pipeline | ⚠ Planned |
| ORM/DB | SQLAlchemy + asyncpg | SQLAlchemy 2.0 async + asyncpg (`backend/app/db/session.py`) | ✅ Verified |
| Migration | Alembic async engine | `alembic.ini`, `env.py`, `script.py.mako`, `001_initial_v51_schema.py` | ✅ Configured |
| Vector store | pgvector 384-dim | pgvector dep + `signals.embedding` column + HNSW index | ✅ Schema |
| LLM reasoning | Local Gemma 3 4B → Grok → BART | Provider chain + real privacy gate + Degraded BART fallback (Cases A-F verified) | ✅ Verified (Mock/Fallback) |
| Privacy Gate | PII/PHI scrubber + Privacy Gate | `PIIPHIScrubber` (email, phone, SSN, MRN, DOB regex) + `validate_privacy_gate` | ✅ Verified |
| Red-Team NLI | 19-rule registry + NLI pre-filter | `RedTeamNLIService` with 19 rules (Rules A–S), priority gating, capping, & caching | ✅ Verified |
| Frontend | Next.js 16, Tailwind 4, shadcn/ui, Recharts, Framer Motion | Next.js 16.3.0 + React 19 + Tailwind 4 + Framer Motion 13 + Recharts 3 + Base UI/shadcn | ✅ Verified |
| API Contract | OpenAPI -> TypeScript contract | FastAPI OpenAPI -> `contracts/openapi.json` -> `frontend/types/api.ts` (deterministic 0-diff) | ✅ Verified |
| Tests | Pytest backend suite + Frontend gates | 18-point `pytest` backend suite + `tsc --noEmit` + `eslint .` + `next build` | ✅ Verified |

## Frontend

**Runtime & Framework:**
- **Next.js `16.3.0`** (App Router) running on **React `19.2.8`** + **TypeScript `5.7.3`** + **Node `20`** (pinned via `frontend/.nvmrc` and `engines` field in `package.json`).
- Dynamic route dispatcher: `frontend/app/[section]/page.tsx` routes section requests (`/dashboard`, `/signals`, `/developments`, `/intelligence`, `/functions`, `/calibrate`, `/sources`, `/settings`) to UI components in `frontend/components/metaradar.tsx`; `/` redirects to `/dashboard`.

**Libraries & UI Systems:**
- `framer-motion` `13.1.0` — drawer/signal-card animations (`AnimatePresence`, `motion`).
- `recharts` `3.10.1` — trend visualization charts.
- `lucide-react` `1.31.0` — icon set.
- `@base-ui/react` `1.7.0` + `class-variance-authority` `0.7.1` + `clsx` `2.1.1` + `tailwind-merge` `3.6.0` — UI primitives and dynamic styling utilities (`frontend/lib/utils.ts`).
- **Styling**: Tailwind CSS v4 (`@tailwindcss/postcss` `4.3.3`, `tailwindcss` `4.3.3`) with `@theme inline` tokens in `frontend/app/globals.css`.
- **Quality Gates**: `frontend/eslint.config.mjs` native flat config with `@next/eslint-plugin-next` v16. `next.config.mjs` sets `typescript: { ignoreBuildErrors: false }` for strict build validation.

## Backend

**Runtime & Infrastructure:**
- **Python 3.11+** (CI pins `3.11` in `.github/workflows/ci.yml`).
- **FastAPI `>=0.110.0`** — app in `backend/app/main.py`.
- **Async SQLAlchemy 2.0** + **asyncpg** — database session in `backend/app/db/session.py`.
- **Alembic** async migration engine in `backend/alembic/env.py`.
- **Pydantic v2** — schemas in `backend/app/schemas/__init__.py`.
- **PII/PHI Scrubber** — `backend/app/services/pii.py`.
- **Red-Team Contradiction Service** — `backend/app/services/redteam.py` with 19 rules (Rules A–S).
- **Test Infrastructure** — 18-point `pytest` test suite (`tests/test_config.py`, `tests/test_api_endpoints.py`, `tests/test_provider_matrix.py`, `tests/test_privacy_boundary.py`, `tests/test_redteam_behavior.py`, `tests/test_contract_drift.py`).

## Data & Container Infrastructure

- **PostgreSQL 16 + pgvector**: `pgvector/pgvector:pg16` image; migration creates `vector` and `pg_trgm` extensions and HNSW index `signals_embedding_hnsw` (`m=16, ef_construction=64`).
- **Redis 7**: `redis:7-alpine` image configured via `REDIS_URL`.
- **Dockerfiles**: Authored `backend/Dockerfile` (Python 3.11-slim, uvicorn, non-root user) and `frontend/Dockerfile` (Node 20-alpine multi-stage build). `docker compose config` schema validated with zero warnings.
