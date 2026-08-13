# Conventions

**Analysis Date:** 2026-08-13

> **Status:** The repository has shifted from docs-only to a working v5.1 foundation. `backend/` (15 `.py` files), `tests/`, `scripts/`, `contracts/`, and a partial `frontend/` skeleton exist but are **untracked in git** (`git status` shows all implementation as `??`). This document records the conventions **actually in use** in the code, with declared intent from `docs/METARADAR_MASTER_PLAN_v5.0.md` and `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` noted where they diverge.

## Language & Framework conventions

- **Backend:** Python 3.11 (CI target, `.github/workflows/ci.yml`) / 3.13 (local env). Framework: **FastAPI** (`backend/app/main.py`) with **Pydantic v2** (`pydantic>=2.6.0`, `pydantic-settings>=2.2.0` in `backend/requirements.txt`).
- **Persistence:** SQLAlchemy 2.0 async (`sqlalchemy.ext.asyncio`), asyncpg driver, pgvector for embeddings (`backend/app/db/session.py`).
- **Frontend:** Next.js 15 (App Router) + React 19 + TypeScript 5, declared in `frontend/package.json`. Tailwind pinned at `^3.4.1` **despite CLAUDE.md declaring TailwindCSS 4** (see Divergences §8).
- **Migration tool:** Alembic (`backend/alembic/versions/001_initial_v51_schema.py`) — but `alembic.ini` and `alembic/env.py` are missing, so `alembic upgrade head` cannot run as committed (see Divergences §6).

## Project structure conventions

```
backend/
├── requirements.txt         # Flat pip deps, no version pins below min bounds
├── alembic/
│   └── versions/             # Hand-written migrations, numbered 001_*.py
└── app/
    ├── main.py               # FastAPI app factory, lifespan, CORS, router registration
    ├── api/v1/endpoints/     # APIRouter modules (health.py)
    ├── connectors/           # Source connector base (SourceConnector, RawSignalPayload)
    ├── core/                 # config.py (pydantic-settings), domain_config.py (YAML loader)
    ├── db/                   # session.py (engine, AsyncSessionLocal, Base, get_db)
    ├── models/__init__.py    # ALL SQLAlchemy ORM models in one module (17 tables)
    ├── providers/            # LLM provider abstraction (base, gemma, grok, degraded, factory)
    ├── schemas/__init__.py   # ALL Pydantic response/domain schemas in one module
    └── services/             # Business logic (deduplication.py, redteam.py)
frontend/src/
├── app/<route>/page.tsx      # App Router pages (only sources/ has a page)
└── types/api.ts              # Generated TS contract file
tests/                        # Single verification script (repo root, not backend/tests/)
config/haemophilia.yaml       # Domain configuration data (175 lines) — loaded by domain_config.py
contracts/openapi.json        # Exported OpenAPI schema
scripts/export_openapi.py     # OpenAPI → TS contract generator
```

- **Package layout rule:** each functional slice of the backend gets its own package under `app/` (`core`, `db`, `models`, `schemas`, `providers`, `services`, `connectors`) with `api/` mirroring the URL tree (`api/v1/endpoints/`).
- **`__init__.py` discipline is inconsistent** — only `models/` and `schemas/` have `__init__.py`; `core`, `db`, `providers`, `services`, `connectors`, `api`, `api/v1`, `api/v1/endpoints` rely on implicit namespace packages. Imports work, but the convention should be: **one `__init__.py` per package**.
- **Flat module layout inside packages:** one module per concern (`config.py`, `session.py`, `deduplication.py`) rather than splitting classes across files.

## Naming conventions

**Python:**
- Modules/files: `snake_case.py` — `deduplication.py`, `domain_config.py`, `session.py`.
- Functions/methods: `snake_case` — `generate_fingerprint`, `chunk_text_for_embedding`, `upsert_signal`, `try_advisory_lock`.
- Classes: `CamelCase` — `Settings`, `ProviderFactory`, `GemmaProvider`, `DegradedProvider`, `RedTeamNLIService`, `DomainConfig`.
- Pydantic schemas: **suffix `Schema`** — `SignalSchema`, `ModelMetadataSchema`, `HealthReadyResponse`-style plain names for response models (mixed).
- Constants & env-backed settings: `UPPER_SNAKE_CASE` — `DATABASE_URL`, `LLM_PROVIDER`, `EMBEDDING_DIMENSION` (`backend/app/core/config.py`).
- Enums: `CamelCase` members with lowercase `str` values — `ProviderCapability.SUMMARIZE = "summarize"`, `DataClassification.PUBLIC = "public"` (`backend/app/providers/base.py`).
- SQLAlchemy columns: `snake_case` with `_id` suffix for PKs/FKs — `signal_id`, `pipeline_run_id`, `development_id`; every table has a UUID or string PK named `{table_singular}_id` (`backend/app/models/__init__.py`).
- DB index/constraint names: `uix_{table}_{column}` (`uix_signals_fingerprint`), `uq_{table}_{cols}` (`uq_raw_source_external`).

**Frontend:**
- Files: `page.tsx` for App Router pages, `kebab-case` route dirs (`sources`, `developments`, `intelligence`).
- Functions/components: `PascalCase` for components (`SourcesPage`), `camelCase` for handlers.
- TS interfaces: `PascalCase` — `ModelMetadata`, `ScoreBreakdown`, `HealthReadyResponse` (`frontend/src/types/api.ts`).
- API field names stay `snake_case` in TS (mirrors the wire contract; no camelCase conversion layer).
- Optional fields use `?` — `pmid?: string`, `fallback_reason?: string`.

## Configuration & Environment

- **App settings** use `pydantic-settings.BaseSettings` with a single module-level `settings = Settings()` singleton — `backend/app/core/config.py`. `SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")`.
- **Env var names** are `UPPER_SNAKE_CASE` and map directly to class fields; all have sane defaults (DB/Redis URLs default to localhost). Secrets (`XAI_API_KEY`, `NEWSAPI_KEY`) default to `Optional[str] = None`.
- **Derived settings** exposed via `@property` on the Settings class — e.g. `cors_origins_list` splits comma-separated `CORS_ORIGINS` (`config.py:25-27`).
- **Domain configuration** lives in YAML (`config/haemophilia.yaml`) validated by Pydantic models in `backend/app/core/domain_config.py`, loaded lazily with a module-level `_domain_config_cache` and env override `DOMAIN_CONFIG_PATH`.
- `.env` is gitignored; `.env.example` exists as a committed template. Read env vars — never hard-code secrets (XAI_API_KEY, NEWSAPI_KEY come from settings only).
- LLM provider selection is configuration-driven, not code-driven: `LLM_PROVIDER=local|xai|auto`, plus `ENABLE_GROK_FALLBACK` (`config.py:30-39`, `providers/factory.py`).

## Error handling

- **Provider fallback chain is the canonical error-handling pattern** (`backend/app/providers/factory.py:18-46`): try local Gemma → on exception `logger.warning` and fall through → try Grok only if `ENABLE_GROK_FALLBACK` and privacy gate passes → always land on `DegradedProvider` (BART factual summary). No error is propagated to callers unless every leg fails.
- **Abstract base classes raise `NotImplementedError`** for methods subclasses must implement (`connectors/base.py:38`, `providers/base.py:32,40`).
- **Failures degrade, they don't abort:** readiness check catches DB/Redis exceptions and flips status to `"degraded"` (`api/v1/endpoints/health.py:29-43`); advisory-lock helpers catch failures, log `logger.warning`, and return `False` instead of raising (`db/session.py:42-56`).
- **Privacy gate raises** `PermissionError` when an external LLM transmission is attempted with a non-public classification (`providers/grok.py:51-52`).
- **DB transactions commit inside the dependency:** `get_db` yields a session, commits on success, rolls back and re-raises on exception (`db/session.py:30-39`).
- Import-time failures are caught only where recoverable — the lifespan handler wraps domain-config loading in try/except and logs rather than crashing startup (`main.py:20-24`).

## Logging

- **Framework:** standard-library `logging` only — no structlog/sentry.
- **Pattern:** module-level `logger = logging.getLogger(__name__)` in every module that logs (`main.py:13`, `db/session.py:8`, `factory.py:9`, `gemma.py:8`). Root config happens once via `logging.basicConfig(level=INFO, ...)` in `backend/app/main.py:9-12` with format `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.
- **Levels:** `logger.info` for lifecycle/startup and fallback delegation; `logger.warning` for recoverable failures (Gemma failed, Grok blocked, advisory lock failed); `logger.error` for startup config failures.
- **F-string interpolation** for log messages (not `%`-style): `logger.warning(f"Gemma execution failed: {e}. Falling back...")`.

## Database conventions

- **Declarative style:** `Base = declarative_base()` in `db/session.py`; models subclass `Base` and use classic `Column(...)` API (not `mapped_column`/`Mapped[]`) — `backend/app/models/__init__.py`.
- **Column typing:** `postgresql.UUID(as_uuid=True)` PKs with `default=uuid.uuid4`; `postgresql.JSONB` for flexible payloads (facts, score_breakdown, error_summary, raw_payload); `String(n)` for codes/enums; `Text` for prose; `DateTime(timezone=True)` for all timestamps; `Vector(settings.EMBEDDING_DIMENSION)` from `pgvector.sqlalchemy` for embeddings.
- **Defaults:** Python-side `default=` on the model; matching `server_default='...'` in migrations. String defaults for status columns (`"queued"`, `"active"`, `"MEDIUM"`).
- **Uniqueness:** partial unique indexes for nullable identity columns using `postgresql_where=(col.isnot(None))` (`uix_signals_pmid`, `uix_signals_nct_id`, `uix_trials_nct_id` — `models/__init__.py:195-201`, `alembic/versions/001_initial_v51_schema.py:188-192`).
- **No FKs with `ondelete` clauses**; FKs via `ForeignKey("table.col")` only.
- **Migrations:** hand-written (not autogenerated-revision-hash) with a readable revision id `001_initial_v51_schema`; `upgrade()` uses `op.create_table` + explicit `op.execute` for partial indexes and HNSW index (`signals_embedding_hnsw` with `vector_cosine_ops`, m=16, ef_construction=64); `downgrade()` drops tables in reverse dependency order.
- DB access is **always async** — `asyncpg`, `AsyncSession`, `await session.execute(...)`.

## API conventions

- **Router-per-module:** each endpoint module defines `router = APIRouter()` and registers handlers; `main.py` mounts via `app.include_router(health.router, prefix=f"{settings.API_V1_STR}/health", tags=["Health & Diagnostics"])` (`main.py:50`).
- **Versioned prefix from settings:** `API_V1_STR = "/api/v1"`; OpenAPI served at `{API_V1_STR}/openapi.json`.
- **Handlers are `async def`,** and endpoints declare `response_model=` referencing the shared Pydantic schemas (`health.py:15,21,54,69`).
- **Dependency injection via `Depends(get_db)`** for sessions (`health.py:22`). No manual session creation in handlers.
- **Docstrings on every endpoint** — one-line summary + optional elaboration ("Liveness check: process is alive.", "Readiness check: requires DB. Redis check is non-blocking.").
- **Response construction:** return schema objects directly (`HealthReadyResponse(...)`, `HealthConnectorsResponse(connectors=connectors)`), not dicts.
- **CORS** configured from settings with allow_credentials=True, methods/headers `["*"]`, only when origins are non-empty (`main.py:40-47`).

## Frontend conventions

- **App Router pattern:** route dirs under `frontend/src/app/` (sources, signals, developments, functions, intelligence, calibrate, dashboard) currently contain only `sources/page.tsx`; default-exported `function XPage()` per route.
- **Contract types are generated, not hand-written:** `frontend/src/types/api.ts` is "Auto-generated from FastAPI OpenAPI Schema — DO NOT EDIT DIRECTLY" by `scripts/export_openapi.py`, and CI verifies it is in sync (`ci.yml:30-33`). Use these `snake_case` interfaces for all API-facing code.
- **Styling:** Tailwind utility classes with the project's bento/card class vocabulary (`bento-card`, emerald/slate color scales, arbitrary-value opacity like `bg-emerald-500/10`) — `sources/page.tsx:20-26`.
- **Formatting:** double-quoted strings, semicolons, 2-space indent (TS — opposite of Python's single-quote/no-semicolon style).
- The five API libraries declared in `package.json` (TanStack Query, Recharts, Framer Motion, lucide-react, clsx/tailwind-merge) are **not yet imported anywhere** — the skeleton has no data fetching, no components/ dir, no `layout.tsx`, no `globals.css`, no `tsconfig.json`, no `next.config.*`, and no `tailwind.config.*` (see Divergences §7).

## Testing conventions

- **Current de-facto convention:** a single plain-Python async verification script, `tests/test_foundation.py`, run as `python tests/test_foundation.py` — print-progress + `assert` style, `asyncio.run(run_tests())` entry, `sys.path.insert` hack to import `app.*` (`test_foundation.py:7-9`). **pytest is NOT used and is NOT in `requirements.txt`** (local env has pytest 9.0.3, CI does not).
- **Input fixture:** real `config/haemophilia.yaml` loaded through `get_domain_config()`; no test doubles for config.
- **Provider tests run against simulated implementations** — `GemmaProvider.generate_intelligence` and `DegradedProvider` return canned strings; tests assert the capability matrix / fallback metadata, not real inference (`test_foundation.py:41-64`).

## Code style

- **Imports:** stdlib → third-party → `app.*` locals, each group separated by a blank line (observed in every module). `from typing import ...` for all type annotations; `Any`, `Dict`, `List`, `Optional`, `Tuple`, `AsyncGenerator` are used extensively.
- **Type hints mandatory** on every public function signature — parameters and return types (e.g., `async def upsert_signal(session: AsyncSession, signal_data: Dict[str, Any]) -> Signal`).
- **Line length:** ~100 chars, no explicit formatter config (no `pyproject.toml`, `ruff`, `black`, `eslint.config.*`, or `.prettierrc` exist).
- **Docstrings:** triple-quoted; module-level (alembic migration), class-level (`RedTeamNLIService` explains the O(N²) optimization), and function-level summaries with rationale. SQL comment-style allowed too.
- **Blank lines:** two blank lines between top-level definitions (PEP 8).
- **No barrel/files exports beyond `schemas/__init__.py` and `models/__init__.py`** — those two aggregate deliberately; every other import is explicit from its own module.
- **Hardcoded literal for version truth:** `VERSION = "5.1.0"` in settings plus hardcoded `"5.1.0"` in `HealthResponse.version` default and log strings (triple duplication — change in one place misses the others).

## Version control / commit style

- **Conventional-commit-ish:** `{type}({scope}): {imperative subject}` — e.g. `docs(readme): reflect current plan status (Master Plan v5.1)...`, `docs(concept): finalize 2-page executive concept note...`, `fix: README update`. Type is lowercase; scope is lowercase word. Imperative/lowercase subject.
- **History is docs-only so far** (latest 20 commits are all `docs(...)`/`(update)`/`(fix)`); **all v5.1 implementation files are currently uncommitted.**
- `.gitignore` excludes `.env`, `*.env`, `__pycache__/`, `models/`, `.cache/`, `node_modules/`, `.next/`, `pgdata/`, `redisdata/` — but has `!.env.example` so the template is committed.

## Divergences from declared intent

1. **pytest suite not adopted** — Master Plan/SDD prescribe pytest + pytest-asyncio + pytest-cov in `backend/tests/` with targeted unit/integration suites and ≥60% critical-path coverage. Actual: one script-based script in root `tests/`, no pytest config, no coverage tooling, pytest not in `requirements.txt` (so CI can't run it even if added).
2. **No LangGraph code yet** — CLAUDE.md/SDD prescribe a 10-node LangGraph workflow (`agents/intelligence_graph.py`, `node_*` functions, `node_` prefix). Actual backend has **no `agents/` package and no graph orchestration**; only the provider fallback chain exists.
3. **Tailwind version mismatch** — CLAUDE.md declares TailwindCSS 4 + shadcn/ui; `frontend/package.json` pins `tailwindcss ^3.4.1` and no shadcn/ui components exist.
4. **SDD backend layout diverged** — SDD prescribes `app/config.py` at app root, `app/types.py`, `app/helpers.py`, `app/db_service.py`, `app/jobs/digest_job.py`, `app/data/pharma_ontology.json`. Actual: `core/config.py` (pydantic-settings), all schemas consolidated in `schemas/__init__.py`, domain config in YAML (`config/haemophilia.yaml`) loaded by `core/domain_config.py`, no jobs/scheduler code yet.
5. **Schemas are loosely typed for enums** — backend Pydantic schemas type `mode`, `priority`, `status` as plain `str` (`schemas/__init__.py:73`), while the TS contract declares unions (`"CRITICAL" | "HIGH" | "MEDIUM" | "LOW"` in `frontend/src/types/api.ts:45`). The provider enums (`DataClassification`, `ProviderCapability`) show the preferred pattern.
6. **Alembic incomplete** — migration `001_initial_v51_schema.py` exists but `alembic.ini` and `alembic/env.py` are missing, so `alembic upgrade head` will not run; the migration also imports `settings` for schema-time defaults (`EMBEDDING_DIMENSION`, `EMBEDDING_MODEL_REVISION`) which freezes configuration into migration history.
7. **Frontend skeleton far below declared structure** — SDD §2.1 declares `components/UI/`, `lib/utils.ts`, `globals.css`, `next.config.js`, auth routes; only `sources/page.tsx` + `types/api.ts` exist, and the app cannot `next build` without `tsconfig.json`.
8. **Stale README status** — README badge says "Status: Pre-Implementation" and "Documentation complete — implementation begins with Week 1" although the v5.1 backend foundation exists and its tests pass.
9. **`datetime.utcnow` usage** — deprecated in Python 3.12+; used as default in every model and schema (`models/__init__.py:17`, `schemas/__init__.py:112`) even though columns are `timezone=True` (yields naive datetimes in a "timezone-aware" column — inconsistent with the declared postgres `timestamptz` intent).

---

*Convention analysis: 2026-08-13*