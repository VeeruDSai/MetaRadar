# Codebase Structure

**Analysis Date:** 2026-08-13

> **Current state:** Backend foundation (FastAPI skeleton + schema) and a substantially built-out Next.js frontend (synthetic demo workspace). The frontend work is currently **uncommitted** in the working tree (`git status` shows `?? frontend/app/`, `?? frontend/components/`, `?? frontend/lib/`, `?? frontend/types/`, modified `frontend/package.json`, and a new `pnpm-lock.yaml`). This map reflects the actual repository tree (verified 2026-08-13) and marks planned locations from the canonical specs.

## Directory Layout (actual, verified)

```
novonordisk/                    # repo root (project: MetaRadar v5.1.0)
├── CLAUDE.md                   # AI agent instructions (GSD blocks: project, stack, workflow)
├── README.md                   # project README (status text lags the built frontend)
├── .env.example                # env var template (no secrets — never commit .env)
├── .gitignore
├── docker-compose.yml          # 5 declared services (4 + gpu profile); Dockerfiles MISSING
├── .github/
│   └── workflows/ci.yml        # CI: install deps → foundation tests → contract sync check
├── backend/                    # FastAPI backend (Python 3.11)
│   ├── requirements.txt        # 12 deps (fastapi, sqlalchemy, asyncpg, pgvector, redis…)
│   ├── alembic/
│   │   └── versions/
│   │       └── 001_initial_v51_schema.py   # sole migration: 16 tables + vector/pg_trgm + HNSW
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI app, lifespan, CORS, router registration
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       └── endpoints/
│       │           └── health.py            # health | ready | models | connectors
│       ├── core/
│       │   ├── config.py                    # pydantic-settings Settings
│       │   └── domain_config.py             # DomainConfig loader (YAML → Pydantic, cached)
│       ├── db/
│       │   └── session.py                   # async engine, sessionmaker, get_db, advisory locks
│       ├── models/
│       │   └── __init__.py                  # 16 SQLAlchemy ORM models (flat package)
│       ├── schemas/
│       │   └── __init__.py                  # Pydantic API schemas (flat package)
│       ├── services/
│       │   ├── deduplication.py             # fingerprints, chunking, ON CONFLICT upsert
│       │   └── redteam.py                   # priority-gated pairwise contradiction scan (seed)
│       ├── providers/
│       │   ├── base.py                      # LLMProvider, ProviderCapability, DataClassification
│       │   ├── gemma.py                     # local Gemma 3 4B (simulated execution)
│       │   ├── grok.py                      # hosted xAI Grok (privacy gate, simulated)
│       │   ├── degraded.py                  # BART factual-summary-only fallback
│       │   └── factory.py                   # ProviderFactory fallback chain + singleton
│       └── connectors/
│           └── base.py                      # SourceConnector interface + RawSignalPayload/Status
├── frontend/                   # Next.js 16.3 frontend — SYNTHETIC DEMO WORKSPACE (new)
│   ├── package.json            # next 16.3, react 19, tailwind 4, framer-motion, recharts,
│   │                           #   @base-ui/react, shadcn — NO tanstack-query (name: "my-project")
│   ├── pnpm-lock.yaml          # pnpm lockfile (package manager = pnpm)
│   ├── next.config.mjs         # typescript.ignoreBuildErrors: true; images.unoptimized: true
│   ├── tsconfig.json           # strict; paths "@/*": ["./*"]
│   ├── postcss.config.mjs      # @tailwindcss/postcss only
│   ├── components.json         # shadcn base-nova style config
│   ├── .gitignore
│   ├── app/                    # ACTIVE App Router tree (root-level)
│   │   ├── layout.tsx          # root layout + metadata + Vercel Analytics (prod)
│   │   ├── page.tsx            # redirect('/dashboard')
│   │   ├── [section]/page.tsx  # dynamic single-segment dispatcher (8 sections)
│   │   └── globals.css         # full design system (CSS variables, light/dark, component classes)
│   ├── components/
│   │   ├── metaradar.tsx       # 'use client' — Shell + DashboardPage/SignalsPage/
│   │   │                       #   IntelligencePage/GenericPage + ~10 internal components
│   │   └── ui/
│   │       └── button.tsx      # shadcn/Base-UI Button (unused by current UI)
│   ├── lib/
│   │   ├── api.ts              # MOCK API layer (delay()-wrapped fixtures; no HTTP)
│   │   ├── mock-data.ts        # signals/overview/sources fixtures
│   │   └── utils.ts            # cn() = clsx + twMerge
│   ├── types/
│   │   └── api.ts              # HAND-WRITTEN UI-domain types (Signal, DashboardOverview…)
│   ├── public/                 # icons (light/dark/apple/svg) + placeholder images
│   └── src/                    # LEGACY/DORMANT tree
│       ├── types/
│       │   └── api.ts          # GENERATED contract types — do not edit (CI-guarded)
│       └── app/
│           └── sources/page.tsx   # stale skeleton page (bento-card class) — superseded
├── contracts/
│   └── openapi.json            # GENERATED — FastAPI OpenAPI 3.1 schema snapshot
├── config/
│   └── haemophilia.yaml        # domain config: diseases, assets, signal types, lifecycle, functions
├── scripts/
│   └── export_openapi.py       # regenerates contracts/openapi.json + frontend/src/types/api.ts
├── tests/
│   └── test_foundation.py      # script-based foundation verification (not pytest yet)
├── docs/                       # 10 numbered specs + concept/ + team research/
│   ├── METARADAR_MASTER_PLAN_v5.0.md   # CANONICAL spec (authoritative — v5.1 content)
│   ├── 1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md
│   ├── 2_SRS_Software_Requirements_Specification.md
│   ├── 3_SOFTWARE_DESIGN_DOCUMENT.md     # SDD — LangGraph state contract, service designs
│   ├── 4_UI_DESIGN_DOCUMENT.md           # UI spec — routes, components, design system
│   ├── 5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md
│   ├── 6_NOVO_NORDISK_ANALYSIS_AND_HACKATHON_INTELLIGENCE.md
│   ├── 7_PITCH_AND_PRESENTATION_NARRATIVE.md
│   ├── 8_CORRECTED_UNIFIED_PLAN.md
│   ├── 9_RISK_AND_GUARDRAILS.md
│   ├── 10_ARCHITECTURE_HARDENING_REPORT.md
│   ├── concept/                # 2-page concept note (tex/pdf) + SVGs (architecture, sources, calibration)
│   └── team research/          # B.Pharm domain research (Ishaaq, Sanjana, Usha)
└── .planning/                  # GSD planning artifacts
    └── codebase/               # THIS codebase map (ARCHITECTURE/STRUCTURE/STACK/… .md)
```

## Directory Deep-Dive

### `backend/app/` — FastAPI application package

- **`main.py`** — app factory. Lifespan hook loads `DomainConfig` (non-fatal on failure); CORS middleware added when `CORS_ORIGINS` set; single router registered (`/api/v1/health`); root `/` returns service metadata. Import path style: absolute `from app.core.config import settings`.
- **`api/v1/endpoints/`** — endpoint modules, one file per router. `health.py` currently the only one (4 GETs). Convention: `router = APIRouter()` + `response_model` from `app.schemas`. New routers must be mounted in `main.py` with `prefix=f"{settings.API_V1_STR}/<resource>"`.
- **`core/`** — configuration. `config.py` = `Settings(BaseSettings)` reading `.env` (`pydantic-settings`, `extra="ignore"`); `cors_origins_list` property parses comma-separated `CORS_ORIGINS`. `domain_config.py` = Pydantic models mirroring `config/haemophilia.yaml` with `get_domain_config()` cached in `_domain_config_cache`; override path via `DOMAIN_CONFIG_PATH` env.
- **`db/session.py`** — module-level async engine (pool 10/overflow 20, `pool_pre_ping`), `AsyncSessionLocal` factory, `get_db()` FastAPI dependency (commit on success / rollback on error), and `try_advisory_lock`/`release_advisory_lock` helpers for scheduler single-execution.
- **`models/__init__.py`** — all 16 ORM models in one file (flat): `PipelineRun, Source, Company, Asset, ClinicalTrial, Development, Event, LifecycleEvent, Confluence, RawSignalBronze, Evidence, Signal, SignalRouting, CalibrationFeedback, WatchItem, AuditLog`. Uses `pgvector.sqlalchemy.Vector` and PG UUID/JSONB types. Partial unique indexes on `signals.pmid/nct_id/regulatory_id/canonical_url` and unique `fingerprint`.
- **`schemas/__init__.py`** — all Pydantic response schemas in one file (flat): health trio + connector status, plus `SignalSchema`, `DevelopmentSchema`, `PipelineRunSchema`, `ScoreBreakdownSchema`, `ModelMetadataSchema`, `FactInterpretationSpeculationSchema`. These are the contract for `contracts/openapi.json`.
- **`services/`** — business logic seeds. `deduplication.py`: `generate_fingerprint()`, `chunk_text_for_embedding()` (256-token budget), `upsert_signal()` (`INSERT … ON CONFLICT (fingerprint) DO UPDATE`). `redteam.py`: `RedTeamNLIService` with priority gating (CRITICAL/HIGH), candidate cap, and a mock rule-based pairwise check (NLI integration planned).
- **`providers/`** — provider-agnostic reasoning layer. `base.py` defines `LLMProvider` (supports()/generate_summary()/generate_intelligence()), `ProviderCapability` enum, `DataClassification` enum. `gemma.py`/`grok.py` simulate local/hosted reasoning; `degraded.py` restricts to `SUMMARIZE` with `reasoning_available=False`. `factory.py` exposes singleton `provider_factory` with `execute_task()` fallback chain: Gemma → (if `ENABLE_GROK_FALLBACK` and privacy gate passes) Grok → BART degraded.
- **`connectors/`** — `base.py` defines the shared adapter contract (`SourceConnector` + `RawSignalPayload` + `ConnectorStatus`). No concrete connectors yet (planned: pubmed, newsapi, clinical_trials, fda, ema, congress, reddit, synthetic).

### `backend/alembic/` — migrations

- No `alembic.ini` or `env.py` yet — only the version module `001_initial_v51_schema.py` (upgrade + downgrade, revision `001_initial_v51_schema`). Creates `vector` + `pg_trgm` extensions, 16 tables, partial unique indexes, and the HNSW index on `signals.embedding`. **Note:** an `alembic.ini`/`env.py` must be added before migrations can be run.

### `backend/requirements.txt`

- FastAPI/uvicorn/pydantic/pydantic-settings, SQLAlchemy 2 + asyncpg + alembic + pgvector, redis, pyyaml, httpx, python-dotenv. **Note:** `langgraph`, `tenacity`, `spacy`, `transformers`, `sentence-transformers` are NOT yet listed — they enter when the workflow/NLP layer is implemented.

### `frontend/` — Next.js 16.3 synthetic workspace (NEW, uncommitted)

- **`app/layout.tsx`** — root layout. `metadata` (title/description/icons incl. theme-conditional light/dark icons), `viewport` themeColor, Vercel `<Analytics />` when `NODE_ENV === 'production'`. Generator metadata says `v0.app`.
- **`app/page.tsx`** — 5 lines: `redirect('/dashboard')`. There is no standalone `/` page.
- **`app/[section]/page.tsx`** — the single routing hub. Server component: awaits params, dispatches `dashboard/signals/intelligence` to dedicated components, maps the `pages` record (developments/functions/calibrate/sources/settings) to `GenericPage`, and wraps every result in `<Shell>`.
- **`app/globals.css`** — the visual system: Tailwind 4 imports + CSS-variable palettes for `:root` and `.dark`, plus bespoke classes (`.app-shell`, `.sidebar`, `.nav-item`, `.topbar`, `.kpi-grid`, `.bento-grid`, `.radar`, `.signal-row`, `.badge-*`, `.drawer-*`, `.athena-*`, `.generic-grid`, media queries at 900/560px, `prefers-reduced-motion`). New UI components should reuse these tokens/classes rather than inventing colors.
- **`components/metaradar.tsx`** — single-file client module (60 lines, heavily compressed). Export list: `Shell` (sidebar/topbar/footer, theme toggle, mobile drawer), `DashboardPage`, `SignalsPage`, `IntelligencePage`, `GenericPage`. Module-private helper components: `Badge`, `Card`, `SectionTitle`, `KPI`, `Radar`, `SignalRow`, `TrendChart`, `SignalDrawer`, `Loading`. Imports: lucide-react icons, framer-motion (`AnimatePresence`/`motion`), recharts (`AreaChart`), `@/lib/api`, `@/types/api`.
- **`components/ui/button.tsx`** — shadcn (base-nova) Button built on `@base-ui/react/button` + CVA; dead code w.r.t. the current UI but the sanctioned pattern for future shadcn components.
- **`lib/api.ts`** — the ONLY data-access module. `getOverview/getSignals/getTrends/getHealth/getSources/askAthena` — all `delay(value)` wrappers over `lib/mock-data.ts` fixtures. This file is the intended seam for real HTTP (swap bodies for `fetch(NEXT_PUBLIC_API_BASE_URL + ...)`).
- **`lib/mock-data.ts`** — 4 signals, 4 sources, `overview` (confluence score 78, lifecycle array, trends Jan–Jul, health). All synthetic; UI banners `DEMO DATA`.
- **`lib/utils.ts`** — canonical `cn()` class merger (clsx + tailwind-merge).
- **`types/api.ts`** — hand-written UI types: `SignalSeverity`, `SignalStatus`, `LifecycleStage`, `SignalSource`, `Signal`, `Confluence`, `LifecycleItem`, `TrendPoint`, `HealthStatus`, `AthenaResponse`, `DashboardOverview`, `CalibrationReview`. camelCase, presentation-oriented.
- **`public/`** — favicon/apple icons (`icon.svg`, `icon-light-32x32.png`, `icon-dark-32x32.png`, `apple-icon.png`) + v0 placeholders (`.jpg`/`.svg` including `placeholder-user.jpg`).
- **`src/`** — dormant legacy tree: `src/types/api.ts` (generated contract, CI-guarded, unused by the running UI) and `src/app/sources/page.tsx` (old static connector page with `bento-card` class; no longer reachable once `app/` is the active root).
- **`components.json`** — shadcn registry config (`style: base-nova`, aliases `components/ui/lib/hooks → @/*`, iconLibrary lucide).

### `contracts/` — shared API contract

- `openapi.json` — snapshot of the FastAPI OpenAPI 3.1 schema (currently only the 4 health paths + root). Regenerated by `scripts/export_openapi.py`; CI ensures `frontend/src/types/api.ts` matches.

### `config/`

- `haemophilia.yaml` — the domain's single source of truth: `domain_config_version`, 2 diseases (ICD-10 D66/D67), factor classifications, inhibitor categories, patient segments, **7 assets** (concizumab/Alhemo, mim8, emicizumab/Hemlibra, Hemgenix, Roctavian, fitusiran/Qfitlia, marstacimab/Hympavzi with `is_novo_nordisk` flags), 7 signal types, 9 lifecycle stages, confluence thresholds (2 / ≥3 / 48h), 6 functions, and the `baseline_routing_matrix`. Loaded at startup by `backend/app/core/domain_config.py`.

### `scripts/`

- `export_openapi.py` — dev/CI utility: imports `app.main`, writes `contracts/openapi.json`, and writes the static TS template to `frontend/src/types/api.ts`. `sys.path` bootstrap handled inline.

### `tests/`

- `test_foundation.py` — plain-Python async verification script (not pytest): asserts DomainConfig loads (≥7 assets, confluence thresholds), fingerprint determinism (`pmid:` prefix), 256-token chunking bound, provider execution via `provider_factory` (expects `local_gemma`, `reasoning_available=True`) and `DegradedProvider` (`degraded_factual`, reasoning/actions disabled). Run: `python tests/test_foundation.py`.

### `.github/workflows/`

- `ci.yml` — on push/PR to `main`/`develop`: setup Python 3.11 → `pip install -r backend/requirements.txt` → `python tests/test_foundation.py` → `python scripts/export_openapi.py` + `git diff --exit-code frontend/src/types/api.ts` (contract-sync gate). **No frontend build/test job exists.**

### `docs/`

- Numbered spec suite (1–10) + `METARADAR_MASTER_PLAN_v5.0.md` (canonical, authoritative). `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` holds the LangGraph state contract and service designs; `docs/4_UI_DESIGN_DOCUMENT.md` holds the route/component spec; `docs/10_ARCHITECTURE_HARDENING_REPORT.md` catalogs v5.1 hardening decisions. `docs/concept/` holds the 2-page concept note (TeX/PDF) + SVG diagrams; `docs/team research/` holds B.Pharm research.

### `docker-compose.yml`

- Services: `postgres` (pgvector/pgvector:pg16, healthcheck, `pgdata` volume) → `redis` (redis:7-alpine, healthcheck, `redisdata` volume) → `backend` (builds `./backend/Dockerfile` — **not yet authored**; `config` read-only mount, `models_cache` volume; depends on healthy postgres+redis; healthcheck curls `/api/v1/health`) → `frontend` (builds `./frontend/Dockerfile` — **not yet authored**; `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`; depends on backend). Extra `backend-gpu` service under `profiles: ["gpu"]` (NVIDIA device reservation, `LLM_DEVICE=cuda:0`). Both backend flavors use the same Dockerfile with different env (`cpu` vs `cuda:0`).

## Where to Add New Code

**New API endpoint (e.g., `/api/v1/signals`):**
- Router: new file `backend/app/api/v1/endpoints/<resource>.py` with `router = APIRouter()`; register in `backend/app/main.py` (`app.include_router(..., prefix=f"{settings.API_V1_STR}/<resource>", tags=[...])`)
- Response schemas: `backend/app/schemas/__init__.py` (or split into `backend/app/schemas/<domain>.py` when the file grows)
- DB access: `Depends(get_db)` from `backend/app/db/session.py`; SQLAlchemy models from `backend/app/models/__init__.py`
- Regenerate contracts: `python scripts/export_openapi.py` (updates the static template in `scripts/export_openapi.py` too, if new schemas are added)

**New LangGraph node (per Master Plan §4):**
- Node implementation: `backend/app/workflows/nodes/<node>.py` (create package — does not exist yet); state contract in `backend/app/workflows/state.py` (typed `IntelligenceState` with reducers); graph assembly in `backend/app/workflows/graph.py` with explicit `set_finish_point("calibrate")`; add `langgraph` to `backend/requirements.txt`

**New source connector (e.g., FDA):**
- Adapter: `backend/app/connectors/<source>.py` subclassing `SourceConnector` from `backend/app/connectors/base.py`; implement `fetch_latest()`, declare `source_id` + `freshness_class`; use `httpx.AsyncClient` + `tenacity` retries (2s/4s/8s); register in the connector registry so `node_ingest` never changes
- Add source row to the `sources` seed and (if domain-relevant) entry in `config/haemophilia.yaml`

**New intelligence service (confluence/lifecycle/missing-signal):**
- Service: `backend/app/services/<name>.py` following the `deduplication.py`/`redteam.py` pattern (async functions / service class, typed params); consumed by the corresponding LangGraph node

**New frontend section/page (current synthetic architecture):**
- Add the section key to the `pages` record in `frontend/app/[section]/page.tsx:3` (title/eyebrow/description) — no new route file needed for generic sections
- For richer views: add a dedicated page component export in `frontend/components/metaradar.tsx` and a dispatch branch in `[section]/page.tsx` (pattern: `dashboard/signals/intelligence`)
- Page-local UX data: extend `frontend/lib/mock-data.ts` if a new fixture is needed; expose accessor in `frontend/lib/api.ts`
- Types: add to `frontend/types/api.ts`; keep them in the UI-domain vocabulary (camelCase) until real wiring lands

**Real backend wiring for the frontend (when the API surface exists):**
- Replace bodies in `frontend/lib/api.ts` with `fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/api/v1/...`)`; map contract (snake_case, `frontend/src/types/api.ts`) → UI types (camelCase, `frontend/types/api.ts`) inside `lib/`, leaving `components/metaradar.tsx` untouched
- Consider introducing shared components for future shadcn additions under `frontend/components/ui/` (pattern: `button.tsx`)

**New domain asset/disease/function:**
- Edit `config/haemophilia.yaml` (single source of truth) — no backend code change; `DomainConfig` validates on load; run `tests/test_foundation.py` (asserts ≥7 assets)

**New environment variable:**
- Add to `backend/app/core/config.py` `Settings` + document in `.env.example` (never commit `.env`); frontend vars use `NEXT_PUBLIC_` prefix (see `docker-compose.yml`)

**New migration:**
- `backend/alembic/versions/` following `00N_<description>.py` numbering; ensure `alembic.ini`/`env.py` bootstrap is added first

**New Dockerfile:**
- `backend/Dockerfile` (python:3.11-slim, uvicorn entry) and `frontend/Dockerfile` (node + `pnpm` install, `next build` + `next start`) — both referenced by `docker-compose.yml` and both missing; `docker compose up --build` is broken until they exist

**New test:**
- `tests/` for backend foundation checks; official test runner (pytest) should live under `backend/tests/` when introduced; frontend tests (vitest/playwright) under `frontend/` with scripts added to `frontend/package.json`; wire into `.github/workflows/ci.yml`

## Naming Conventions

**Files:**
- Backend Python: `snake_case.py` (`deduplication.py`, `health.py`); node files prefixed `node_` when inside the workflow (`node_ingest`, `node_confluence` per specs)
- Frontend: Next.js route files `page.tsx`/`layout.tsx`; component files `PascalCase.tsx` (e.g. `metaradar.tsx` however is lowercase — established by the v0 scaffold); shadcn registry files under `components/ui/` are `kebab-case.tsx` (`button.tsx`); API/utils modules `kebab-case.ts` (`mock-data.ts`, `utils.ts`)
- Docs: `{N}_{TOPIC}.md` numbered specs; `{Author}_research.md` research docs
- Alembic: `00N_<description>.py` (currently `001_initial_v51_schema.py`)

**Python code:**
- Modules/functions: `snake_case` (`generate_fingerprint`, `chunk_text_for_embedding`, `upsert_signal`)
- Classes: `PascalCase` (`Settings`, `DomainConfig`, `SourceConnector`, `LLMProvider`, `ProviderFactory`, `RedTeamNLIService`)
- Enums: `PascalCase` members with `UPPER_SNAKE` values (`ProviderCapability.REASON`, `DataClassification.PUBLIC`)
- DB columns: `snake_case`; primary keys `*_id` UUID strings; foreign keys `snake_case` references; versioning columns `*_version`
- Config singletons: module-level `settings` and `provider_factory` (imported, never re-instantiated)
- API prefix: all routes under `/api/v1` via `settings.API_V1_STR`

**TypeScript code:**
- Types: `PascalCase` interfaces + union type aliases (`SignalSeverity = 'critical' | 'high' | …`)
- Functions: `camelCase` (`getOverview`, `askAthena`, `cn`)
- Components: exported `PascalCase` function components (`Shell`, `DashboardPage`, `GenericPage`); module-private helpers same naming
- Props: inline `{ prop: Type }` destructured type annotations (no separate Props interface in `metaradar.tsx`)

**CSS classes:** `kebab-case` component/token classes (`.signal-row`, `.kpi-grid`, `.brand-mark`); CSS variables `--kebab-case` (`--priority-critical`, `--surface-glass`); severity variants share the `badge-<tone>` / `severity-dot.<tone>` suffix pattern (`critical|high|medium|low|neutral`).

**Env vars:** `UPPER_SNAKE` (`DATABASE_URL`, `REDIS_URL`, `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `EMBEDDING_MODEL`, `EMBEDDING_DIMENSION`, `CORS_ORIGINS`, `NEWSAPI_KEY`, `XAI_API_KEY`, `ENABLE_GROK_FALLBACK`); frontend runtime vars `NEXT_PUBLIC_*` (`NEXT_PUBLIC_API_BASE_URL`) — see root `.env.example` and `docker-compose.yml`

**Signal/Domain vocabulary:** fixed uppercase enumerations — signal types (`CLINICAL_TRIAL`, `PUBLICATIONS`, `CONGRESS`, `REGULATORY`, `COMMERCIAL_PATENT`, `SAFETY`, `ACCESS`), lifecycle stages (lowercase: `announced … post_market | discontinued`), functions (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`, `LEADERSHIP`), priorities (`CRITICAL | HIGH | MEDIUM | LOW`), freshness classes (`real_time | near_real_time | delayed | batch | adapter_ready | synthetic`) — all in `config/haemophilia.yaml` + model comments. The UI mirrors severity with lowercase UI tones (`critical|high|medium|low`) in `frontend/types/api.ts`.

## Special Directories

**`contracts/`:**
- Purpose: Shared API contract snapshot
- Generated: Yes (by `scripts/export_openapi.py`)
- Committed: Yes (CI enforces sync for the frontend copy)

**`frontend/src/types/api.ts`:**
- Purpose: Generated TS interfaces mirroring the backend contract
- Generated: Yes — do NOT hand-edit
- Committed: Yes (uncommitted today only because the whole frontend build is uncommitted)

**`frontend/src/` (dormant):**
- Purpose: Pre-refactor frontend tree — superseded by the root-level `frontend/app/` tree; `src/app/sources/page.tsx` and `src/types/api.ts` remain in place (the latter because CI's contract gate diffs it)
- Generated/Mixed: `src/types/api.ts` generated; `src/app/` hand-authored
- Action: reconcile before `next build` (two `app/` roots are ambiguous); keep `src/types/api.ts` as the generated contract target

**`docs/`:**
- Purpose: Spec + research (master plan is canonical)
- Generated: No (hand-authored)
- Committed: Yes

**`.planning/codebase/`:**
- Purpose: GSD codebase map (this directory)
- Generated: Yes (by `/gsd:map-codebase`)
- Committed: Yes

**`docker-compose.yml` volumes:**
- `pgdata` (postgres data), `redisdata` (redis data), `models_cache` (mounted at `/app/models` in backend containers — model weights downloaded once, shared across backend/backend-gpu)

---

*Structure analysis: 2026-08-13*