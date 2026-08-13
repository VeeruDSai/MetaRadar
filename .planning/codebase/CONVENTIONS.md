# Conventions

**Analysis Date:** 2026-08-13

> **Status:** The v5.1 backend foundation (`backend/`, `tests/`, `scripts/`, `contracts/`) is unchanged since the previous map, and the **frontend has been substantially built out** since. The new frontend (Next.js 16 + React 19 + TS strict + Tailwind 4 + shadcn/ui "base-nova") lives in `frontend/app/`, `frontend/components/`, `frontend/lib/`, `frontend/types/` and is **functional against mock data** (no backend calls). A stale skeleton tree (`frontend/src/app/`, `frontend/src/types/`) from the earlier OpenAPI-generation approach still exists and is **not used by the running app**. Most new frontend files are uncommitted (`git status` shows `?? frontend/app/`, `?? frontend/components/`, `?? frontend/lib/`, `?? frontend/types/`, `?? frontend/tsconfig.json`, `?? frontend/next.config.mjs`, `?? frontend/pnpm-lock.yaml`). This document records conventions **actually in use**, with declared intent from `docs/METARADAR_MASTER_PLAN_v5.0.md` and `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` noted where they diverge.

## Language & Framework conventions

- **Backend:** Python 3.11 (CI target, `.github/workflows/ci.yml`) / 3.13 (local env). Framework: **FastAPI** (`backend/app/main.py`) with **Pydantic v2** (`pydantic>=2.6.0`, `pydantic-settings>=2.2.0` in `backend/requirements.txt`).
- **Persistence:** SQLAlchemy 2.0 async (`sqlalchemy.ext.asyncio`), asyncpg driver, pgvector for embeddings (`backend/app/db/session.py`).
- **Frontend:** **Next.js 16.3.0 + React 19 + TypeScript 5.7.3**, package manager **pnpm** (`frontend/pnpm-lock.yaml`), in `frontend/package.json`. This **upgraded from the declared Next.js 15** (see Divergences §2). TailwindCSS **4.3.3** now matches the declared stack (previously pinned at v3 — see Divergences §3). Styling pipeline is CSS-first: `@tailwindcss/postcss` in `frontend/postcss.config.mjs`, no `tailwind.config.*` file.
- **Component system:** shadcn/ui in "base-nova" style (`frontend/components.json`), backed by **Base UI** (`@base-ui/react`) rather than Radix; `class-variance-authority` for variants, `clsx` + `tailwind-merge` for class merging, `tw-animate-css` + `shadcn/tailwind.css` for motion.
- **Frontend ancillary libs:** framer-motion (animations), recharts (charts), lucide-react (icons), `@vercel/analytics`. **TanStack Query v5 is declared but not imported anywhere** (see Divergences §4).
- **Migration tool:** Alembic (`backend/alembic/versions/001_initial_v51_schema.py`) — still missing `alembic.ini` and `alembic/env.py`, so `alembic upgrade head` cannot run as committed.

## Project structure conventions

```
backend/
├── requirements.txt         # Flat pip deps, no version pins below min bounds
├── alembic/versions/        # Hand-written migrations, numbered 001_*.py
└── app/
    ├── main.py              # FastAPI app, lifespan, CORS, router registration
    ├── api/v1/endpoints/    # APIRouter modules (health.py)
    ├── connectors/          # Source connector base (SourceConnector, RawSignalPayload)
    ├── core/                # config.py (pydantic-settings), domain_config.py (YAML loader)
    ├── db/                  # session.py (engine, AsyncSessionLocal, Base, get_db)
    ├── models/__init__.py   # ALL SQLAlchemy ORM models in one module
    ├── providers/           # LLM provider abstraction (base, gemma, grok, degraded, factory)
    ├── schemas/__init__.py  # ALL Pydantic response/domain schemas in one module
    └── services/            # Business logic (deduplication.py, redteam.py)
frontend/                    # ACTIVE frontend (v0/shadcn build)
├── app/                     # App Router: layout.tsx, page.tsx (redirect), [section]/page.tsx, globals.css
├── components/              # metaradar.tsx (all pages + shell), ui/button.tsx (shadcn)
├── lib/                     # api.ts (mock layer), mock-data.ts, utils.ts (cn)
├── types/                   # api.ts — hand-written frontend domain types (camelCase)
├── public/                  # icons, placeholder images (v0 assets)
├── src/app/, src/types/     # STALE skeleton: 1 old page + generated contract (see Divergences §1)
├── tsconfig.json, next.config.mjs, postcss.config.mjs, components.json, package.json, pnpm-lock.yaml
tests/                       # Single verification script (repo root, not backend/tests/)
config/haemophilia.yaml      # Domain configuration data — loaded by domain_config.py
contracts/openapi.json       # Exported OpenAPI schema
scripts/export_openapi.py    # OpenAPI → TS contract generator (hardcoded template)
```

- **Backend package rule:** each functional slice gets its own package under `app/` (`core`, `db`, `models`, `schemas`, `providers`, `services`, `connectors`) with `api/` mirroring the URL tree (`api/v1/endpoints/`).
- **`__init__.py` discipline is inconsistent** — only `models/` and `schemas/` have `__init__.py`; `core`, `db`, `providers`, `services`, `connectors`, `api/*` rely on implicit namespace packages. Convention: **one `__init__.py` per package**.
- **Frontend route convention:** a **single dynamic catch-all** `app/[section]/page.tsx` serves all sections (`dashboard`, `signals`, `intelligence`, `developments`, `functions`, `calibrate`, `sources`, `settings`) by dispatching to exported page components in `components/metaradar.tsx`; `app/page.tsx` simply `redirect('/dashboard')`. **Do not create per-route page.tsx files** for these sections — extend `metaradar.tsx` instead (the stale `src/app/<route>/page.tsx` layout contradicts this).
- **Flat module layout inside packages:** one module per concern (`config.py`, `session.py`, `deduplication.py`, `metaradar.tsx`) rather than splitting per component.

## Naming conventions

**Python:**
- Modules/files: `snake_case.py` — `deduplication.py`, `domain_config.py`, `session.py`.
- Functions/methods: `snake_case` — `generate_fingerprint`, `chunk_text_for_embedding`, `upsert_signal`, `try_advisory_lock`.
- Classes: `CamelCase` — `Settings`, `ProviderFactory`, `GemmaProvider`, `RedTeamNLIService`, `DomainConfig`.
- Pydantic schemas: suffix `Schema` — `SignalSchema`, `ModelMetadataSchema`; response models use plain names (`HealthReadyResponse`, `HealthConnectorsResponse`).
- Constants & env-backed settings: `UPPER_SNAKE_CASE` — `DATABASE_URL`, `LLM_PROVIDER`, `EMBEDDING_DIMENSION` (`backend/app/core/config.py`).
- Enums: `CamelCase` members with lowercase `str` values — `ProviderCapability.SUMMARIZE = "summarize"`, `DataClassification.PUBLIC = "public"` (`backend/app/providers/base.py`).
- SQLAlchemy columns: `snake_case` with `_id` suffix for PKs/FKs — `signal_id`, `pipeline_run_id`; every table has a UUID or string PK named `{table_singular}_id` (`backend/app/models/__init__.py`).
- DB index/constraint names: `uix_{table}_{column}`, `uq_{table}_{cols}`.

**Frontend (active tree):**
- Files: `page.tsx` / `layout.tsx` (App Router conventions), `ui/button.tsx` for shadcn primitives, `lib/utils.ts` for helpers, `types/api.ts` for types.
- Components: `PascalCase` **exported function declarations** — `Shell`, `DashboardPage`, `SignalsPage`, `IntelligencePage`, `GenericPage`, `SectionTitle`, `SignalRow`, `TrendChart`, `Radar`, `Badge`, `Card`, `KPI` (`frontend/components/metaradar.tsx`). shadcn primitive is a plain `function Button(...)` exporting both `Button` and `buttonVariants` (`frontend/components/ui/button.tsx`).
- TS interfaces/types: `PascalCase` — `Signal`, `DashboardOverview`, `AthenaResponse` (`frontend/types/api.ts`). Union literal types for closed sets: `SignalSeverity = 'critical' | 'high' | 'medium' | 'low'`.
- **API-facing field names are camelCase** in the hand-written types (`detectedAt`, `sourceId`, `stakeholders`) — this diverges from the wire contract's snake_case (see Divergences §1, §5).
- Route segments: kebab-case words (`/dashboard`, `/signals`, `/developments`); nav labels capitalized in `components/metaradar.tsx:12-15`.

## Configuration & Environment

- **App settings** use `pydantic-settings.BaseSettings` with a single module-level `settings = Settings()` singleton — `backend/app/core/config.py`. `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`.
- **Env var names** are `UPPER_SNAKE_CASE` and map directly to class fields; all have sane defaults (DB/Redis URLs default to localhost). Secrets (`XAI_API_KEY`, `NEWSAPI_KEY`) default to `Optional[str] = None`.
- **Derived settings** exposed via `@property` — `cors_origins_list` splits comma-separated `CORS_ORIGINS` (`config.py:25-27`).
- **Domain configuration** lives in YAML (`config/haemophilia.yaml`) validated by Pydantic models in `backend/app/core/domain_config.py`, loaded lazily with a module-level `_domain_config_cache` and env override `DOMAIN_CONFIG_PATH`.
- `.env` is gitignored (root `.gitignore`); `.env.example` is the committed template. `frontend/.gitignore` additionally ignores `node_modules/`, `.next/`, `.env*.local`, and v0 sandbox internals.
- LLM provider selection is configuration-driven: `LLM_PROVIDER=local|xai|auto` + `ENABLE_GROK_FALLBACK` (`config.py:30-39`, `providers/factory.py`).
- **Frontend config:** `frontend/tsconfig.json` sets `strict: true`, `noEmit`, `moduleResolution: "bundler"`, `jsx: "react-jsx"`, path alias `@/*` → `./*`; `frontend/next.config.mjs` sets `typescript.ignoreBuildErrors: true` (build skips type-checking — see TESTING.md Lint/Typecheck) and `images.unoptimized: true`; `frontend/components.json` maps `@/components`, `@/lib/utils`, `@/components/ui`.
- **No frontend env vars are actually consumed** — `lib/api.ts` returns mock data and never reads `NEXT_PUBLIC_API_BASE_URL` (which `docker-compose.yml` still injects). Only `process.env.NODE_ENV` is used (`app/layout.tsx:45`, for Vercel Analytics).

## Error handling

- **Provider fallback chain is the canonical backend error-handling pattern** (`backend/app/providers/factory.py:18-46`): local Gemma → `logger.warning` + fall through → Grok only if `ENABLE_GROK_FALLBACK` and privacy gate passes → always land on `DegradedProvider` (BART factual summary). No error propagates unless every leg fails.
- **Abstract base classes raise `NotImplementedError`** for methods subclasses must implement (`connectors/base.py:38`, `providers/base.py:32,40`).
- **Failures degrade, they don't abort:** readiness check catches DB/Redis exceptions and flips status to `"degraded"` (`api/v1/endpoints/health.py:29-43`); advisory-lock helpers catch, `logger.warning`, return `False` (`db/session.py:42-56`).
- **Privacy gate raises** `PermissionError` on external LLM transmission with non-public classification (`providers/grok.py:51-52`).
- **DB transactions commit inside the dependency:** `get_db` yields a session, commits on success, rolls back and re-raises on exception (`db/session.py:30-39`).
- **Frontend:** errors are not surfaced at all — `lib/api.ts` `delay()` never rejects and no component has error/empty-state boundaries beyond `Loading`; `askAthena` returns a canned string. No try/catch, no error boundary, no toast.

## Logging

- **Framework:** standard-library `logging` only — no structlog/sentry.
- **Pattern:** module-level `logger = logging.getLogger(__name__)` in every backend module that logs (`main.py:13`, `db/session.py:8`, `factory.py:9`, `gemma.py:8`). Root config once via `logging.basicConfig(level=INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")` in `backend/app/main.py:9-12`.
- **Levels:** `logger.info` for lifecycle/startup and fallback delegation; `logger.warning` for recoverable failures; `logger.error` for startup config failures.
- **F-string interpolation** for messages: `logger.warning(f"Gemma execution failed: {e}. Falling back...")`.
- **Frontend:** no logging/observability in the client; Vercel Analytics is the only telemetry (`app/layout.tsx:45`).

## Database conventions

- **Declarative style:** `Base = declarative_base()` in `db/session.py`; models subclass `Base` and use classic `Column(...)` API (not `mapped_column`/`Mapped[]`) — `backend/app/models/__init__.py`.
- **Column typing:** `postgresql.UUID(as_uuid=True)` PKs with `default=uuid.uuid4`; `postgresql.JSONB` for flexible payloads (facts, score_breakdown, raw_payload); `String(n)` for codes/enums; `Text` for prose; `DateTime(timezone=True)` for timestamps; `Vector(settings.EMBEDDING_DIMENSION)` for embeddings.
- **Defaults:** Python-side `default=` on the model; matching `server_default='...'` in the migration. String defaults for status columns (`"queued"`, `"active"`, `"MEDIUM"`).
- **Uniqueness:** partial unique indexes for nullable identity columns via `postgresql_where=(col.isnot(None))` (`uix_signals_pmid`, `uix_signals_nct_id`, `uix_trials_nct_id` — `models/__init__.py:195-201`).
- **No FKs with `ondelete` clauses**; FKs via `ForeignKey("table.col")` only.
- **Migrations:** hand-written with readable revision id `001_initial_v51_schema`; `upgrade()` uses `op.create_table` + explicit `op.execute` for partial indexes and HNSW vector index (`signals_embedding_hnsw`, `vector_cosine_ops`, m=16, ef_construction=64).
- DB access is **always async** — `asyncpg`, `AsyncSession`, `await session.execute(...)`.

## API conventions

- **Router-per-module:** each endpoint module defines `router = APIRouter()`; `main.py` mounts via `app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health & Diagnostics"])` (`main.py:50`).
- **Versioned prefix from settings:** `API_V1_STR = "/api/v1"`; OpenAPI served at `{API_V1_STR}/openapi.json`.
- **Handlers are `async def`** and declare `response_model=` referencing shared Pydantic schemas (`health.py:15,21,54,69`).
- **Dependency injection via `Depends(get_db)`** for sessions (`health.py:22`); no manual session creation in handlers.
- **Docstrings on every endpoint** — one-line summary + optional elaboration.
- **Response construction:** return schema objects directly (`HealthReadyResponse(...)`), not dicts.
- **CORS** from settings with `allow_credentials=True`, methods/headers `["*"]`, only when origins non-empty (`main.py:40-47`).
- **Contract export:** `scripts/export_openapi.py` writes `contracts/openapi.json` from `app.openapi()` and (re)writes `frontend/src/types/api.ts` from a **hardcoded TS template** (not derived from the schema) — see TESTING.md CI integration.

## Frontend conventions (React/Next/TS/shadcn)

- **App Router:** root layout `app/layout.tsx` exports `metadata` and `viewport` (typed `Metadata`/`Viewport`), renders `<html lang="en">` + `<body className="antialiased">`; global CSS imported as `import './globals.css'`. `app/page.tsx` calls `redirect('/dashboard')` from `next/navigation`.
- **Dynamic route + async params:** `app/[section]/page.tsx` uses the Next 15+ contract — `{ params }: { params: Promise<{ section: string }> }` with `await params`, and is a **server component** (no hooks). Per-section config is a `Record<string, { title; eyebrow; description }>` map with a fallback to `pages.developments` for unknown slugs.
- **Server vs client:** only `components/metaradar.tsx` carries `'use client'` (it uses `useState`, `useEffect`, `useMemo`, `usePathname`). Everything else is a server component by default. **Convention: keep 'use client' at the top of the single interactive component; add new interactive islands as exported client components in `components/`.**
- **Data fetching:** no TanStack Query, no `fetch`, no Server Actions. `lib/api.ts` exports `getOverview/getSignals/getTrends/getHealth/getSources/askAthena` that resolve **mock data from `lib/mock-data.ts`** after a `delay(ms)` (default 360 ms; 700 ms for Athena). Pages consume via `useEffect(() => { getOverview().then(setData) }, [])` in client components, rendering `<Loading />` until data arrives. **Convention: the async API surface lives in `lib/api.ts` with typed return types; swapping mock for real HTTP later should only touch that module.**
- **State:** local component state only (no global store). `SignalsPage` keeps `filter` + `selected` locally and derives filtered lists with `useMemo`.
- **Styling:** a **two-layer system**:
  1. shadcn/ui Tailwind-utility layer — the `ui/button.tsx` primitive (`cva` variants, `cn(buttonVariants(...))`, `data-slot="button"`, Base UI `ButtonPrimitive`), plus the token bridge in `app/globals.css` (`@theme inline` mapping `--color-*`, `--radius-*`).
  2. **Hand-written semantic CSS classes** in `app/globals.css` (33 very dense lines) — `.app-shell`, `.sidebar`, `.panel`, `.badge`, `.kpi-grid`, `.bento-grid`, `.signal-row`, `.athena-card`, `.drawer-*`, etc., styled with CSS variables and `color-mix()`; light/dark theming via `.dark` class toggled in `Shell` (`useEffect` toggles `document.documentElement.classList`). **Convention: page layout components use these semantic classes (not raw Tailwind utilities) — the stale `src/app/sources/page.tsx` uses bare Tailwind utilities and is the outlier.**
  - Motion: framer-motion `AnimatePresence`/`motion.aside` for the signal drawer; recharts `AreaChart` for trends. Icons: lucide-react, imported individually: `import { Activity, Bell, ... } from 'lucide-react'`.
- **Formatting:** single quotes, **no semicolons**, 2-space indent, trailing commas in multiline objects — the v0/shadcn default. The stale tree (`src/app/sources/page.tsx`, `src/types/api.ts`) uses double quotes + semicolons (generator output) — do not copy that style.
- **Import ordering:** `react` → `next/*` → third-party (framer-motion, lucide-react, recharts) → `@/lib` → `@/types` → local. Type-only imports use `import type { ... }` (`metaradar.tsx:10`, `lib/mock-data.ts:1`).
- **TypeScript strictness:** `strict: true` is on, but **type errors do not fail the build** because `next.config.mjs` sets `typescript.ignoreBuildErrors: true` — type-checking is effectively opt-in (`npx tsc --noEmit`).
- **Accessibility:** `aria-label` on icon-only buttons, semantic `<nav>`, `<main>`, `<section>`, `<button>` elements, `prefers-reduced-motion` media query honored in `globals.css:35`.
- **Package identity:** `package.json` is named `"my-project"` (never renamed) and `metadata.generator: 'v0.app'` — the app was generated in v0 and shipped via pnpm with `pnpm.overrides` pinning `hono` (transitive). Lockfile `frontend/pnpm-lock.yaml` is committed; `node_modules` is not installed in the workspace (build/lint not runnable without `pnpm install`).

## Testing conventions

- **Backend (de-facto):** a single plain-Python async verification script `tests/test_foundation.py` run as `python tests/test_foundation.py` — print-progress + `assert` style, `asyncio.run(run_tests())` entry, `sys.path.insert` bootstrap to import `app.*`. **pytest is NOT used and NOT in `requirements.txt`.** See TESTING.md.
- **Frontend:** no test framework, no `test` script, no component tests.
- **Contract sync as a "test":** CI regenerates `frontend/src/types/api.ts` via `scripts/export_openapi.py` and `git diff --exit-code`s it — a convention that keeps the generated file deterministic, though it validates a hardcoded template, not schema truth.

## Code style

- **Backend imports:** stdlib → third-party → `app.*` locals, blank line between groups (observed in every module). `from typing import ...` for annotations; `Any`, `Dict`, `List`, `Optional`, `Tuple`, `AsyncGenerator` used extensively.
- **Type hints mandatory** on every public function signature — parameters and return types (e.g. `async def upsert_signal(session: AsyncSession, signal_data: Dict[str, Any]) -> Signal`).
- **Line length:** ~100 chars; **no formatter/linter config anywhere** (no `pyproject.toml`, `ruff`, `black`, `flake8`; frontend has **no `eslint.config.*`** even though `package.json` declares `"lint": "eslint ."` and `eslint-config-next` — `eslint .` cannot resolve a config as committed).
- **Docstrings:** triple-quoted; module-level, class-level (e.g. `RedTeamNLIService` explains the O(N²) optimization), and function-level summaries with rationale.
- **Blank lines:** two between top-level Python definitions (PEP 8).
- **Frontend JSX density:** `metaradar.tsx` packs entire screens into single-line expressions with inline arrow components — readable but far outside typical formatting; no prettier is configured to fix this.
- **Hardcoded literal for version truth:** `VERSION = "5.1.0"` in settings plus hardcoded `"5.1.0"` in `HealthResponse.version` and log strings — change in one place misses the others.

## Version control / commit style

- **Conventional-commit-ish:** `{type}({scope}): {imperative subject}` — e.g. `docs(readme): reflect current plan status (Master Plan v5.1)...`, `feat: initial project structure, backend foundational services...`. Type lowercase; scope lowercase; imperative subject.
- **State:** history is docs-heavy; the latest commit (`ddf4f97 feat: ...`) committed the backend foundation, but **the entire new frontend is uncommitted** (`git status` `??` for `frontend/app`, `frontend/components`, `frontend/lib`, `frontend/types`, config files, lockfile) and `frontend/package.json` is modified.
- **Root `.gitignore`** excludes `.env`/`*.env` (keeps `!.env.example`), `__pycache__/`, `.pytest_cache/`, `.coverage`, `node_modules/`, `.next/`, `out/`, `models/`, `.cache/`, `pgdata/`, `redisdata/`.

## Divergences from declared intent

1. **Two frontend trees / contract not consumed by the app:** the declared contract flow (SDD §2, `ci.yml`) treats `frontend/src/types/api.ts` as *the* API contract — but the running app imports hand-written camelCase types from `frontend/types/api.ts` and never touches the generated file. The stale `frontend/src/app/sources/page.tsx` and empty `src/app/<route>/` dirs remain as dead code. CI's contract-sync gate therefore guards a file the product doesn't use.
2. **Next.js 16, not 15:** Master Plan §Stack, SDD, and pitch docs declare Next.js 15; `frontend/package.json` pins `"next": "16.3.0"` with `eslint-config-next` 16 and `eslint` 10.
3. **Tailwind now aligned (resolved divergence):** previously v3 vs declared v4; now `tailwindcss ^4.3.3` + `@tailwindcss/postcss`, matching CLAUDE.md and SDD.
4. **TanStack Query v5 declared, unused:** SDD §3 and CLAUDE.md prescribe TanStack Query for server-state; zero imports exist. Data flows through a hand-rolled `lib/api.ts` mock layer with `useEffect` + `useState`.
5. **Naming polarity on API fields:** the hand-written `frontend/types/api.ts` uses camelCase (`detectedAt`, `credibility`) while backend Pydantic schemas and the generated contract use snake_case (`signal_id`, `published_at`). Any switch to real API calls will need a mapping layer or a types rewrite.
6. **Frontend build is not type-checked:** `next.config.mjs` sets `typescript.ignoreBuildErrors: true` — the strict tsconfig is effectively advisory in CI-less local builds; no typecheck or lint script is run anywhere in CI.
7. **Lint script is broken as committed:** `frontend/package.json` declares `"lint": "eslint ."` with no `eslint.config.mjs` present; ESLint 10 requires a flat config, so `pnpm lint` fails until a config is added. No CI job runs it regardless.
8. **Backend untested beyond foundation script:** no pytest (declared in SDD/Master Plan with ≥60% coverage), no API tests (FastAPI TestClient), no model↔migration parity test, no provider failure-injection tests (Master Plan EV-19/EV-20). Full detail in TESTING.md.
9. **Frontend is mock-only and Docker-free:** `docker-compose.yml` still declares a `frontend:` service with `NEXT_PUBLIC_API_BASE_URL` and a `./frontend/Dockerfile` — **no Dockerfile exists anywhere in the repo**, so `docker compose up` cannot build the frontend, and the new app ignores the env var entirely (mock data only). `backend-gpu` likewise references a missing Dockerfile.
10. **`datetime.utcnow` usage:** deprecated in 3.12+; used as default in models and schemas (`models/__init__.py:17`, `schemas/__init__.py:112`) even though columns are `timezone=True` (yields naive datetimes in a "timezone-aware" column).
11. **Package identity left at generator defaults:** `frontend/package.json` name is `"my-project"`, `layout.tsx` metadata declares `generator: 'v0.app'` — branding not aligned to the MetaRadar product name.

---

*Convention analysis: 2026-08-13*
