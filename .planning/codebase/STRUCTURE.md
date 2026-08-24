# Codebase Structure

**Analysis Date:** 2026-08-24

## Directory Layout

```text
novonordisk/
├── backend/                    # FastAPI backend (Python 3.11+)
│   ├── alembic/                # DB migrations (001_initial → 011_widen_fingerprint)
│   │   └── versions/           # 11 versioned migration scripts
│   ├── app/
│   │   ├── api/v1/endpoints/   # FastAPI routers (10 endpoint modules)
│   │   ├── connectors/         # 5 source adapters + abstract base
│   │   ├── core/               # config, domain_config, logging, middleware, redact
│   │   ├── data/               # Bundled synthetic_signals.json fallback fixture
│   │   ├── db/                 # session.py (engine/sessions), seed.py
│   │   ├── models/             # SQLAlchemy ORM — all 22 tables in __init__.py
│   │   ├── providers/          # LLM providers: gemma, grok, degraded + factory
│   │   ├── schemas/            # Pydantic request/response contracts
│   │   ├── services/           # Domain services (14 modules)
│   │   ├── workflows/          # LangGraph graph/state/runner
│   │   │   └── nodes/          # 11 pipeline node functions
│   │   └── main.py             # FastAPI entrypoint
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js 16 App Router (React 19, TypeScript)
│   ├── app/
│   │   ├── layout.tsx          # Root layout + theme bootstrap script
│   │   ├── page.tsx            # Redirects to /dashboard
│   │   ├── globals.css         # Design tokens + global styles
│   │   ├── [section]/page.tsx  # Section router → workspace components
│   │   └── signals/[signalId]/ # Signal detail route
│   ├── components/             # One dir per UI domain + metaradar.tsx shell
│   │   ├── calibration/ contradictions/ confluence/ developments/
│   │   ├── functions/ intelligence/ missing-signals/ observability/
│   │   ├── settings/ signals/ sources/
│   │   ├── common/             # EvidenceDrawer, EmptyState, ErrorState, badges
│   │   ├── theme/              # ThemeProvider (context)
│   │   ├── ui/                 # Primitives: Counter, Stepper, SpecularButton…
│   │   ├── effects/star-portal/# Canvas/WebGL renderers (visual effects)
│   │   └── metaradar.tsx       # App Shell + Dashboard/Lifecycle pages (2,249 lines)
│   ├── lib/                    # api.ts, mappers.ts, hooks.ts, errors.ts, utils.ts
│   ├── types/api.ts            # Generated OpenAPI contract mirror (do not hand-edit)
│   ├── public/                 # Static assets (icon.svg etc.)
│   ├── next.config.mjs · tsconfig.json · eslint.config.mjs · Dockerfile
├── config/
│   └── haemophilia.yaml        # Canonical domain config: ontology, assets, connector profiles
├── contracts/
│   └── openapi.json            # Exported OpenAPI 3.1 snapshot
├── data/
│   └── synthetic_signals.json  # Seed/demo fallback dataset
├── docs/
│   ├── rules/                  # ENGINEERING_STANDARDS, TESTING_STRATEGY, ARCHITECTURE_RULES…
│   ├── audits/ concept/ manifests/ release/ templates/ team research/
├── models/                     # Local GGUF reasoning weights (gitignored artifacts)
├── scripts/                    # export_openapi.py, download_model.py, apply_phase7_migrations.py,
│                               # generate_parity_matrix.py, test_live_ingestion_e2e.py, check-banned-classes.mjs
├── tests/                      # pytest suite at repo root (23 test files)
├── logs/                       # Runtime log output from start.py (uncommitted)
├── scratch/                    # Throwaway experiments
├── .github/workflows/ci.yml    # CI: pytest + contract-sync check + frontend build
├── docker-compose.yml          # postgres (pgvector), redis, backend, frontend, ollama
├── setup.py                    # Zero-config environment setup wizard
├── start.py                    # Unified process launcher
├── pytest.ini                  # Test config (root-level)
├── AGENTS.md / CLAUDE.md / GEMINI.md / README.md
└── .env.example                # Environment template (never commit .env)
```

## Directory Purposes

**`backend/app/api/v1/endpoints/`:**
- Purpose: HTTP layer — one router per resource
- Contains: `signals.py` (563 lines, incl. Athena Q&A), `intelligence.py`, `health.py`, `observability.py`, `feedback.py`, `ingestion.py`, `pipeline.py`, `registry.py`, `search.py`, `cache.py`
- Key files: `signals.py` is the largest surface; `pipeline.py` triggers manual LangGraph runs

**`backend/app/services/`:**
- Purpose: Business logic shared by endpoints, scheduler, and workflow nodes
- Key files: `scheduler.py` (autonomous polling loops), `ingestion.py` (`IngestionService`), `scoring.py` (`priority_scorer` singleton), `embeddings.py` (`embedding_service`), `confluence.py`, `calibration.py` (572 lines), `deduplication.py`, `pii.py`, `provenance_urls.py`, `vector_query.py`

**`backend/app/workflows/`:**
- Purpose: LangGraph intelligence engine
- Key files: `graph.py` (`build_graph()`), `state.py` (`MetaRadarState` + reducers + `create_initial_state` factory), `runner.py` (`PipelineRunner` with DB persistence); `nodes/node_*.py` — 11 node modules named after their stage

**`backend/app/connectors/`:**
- Purpose: External source adapters under a strict bronze-only persistence contract
- Key files: `base.py` (abstract `SourceConnector`, retry/backoff, health logging), `__init__.py` (`ALL_CONNECTORS` registry list), one module per source

**`backend/app/models/`:**
- Purpose: SQLAlchemy ORM definitions
- Key files: `__init__.py` holds ALL model classes (400 lines) — there are no per-model files; import models from `app.models`

**`backend/app/core/`:**
- Purpose: Cross-cutting infrastructure
- Key files: `config.py` (pydantic-settings `Settings` singleton + `configuration_error_for`), `domain_config.py` (YAML loader → Pydantic), `logging.py` (structlog setup), `middleware.py` (`CorrelationIdMiddleware`), `redact.py` (PII scrubbing for logs)

**`frontend/components/<domain>/`:**
- Purpose: One self-contained workspace component per product domain
- Naming pattern: `<Domain>Workspace.tsx` (e.g., `ConfluenceWorkspace.tsx`, `CalibrationWorkspace.tsx`)

**`frontend/lib/`:**
- Purpose: All data fetching and normalization
- Key files: `api.ts` (550 lines — single fetch layer, `apiFetch<T>` at line ~149), `mappers.ts` (API→view model transforms), `hooks.ts` (`useLiveData` polling hook), `errors.ts` (`ApiError`)

**`tests/`:**
- Purpose: Backend pytest suite (repo root level, not inside backend/)
- Contains: 23 `test_*.py` files covering API, ingestion, intelligence nodes, provenance, truthfulness invariants, failure injection, calibration, privacy boundary, contract drift

**`docs/rules/`:**
- Purpose: Mandatory engineering standards governing all agents/contributors (see root `AGENTS.md`)
- Key files: `ENGINEERING_STANDARDS.md`, `TESTING_STRATEGY.md`, `ARCHITECTURE_RULES.md`

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app, middleware, routers, lifespan scheduler
- `frontend/app/layout.tsx`: Root layout with theme bootstrapping
- `start.py`: Unified launcher (Docker + migrations + both apps)
- `setup.py`: Environment/model setup wizard

**Configuration:**
- `config/haemophilia.yaml`: Canonical domain ontology and connector query profiles
- `backend/app/core/config.py`: All runtime settings (env-driven via `.env`)
- `backend/alembic.ini` + `backend/alembic/versions/`: Schema migrations
- `docker-compose.yml`: Service topology (postgres/redis/backend/frontend/ollama)
- `.github/workflows/ci.yml`: CI gates (pytest, contract sync, Next build)
- `pytest.ini`: Pytest configuration
- `.env.example`: Template of required environment variables (`.env` itself is forbidden reading material)

**Core Logic:**
- `backend/app/workflows/graph.py` + `runner.py` + `state.py`: Intelligence pipeline
- `backend/app/services/scheduler.py`: Autonomous ingestion scheduling
- `backend/app/connectors/base.py`: Connector framework
- `backend/app/providers/factory.py`: LLM fallback chain

**Contract Synchronization (critical trio):**
- `scripts/export_openapi.py`: Canonical template + exporter
- `contracts/openapi.json`: Exported snapshot
- `frontend/types/api.ts`: Generated TS mirror consumed by `frontend/lib/api.ts`

**Testing:**
- `tests/test_*.py`: All backend tests (repo-root level; run from root with `PYTHONPATH=backend:.` per CI)

## Naming Conventions

**Files (Python):**
- `snake_case.py` throughout; services named after capability (`priority scoring` → `scoring.py`); workflow nodes prefixed `node_` (`node_ingest.py` defines `node_ingest()`)
- Tests: `test_<area>.py` at repo-root `tests/`

**Files (TypeScript/React):**
- Components: `PascalCase.tsx` (`SignalCard.tsx`, `EvidenceDrawer.tsx`)
- Lib modules: `camelCase.ts` (`api.ts`, `hooks.ts`)
- Route segments: kebab-case dynamic dirs (`[section]`, `[signalId]`, `missing-signals/`)
- Workspace components: `<Domain>Workspace.tsx`

**Directories:**
- Backend packages: lowercase plural nouns by role (`models/`, `schemas/`, `services/`, `connectors/`, `providers/`, `workflows/`, `endpoints/`)
- Frontend component dirs: kebab-case domain names (`missing-signals/`, `star-portal/`)

**Database:**
- Tables: `snake_case` plural (`raw_signals_bronze`, `source_health_logs`)
- Alembic versions: `NNN_description.py` (`007_sources_operational_telemetry.py`)
- Models: singular PascalCase class names matching table via explicit `__tablename__`

**Identifiers:**
- Source IDs: lowercase source names (`pubmed`, `clinical_trials`, `fda`, `ema`, `newsapi`)
- Pipeline state keys: `snake_case` matching state channels (`validated_signals`, `node_statuses`)

## Where to Add New Code

**New API Endpoint:**
1. Handler: `backend/app/api/v1/endpoints/<resource>.py` (new file or existing router)
2. Register router in `backend/app/main.py` via `app.include_router(...)` with prefix `settings.API_V1_STR`
3. Request/response schemas: `backend/app/schemas/intelligence.py` or `registry.py`, re-export from `backend/app/schemas/__init__.py`
4. **Contract sync:** update the canonical template in `scripts/export_openapi.py`, then run `python scripts/export_openapi.py` to regenerate `frontend/types/api.ts` — CI fails otherwise
5. Frontend client wrapper: `frontend/lib/api.ts` using `apiFetch<T>`; add types to `frontend/types/api.ts` only via regeneration
6. Tests: `tests/test_api_endpoints.py` or new `tests/test_<resource>.py`

**New LangGraph Node:**
1. Implement async `node_xxx(state: MetaRadarState) -> Dict[str, Any]` returning only changed channels, in `backend/app/workflows/nodes/node_xxx.py`; re-export from `nodes/__init__.py`
2. Wire edges in `backend/app/workflows/graph.py` (insert into the linear chain before `END`)
3. If new state channels are needed, add them to `MetaRadarState` in `backend/app/workflows/state.py` choosing the correct reducer (`operator.add` to accumulate, `merge_dicts` for dict merge, `replace_list` when re-emitting whole lists)
4. Persistence of new entities: extend `_persist_state_to_db` in `backend/app/workflows/runner.py` with FK-validity pre-checks
5. Tests: `tests/test_intelligence_nodes.py`

**New Source Connector:**
1. Subclass `SourceConnector` in `backend/app/connectors/<source>.py`, implementing `fetch_latest()` and `run_profile()`; reuse `_fetch_with_retry`, `_persist_bronze`, `_read_connector_state`/`_write_connector_state`, `_persist_health_log` from the base class
2. Instantiate and register in `ALL_CONNECTORS` in `backend/app/connectors/__init__.py`
3. Add a `connectors:` block (freshness class, tier, backfill days, profiles) to `config/haemophilia.yaml` — connectors execute configured profiles, never hardcode queries
4. Scheduler picks it up automatically (workers built from `ALL_CONNECTORS`); add interval via `SCHEDULER_*` setting if needed in `backend/app/core/config.py`

**New Service:**
- Implementation: `backend/app/services/<capability>.py`; expose a module-level singleton only if it's stateless/config-like (pattern: `priority_scorer`, `embedding_service`); take an `AsyncSession` parameter when session-scoped (pattern: `IngestionService(session)`)

**New ORM Model:**
- Add the class to `backend/app/models/__init__.py` (all models live in this single file) and create an Alembic migration in `backend/alembic/versions/` following the `NNN_description.py` naming

**New UI Workspace/Page:**
1. Component: `frontend/components/<domain>/<Domain>Workspace.tsx` ('use client', consume `useLiveData` + typed wrappers from `frontend/lib/api.ts`)
2. Route wiring: add a `case` in the switch in `frontend/app/[section]/page.tsx`
3. Navigation entry: `frontend/components/metaradar.tsx` (Shell nav)
4. View-model mapping (if needed): `frontend/lib/mappers.ts`

**Utilities:**
- Python helpers: colocate in the most specific package; cross-cutting infra goes in `backend/app/core/`
- Shared frontend helpers: `frontend/lib/utils.ts`; React hooks: `frontend/lib/hooks.ts`

## Special Directories

**`models/`:**
- Purpose: Local GGUF reasoning weights (e.g., `gemma-3-4b-it-Q4_K_M.gguf`)
- Generated: Yes (downloaded by `setup.py` / `scripts/download_model.py`)
- Committed: No (large binaries; mounted as Docker volume `models_cache`)

**`logs/`:**
- Purpose: Runtime output streamed by `start.py`
- Generated: Yes
- Committed: No

**`scratch/`:**
- Purpose: Disposable experiments
- Committed: Avoid adding anything durable here

**`frontend/.next/`, `__pycache__/`, `.pytest_cache/`:**
- Build/test artifacts; never commit, never edit

**`.planning/`:**
- Purpose: GSD planning documents (this analysis lives in `.planning/codebase/`)
- Committed: Yes (per repo convention)

---

*Structure analysis: 2026-08-24*
