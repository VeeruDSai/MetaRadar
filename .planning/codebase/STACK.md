# Technology Stack

**Analysis Date:** 2026-08-13

> **Current state:** Backend foundation (FastAPI app, DB models, Alembic migration, LLM provider abstraction, config) is in place but **simulated** at the AI/ML layer. The frontend has been **substantially built out since the previous map** — a full v0.app-generated Next.js workspace now lives at `frontend/` (`app/`, `components/`, `lib/`, `types/`, `pnpm-lock.yaml`). The AI/ML model layer and all external data connectors remain **simulated/scaffolded, not wired to real libraries or endpoints**. The Master Plan ([`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md)) and CLAUDE.md prescribe the full stack; this document records what is *actually in code* and flags discrepancies.

## Prescribed vs. Implemented (quick alignment)

| Layer | Prescribed (Master Plan / CLAUDE.md) | Actually in code | Gap |
|---|---|---|---|
| Backend API | FastAPI 0.110+ | FastAPI `>=0.110.0` ([`backend/requirements.txt`](backend/requirements.txt)); only health router mounted | ✅ partial |
| Workflow | LangGraph 10-node pipeline | None (no `langgraph` dep, no `app/workflows/`) | ❌ not started |
| Scheduler | APScheduler in-process | None | ❌ not started |
| ORM/DB | SQLAlchemy + asyncpg | SQLAlchemy 2.0 async + asyncpg ([`backend/app/db/session.py`](backend/app/db/session.py)) | ✅ |
| Vector store | pgvector 384-dim | pgvector dep + `signals.embedding` column + HNSW index ([`backend/alembic/versions/001_initial_v51_schema.py`](backend/alembic/versions/001_initial_v51_schema.py)) | ✅ schema; ❌ no embeddings written |
| LLM reasoning | Local Gemma 3 4B → Grok → BART | Provider chain + real privacy gate but **simulated inference** ([`backend/app/providers/`](backend/app/providers/)) | ⚠ scaffold only |
| NER | spaCy `en_core_sci_md` | Not in requirements, no code | ❌ |
| NLI (red-team) | BART MNLI zero-shot | Rule-based mock ([`backend/app/services/redteam.py`](backend/app/services/redteam.py)) | ⚠ mock only |
| Data connectors | PubMed, NewsAPI, ClinicalTrials.gov, OpenFDA, EMA RSS, congress, Reddit | Abstract base only ([`backend/app/connectors/base.py`](backend/app/connectors/base.py)) | ❌ none implemented |
| Frontend | Next.js 15, Tailwind 4, shadcn/ui, TanStack Query, Recharts, Framer Motion | Next.js **16.3.0** + React 19.2.4 + Tailwind **v4.3.3** + shadcn v4 + Recharts + Framer Motion — **but all data is mocked** ([`frontend/lib/api.ts`](frontend/lib/api.ts)); TanStack Query **absent** | ⚠ UI built, API layer mock |
| Retry | tenacity (2s/4s/8s) | Not in requirements | ❌ |
| Tests | pytest suite | Plain script `tests/test_foundation.py` (no pytest) | ⚠ minimal |

## Frontend

**Runtime/Framework (verified from [`frontend/package.json`](frontend/package.json) + [`frontend/pnpm-lock.yaml`](frontend/pnpm-lock.yaml)):**
- **Next.js `16.3.0`** (App Router) — note: **v16, not the v15 prescribed by the Master Plan/CLAUDE.md**. Runs on **React `19.2.4`** + **react-dom `19.2.4`** + **TypeScript `5.7.3`** (pinned).
- Node.js runtime not pinned in the repo (no `.nvmrc`, no `engines` field); Next.js 16 requires Node ≥ 20.9.
- Dynamic route shell: `frontend/app/[section]/page.tsx` dispatches all sections to components exported from `frontend/components/metaradar.tsx`; `frontend/app/page.tsx` redirects `/` → `/dashboard`.

**Key libraries and purpose:**
- `framer-motion` `13.1.0` — drawer/signal-card animations (`AnimatePresence`, `motion`) in [`frontend/components/metaradar.tsx`](frontend/components/metaradar.tsx)
- `recharts` `3.10.1` — `AreaChart` trend visualization (dashboard "Portfolio momentum")
- `lucide-react` `1.17.0` — icon set (nav, topbar, empty states)
- `@vercel/analytics` `1.6.1` — `<Analytics />` rendered only in production ([`frontend/app/layout.tsx`](frontend/app/layout.tsx))
- `@base-ui/react` `1.5.0` — Base UI primitives backing the shadcn v4 button component ([`frontend/components/ui/button.tsx`](frontend/components/ui/button.tsx))
- `class-variance-authority` `0.7.1`, `clsx` `2.1.1`, `tailwind-merge` `3.4.0` — CVA variants + `cn()` utility ([`frontend/lib/utils.ts`](frontend/lib/utils.ts))
- **NOT present** (contra earlier map & Master Plan): `@tanstack/react-query`, `zod`, `axios`. No `NEXT_PUBLIC_API_BASE_URL` usage, no `fetch()` anywhere — the frontend is **100% mock-data driven**.

**Styling:**
- **Tailwind CSS v4.3.3** (`tailwindcss` + `@tailwindcss/postcss` `4.3.3`, both devDependencies) — **CSS-first config**: no `tailwind.config.*` file; theme tokens declared via `@theme inline` in [`frontend/app/globals.css`](frontend/app/globals.css)
- `tw-animate-css` `1.4.0` — animation utilities imported in `globals.css`
- **shadcn/ui v4** (`shadcn` CLI `4.10.0`): [`frontend/components.json`](frontend/components.json) uses style `"base-nova"`, CSS variables on, `@/*` alias, lucide icon library; `globals.css` imports `shadcn/tailwind.css` and `@custom-variant dark`
- Only one shadcn component is materialized so far: `frontend/components/ui/button.tsx`

**Structure & data flow:**
- Active surface: `frontend/app/` (layout, page, `[section]`), `frontend/components/metaradar.tsx` (single 60-line multi-export client component containing `Shell`, `DashboardPage`, `SignalsPage`, `IntelligencePage`, `GenericPage`, `SignalDrawer`, `TrendChart`), `frontend/lib/` (`api.ts` mock-delay wrapper, `mock-data.ts` 4 synthetic signals, `utils.ts`), `frontend/types/api.ts` (mock types), `frontend/public/` (icons, placeholders)
- **Legacy/duplicate surface (tracked, older):** `frontend/src/app/sources/page.tsx` (hardcoded connector-status grid) and `frontend/src/types/api.ts` (auto-generated OpenAPI contract). The new build is untracked in git (`git status` shows `?? frontend/app/`, `?? frontend/components/`, `?? frontend/lib/`, `?? frontend/types/`).
- TypeScript path alias `@/*` → frontend root ([`frontend/tsconfig.json`](frontend/tsconfig.json)); `frontend/next.config.mjs` sets `typescript.ignoreBuildErrors: true` and `images.unoptimized: true`.
- **Missing:** `eslint.config.*` — `eslint` + `eslint-config-next` are declared but there is no config file, so `pnpm lint` has nothing to read. No `frontend/Dockerfile`, no `frontend/README.md`, no test setup.

## Backend

**Runtime/Framework:**
- **Python 3.11** (CI pins `python-version: "3.11"` in [`.github/workflows/ci.yml`](.github/workflows/ci.yml); local dev machines show 3.13 `.pyc` artifacts)
- **FastAPI `>=0.110.0`** — app in [`backend/app/main.py`](backend/app/main.py); **only 5 routes**: `/`, `/api/v1/health`, `/api/v1/health/ready`, `/api/v1/health/models`, `/api/v1/health/connectors`
- **Uvicorn `>=0.28.0`** — declared (no run config committed)
- **Pydantic v2 `>=2.6.0`** + **pydantic-settings `>=2.2.0`** — `Settings(BaseSettings)` in [`backend/app/core/config.py`](backend/app/core/config.py)

**Key libraries and modules ([`backend/requirements.txt`](backend/requirements.txt) — floor-pinned, no lockfile):**
- `sqlalchemy>=2.0.28` (async) + `asyncpg>=0.29.0` — engine/session in [`backend/app/db/session.py`](backend/app/db/session.py) (pool_size=10, max_overflow=20, pool_pre_ping)
- `alembic>=1.13.1` — migration [`backend/alembic/versions/001_initial_v51_schema.py`](backend/alembic/versions/001_initial_v51_schema.py) (17 tables, `vector` + `pg_trgm`, HNSW index); **`alembic.ini` missing** (not bootstrapped)
- `pgvector>=0.2.5` — `Vector(384)` column on `signals` ([`backend/app/models/__init__.py`](backend/app/models/__init__.py))
- `redis>=5.0.3` — `redis.asyncio` ping only ([`backend/app/api/v1/endpoints/health.py`](backend/app/api/v1/endpoints/health.py))
- `pyyaml>=6.0.1` — domain config loader [`backend/app/core/domain_config.py`](backend/app/core/domain_config.py) → `config/haemophilia.yaml` (7 competitor assets, 7 signal types, 9 lifecycle stages, 6 functions, baseline routing matrix)
- `httpx>=0.27.0` — declared but **never imported** (no external HTTP client code yet)
- `python-dotenv>=1.0.1` — env loading

**Module layout (`backend/app/`):**
- `core/config.py` — env-driven Settings (DB, Redis, LLM provider/device/dtype, embedding model+revision+dimension, CORS, NewsAPI key)
- `core/domain_config.py` — YAML-driven `DomainConfig` with module-level cache
- `db/session.py` — async engine, `get_db` dependency, `pg_try_advisory_lock`/`pg_advisory_unlock` helpers
- `models/__init__.py` — 17 ORM tables (pipeline_runs, sources, companies, assets, trials, developments, events, lifecycle_events, confluences, raw_signals_bronze, evidence, signals, signal_routing, calibration_feedback, watch_items, audit_log)
- `schemas/__init__.py` — Pydantic response schemas (Signal, Development, Health*, ConnectorHealthStatus, ModelMetadata…)
- `providers/` — LLM abstraction (base, factory, gemma, grok, degraded)
- `connectors/base.py` — `SourceConnector` abstract base + `RawSignalPayload`; **zero concrete connectors**
- `services/deduplication.py` — fingerprinting (pmid/nct/reg/hash) + `upsert_signal` ON CONFLICT DO UPDATE
- `services/redteam.py` — mock pairwise contradiction checker (rule-based, in-memory cache)
- `api/v1/endpoints/health.py` — the only mounted router

## Data & Storage

**Databases:**
- **PostgreSQL 16 + pgvector** — `pgvector/pgvector:pg16` image ([`docker-compose.yml`](docker-compose.yml)); migration creates `vector` + `pg_trgm` extensions and HNSW index `signals_embedding_hnsw` (`m=16, ef_construction=64`, `vector_cosine_ops`)
- Connection: `DATABASE_URL` (`postgresql+asyncpg://…`; localhost default in `config.py`, compose overrides to `postgres:5432`)
- Client: SQLAlchemy 2.0 async + asyncpg

**Caching:**
- **Redis 7** — `redis:7-alpine` image; `REDIS_URL` configured; **only usage is the non-blocking health ping** — no cache/rate-limit/session code

**Vector store:** pgvector (384-dim) in PostgreSQL. Config: `EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2`, pinned revision `e4bb823e5956b6277b069d276b978c48a73507c7`, `EMBEDDING_DIMENSION=384`, `EMBEDDING_MAX_SEQ_LENGTH=256` ([`backend/app/core/config.py`](backend/app/core/config.py)). **No embedding generation code exists** (no sentence-transformers dependency; column never populated).

## AI / ML

**All model execution is SIMULATED** — the three provider classes return canned/truncated strings; no model weights are loaded (no `transformers`, `sentence-transformers`, or `spaCy` in `requirements.txt`).

**Provider abstraction ([`backend/app/providers/`](backend/app/providers/)):**
- `base.py` — `LLMProvider` with capability enum (SUMMARIZE, CLASSIFY, REASON, GENERATE_ACTIONS, STRUCTURED_OUTPUT) and `DataClassification` enum (PUBLIC, SYNTHETIC, CONFIDENTIAL, INTERNAL, PATIENT_IDENTIFIABLE, UNKNOWN)
- `gemma.py` — `GemmaProvider` (`google/gemma-3-4b-it` from `LOCAL_LLM_MODEL`); **simulated** — hardcoded output, `primary_function=MEDICAL_AFFAIRS`; declares all five capabilities
- `grok.py` — `GrokProvider` (`grok-beta`); **simulated inference but real mandatory privacy gate** (`validate_privacy_gate`: only PUBLIC/SYNTHETIC pass; requires `ENABLE_GROK_FALLBACK=true` + `XAI_API_KEY`)
- `degraded.py` — `DegradedProvider` (`facebook/bart-large-cnn`); **simulated** — naive 300-char truncation, `mode="degraded_factual"`, `reasoning_available=False`, `actions_available=False`
- `factory.py` — `ProviderFactory.execute_task()` fallback chain **local Gemma → Grok (gated) → BART degraded**, driven by `settings.LLM_PROVIDER` (`local`|`xai`|`auto`)

**LLM/embedding configuration (`backend/app/core/config.py`):**
- `LLM_PROVIDER=local`, `LOCAL_LLM_MODEL=google/gemma-3-4b-it`, `LLM_DEVICE=auto` (compose overrides `cpu` or `cuda:0` for the gpu profile), `LLM_DTYPE=int4`, `MAX_CONTEXT_TOKENS=2048`, `MAX_OUTPUT_TOKENS=512`
- `ENABLE_GROK_FALLBACK=false`, `XAI_API_KEY` optional
- Every provider response embeds `ModelMetadataSchema` (provider, mode, model, fallback flags, latency) for traceability

**NLP services:**
- `services/redteam.py` — `RedTeamNLIService`; **mock pairwise contradiction check** (same-asset + different-type rule), in-memory cache, candidate cap 10, HIGH/CRITICAL priority gating. Prescribed `facebook/bart-large-mnli` **not implemented**
- `services/deduplication.py` — real deterministic fingerprinting (`pmid:`/`nct:`/`reg:` prefixes, else `hash:sha256` of normalized title|publisher|date|company|asset) + 256-token chunking for the embedding model's max sequence length

## Workflow Orchestration

- **LangGraph 10-node pipeline: NOT implemented** — no `langgraph` dependency, no `app/workflows/` module. Only orchestration artifacts: abstract `SourceConnector` base ([`backend/app/connectors/base.py`](backend/app/connectors/base.py)) and the `pipeline_runs` table schema
- **Scheduler: NOT implemented** — no APScheduler, no Celery (prescribed: single in-process APScheduler, Master Plan §14.9); PostgreSQL advisory-lock helpers in [`backend/app/db/session.py`](backend/app/db/session.py) anticipate single-execution scheduling but nothing calls them

## DevOps / Infra

**Containerization ([`docker-compose.yml`](docker-compose.yml)):**
- Services: `postgres` (pgvector/pgvector:pg16 + healthcheck), `redis` (redis:7-alpine + healthcheck), `backend` (port 8000), `backend-gpu` (profile `gpu`, `LLM_DEVICE=cuda:0`, nvidia device reservation), `frontend` (port 3000, `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`)
- Volumes: `pgdata`, `redisdata`, `models_cache` (mounted at `/app/models` in backend)
- **⚠ Dockerfiles missing:** compose references `backend/Dockerfile` and `frontend/Dockerfile` but **neither exists** — `docker compose up --build` will fail
- Config mounted read-only: `./config:/app/config:ro`

**CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)):**
- Ubuntu runner, Python 3.11, `pip install -r backend/requirements.txt`, runs `tests/test_foundation.py` (plain async script — **no pytest**), verifies OpenAPI↔TypeScript contract sync via `scripts/export_openapi.py` + `git diff --exit-code` against `frontend/src/types/api.ts`

**Contract generation:**
- [`scripts/export_openapi.py`](scripts/export_openapi.py) — dumps `contracts/openapi.json` and writes `frontend/src/types/api.ts` (content is a hardcoded template string, not derived from the schema)

**Tests:**
- [`tests/test_foundation.py`](tests/test_foundation.py) — 3 checks: DomainConfig loading, dedup fingerprint + chunking, provider fallback chain (Gemma reason + degraded BART). Runnable: `python tests/test_foundation.py`

**Environment:**
- `.env.example` committed; `.env` gitignored (never read — see <forbidden_files>); root `.gitignore` also ignores `models/` and `.cache/` (local LLM weights)
- Frontend lockfile `pnpm-lock.yaml` (lockfileVersion 9.0); **no Python lockfile** (requirements.txt is floor-pinned only)

## Package Manager & Tooling

- **Frontend: pnpm** — `frontend/pnpm-lock.yaml` (lockfileVersion 9.0) present; includes a `pnpm.overrides` pinning `hono: 4.12.25` (transitive, from the shadcn CLI dep tree). Scripts: `dev` / `build` / `start` / `lint`
- **Backend: pip** — unpinned floor constraints in `backend/requirements.txt`; no venv/poetry/uv config committed
- **Code quality tooling:** ESLint 10 + `eslint-config-next` 16 declared but **no config file**; Prettier/Biome not configured; TypeScript `strict: true` with build errors ignored (`next.config.mjs`)

## Not Used (explicitly avoided or absent)

- **LangGraph** — prescribed by Master Plan but **absent from code**
- **Weaviate** — explicitly replaced by pgvector (Master Plan)
- **OpenAI / Claude APIs** — explicitly not used; optional hosted reasoning is xAI Grok only, privacy-gated
- **Celery** — deliberately avoided (Master Plan §14.9); scheduler not yet implemented
- **tenacity** — prescribed for retry (3 retries 2s/4s/8s) but **not in requirements.txt**
- **spaCy, transformers, sentence-transformers** — prescribed for NER/NLI/embeddings but **not in requirements.txt** (models simulated only)
- **TanStack Query, zod** — prescribed for the frontend (CLAUDE.md) but **absent** from `frontend/package.json`; data layer is mock-only
- **praw (Reddit), feedparser (EMA RSS)** — prescribed data-source clients, **absent**

---

*Stack analysis: 2026-08-13*
