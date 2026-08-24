# Codebase Structure

**Analysis Date:** 2026-08-24

## Directory Layout

```
novonordisk/                    # MetaRadar v5.1 monorepo root
├── backend/                    # FastAPI Python service
│   ├── app/
│   │   ├── api/                # HTTP layer
│   │   │   ├── deps.py         # Mutation auth + rate-limit dependencies
│   │   │   └── v1/endpoints/   # 10 routers (health, signals, pipeline, ...)
│   │   ├── connectors/         # External source adapters (5 sources + base)
│   │   ├── core/               # config.py, domain_config.py, logging, middleware, redact
│   │   ├── data/               # synthetic_signals.json fixture
│   │   ├── db/                 # session.py (engine, get_db, advisory locks), seed.py
│   │   ├── models/             # ALL SQLAlchemy models in __init__.py
│   │   ├── providers/          # LLM providers: gemma, grok, degraded, factory, base
│   │   ├── schemas/            # Pydantic DTOs (intelligence.py, registry.py)
│   │   ├── services/           # Business logic (17 modules)
│   │   ├── workflows/          # LangGraph pipeline (state, graph, nodes/, runner)
│   │   └── main.py             # FastAPI app entry point
│   ├── alembic/                # Migrations env + versions/001–012
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js 16 App Router UI
│   ├── app/                    # Routes: layout, page (redirect), [section]/, signals/[signalId]/
│   ├── components/             # Domain workspaces + ui/ primitives + theme + effects
│   ├── lib/                    # api.ts, hooks.ts, mappers.ts, errors.ts, utils.ts
│   ├── types/api.ts            # Shared API response types
│   ├── public/                 # Static assets (icon.svg etc.)
│   ├── next.config.mjs, tsconfig.json, eslint.config.mjs, postcss.config.mjs
│   └── Dockerfile
├── config/
│   └── haemophilia.yaml        # Domain source of truth (assets, connectors, thresholds)
├── contracts/
│   └── openapi.json            # Exported API contract (drift-tested)
├── tests/                      # Root-level pytest suite (26 files)
├── scripts/                    # Ops/utility scripts (migrations, OpenAPI export, e2e)
├── docs/                       # SRS/SDD/rules/standards (governance docs)
├── data/synthetic_signals.json # Synthetic seed dataset
├── models/                     # Local GGUF weights (gitignored except .gitkeep/README)
├── logs/                       # start.py runtime logs (backend.log, frontend.log)
├── scratch/                    # Throwaway analysis/generation scripts
├── .github/workflows/ci.yml    # CI pipeline
├── docker-compose.yml          # postgres+pgvector, redis, backend(+gpu), frontend, ollama
├── setup.py                    # Zero-config environment bootstrap launcher
├── start.py                    # Unified process orchestrator
├── pytest.ini                  # Root pytest config (testpaths=tests, pythonpath=backend .)
└── AGENTS.md                   # Agent operating standard
```

## Directory Purposes

**`backend/app/api/v1/endpoints/`:**
- Purpose: All REST endpoints, one file per resource area
- Contains: `health.py`, `signals.py` (largest — overview/signals/detail/review), `intelligence.py`, `registry.py`, `observability.py`, `cache.py`, `pipeline.py`, `ingestion.py`, `search.py` (vector), `feedback.py`
- Key files: `signals.py` (~1000 lines), `ingestion.py`

**`backend/app/services/`:**
- Purpose: Business logic shared by endpoints, nodes, and scheduler
- Contains: `scheduler.py` (autonomous ingestion), `ingestion.py`, `scoring.py` (`priority_scorer` singleton), `routing.py`, `confluence.py` (`confluence_engine`), `embeddings.py` (`embedding_service`), `deduplication.py`, `calibration.py`, `authority.py`, `source_independence.py`, `vector_query.py`, `pii.py`, `redact`-adjacent `provenance_urls.py`, `relevance.py`, `redteam.py`, `embeddings_backfill.py`

**`backend/app/workflows/`:**
- Purpose: LangGraph intelligence pipeline
- Contains: `state.py` (`MetaRadarState` + reducers), `graph.py` (`build_graph()` linear 11-node graph), `runner.py` (`PipelineRunner` DB orchestration), `nodes/` (one file per node: `ingest.py`, `validate.py`, `embed.py`, `nlp_extract.py`, `ontology.py`, `confluence.py`, `lifecycle.py`, `redteam.py`, `missing_signal.py`, `synthesize.py`, `calibrate.py`)

**`backend/app/connectors/`:**
- Purpose: Source adapters for PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS
- Key files: `base.py` defines the full connector contract (retry, bronze persistence, state I/O, health logging); each concrete connector subclasses it; `__init__.py` exposes `ALL_CONNECTORS`

**`backend/app/providers/`:**
- Purpose: LLM execution with fallback chain and privacy gate
- Key files: `factory.py` (`ProviderFactory.execute_task`), `gemma.py` (Ollama/GGUF dual engine), `grok.py` (hosted xAI, privacy-gated), `degraded.py` (summarize-only fallback)

**`backend/app/models/`:**
- Purpose: SQLAlchemy ORM entities — all in `__init__.py`
- Key tables: `pipeline_runs`, `sources`, `source_health_logs`, `raw_signals_bronze`, `connector_state`, `signals` (silver, with pgvector embedding), `developments`, `confluences`, `contradictions`, `evidence`, `lifecycle_events`, `watch_items`, `calibration_*`, `scoring_weights`, `signal_routing`, `audit_log`

**`frontend/components/`:**
- Purpose: UI organized by domain workspace
- Contains: one directory per workspace (`signals/`, `confluence/`, `contradictions/`, `missing-signals/`, `developments/`, `intelligence/`, `functions/`, `calibration/`, `sources/`, `observability/`, `settings/`) plus `metaradar.tsx` (shell + dashboard exports), `ui/` primitives, `theme/ThemeProvider`, `common/`, `effects/star-portal/`

**`frontend/lib/`:**
- Purpose: Client-side data layer — the ONLY place components call the network
- Key files: `api.ts` (all endpoint wrappers + `apiFetch`), `hooks.ts` (`useLiveData` polling hook), `mappers.ts`, `errors.ts` (`ApiError`)

**`tests/`:**
- Purpose: Backend test suite at repo root (not inside backend/)
- Contains: unit/integration tests per capability (`test_intelligence_nodes.py`, `test_ingestion.py`, `test_contract_drift.py`, `test_privacy_boundary.py`, `test_truthfulness_and_invariants.py`, live-marked tests, etc.)

**`config/`:**
- Purpose: YAML domain configuration mounted read-only into backend container
- Key file: `haemophilia.yaml` (diseases, assets, confluence thresholds, connector profiles with query blocks, routing matrix)

**`docs/`:**
- Purpose: Governance + design documents (SRS, SDD, architecture rules, testing strategy, security standards under `docs/rules/`)
- Note: Reference material only — code lives in backend/frontend

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI app creation, lifespan (starts/stops `SourceScheduler`), router registration
- `frontend/app/[section]/page.tsx`: section router mapping URL segment → workspace component
- `start.py` / `setup.py`: repo-root process launchers
- `docker-compose.yml`: containerized stack definition

**Configuration:**
- `backend/app/core/config.py`: pydantic-settings `Settings` (DB URL, LLM, scheduler intervals, API keys as optional env)
- `backend/app/core/domain_config.py`: typed loader for YAML domain config
- `config/haemophilia.yaml`: the actual domain values
- `.env.example`: template for required environment variables (never commit real `.env`)
- `pytest.ini`: root test configuration

**Core Logic:**
- Pipeline assembly: `backend/app/workflows/graph.py`
- Persistence of pipeline output: `backend/app/workflows/runner.py`
- Provider fallback chain: `backend/app/providers/factory.py`
- Connector contract: `backend/app/connectors/base.py`
- Scheduler loop + advisory locking: `backend/app/services/scheduler.py`
- Scoring/routing/calibration: `backend/app/services/scoring.py`, `routing.py`, `calibration.py`

**Testing:**
- `tests/test_*.py`: all suites
- `contracts/openapi.json` + `tests/test_contract_drift.py`: contract sync gate
- `scripts/generate_parity_matrix.py` + `tests/test_parity_matrix.py`: feature parity verification

## Naming Conventions

**Files:**
- Python: `snake_case.py`; workflow nodes prefixed `node_` internally (`node_ingest`, exported from `nodes/<name>.py`)
- React components: `PascalCase.tsx` (`SignalCard.tsx`, `ConfluenceWorkspace.tsx`)
- Frontend libs/types: `camelCase.ts` (`api.ts`, `hooks.ts`, `mappers.ts`)
- Tests: `test_<area>.py` (Python) — no frontend test files exist

**Directories:**
- Frontend multi-word domains use `kebab-case` (`missing-signals/`, `star-portal/`)
- Backend packages `snake_case` (`api/v1/endpoints`, `workflows/nodes`)

**Symbols:**
- Services: class + module-level singleton instance (`priority_scorer = PriorityScorer()`)
- Connectors: `<Source>Connector(SourceConnector)`
- Providers: `<Name>Provider(LLMProvider)` + `ProviderCapability` enum gating
- Pydantic schemas: suffixed `Schema` in backend (`SignalSchema`, `ScoreBreakdownSchema`); frontend types unsuffixed in `types/api.ts`

## Where to Add New Code

**New REST endpoint:**
- Handler: `backend/app/api/v1/endpoints/<resource>.py` with `router = APIRouter()`
- Register: import + `app.include_router(...)` in `backend/app/main.py`
- DTOs: add request/response schemas in `backend/app/schemas/`
- Then regenerate `contracts/openapi.json` via `scripts/export_openapi.py` (contract-drift test will fail otherwise)

**New business service:**
- Implementation: `backend/app/services/<name>.py`
- Follow existing style: class exposing behavior + module-level singleton when stateless/shared

**New DB table/model:**
- Add model class to `backend/app/models/__init__.py` (this is where `Base`-derived models live)
- Migration: new revision in `backend/alembic/versions/` following `NNN_description.py` numbering (next is 013)

**New source connector:**
- Subclass `SourceConnector` in `backend/app/connectors/<source>.py`; implement `fetch_latest()` and `run_profile()`
- Register instance in `ALL_CONNECTORS` (`backend/app/connectors/__init__.py`)
- Add `ConnectorConfig` block (query profiles, backfill/quota) to `config/haemophilia.yaml`
- Add scheduler interval setting if non-default cadence needed in `backend/app/core/config.py`

**New pipeline node:**
- Create `backend/app/workflows/nodes/<name>.py` exporting `async def node_<name>(state: MetaRadarState)`
- Export from `backend/app/workflows/nodes/__init__.py`
- Wire edge in `build_graph()` (`backend/app/workflows/graph.py`) and extend `MetaRadarState` with an annotated reducer channel in `backend/app/workflows/state.py` if new outputs are produced

**New LLM provider:**
- Subclass `LLMProvider` in `backend/app/providers/<name>.py`, declare `capabilities`
- Insert into fallback chain in `ProviderFactory.execute_task` (`backend/app/providers/factory.py`), respecting the privacy-gate pattern (`validate_privacy_gate(classification)`)

**New frontend workspace/section:**
- Component dir: `frontend/components/<section>/` with a `<Section>Workspace.tsx`
- Register case in the switch in `frontend/app/[section]/page.tsx`
- Add nav entry in `frontend/components/metaradar.tsx` (Shell navigation list)
- Data access: add typed wrapper in `frontend/lib/api.ts` + response type in `frontend/types/api.ts`; consume through `useLiveData` (`frontend/lib/hooks.ts`)

**New UI primitive:**
- `frontend/components/ui/<Name>.tsx` (PascalCase), styled with Tailwind v4 utilities; shared helpers in `frontend/lib/utils.ts` (`cn()` pattern)

**New tests:**
- `tests/test_<area>.py` at repo root; async tests run under `asyncio_mode=auto`; mark live-service tests with `@pytest.mark.live`

## Special Directories

**`models/`:**
- Purpose: Local GGUF model weights for offline Gemma inference (discovered by `find_local_gguf_model()`)
- Generated: Yes (downloaded by `scripts/download_model.py` / `setup.py --download-model`)
- Committed: No (weights ignored; `.gitkeep` + `README.md` committed). A local `gemma-3-4b-it-Q4_K_M.gguf` currently exists on disk.

**`logs/`:**
- Purpose: Runtime stdout/stderr captured by `start.py` (`backend.log`, `frontend.log`)
- Generated: Yes, at runtime
- Committed: No

**`.planning/`, `.claude/`, `.agents/`:**
- Purpose: GSD planning artifacts and agent tooling/config
- Generated: Tool-managed
- Committed: Planning docs yes (per GSD convention); agent caches vary

**`frontend/.next/`, `__pycache__/`, `.pytest_cache/`:**
- Purpose: Build/test caches
- Generated: Yes
- Committed: No

**`scratch/`:**
- Purpose: One-off generator/inspection scripts (diagram SVGs, synthetic signal generation, DB inspection)
- Generated: Manually authored, throwaway quality
- Committed: Yes — do not import from production code

---

*Structure analysis: 2026-08-24*
