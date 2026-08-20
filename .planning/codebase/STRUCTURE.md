# Codebase Structure

**Analysis Date:** 2026-08-20

## Directory Layout

```
[project-root]/
├── backend/                 # FastAPI service (Python)
│   ├── alembic/             # DB migrations
│   │   └── versions/        # 001, 002, 003 migration scripts
│   ├── app/
│   │   ├── main.py          # FastAPI app factory + router registration
│   │   ├── api/v1/endpoints/# 8 HTTP routers
│   │   ├── connectors/      # 5 source adapters + base contract
│   │   ├── core/            # Settings + DomainConfig
│   │   ├── data/            # synthetic_signals.json fallback
│   │   ├── db/              # async engine, session, seed
│   │   ├── models/          # ALL SQLAlchemy ORM models (single file)
│   │   ├── providers/       # LLM abstraction + fallback chain
│   │   ├── schemas/         # Pydantic API contracts
│   │   ├── services/        # business logic layer
│   │   └── workflows/       # LangGraph engine (graph/state/runner/nodes)
│   ├── Dockerfile
│   ├── alembic.ini
│   └── requirements.txt
├── config/
│   └── haemophilia.yaml     # Domain ontology + connector query blocks
├── contracts/
│   └── openapi.json         # Canonical exported OpenAPI contract
├── data/
│   └── synthetic_signals.json  # 500-signal demo dataset
├── docs/                    # SRS, SDD, master plan, rules/, audits/
│   ├── rules/               # Authoritative process standards (mirrored in .agents/rules/)
│   ├── audits/
│   ├── concept/
│   ├── manifests/
│   ├── release/
│   └── team research/
├── frontend/                # Next.js 16 service
│   ├── app/                 # ACTIVE App Router tree (canonical per ARCHITECTURE_RULES)
│   │   ├── layout.tsx       # Root layout + metadata
│   │   ├── page.tsx         # Redirect → /dashboard
│   │   ├── globals.css
│   │   └── [section]/       # Dynamic section route → page components
│   ├── components/          # metaradar.tsx (monolith) + ui/ primitives
│   ├── lib/                 # api client, hooks, utils, mock-data
│   ├── public/              # icons
│   ├── src/                 # LEGACY/stub tree (mostly empty; one page)
│   ├── types/               # api.ts auto-generated contract
│   ├── Dockerfile
│   ├── package.json         # pnpm-managed
│   └── next.config.mjs
├── scripts/
│   ├── export_openapi.py    # OpenAPI + TS contract generator
│   └── generate_parity_matrix.py
├── tests/                   # 16 pytest files (root-level suite)
├── logs/                    # backend.log / frontend.log (runtime)
├── scratch/                 # throwaway diagram/signal generators
├── .agents/rules/           # Agent process standards (mirror of docs/rules/)
├── .github/workflows/ci.yml # CI: pytest → contract sync → frontend build
├── .planning/               # GSD planning artifacts (phases, codebase maps)
├── start.py                 # Unified process launcher
├── setup.py                 # Zero-config environment setup
├── docker-compose.yml       # Postgres + Redis (+ Ollama) backing services
├── pytest.ini
└── AGENTS.md / CLAUDE.md / GEMINI.md   # Agent operating standards
```

## Directory Purposes

**`backend/app/`:**
- Purpose: FastAPI application package (imported as `app.*` with `PYTHONPATH=backend`)
- Contains: endpoints, connectors, core, db, models, providers, schemas, services, workflows
- Key files: `backend/app/main.py` (entry), `backend/app/core/config.py`, `backend/app/workflows/graph.py`

**`backend/app/api/v1/endpoints/`:**
- Purpose: HTTP routers — one file per feature area
- Contains: `health.py` (`/health`, `/health/ready`, `/health/models`, `/health/connectors`), `signals.py` (`/signals`, `/overview`, `/athena`), `pipeline.py` (`/pipeline/run`, `/pipeline/status/{id}`), `search.py` (`/search`), `feedback.py` (`/feedback`, `/feedback/summary`, `/calibrate`, `/calibration/weights`, `/watch-items/confirm`), `intelligence.py` (`/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`), `registry.py` (`/developments`, `/sources`), `cache.py` (`/cache/clear`)
- Pattern: each file defines `router = APIRouter()`; registered in `backend/app/main.py:59-66`

**`backend/app/workflows/`:**
- Purpose: LangGraph intelligence engine
- Contains: `graph.py` (11-node linear StateGraph), `state.py` (MetaRadarState + reducers), `runner.py` (PipelineRunner), `nodes/` (11 `node_<name>` functions)

**`backend/app/services/`:**
- Purpose: Reusable business logic consumed by endpoints AND workflow nodes
- Contains: `embeddings.py` (EmbeddingService), `vector_query.py` (VectorQueryService), `calibration.py` (StakeholderCalibrationService + HeuristicWatchParser), `deduplication.py` (fingerprints + bronze persistence), `pii.py` (PIIPHIScrubber), `redteam.py` (RedTeamNLIService), `source_independence.py` (SourceIndependenceClassifier), `embeddings_backfill.py` (CLI backfill script)

**`backend/app/connectors/`:**
- Purpose: External source adapters, all extending `SourceConnector`
- Contains: `base.py`, `pubmed.py`, `clinical_trials.py`, `newsapi.py`, `fda.py`, `ema.py`, `__init__.py` (instantiates `ALL_CONNECTORS`)

**`backend/app/providers/`:**
- Purpose: LLM execution layer
- Contains: `base.py` (contracts), `gemma.py`, `grok.py`, `degraded.py`, `factory.py` (fallback chain)

**`backend/app/schemas/`:**
- Purpose: Pydantic request/response models
- Contains: `__init__.py` (main schemas incl. SignalSchema, OverviewResponse, calibration schemas), `intelligence.py` (confluence/lifecycle/red-team/missing-signal items), `registry.py` (DevelopmentSummary, SourceRegistryItem)

**`backend/app/models/__init__.py`:**
- Purpose: Single-module ORM layer — all tables (PipelineRun, Source, Company, Asset, ClinicalTrial, Development, Event, LifecycleEvent, Confluence, RawSignalBronze, ConnectorState, Evidence, Signal, Contradiction, CalibrationHistory, ScoringWeights, SignalRouting, CalibrationFeedback, WatchItem, AuditLog)
- Note: 317 lines; split by domain if it grows further

**`backend/alembic/versions/`:**
- Purpose: Schema migrations — `001_initial_v51_schema.py`, `002_phase1_connector_state_and_cross_source.py`, `003_contradictions_scoring.py`
- Pattern: sequential numeric prefixes; async env in `backend/alembic/env.py` reads `settings.DATABASE_URL`

**`config/`:**
- Purpose: YAML domain configuration (the "brain" of the domain ontology)
- Contains: `haemophilia.yaml` — diseases, assets, signal types, lifecycle stages, confluence thresholds, functions, baseline routing matrix, per-connector query profiles, cross-source group rules, lag thresholds
- Typed by: `backend/app/core/domain_config.py`

**`contracts/`:**
- Purpose: Canonical API contract artifacts
- Contains: `openapi.json` (exported by `scripts/export_openapi.py`)

**`frontend/app/`:**
- Purpose: ACTIVE Next.js App Router tree (canonical)
- Contains: `layout.tsx`, `page.tsx` (redirect), `[section]/page.tsx` (dynamic dispatch), `globals.css`
- Note: `[section]` is the single route catching all 12 workspace sections — do not add sibling route folders here without a reason

**`frontend/components/`:**
- Purpose: UI components
- Contains: `metaradar.tsx` (1892-line monolith: Shell + all 11 page components + modals + primitives), `ui/button.tsx` (shadcn-style Base UI primitive)

**`frontend/lib/`:**
- Purpose: Frontend infrastructure
- Contains: `api.ts` (API client + mappers), `hooks.ts` (useLiveData), `utils.ts` (cn), `mock-data.ts` (demo fallback data)

**`frontend/types/`:**
- Purpose: Auto-generated TypeScript API contract
- Contains: `api.ts` — generated by `scripts/export_openapi.py`; DO NOT EDIT (CI drift check)

**`frontend/src/`:**
- Purpose: LEGACY/stub tree — `src/app/sources/page.tsx` (static, non-API page) + empty section dirs; `src/types/api.ts` re-exports canonical types
- Note: Not the active tree; `ARCHITECTURE_RULES.md` declares `frontend/app/` canonical. Avoid adding code here.

**`tests/`:**
- Purpose: Root-level pytest suite (16 files, `pythonpath = backend .` in `pytest.ini`)
- Contains: `test_api_endpoints.py`, `test_signals_endpoints.py`, `test_intelligence_nodes.py`, `test_ingestion.py`, `test_retrieval.py`, `test_calibration_service.py`, `test_e2e_calibration_scenario.py`, `test_provider_matrix.py`, `test_providers_live.py`, `test_redteam_behavior.py`, `test_privacy_boundary.py`, `test_contract_drift.py`, `test_parity_matrix.py`, `test_foundation.py`, `test_config.py`, `test_launchers.py`

**`scripts/`:**
- Purpose: Dev/CI tooling (not shipped to runtime)
- Contains: `export_openapi.py`, `generate_parity_matrix.py`

**`docs/`:**
- Purpose: Specification and governance documentation
- Contains: numbered design docs (1–10), `rules/` (authoritative standards — mirrored at `.agents/rules/`), `audits/`, `manifests/feature_parity_manifest.json`, `release/v5.1_RELEASE_NOTES.md`, `concept/` (PDF/SVG diagrams), `templates/`

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app — `uvicorn app.main:app` with `PYTHONPATH=backend`
- `frontend/app/page.tsx`: Next.js root (redirects to `/dashboard`)
- `frontend/app/[section]/page.tsx`: dynamic section router
- `start.py`: process launcher (docker + backend + frontend)
- `setup.py`: environment bootstrap (deps, migrations, seed, models)
- `scripts/export_openapi.py`: contract generation

**Configuration:**
- `backend/app/core/config.py`: env settings (`.env` via pydantic-settings)
- `.env.example`: documented env var template (DATABASE_URL, REDIS_URL, LLM_PROVIDER, XAI_API_KEY, EMBEDDING_MODEL, NEWSAPI_KEY, CORS_ORIGINS)
- `config/haemophilia.yaml`: domain ontology + connector config
- `backend/alembic.ini` + `backend/alembic/env.py`: migration config
- `pytest.ini`: test discovery + `pythonpath`
- `frontend/next.config.mjs`, `frontend/tsconfig.json`, `frontend/eslint.config.mjs`, `frontend/postcss.config.mjs`
- `frontend/package.json`: pnpm scripts (`dev`, `build`, `start`, `lint`)
- `docker-compose.yml`: postgres, redis (+ Ollama) backing services

**Core Logic:**
- `backend/app/workflows/graph.py`: pipeline topology
- `backend/app/workflows/state.py`: pipeline state contract + reducers
- `backend/app/workflows/runner.py`: execution orchestration
- `backend/app/workflows/nodes/*.py`: 11 processing stages
- `backend/app/services/vector_query.py`: hybrid semantic search
- `backend/app/services/calibration.py`: stakeholder weight calibration
- `frontend/components/metaradar.tsx`: all workspace UI
- `frontend/lib/api.ts`: all backend calls + mappers

**Testing:**
- `tests/`: root pytest suite
- `frontend`: no frontend test framework configured (CI runs tsc/lint/build only — `.github/workflows/ci.yml:52-58`)

## Naming Conventions

**Files:**
- Python: `snake_case.py` — e.g. `clinical_trials.py`, `vector_query.py`, `embeddings_backfill.py`
- TypeScript/TSX: kebab-case — e.g. `mock-data.ts`, `globals.css`; framework files `layout.tsx`, `page.tsx`
- Alembic: `<NNN>_<snake_description>.py` — e.g. `001_initial_v51_schema.py`
- Tests: `test_<subject>.py` — e.g. `test_signals_endpoints.py` (enforced by `pytest.ini` `python_files = test_*.py`)

**Directories:**
- Python packages: `snake_case` (`api/v1/endpoints`, `workflows/nodes`, `providers`)
- Frontend: singular lowercase (`app`, `components`, `lib`, `types`, `public`)
- Next.js special dirs: `[section]` bracket syntax for dynamic routes

**Functions:**
- Python: `snake_case`; workflow nodes prefixed `node_<name>` (`node_ingest`, `node_calibrate`); async where I/O (`async def node_embed`)
- TypeScript: `camelCase` for fetchers/hooks (`getOverview`, `askAthena`, `useLiveData`, `mapSignal`)

**Classes/Components:**
- Python: `PascalCase` services with `Service`/`Provider`/`Connector`/`Scrubber`/`Classifier` suffixes — `VectorQueryService`, `GemmaProvider`, `PubMedConnector`, `PIIPHIScrubber`, `SourceIndependenceClassifier`
- TypeScript: `PascalCase` React components exported as named functions — `Shell`, `DashboardPage`, `SignalDrawer`, `SearchModal` (`frontend/components/metaradar.tsx`)

**Constants:**
- Python: `UPPER_SNAKE` module-level constants — `ALL_CONNECTORS`, `DEFAULT_CALIBRATION_WEIGHTS`, `LIFECYCLE_STAGE_ORDER` (`backend/app/workflows/nodes/lifecycle.py:11`), `SIGNAL_TYPE_CREDIBILITY` (`backend/app/workflows/nodes/confluence.py:12`)

**Routers:**
- Every endpoint file exports `router = APIRouter()`; route paths defined in the router file, mounted in `backend/app/main.py`

## Where to Add New Code

**New API Endpoint:**
1. Add `backend/app/api/v1/endpoints/<feature>.py` with `router = APIRouter()`
2. Define Pydantic request/response models in `backend/app/schemas/` (or `backend/app/schemas/<feature>.py` for new domains)
3. Register router in `backend/app/main.py:59-66`
4. Add fetcher in `frontend/lib/api.ts`; run `python scripts/export_openapi.py` to refresh `frontend/types/api.ts` + `contracts/openapi.json`
5. Add tests in `tests/test_<feature>.py`

**New Workflow Node:**
1. Create `backend/app/workflows/nodes/<name>.py` with `async def node_<name>(state: MetaRadarState, session=None) -> Dict[str, Any]`
2. Export it in `backend/app/workflows/nodes/__init__.py`
3. Add node + edge in `backend/app/workflows/graph.py` (update the docstring node list)
4. Add any new state channels to `backend/app/workflows/state.py` with appropriate reducer (`operator.add` for append, `replace_list` for whole-list re-emission, `merge_dicts` for dict merges)

**New External Source Connector:**
1. Create `backend/app/connectors/<source>.py` extending `SourceConnector` from `backend/app/connectors/base.py`
2. Implement `fetch_latest` / `run_profile`; reuse `_fetch_with_retry`, `_persist_bronze`, `_write_connector_state`
3. Register in `backend/app/connectors/__init__.py` (`ALL_CONNECTORS`)
4. Add query profile config in `config/haemophilia.yaml` under `connectors.<source_id>`

**New LLM Provider:**
1. Create `backend/app/providers/<name>.py` extending `LLMProvider` (`backend/app/providers/base.py`) with `capabilities` + `generate_intelligence`
2. Wire into the fallback chain in `backend/app/providers/factory.py`
3. Ensure degraded-fallback metadata contract (`ModelMetadataSchema`) is honored

**New Frontend Page/Section:**
1. Add case to the `switch` in `frontend/app/[section]/page.tsx:26-69`
2. Add the page component (or extend an existing one) in `frontend/components/metaradar.tsx` — or better, split into `frontend/components/pages/<Page>.tsx` per the anti-pattern guidance in ARCHITECTURE.md
3. Add nav entry in the `nav`/`secondary` arrays (`frontend/components/metaradar.tsx:91-106`)
4. Add fetchers to `frontend/lib/api.ts` + types to `frontend/types/api.ts` via contract export

**New Database Table:**
1. Add ORM class in `backend/app/models/__init__.py` (uses `Base` from `backend/app/db/session.py`)
2. Generate migration: `alembic revision --autogenerate -m "<desc>"` then review the file in `backend/alembic/versions/`
3. Add seed data in `backend/app/db/seed.py` if needed

**New Service (shared logic):**
- Add `backend/app/services/<domain>.py` with a class exposing async methods; consume from endpoints and/or workflow nodes (do not duplicate logic in endpoints — the endpoint stays thin, per the layering in ARCHITECTURE.md)

**New Config (domain knowledge):**
- Extend `config/haemophilia.yaml` and mirror the fields in the matching Pydantic model in `backend/app/core/domain_config.py` (e.g. add a new signal type to `signal_types` + `baseline_routing_matrix`)

**Utilities / scripts:**
- Backend/CLI tooling: `scripts/`
- Frontend shared helpers: `frontend/lib/utils.ts` (or a new `frontend/lib/<helper>.ts`)

## Special Directories

**`frontend/src/`:**
- Purpose: Stub/legacy App Router tree (one static sources page + re-export types)
- Generated: No
- Committed: Yes
- Note: Do NOT add new code here — `frontend/app/` is the canonical tree (`docs/rules/ARCHITECTURE_RULES.md:5`)

**`logs/`:**
- Purpose: Runtime process logs written by `start.py` (`backend.log`, `frontend.log`)
- Generated: Yes (runtime)
- Committed: No (gitignored)

**`scratch/`:**
- Purpose: Throwaway generators (SVG diagrams, synthetic data)
- Generated: No
- Committed: Yes (low-value, cleanup candidate)

**`data/`:**
- Purpose: Synthetic demo dataset (`synthetic_signals.json`, ~500 signals) used as ingestion fallback when bronze is empty (`backend/app/workflows/nodes/ingest.py:15-29`)
- Generated: Partially (regenerable via `scratch/generate_synthetic_signals.py`)
- Committed: Yes

**`.planning/`:**
- Purpose: GSD workflow artifacts — `codebase/` (this map), `phases/`, `milestones/`, `PROJECT.md`, `ROADMAP.md`, `STATE.md`
- Generated: Yes (by GSD commands)
- Committed: Yes

**`.agents/rules/`:**
- Purpose: Agent-facing process standards (mirror of `docs/rules/`)
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-08-20*