# Codebase Structure

**Analysis Date:** 2026-08-23

## Directory Layout

```text
novonordisk/ (MetaRadar)
├── AGENTS.md / CLAUDE.md / GEMINI.md   # AI agent operating standards
├── README.md                            # Project overview & validation results
├── .env.example                         # Environment template (.env gitignored)
├── docker-compose.yml                   # postgres(pgvector), redis, ollama, backend, frontend
├── start.py                             # Unified zero-friction launcher (docker + migrations + servers)
├── setup.py                             # Zero-config environment & reasoning model setup wizard
├── pytest.ini                           # Root pytest configuration
├── models/                              # Root local reasoning models directory (*.gguf format)
│   ├── .gitkeep
│   ├── README.md
│   └── gemma-3-4b-it-Q4_K_M.gguf        # Downloaded local Q4 GGUF reasoning model (2.48 GB)
├── backend/
│   ├── alembic.ini                      # Alembic config (async engine)
│   ├── alembic/
│   │   └── versions/                    # 001_initial … 011_widen_fingerprint
│   ├── app/
│   │   ├── main.py                      # FastAPI entrypoint, lifespan, router registration
│   │   ├── api/v1/endpoints/            # 10 router modules (signals, health, ingestion, …)
│   │   ├── connectors/                  # 5 source adapters + SourceConnector base + registry
│   │   ├── core/                        # config.py, domain_config.py, logging.py, middleware.py
│   │   ├── data/                        # synthetic_signals.json (in-package fallback copy)
│   │   ├── db/                          # session.py (engine/sessions/advisory locks), seed.py
│   │   ├── models/__init__.py           # ALL ORM models — single module, 22 tables
│   │   ├── providers/                   # LLM abstraction: base, factory, gemma, grok, degraded
│   │   ├── schemas/                     # Pydantic v2 request/response schemas
│   │   ├── services/                    # scheduler, ingestion, scoring, confluence, calibration…
│   │   └── workflows/                   # graph.py, runner.py, state.py, nodes/ (11 nodes)
│   ├── Dockerfile
│   └── requirements.txt                 # Backend dependencies
├── frontend/
│   ├── app/                             # Next.js App Router
│   │   ├── layout.tsx                   # Root layout, theme bootstrap script
│   │   ├── page.tsx                     # Redirect → /dashboard
│   │   ├── [section]/page.tsx           # Section switcher → workspace components
│   │   └── globals.css                  # Design tokens + custom rectangular scrollbar styling
│   ├── components/
│   │   ├── metaradar.tsx                # Shell, nav, DashboardPage, shared widgets
│   │   ├── <domain>/                    # One dir per workspace (calibration, confluence,
│   │   │                                #   contradictions, developments, functions,
│   │   │                                #   intelligence, missing-signals, observability,
│   │   │                                #   settings, signals, sources)
│   │   ├── common/                      # DataModeBadge, EmptyState, ErrorState, EvidenceDrawer, SpecularButton
│   │   ├── theme/ThemeProvider.tsx      # Dark/light adaptive theming
│   │   └── ui/button.tsx                # Primitive button
│   ├── lib/                             # api.ts, hooks.ts, mappers.ts, errors.ts, utils.ts
│   ├── types/api.ts                     # Synced TypeScript API contracts (from OpenAPI)
│   ├── public/                          # Static assets (icon.svg - adaptive pharma radar logo)
│   ├── package.json / tsconfig.json / components.json
│   └── next-env.d.ts
├── config/
│   └── haemophilia.yaml                 # Canonical domain config: diseases, assets, connector
│                                        #   query profiles, routing matrix, lag thresholds
├── contracts/
│   └── openapi.json                     # Exported OpenAPI spec (contract sync source of truth)
├── data/
│   └── synthetic_signals.json           # Synthetic fallback dataset (flagged as fixtures)
├── docs/                                # Canonical rules (ENGINEERING_STANDARDS.md, ARCHITECTURE_RULES.md,
│                                        #   TESTING_STRATEGY.md, …), SRS/SDD/UI docs, audits, manifests
├── logs/                                # Runtime log streams written by start.py (gitignored artifacts)
├── scripts/                             # export_openapi.py, generate_parity_matrix.py,
│                                        #   download_model.py, check-banned-classes.mjs
├── tests/                               # Backend pytest suite (25 test files, 119 passing tests)
├── scratch/                             # Scratch space (gitignored)
├── .planning/                           # GSD planning artifacts (phases, milestones, codebase/)
└── .github/workflows/                   # CI pipelines
```

## Directory Purposes

**`backend/app/api/v1/endpoints/`:**
- Purpose: HTTP surface of the platform
- Contains: one module per resource group; each exposes `router = APIRouter()`
- Key files: `signals.py` (overview/signals/Athena), `intelligence.py` (confluence, lifecycles, red-team, missing-signals), `ingestion.py` (manual sync triggers), `health.py`, `observability.py`, `feedback.py` (HITL calibration), `search.py` (pgvector search), `pipeline.py`, `registry.py`, `cache.py`

**`backend/app/workflows/`:**
- Purpose: the LangGraph intelligence engine
- Key files: `graph.py` (build/wire 11 nodes), `state.py` (MetaRadarState contract), `runner.py` (PipelineRunner + DB persistence), `nodes/*.py` (one file per node)

**`backend/app/services/`:**
- Purpose: stateless-ish business logic reused by endpoints and nodes
- Key files: `scheduler.py`, `ingestion.py`, `scoring.py`, `confluence.py`, `embeddings.py`, `calibration.py`, `deduplication.py`, `pii.py`, `relevance.py`, `redteam.py`, `vector_query.py`, `source_independence.py`, `embeddings_backfill.py`

**`backend/app/connectors/`:**
- Purpose: external-source adapters producing bronze records only
- Key files: `base.py` (SourceConnector ABC, ProfileRunResult, RunStatus), `pubmed.py`, `clinical_trials.py`, `fda.py`, `ema.py`, `newsapi.py`, `__init__.py` (`ALL_CONNECTORS` registry)

**`backend/app/models/`:**
- Purpose: SQLAlchemy ORM schema — deliberately a single module
- Key files: `__init__.py` defines PipelineRun, Source, SourceHealthLog, Company, Asset, ClinicalTrial, Development, Event, LifecycleEvent, Confluence, RawSignalBronze, ConnectorState, Evidence, Signal (with pgvector column), Contradiction, CalibrationRun, CalibrationHistory, ScoringWeights, SignalRouting, CalibrationFeedback, WatchItem, AuditLog

**`frontend/components/<domain>/:`:**
- Purpose: self-contained workspace per UI section
- Pattern: `<Name>Workspace.tsx` client component consuming `@/lib/api` via `useLiveData`

**`config/`:**
- Purpose: domain behavior without code changes — assets, diseases, lifecycle stages, confluence thresholds, baseline function-routing matrix, per-connector query profiles

**`contracts/` + `scripts/export_openapi.py` + `tests/test_contract_drift.py`:**
- Purpose: FE/BE contract synchronization loop

**`docs/rules/`:**
- Purpose: mandatory process standards referenced by `AGENTS.md` (engineering, testing, security, CI/CD, workflow)

## Key File Locations

**Entry Points:**
- `start.py`: unified launcher (Docker services → migrations → uvicorn → next dev)
- `backend/app/main.py`: FastAPI app factory-equivalent (module-level `app`); lifespan starts/stops scheduler
- `frontend/app/layout.tsx` + `frontend/app/[section]/page.tsx`: UI entry chain
- `docker-compose.yml`: full-containerized alternative

**Configuration:**
- `backend/app/core/config.py`: env-driven Settings singleton (DB/Redis URLs, LLM provider, scheduler intervals, embedding model pin)
- `config/haemophilia.yaml`: canonical domain configuration loaded by `backend/app/core/domain_config.py`
- `.env` / `.env.example`: secrets & environment (`.env` gitignored — existence only, never read contents)
- `backend/alembic.ini`: migration config
- `pytest.ini`: root test runner config
- `frontend/tsconfig.json`: path alias `@/*` → frontend root

**Core Logic:**
- `backend/app/workflows/graph.py` + `nodes/`: intelligence pipeline
- `backend/app/workflows/runner.py`: persistence bridge pipeline→DB
- `backend/app/services/scheduler.py`: autonomous ingestion loops
- `backend/app/connectors/base.py`: ingestion contract
- `backend/app/models/__init__.py`: full relational schema

**Testing:**
- `tests/test_*.py`: all backend tests (flat, root-configured by `pytest.ini`)
- `scripts/test_live_ingestion_e2e.py`: live E2E ingestion script
- No frontend unit tests detected; verification is strict `tsc`/`next build` + backend suite

## Naming Conventions

**Files:**
- Python modules: `snake_case.py` (`domain_config.py`, `vector_query.py`)
- Workflow nodes: named after the node — `node_ingest` lives in `nodes/ingest.py`
- React components: `PascalCase.tsx` (`CalibrationWorkspace.tsx`, `SignalList.tsx`)
- Frontend lib modules: `camelCase.ts` (`api.ts`, `mappers.ts`, `errors.ts`)
- Migrations: `NNN_snake_description.py` (`004_phase7_truthfulness_and_provenance.py`)
- Tests: `test_<area>.py` flat under `tests/`

**Directories:**
- Frontend component domains: `kebab-case` (`missing-signals/`, matching the `/missing-signals` route section)
- Backend packages: singular nouns where possible (`connector` logic lives in `connectors/`, models in `models/`)

**Code symbols:**
- Python classes: PascalCase (`SourceScheduler`, `PipelineRunner`, `RawSignalBronze`)
- Python functions/variables: `snake_case`; node entry points prefixed `node_`
- Service singletons exported as lowercase instances (`priority_scorer`, `embedding_service`, `provider_factory`, `confluence_engine`)
- React hooks: `useX` prefix (`useLiveData`)
- API client functions: `fetchX` for raw fetchers, `getX` aliases for backward compatibility (`frontend/lib/api.ts:38-126`)

## Where to Add New Code

**New REST endpoint:**
1. Add handler to the relevant router in `backend/app/api/v1/endpoints/` (create new module only for a genuinely new resource group; register it in `backend/app/main.py`)
2. Define response models in `backend/app/schemas/intelligence.py` or `registry.py`
3. Run `python scripts/export_openapi.py` and sync `frontend/types/api.ts` (CI enforces zero drift via `tests/test_contract_drift.py`)
4. Add typed client function in `frontend/lib/api.ts`

**New source connector:**
1. Subclass `SourceConnector` in `backend/app/connectors/<source>.py`
2. Register instance in `ALL_CONNECTORS` (`backend/app/connectors/__init__.py`)
3. Add a `connectors.<source_id>` block with query profiles to `config/haemophilia.yaml`
4. Optionally add `SCHEDULER_<SOURCE>_INTERVAL_MINUTES` to `Settings` (`backend/app/core/config.py`) and wire into `_init_job_states` (`backend/app/services/scheduler.py:63-73`)
5. Add tests under `tests/test_connector_health.py` patterns

**New LangGraph node:**
1. Create `backend/app/workflows/nodes/<name>.py` exporting `async def node_<name>(state: MetaRadarState, session: Optional[AsyncSession] = None)`
2. Follow the error pattern: catch exceptions → append to `errors` channel → set `node_statuses`
3. Register in `graph.py` (`add_node` + edges) and import from `nodes/__init__.py`
4. Extend `MetaRadarState` channels in `state.py` if new data must flow (choose reducer carefully)

**New database table/column:**
1. Add model class to `backend/app/models/__init__.py`
2. Generate revision: `alembic revision -N NNN_description` in `backend/`; hand-write upgrade/downgrade against `Base.metadata` conventions used by existing versions
3. Update seed data if needed (`backend/app/db/seed.py`)

**New frontend workspace/section:**
1. Create `frontend/components/<domain>/<Name>Workspace.tsx` ('use client', consume `@/lib/api` through `useLiveData`)
2. Add case to the switch in `frontend/app/[section]/page.tsx`
3. Add nav entry to the `nav`/`secondary` arrays in `frontend/components/metaradar.tsx`
4. Use `common/ErrorState.tsx`, `common/EmptyState.tsx`, `common/EvidenceDrawer.tsx` for consistency

**Utilities:**
- Shared backend helpers → `backend/app/services/` (if domain logic) or `backend/app/core/` (if infra)
- Shared frontend helpers → `frontend/lib/utils.ts` or a focused module in `frontend/lib/`

## Special Directories

**`data/` and `backend/app/data/`:**
- Purpose: synthetic fallback signal dataset (`synthetic_signals.json`) duplicated at both paths so the pipeline finds it from any working directory (`backend/app/workflows/nodes/ingest.py:15-36`)
- Generated: No — curated fixture content
- Committed: Yes

**`logs/`:**
- Purpose: runtime stdout/stderr streams captured by `start.py`
- Generated: Yes (runtime)
- Committed: No (gitignored via `*.log` rules)

**`scratch/`:**
- Purpose: throwaway experiments
- Generated: ad hoc
- Committed: No (explicitly gitignored)

**`.planning/`:**
- Purpose: GSD workflow artifacts (phases, milestones, codebase maps like this document)
- Committed: Yes (planning history is tracked)

**`docs/`:**
- Purpose: canonical standards and design documents; `docs/rules/` is normative for all agents per `AGENTS.md`
- Committed: Yes

---

*Structure analysis: 2026-08-23*
