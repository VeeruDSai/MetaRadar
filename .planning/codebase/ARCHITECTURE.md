<!-- refreshed: 2026-08-13 -->
# Architecture

**Analysis Date:** 2026-08-13

> **Current state:** Foundation-stage backend + a substantially built-out Next.js frontend. The backend (`backend/app/`) is a FastAPI skeleton with 4 health endpoints, a 16-table ORM schema + Alembic migration, a provider-agnostic (but simulated) LLM layer, and seed services. The frontend (`frontend/`) is a v0.app-generated synthetic decision-intelligence workspace: an App Router route tree driven by one dynamic `[section]` route, a large client-side component module (`components/metaradar.tsx`), a mock-only data layer (`lib/api.ts` + `lib/mock-data.ts`), and a custom CSS design system (`app/globals.css`). The 10-node LangGraph workflow, live source connectors, scheduler, and intelligence services remain **specified but unimplemented** — the canonical design in [`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md) §4 is authoritative for what will be built.

## System Overview

### Implemented today

```text
┌────────────────────────────────────────────────────────────────────┐
│            Next.js 16.3 frontend — synthetic workspace              │
│  frontend/app/layout.tsx · app/page.tsx (→ /dashboard)             │
│  app/[section]/page.tsx  (single dynamic route → 8 pages)          │
│  components/metaradar.tsx  ('use client' — Shell + page components)│
│  lib/api.ts + lib/mock-data.ts  (MOCK data — no live fetch)        │
└──────────────────────────────┬─────────────────────────────────────┘
                               │   /api/v1 (REST, JSON) — CORS :3000
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                  FastAPI backend skeleton (v5.1.0)                  │
│  backend/app/main.py — app + CORS + lifespan                        │
│  backend/app/api/v1/endpoints/health.py — health|ready|models|      │
│    connectors                                                       │
│  backend/app/core/config.py — pydantic-settings Settings            │
│  backend/app/core/domain_config.py — YAML config loader             │
│  backend/app/db/session.py — async SQLAlchemy engine + links        │
│  backend/app/models/__init__.py — 16-table ORM schema               │
│  backend/app/services/deduplication.py · redteam.py (seeds)         │
│  backend/app/providers/ — base | gemma | grok | degraded | factory  │
│  backend/app/connectors/base.py — SourceConnector interface         │
└──────────┬──────────────────────────┬──────────────────────────────┘
           │ asyncpg                  │ redis.asyncio
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│ PostgreSQL 16 +      │   │ Redis 7              │
│ pgvector (pg16 image)│   │ (docker-compose.yml) │
│ + HNSW vector index  │   │ /0 db                │
└──────────────────────┘   └──────────────────────┘
```

**Note:** `docker-compose.yml` also declares `backend` / `backend-gpu` / `frontend` services that `build:` from `backend/Dockerfile` / `frontend/Dockerfile` — **neither Dockerfile exists yet**, so `docker compose up --build` cannot currently succeed. The frontend currently runs standalone via `next dev` with mock data; the backend via `uvicorn app.main:app`.

### Target (prescribed — Master Plan §4, once implemented)

```text
                    PUBLIC EXTERNAL SIGNALS
         LIVE: NCBI PubMed (E-utilities) · NewsAPI · ClinicalTrials.gov
         ADAPTER-READY: FDA · EMA · Congress (ASH/ISTH/WFH/EHA) · Reddit
         SYNTHETIC-DEMO: 500 curated labelled haemophilia signals
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│          10-NODE LANGGRAPH WORKFLOW (backend/app/workflows/)     │
│  ingest → validate → nlp_extract → ontology_enrich → confluence  │
│  → lifecycle → redteam → missing_signal → synthesize → calibrate │
│  (explicit termination: node_calibrate → END)                    │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│          FOUR-QUESTION DECISION INTERFACE (Next.js 16)           │
│  Q1 What changed? · Q2 Why it matters · Q3 Which function?       │
│  Q4 What action? + evidence chain + FACT/INTERPRETATION/         │
│  SPECULATION labels                                              │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  PostgreSQL 16 + pgvector (relational + 384-dim vector search)   │
│  Redis 7 (2h-TTL hot cache) · APScheduler (single, in-process)   │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Backend (implemented foundation)

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app | App factory, lifespan (domain config load), CORS, router wiring | `backend/app/main.py` |
| Settings | All env-driven configuration (DB, Redis, LLM provider, embeddings, CORS) | `backend/app/core/config.py` |
| DomainConfig | Loads + caches `config/haemophilia.yaml` into typed Pydantic models | `backend/app/core/domain_config.py` |
| Async DB session | Engine pool, session factory, `get_db` dependency, PostgreSQL advisory locks for single-execution scheduling | `backend/app/db/session.py` |
| ORM models | 16-table canonical entity schema (pipeline_runs → audit_log), pgvector embedded column | `backend/app/models/__init__.py` |
| Pydantic schemas | API response contracts (Health*, Signal, Development, PipelineRun, ScoreBreakdown, ModelMetadata) | `backend/app/schemas/__init__.py` |
| Health endpoints | Liveness `/health`, readiness `/ready` (DB mandatory + non-blocking Redis), model/provider status `/models`, connector status `/connectors` | `backend/app/api/v1/endpoints/health.py` |
| Deduplication service | Deterministic fingerprints (pmid/nct/reg/hash), embedding-safe text chunking, `ON CONFLICT` upsert | `backend/app/services/deduplication.py` |
| Red-Team service | Priority-gated pairwise contradiction scan (currently mock rule-based; NLI model planned) | `backend/app/services/redteam.py` |
| LLM provider layer | `LLMProvider` interface + capability matrix + data classification; Gemma (local) / Grok (hosted, privacy-gated) / BART degraded providers + `ProviderFactory` fallback chain — **all three currently return simulated output** | `backend/app/providers/*.py` |
| Connector interface | Shared `SourceConnector` base + `RawSignalPayload`/`ConnectorStatus` contracts; concrete adapters not yet implemented | `backend/app/connectors/base.py` |
| Alembic migration | Initial v5.1 schema: 16 tables, `vector`/`pg_trgm` extensions, partial unique indexes, HNSW index | `backend/alembic/versions/001_initial_v51_schema.py` |

### Frontend (implemented — built since the last map)

| Component | Responsibility | File |
|-----------|----------------|------|
| Root layout | HTML shell, metadata/icons, theme color, Vercel Analytics (prod only) | `frontend/app/layout.tsx` |
| Root page | `redirect('/dashboard')` | `frontend/app/page.tsx` |
| Dynamic section route | Resolves any single-segment path to page component inside `Shell` | `frontend/app/[section]/page.tsx` |
| Shell | App chrome: sidebar nav, topbar, theme toggle, footer (`'use client'`) | `frontend/components/metaradar.tsx` |
| DashboardPage | KPI grid, confluence radar, trend chart, priority signals + drawer | `frontend/components/metaradar.tsx` |
| SignalsPage | Severity-filterable signal list + detail drawer | `frontend/components/metaradar.tsx` |
| IntelligencePage | "Ask Athena" prompt UI (mock conversational synthesis) | `frontend/components/metaradar.tsx` |
| GenericPage | Placeholder for developments/functions/calibrate/sources/settings | `frontend/components/metaradar.tsx` |
| shadcn Button | Base UI button with CVA variants (currently unused by the workspace UI) | `frontend/components/ui/button.tsx` |
| Mock API layer | All data functions return `delay()`-wrapped mock fixtures from `lib/mock-data.ts` — no `fetch`/HTTP anywhere | `frontend/lib/api.ts` |
| Mock fixtures | Signal/overview/source datasets for the demo | `frontend/lib/mock-data.ts` |
| UI-domain types | Hand-written TS types for the workspace (`Signal`, `DashboardOverview`, `AthenaResponse`, …) | `frontend/types/api.ts` |
| Contract types | **Generated** mirror of the FastAPI OpenAPI schema (differs from the UI-domain types) | `frontend/src/types/api.ts` |
| Stale skeleton page | Earlier static connectors page (superseded by the `app/` tree; retains `bento-card` class name) | `frontend/src/app/sources/page.tsx` |
| Design system | Tailwind 4 + full custom CSS-variable design token system w/ light/dark themes, radar/KPI/bento component classes | `frontend/app/globals.css` |

### Shared / infrastructure

| Component | Responsibility | File |
|-----------|----------------|------|
| Domain config data | Haemophilia diseases, 7 assets, 7 signal types, 9 lifecycle stages, 6 functions, baseline routing matrix | `config/haemophilia.yaml` |
| Contract export | Generates `contracts/openapi.json` + `frontend/src/types/api.ts` from the FastAPI app (static TS template, not schema-driven codegen) | `scripts/export_openapi.py` |
| Foundation tests | Script-based verification of DomainConfig, dedup fingerprinting, provider fallback chain | `tests/test_foundation.py` |
| CI | Python 3.11 + requirements install, runs foundation tests, enforces contract sync via `git diff --exit-code` on `frontend/src/types/api.ts` | `.github/workflows/ci.yml` |
| Docker Compose | postgres (pgvector/pg16) · redis (7-alpine) · backend · frontend + optional `backend-gpu` profile; healthchecks & dependencies; **refers to two Dockerfiles that do not exist yet** | `docker-compose.yml` |

### Planned (prescribed, not yet present)

| Component | Responsibility | Planned location per specs |
|-----------|----------------|------|
| LangGraph workflow | 10-node StateGraph with typed `IntelligenceState`, reducers for accumulating fields, `node_calibrate → END` | `backend/app/workflows/` + node files |
| Source connectors | PubMed/NewsAPI/ClinicalTrials.gov live adapters; FDA/EMA/Congress/Reddit adapter-ready; synthetic fallback; `tenacity` retries (2s/4s/8s) | `backend/app/connectors/<source>.py` |
| APScheduler | Single in-process scheduler: 2h fetch, nightly digest, on-demand recalibration (Celery deliberately NOT used) | in-process inside FastAPI |
| Intelligence services | Confluence detection (48h/≥3 types), lifecycle FSM tracker, missing-signal + watch rules, StakeholderCalibrationService (HITL) | `backend/app/services/*` |
| spaCy NER + ontology enrichment | `en_core_sci_md` entity extraction; haemophilia ontology mapping | `backend/app/nlp/`, `backend/app/ontology/` |
| Real backend wiring in the UI | Replace `lib/api.ts` mock layer with a fetch client against `/api/v1` (base URL `NEXT_PUBLIC_API_BASE_URL`, already in `docker-compose.yml`) | `frontend/lib/api.ts` |
| Dockerfiles | `backend/Dockerfile` and `frontend/Dockerfile` (referenced by compose, not yet authored) | `backend/Dockerfile`, `frontend/Dockerfile` |

## Pattern Overview

**Overall:** "Evidence-story" signal pipeline — public signals are treated as *evidence events belonging to developing stories*, orchestrated by a stateful LangGraph workflow (Master Plan §4). The implemented foundation encodes the core data model (bronze raw layer, deterministic fingerprints, immutable baseline vs calibrated routing) and the provider-agnostic reasoning contract. The implemented UI is a **synthetic demo surface**: it demonstrates the intended Four-Question UX using mock data and deliberately labels itself "DEMO DATA" (`frontend/components/metaradar.tsx`, `synthetic-banner`).

**Key Characteristics (verified in code):**

**Backend:**
- **Raw-signal replay:** `raw_signals_bronze` persists `raw_payload` verbatim with `content_hash` and `connector_version` (`backend/app/models/__init__.py:125`)
- **Deterministic dedup before any AI:** `generate_fingerprint()` prefers stable IDs (pmid/nct/reg), falls back to normalized title+publisher+date+company+asset SHA-256 (`backend/app/services/deduplication.py:11`)
- **Idempotent persistence:** `upsert_signal()` uses PostgreSQL `ON CONFLICT DO UPDATE` on the unique fingerprint (`backend/app/services/deduplication.py:52`)
- **Immutable baseline vs calibrated output:** `signal_routing` stores `baseline_*` (immutable AI outputs) alongside `calibrated_*` fields so calibration is auditable (`backend/app/models/__init__.py:204`)
- **Provider-agnostic reasoning:** `ProviderFactory.execute_task()` resolves `Gemma → Grok (privacy-gated) → BART degraded` based on required `ProviderCapability` (`backend/app/providers/factory.py:18`); all providers currently simulate output
- **Honest degraded mode:** `DegradedProvider` supports only `SUMMARIZE`; `reasoning_available=false` and `actions_available=false` propagate via `ModelMetadataSchema` (`backend/app/providers/degraded.py`)
- **WORM audit:** `audit_log` table is append-only by design (`CREATE | UPDATE | ROUTE | CALIBRATE` actions) (`backend/app/models/__init__.py:250`)
- **One engine → six functions:** baseline routing matrix in `config/haemophilia.yaml:154` maps signal_types to primary/secondary functions

**Frontend:**
- **Single dynamic route:** all top-level pages (`/dashboard`, `/signals`, `/intelligence`, `/developments`, `/functions`, `/calibrate`, `/sources`, `/settings`) are served by one server component `app/[section]/page.tsx` that switches on the `section` param and wraps the result in `Shell` (`frontend/app/[section]/page.tsx:11`)
- **Client-heavy page set:** page components (`DashboardPage`, `SignalsPage`, `IntelligencePage`, `GenericPage`) are `'use client'` components inside `components/metaradar.tsx` (line 1); only `layout.tsx` and `[section]/page.tsx` remain server components
- **Mock-first data layer:** `lib/api.ts` exposes an async API (`getOverview`, `getSignals`, `getTrends`, `getHealth`, `getSources`, `askAthena`) but every function resolves to `delay(<mock-value>)` — there is no HTTP client, no TanStack Query, and no `NEXT_PUBLIC_API_BASE_URL` usage in code (the env var exists only in `docker-compose.yml`)
- **Local component state:** data fetching is `useState` + `useEffect` per page (`frontend/components/metaradar.tsx:48-49`); no SWR/React Query/context/store
- **Single-file components:** `metaradar.tsx` contains the Shell, 4 page components, and ~10 internal presentational components (Badge, Card, SectionTitle, KPI, Radar, SignalRow, TrendChart, SignalDrawer, Loading) in one export file
- **Two type systems:** the UI uses hand-written domain types in `frontend/types/api.ts`; the generated backend contract lives in `frontend/src/types/api.ts`. The two are structurally different (e.g. UI `Signal` has `severity/status/sources/stakeholders`; contract `Signal` has `signal_id/signal_type/score_breakdown`). CI only guards the generated file
- **Design system via CSS variables:** `app/globals.css` defines `:root`/`.dark` token sets (`--background`, `--signal`, `--priority-critical`, …) consumed by utility classes (`.panel`, `.badge`, `.signal-row`, `.radar`, `.bento-grid`); Tailwind 4 `@theme inline` maps a subset (`@apply`-style tokens); `tw-animate-css` + `shadcn/tailwind.css` imported at top
- **Dark-mode via class toggle:** `Shell` flips `document.documentElement.classList.toggle('dark', dark)` (`frontend/components/metaradar.tsx:23`), paired with a `@custom-variant dark (&:is(.dark *))` in CSS

## Layers

**Frontend layer (implemented):**
- Purpose: Synthetic decision-intelligence workspace — dashboard, signals, Ask Athena, placeholder sections
- Location: `frontend/`
- Contains (current): `app/` (layout.tsx, page.tsx, `[section]/page.tsx`, globals.css), `components/metaradar.tsx`, `components/ui/button.tsx`, `lib/api.ts`, `lib/mock-data.ts`, `lib/utils.ts`, `types/api.ts`, `public/` (icons + placeholders)
- Data access: none (mock); planned: REST client over `/api/v1` with `NEXT_PUBLIC_API_BASE_URL`
- Used by: stakeholder personas (Medical Affairs, Regulatory, etc.) via simulated workspace

**API layer:**
- Purpose: Expose pipeline results + health/diagnostics
- Location: `backend/app/api/v1/endpoints/`
- Contains: `health.py` (4 GET endpoints). Versioned under `/api/v1` (`API_V1_STR` in `backend/app/core/config.py:15`)
- Depends on: `core/config.py`, `db/session.py`, `schemas/`
- Used by: Docker healthchecks, CI, frontend (planned)

**Domain/Config layer:**
- Purpose: Typed, env-driven and YAML-driven configuration
- Location: `backend/app/core/`
- Contains: `config.py` (Settings), `domain_config.py` (DomainConfig loader with module-level cache)
- Used by: all layers via `from app.core.config import settings`

**Persistence layer:**
- Purpose: Raw replay, normalized signals, entities, routing/calibration, audit
- Location: PostgreSQL 16 + pgvector (`docker-compose.yml`), ORM in `backend/app/models/__init__.py`, async session in `backend/app/db/session.py`
- Contains: 16 tables; 384-dim `Vector` column + HNSW cosine index on `signals.embedding` (`001_initial_v51_schema.py:195`)
- Used by: all backend layers

**Provider layer (reasoning/NLP):**
- Purpose: Model-agnostic intelligence generation
- Location: `backend/app/providers/`
- Contains: `LLMProvider` base + capability/data-classification enums, Gemma/Grok/Degraded implementations, `ProviderFactory`
- Depends on: `core/config.py`, `schemas/`
- Used by (planned): `node_synthesize`, Ask Athena

## Data Flow

### Primary Signal Path (prescribed — INGEST → VALIDATE → UNDERSTAND → ANALYZE → SYNTHESIZE → CALIBRATE → BRIEF)

1. **INGEST** — `node_ingest` runs all enabled `SourceConnector` adapters via `httpx` async clients; every raw payload persisted verbatim to `raw_signals_bronze` before transformation (Master Plan §4.1). *Seed:* connector contract in `backend/app/connectors/base.py`.
2. **VALIDATE** — `node_validate` filters short text (<50 chars), non-English, out-of-scope; deterministic dedup + source-independence classification; PII/PHI scrub before persistence. *Seed:* `backend/app/services/deduplication.py`.
3. **UNDERSTAND** — `node_nlp_extract` (spaCy `en_core_sci_md` NER) → `node_ontology_enrich` (maps entities against the haemophilia ontology).
4. **ANALYZE** — four parallel intelligence mechanisms: `node_confluence` (48h/≥3 types; NEW EVIDENCE vs NEW DEVELOPMENT), `node_lifecycle` (FSM over the 9 canonical stages), `node_redteam` (pairwise NLI; *seed:* `backend/app/services/redteam.py`), `node_missing_signal` (FSM lag + stakeholder WATCH rules → `watch_items`).
5. **SYNTHESIZE** — `node_synthesize`: evidence-sufficiency gate → F-I-S labels → Four-Question brief via the provider-agnostic reasoning layer. *Seed:* `backend/app/providers/factory.py`.
6. **CALIBRATE** — `node_calibrate`: `StakeholderCalibrationService` updates function-scoring weights from feedback; explicit termination `node_calibrate → END`.
7. **BRIEF** — role-specific formatted output: `primary_function` + `secondary_functions[]` + `routing_reason`, previewed via the Four-Question framework in the UI.

### Runtime flow as implemented today

**Backend:**
1. Client hits `GET /` or `GET /api/v1/health` → `backend/app/main.py:53` / `backend/app/api/v1/endpoints/health.py`
2. `GET /api/v1/health/ready` runs `SELECT 1` on postgres (mandatory) and a non-blocking Redis ping → `ready|degraded` (`backend/app/api/v1/endpoints/health.py:22`)
3. `GET /api/v1/models` and `/connectors` report configured provider/connector state from `settings` + a hardcoded source roster (`backend/app/api/v1/endpoints/health.py:54`)
4. `scripts/export_openapi.py` regenerates `contracts/openapi.json` + `frontend/src/types/api.ts`; CI fails if the latter drifts (`.github/workflows/ci.yml:30`)

**Frontend (mock, no backend dependency):**
1. `GET /` → `app/page.tsx` `redirect('/dashboard')` (`frontend/app/page.tsx:4`)
2. `/dashboard` matches `app/[section]/page.tsx`; `section === 'dashboard'` renders `<Shell><DashboardPage/></Shell>` (`frontend/app/[section]/page.tsx:14`)
3. `DashboardPage` mounts → `useEffect` calls `getOverview()` → `lib/api.ts` resolves `delay(overview)` from `lib/mock-data.ts` after ~360 ms → renders KPIs, radar, trend chart, top signals (`frontend/components/metaradar.tsx:47-49`)
4. Selecting a signal opens `SignalDrawer` (framer-motion slide-in) rendering the Four-Question sections with mock evidence/provenance
5. `/signals` → `SignalsPage` filters the same mock array by severity (`frontend/components/metaradar.tsx:55`)
6. `/intelligence` → `IntelligencePage` calls `askAthena(prompt)` which resolves a hardcoded template answer + 87% confidence (`frontend/lib/api.ts:10`)
7. All other sections render `GenericPage` placeholders (`frontend/app/[section]/page.tsx:17`)

**State Management:**
- Authoritative state: PostgreSQL (async sessions via `get_db` in `backend/app/db/session.py:30`)
- Frontend state: ephemeral React local state (`useState`/`useEffect`); no global store
- Cache (planned): Redis 2h-TTL hot cache (`REDIS_URL` in `backend/app/core/config.py:20`)
- Pipeline state (planned): LangGraph `IntelligenceState` TypedDict with typed reducers (SDD — `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`)

## LangGraph Workflow (planned — node by node)

**Reality check:** no `backend/app/workflows/` package exists and `langgraph` is not in `backend/requirements.txt`. The workflow below is fully specified (Master Plan §4, SDD §2.3) but **prescribed, not implemented**.

| Node | Reads (state) | Writes (state) | Persists to | Notes |
|------|--------------|----------------|-------------|-------|
| `ingest` | — | `raw_signals` | `raw_signals_bronze` | Parallel connectors; append reducer; contract seeded in `backend/app/connectors/base.py` |
| `validate` | `raw_signals` | `validated_signals` | `signals` (pre-NLP) | quality, dedup, source-independence, PII scrub; dedup seeded in `backend/app/services/deduplication.py` |
| `nlp_extract` | `validated_signals` | `extracted_entities` | — | spaCy `en_core_sci_md` |
| `ontology_enrich` | `extracted_entities` | `ontology_entities` | — | maps to haemophilia ontology |
| `confluence` | `ontology_entities` | `confluent_stories` | `developments`, `confluences` | 48h/≥3 types; dev-link decision |
| `lifecycle` | `confluent_stories` | `lifecycle_events` | `lifecycle_events` | FSM advance; 9 stages from `config/haemophilia.yaml:124` |
| `redteam` | `lifecycle_events` | `redteam_flags` | — | pairwise NLI (BART MNLI); seed: `backend/app/services/redteam.py` |
| `missing_signal` | `lifecycle_events` | `missing_signals` | `watch_items` | FSM lag rules + stakeholder watch rules |
| `synthesize` | pooled evidence | `role_briefs` | `signal_routing` (baseline) + `evidence` | evidence-sufficiency gate → F-I-S labels → Four-Question brief via `ProviderFactory` |
| `calibrate` | `role_briefs` + feedback | `model_metadata`, `errors` | `signal_routing` (calibrated), `calibration_feedback`, `audit_log` | HITL weight update; **explicit `node_calibrate → END`** |

Graph shape: linear chain `ingest → validate → nlp → confluence → lifecycle → red_team → missing_signal → synthesize → brief → calibrate`, `set_entry_point("ingest")`, `set_finish_point("calibrate")` (SDD §2.3). Failure semantics: per-node error boundaries, `recursion_limit` configured, one node's failure does not kill the pipeline.

## Backend API Design

**Framework:** FastAPI 0.110+ (`backend/requirements.txt:1`), ASGI via uvicorn.

**Versioning:** All endpoints under `/api/v1` (`API_V1_STR` in `backend/app/core/config.py:15`; routers mounted with `prefix=f"{settings.API_V1_STR}/..."` in `backend/app/main.py:50`). OpenAPI schema served at `/api/v1/openapi.json`.

**Router structure (current):**
- `backend/app/api/v1/endpoints/health.py` — `APIRouter()` with 4 GET endpoints, mounted at `/api/v1/health` with tag `"Health & Diagnostics"`
- No other routers registered in `backend/app/main.py:50`

**Auth:** None implemented. The current app exposes read-only health endpoints with no auth.

**CORS:** Configurable via `CORS_ORIGINS` env (default `http://localhost:3000`); middleware added only when non-empty (`backend/app/main.py:40`).

**Response contracts:** All handlers declared with `response_model` from `backend/app/schemas/__init__.py` (HealthResponse, HealthReadyResponse, HealthModelsResponse, HealthConnectorsResponse).

**Contract sync:** `scripts/export_openapi.py` imports `app.main.app`, dumps `openapi.json` to `contracts/`, and overwrites `frontend/src/types/api.ts` with a **static template** mirror (kept in sync by `.github/workflows/ci.yml` via `git diff --exit-code`). Note: the TS generator is a fixed f-string template, not schema-driven codegen — adding an endpoint requires editing the template in `scripts/export_openapi.py:30-135`.

**Planned endpoints (per SDD; not yet implemented):** `/api/v1/signals` (role-filtered feed), `/api/v1/feedback` (stakeholder calibration), plus ingestion/status/intelligence endpoints.

## Frontend Architecture

**Framework:** Next.js **16.3.0** App Router (not 15 — the previous map's version is stale), React 19, TypeScript 5.7.3 (`frontend/package.json:11-36`). Tailwind **4** via `@tailwindcss/postcss` (`frontend/postcss.config.mjs`). Package manager: **pnpm** (`frontend/pnpm-lock.yaml`). Vercel Analytics (`@vercel/analytics/next`) mounted in production (`frontend/app/layout.tsx:45`).

**Bare vs shipped config note:** `next.config.mjs` sets `typescript.ignoreBuildErrors: true` and `images.unoptimized: true` — type errors are not build blockers, which weakens the "contract discipline" story (the UI's hand-written `types/api.ts` is never type-checked against the generated contract). `package.json` is still named `"my-project"` (v0.app artifact) and `lint` runs `eslint .` with no eslint config file present.

**Route tree (App Router):**
- `frontend/app/layout.tsx` — root layout, metadata (generator: `v0.app`), theme color via `viewport`
- `frontend/app/page.tsx` — `redirect('/dashboard')`
- `frontend/app/[section]/page.tsx` — **single dynamic segment** resolving: `dashboard → DashboardPage`, `signals → SignalsPage`, `intelligence → IntelligencePage`, everything else → `GenericPage` with per-section copy from the `pages` map (`developments`, `functions`, `calibrate`, `sources`, `settings`)
- `frontend/app/globals.css` — design system (see below)

**Components:**
- `frontend/components/metaradar.tsx` — single 'use client' module. Exports: `Shell`, `DashboardPage`, `SignalsPage`, `IntelligencePage`, `GenericPage`. Internal: `Badge` (tone variants), `Card` (.panel), `SectionTitle`, `KPI`, `Radar` (animated confluence sweep), `SignalRow`, `TrendChart` (Recharts AreaChart), `SignalDrawer` (framer-motion), `Loading`. Navigation definition (`nav` + `secondary` arrays, lines 12-15) drives both sidebar and breadcrumbs.
- `frontend/components/ui/button.tsx` — shadcn/Base UI Button (CVA variants, sizes) — scaffolding from `components.json` (base-nova style); **not imported anywhere in `metaradar.tsx`** (the UI uses custom `.icon-button`/`.search-button`/`.theme-toggle` CSS classes instead)

**Data fetching model:** none against the backend. All calls flow: `component useEffect/event → lib/api.ts function → delay() → lib/mock-data.ts fixture`. TanStack Query is **not installed** (previous map claimed it was in `package.json` — the rebuilt dependencies no longer include `@tanstack/react-query`). `NEXT_PUBLIC_API_BASE_URL` is defined in `docker-compose.yml:105` but unused by code. When real wiring lands, the natural seam is to replace `lib/api.ts` sync-with-delay bodies with `fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/...`)`.

**State management:** local `useState` per page + `useMemo` (severity filtering on `SignalsPage`). `Shell` owns `open` (mobile drawer) and `dark` (theme) state and toggles the `.dark` class on `<html>` via `useEffect` (`frontend/components/metaradar.tsx:22-23`).

**Type sharing (two systems):**
1. `frontend/types/api.ts` — hand-written **UI-domain model** (severity/status/scoring/confluence vocabulary). Imported by `metaradar.tsx`, `lib/api.ts`, `lib/mock-data.ts`.
2. `frontend/src/types/api.ts` — **generated backend contract** (snake_case, `signal_id`, `HealthReadyResponse`, etc). Imported by nothing in the current UI. CI guards it.
This split means the OpenAPI contract and the rendered data model can (and do) drift without any test or build failure.

**Styling system:** `app/globals.css` imports `tailwindcss`, `tw-animate-css`, and `shadcn/tailwind.css`; declares `@custom-variant dark`; defines `:root` and `.dark` CSS variable palettes (background/surface/foreground/border/primary/accent/success/warning/danger + priority severity tokens); utility classes generally referenced directly (`.app-shell`, `.sidebar`, `.kpi-grid`, `.bento-grid`, `.signal-list`, `.drawer-backdrop`, `@keyframes sweep`, responsive breakpoints at 900px/560px, `prefers-reduced-motion`). Tailwind utility classes are also used (`flex`, `muted max-w-xs text-right`, etc.) — a hybrid.

## Contract-Sync Between Frontend and Backend

**Single source of truth:** the FastAPI app (`app.main.app`) → `scripts/export_openapi.py`:
1. Writes `contracts/openapi.json` (OpenAPI 3.1 snapshot)
2. Writes `frontend/src/types/api.ts` from a static f-string template (banner: "Auto-generated from FastAPI OpenAPI Schema — DO NOT EDIT DIRECTLY")

**Enforcement:** `.github/workflows/ci.yml:30-32` runs `python scripts/export_openapi.py` then `git diff --exit-code frontend/src/types/api.ts` — drift fails CI. Only the frontend file is diffed; `contracts/openapi.json` is not independently checked.

**Current contract surface:** exactly 5 paths (`/`, `/api/v1/health`, `/api/v1/health/ready`, `/api/v1/health/models`, `/api/v1/health/connectors`) and 5 schemas (`HealthResponse`, `HealthReadyResponse`, `HealthModelsResponse`, `HealthConnectorsResponse`, `ConnectorHealthStatus`) — `contracts/openapi.json`.

**Known friction:** the generated contract types are not consumed by the executing UI. The hand-written `frontend/types/api.ts` (severity/status/`DashboardOverview`) is the de-facto contract for the frontend, so "contract-first" holds for CI artifacts only, not for the rendered application. The `Signal` types in the two files are entirely different shapes.

## Database Schema Overview

ORM source of truth: `backend/app/models/__init__.py` (16 models); migration: `backend/alembic/versions/001_initial_v51_schema.py` (creates `vector` + `pg_trgm` extensions, 16 tables, partial unique indexes, HNSW index).

| Group | Tables | Purpose |
|-------|--------|---------|
| Pipeline bookkeeping | `pipeline_runs` | run status, trigger (scheduled/manual/test), signal counters, error summary JSONB |
| Source catalog | `sources` | source_id PK, freshness_class (real_time/near_real_time/delayed/batch/adapter_ready/synthetic), syndication_group, quota, last_success/last_error |
| Domain entities | `companies`, `assets`, `trials`, `developments`, `events` | canonical entity layer; assets FK→companies; developments FK→assets/companies; events/lifecycle_events FK→developments |
| Evidence & raw layer | `raw_signals_bronze`, `evidence` | verbatim replay (`raw_payload` JSONB, content_hash, unique(source_id, external_id)); evidence excerpts FK→raw signal |
| Normalized signals | `signals` | fingerprint + pmid/nct_id/regulatory_id/canonical_url partial unique indexes; facts/interpretation/speculation JSONB; priority; score_breakdown; **pgvector `embedding` (384-dim) + HNSW index**; model/scoring/prompt versioning columns |
| Routing & calibration | `signal_routing`, `calibration_feedback` | immutable `baseline_*` vs `calibrated_*`; feedback ratings 1–5 with action_appropriate |
| Watch & audit | `watch_items`, `audit_log` | stakeholder watch rules with status vocabulary; append-only audit (entity_name/entity_id/action/performed_by/details JSONB) |

**Postgres extensions enabled:** `vector` (pgvector), `pg_trgm`. **Vector index:** HNSW cosine ops, `m=16, ef_construction=64` on `signals.embedding` (`001_initial_v51_schema.py:195-200`).

**Connection:** async engine with `pool_size=10, max_overflow=20, pool_pre_ping=True` (`backend/app/db/session.py:10`); advisory lock helpers `try_advisory_lock`/`release_advisory_lock` ready for scheduler single-execution protection.

**Migration tooling gap:** `backend/alembic/` contains only `versions/001_initial_v51_schema.py` — no `alembic.ini`, no `env.py`, so `alembic upgrade head` cannot be run yet.

## Cross-Cutting Concerns

**Logging:** stdlib `logging` with INFO level, format `%(asctime)s [%(levelname)s] %(name)s: %(message)s`, configured in `backend/app/main.py:9`. WORM `audit_log` table for CREATE/UPDATE/ROUTE/CALIBRATE actions (engineering analogy — no 21 CFR Part 11 / GxP claim).

**Audit/traceability:** every AI output intended to carry `model_metadata` (provider, mode, fallback_used, fallback_reason, latency_ms — `backend/app/schemas/__init__.py:7`); scoring/calibration/embedding/prompt versions stored per signal (`backend/app/models/__init__.py:187-191`). Frontend: `SignalDrawer` surfaces mock evidence & provenance (source name/type/credibility badges) mirroring the planned evidence-chain UI.

**Honesty labels:** the UI explicitly banners "All intelligence shown is synthetic and for interface demonstration only" + "DEMO DATA" badge (`frontend/components/metaradar.tsx:50`, `.synthetic-banner`) and the footer says "Demo environment · Synthetic data". The README and Master Plan enforce the same rule for the synthetic fallback dataset.

**PII/PHI:** prescribed detection + redaction layer before persistence in `node_validate`; low-confidence content rejected/quarantined; spaCy NER is not a guaranteed scrubber (Master Plan §4.2). Not yet implemented.

**Security:** no auth in place; CORS restricted to `CORS_ORIGINS`; secrets gitignored (`frontend/.gitignore`, root `.gitignore`); `docker-compose.yml` uses dev credentials only. `.env.example` exists at root (template only — contents not read).

**External-LLM privacy gate:** mandatory for any hosted Grok call — only `PUBLIC`/`SYNTHETIC` classifications allowed (`backend/app/providers/grok.py` `validate_privacy_gate`; `DataClassification` enum in `backend/app/providers/base.py:15`).

**Observability:** liveness/readiness/model/connector health endpoints implemented (`backend/app/api/v1/endpoints/health.py`); `run_id`/`signal_id`/`model_request_id` correlation prescribed (Master Plan §14.14). Frontend shows a static "Last sync" time (`frontend/components/metaradar.tsx:40`).

**Resilience:** `tenacity` exponential backoff (2s/4s/8s) prescribed for connectors (not yet a dependency); provider fallback chain implemented (`backend/app/providers/factory.py`); advisory locks for scheduler exclusivity; `pool_pre_ping` for DB.

## Tradeoffs / Decisions

| Decision | Rationale | Where encoded |
|----------|-----------|---------------|
| pgvector instead of Weaviate | One DB for relational + vector; simpler compose; HNSW index | `001_initial_v51_schema.py`, `docker-compose.yml` |
| Single in-process APScheduler, **no Celery** | 4-service compose footprint; heavy runs offloaded via asyncio/thread-pool; advisory locks guard single execution | `backend/app/db/session.py`, docker-compose (no worker service) |
| Default local LLM (Gemma 3 4B), optional Grok, BART degraded | Zero API cost; privacy; never-crash fallback; `LLM_PROVIDER=local\|xai\|auto` | `backend/app/providers/factory.py`, `backend/app/core/config.py:30` |
| Deterministic dedup before AI | Stable ID-based fingerprints prevent double-counting; syndication never inflates evidence | `backend/app/services/deduplication.py` |
| Contract-first TS types (CI-enforced) | Generated `frontend/src/types/api.ts` synced by CI; drift fails the build | `scripts/export_openapi.py`, `.github/workflows/ci.yml` |
| **Synthetic-first UI** | v0.app-generated workspace demonstrates the Four-Question UX with zero backend dependency, so UI polish and pipeline work can proceed in parallel | `frontend/lib/api.ts`, `frontend/lib/mock-data.ts` |
| **Single dynamic `[section]` route** | One server component dispatches all sections (fast scaffolding); loses per-route `generateMetadata`/loading.tsx granularity | `frontend/app/[section]/page.tsx` |
| Immutable baseline vs calibrated outputs | Auditable BEFORE/AFTER for stakeholder calibration demo | `signal_routing` model |
| Verbatim bronze-layer persistence | Replayable ingestion; zero data loss on NLP failure | `raw_signals_bronze` |
| Health endpoints with non-blocking Redis | Dashboard/CI availability independent of cache | `backend/app/api/v1/endpoints/health.py:22` |

## Architectural Constraints

- **Threading:** async-first (FastAPI ASGI, asyncpg, `redis.asyncio`); local model inference runs off the event loop via thread-pool/`asyncio.to_thread` (prescribed); Gemma GPU budget on RTX 3050 4GB VRAM with `LLM_DEVICE`/`LLM_DTYPE`/context limits — never-crash fallback chain
- **Global state:** module-level `settings` singleton (`backend/app/core/config.py:54`) and `_domain_config_cache` (`backend/app/core/domain_config.py:57`) — the only two module-level singletons on the backend; frontend state is per-component only
- **No autonomous decisions:** AI suggests → human reviews → human decides; controlled action vocabulary; degraded mode never fabricates reasoning; UI wording maintains "Suggested — requires human review"
- **Data boundaries:** public + synthetic only; external LLM transmission gated by privacy classification; demo UI must keep the synthetic banner visible
- **Contract discipline:** `frontend/src/types/api.ts` and `contracts/openapi.json` are generated artifacts — edit `backend/app/` schemas, then run `scripts/export_openapi.py`; do **not** hand-edit the generated file
- **App-directory ambiguity:** Next.js finds both `frontend/app/` and `frontend/src/app/` — one is shadowed/conflicting at build time (verify with `next build`; the active tree today is the root `app/`)
- **Circular imports:** none observed; `app.db.session.Base` is imported by `app.models`, which is imported by services — keep `app/db/session.py` free of model imports

## Anti-Patterns (to avoid)

### Failing to regenerate contracts after schema changes
**What happens:** Schema changes in `backend/app/schemas/` or endpoints are not reflected in `frontend/src/types/api.ts`.
**Why it's wrong:** CI `git diff --exit-code` fails; frontend types drift silently (and the executing UI would not notice — it doesn't import the generated file today).
**Do this instead:** Run `python scripts/export_openapi.py` after every API schema change (`.github/workflows/ci.yml` enforces this); keep `frontend/types/api.ts` aligned with the contract when the UI is wired to real endpoints.

### Maintaining two divergent type systems
**What happens:** The UI renders against hand-written `frontend/types/api.ts` while the backend contract lives in generated `frontend/src/types/api.ts`; today both contain a type named `Signal` with incompatible shapes.
**Why it's wrong:** When real API wiring lands, the mismatch (snake_case contract fields vs camelCase UI fields) becomes a silent mapping layer full of bugs; type drift is undetectable at build time (`typescript.ignoreBuildErrors: true`).
**Do this instead:** After the API surface exists, either derive the UI types from the contract (adapter in `lib/`) or standardize one shared type set and delete the other.

### Adding a connector by modifying `node_ingest`
**What happens:** Each new source becomes a bespoke branch in the ingestion node.
**Why it's wrong:** Violates the "adding a source requires a new adapter only" contract (Master Plan §14.3).
**Do this instead:** Implement a subclass of `SourceConnector` (`backend/app/connectors/base.py`) exposing `fetch_latest()`, declare `source_id`/`freshness_class`, and register it — `node_ingest` never changes.

### Treating the mock layer as the real API
**What happens:** `lib/api.ts` returns delayed fixtures; feature work sits on top of it and acquires mock-shaped dependencies (`Signal.severity`, `DashboardOverview.trends`).
**Why it's wrong:** The backend contract (`frontend/src/types/api.ts`) exposes none of these shapes; re-wiring later is a refactor of every page.
**Do this instead:** Keep `lib/api.ts` as the only seam — replace the function bodies with HTTP calls and map contract → UI types inside `lib/`, leaving page components untouched.

### Routing the same signal to everyone
**What happens:** Broadcast-style routing recreates inbox noise.
**Why it's wrong:** Contradicts "not every signal needs to go to everyone" and the calibration loop.
**Do this instead:** Use `primary_function` + `secondary_functions[]` + per-function relevance scores + `routing_reason` from the seeded matrix in `config/haemophilia.yaml:154`; let calibration adjust weights.

## Error Handling

**Strategy:** per-node error boundaries in the workflow (planned); provider `try/except` cascade with explicit `logger.warning` on each fallback step (`backend/app/providers/factory.py`); readiness endpoint degrades rather than failing (`backend/app/api/v1/endpoints/health.py:45`); `tenacity` backoff prescribed for external APIs. Frontend: minimal — pages show a `Loading` screen while promises resolve; no error/retry states exist in `metaradar.tsx`.

**Patterns:**
- Provisioning failures logged, app still starts (`backend/app/main.py:23`)
- DB failures → `rollback() → raise` in `get_db` (`backend/app/db/session.py:34`), readiness reports `degraded`
- Redis failures → non-blocking warning, never kills readiness (`backend/app/api/v1/endpoints/health.py:36-43`)
- Provider failures → fallback chain, never crash
- Frontend mock failures → none possible today; add `.catch` branches when real HTTP lands

---

*Architecture analysis: 2026-08-13*