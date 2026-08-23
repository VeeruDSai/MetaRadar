<!-- refreshed: 2026-08-23 -->
# Architecture

**Analysis Date:** 2026-08-23

## System Overview

MetaRadar is an AI-powered competitive-intelligence platform for haemophilia. It is a two-tier system: a Next.js 16 frontend consuming a FastAPI backend, which runs a LangGraph intelligence pipeline over data ingested from five public biomedical sources.

```text
┌──────────────────────────────────────────────────────────────────────┐
│                  Presentation — Next.js 16 / React 19                │
│   Route switcher  `frontend/app/[section]/page.tsx`                  │
│   Workspaces      `frontend/components/<domain>/*Workspace.tsx`      │
│   API client      `frontend/lib/api.ts`                              │
│   Polling hook    `frontend/lib/hooks.ts` (useLiveData)              │
│   Contracts       `frontend/types/api.ts` (synced from OpenAPI)      │
└──────────────────────────────┬───────────────────────────────────────┘
                               │ fetch → http://localhost:8000/api/v1/*
                               ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    API Layer — FastAPI (`backend/app/main.py`)       │
│    Routers: `backend/app/api/v1/endpoints/*.py` (10 modules)         │
├───────────────┬─────────────────────────────┬────────────────────────┤
│ Service Layer │ Intelligence Engine          │ Ingestion Plane        │
│               │ (LangGraph)                  │                        │
│ `app/services/│ `app/workflows/graph.py`     │ `app/services/scheduler│
│  scoring,     │ 11 nodes in linear chain:    │  .py` (singleton,      │
│  confluence,  │  ingest → validate → embed → │  asyncio workers)      │
│  embeddings,  │  nlp_extract → ontology →    │ `app/connectors/*`     │
│  calibration, │  confluence → lifecycle →    │ (5 source adapters)    │
│  pii, dedup,  │  redteam → missing_signal →  │                        │
│  vector_query │  synthesize → calibrate      │ LLM providers:         │
│               │ Runner: `workflows/runner.py`│ `app/providers/*`      │
├───────────────┴──────────────┬──────────────┴────────────────────────┤
│            Persistence — SQLAlchemy 2.0 async ORM                   │
│            `backend/app/models/__init__.py` (22 tables)             │
│            PostgreSQL 16 + pgvector · Redis 7 (locks/cache)         │
│            Migrations: `backend/alembic/versions/001–011`           │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app | Router registration, CORS, correlation middleware, lifespan scheduler start | `backend/app/main.py` |
| Endpoint routers | HTTP handlers, Pydantic response serialization | `backend/app/api/v1/endpoints/*.py` |
| PipelineRunner | Orchestrates graph runs; persists gold/silver entities to DB; tracks `PipelineRun` lifecycle | `backend/app/workflows/runner.py` |
| MetaRadarState | Typed state contract for all pipeline channels (with reducers) | `backend/app/workflows/state.py` |
| Graph builder | Assembles/wires the 11-node linear pipeline | `backend/app/workflows/graph.py` |
| Workflow nodes | One atomic transformation per node (ingest, validate, embed, extract, ontology, confluence, lifecycle, redteam, missing-signal, synthesize, calibrate) | `backend/app/workflows/nodes/*.py` |
| SourceScheduler | Singleton background asyncio scheduler: per-connector worker loops, jitter, exponential backoff, circuit breaker, PG advisory locks | `backend/app/services/scheduler.py` |
| IngestionService | Executes connector profiles, resolves truthful health status precedence, writes `sources`/`source_health_logs` telemetry | `backend/app/services/ingestion.py` |
| SourceConnector ABC | Contract for isolated, idempotent, config-driven source adapters (bronze-only persistence) | `backend/app/connectors/base.py` |
| Connector registry | Instantiates the five adapters at import time | `backend/app/connectors/__init__.py` |
| LLM providers | Capability-based abstraction: local Gemma (`gemma.py`), xAI Grok fallback (`grok.py`), degraded stub (`degraded.py`), selection via `factory.py` | `backend/app/providers/*.py` |
| Domain config loader | Validates `config/haemophilia.yaml` into typed pydantic models (assets, diseases, connectors, routing matrix, lag thresholds) | `backend/app/core/domain_config.py` |
| Settings | Env-driven configuration via pydantic-settings | `backend/app/core/config.py` |
| ORM models | All 22 tables in one module (Signal carries pgvector embedding column) | `backend/app/models/__init__.py` |
| DB session | Async engine/session factory, per-request `get_db` dependency, advisory-lock helpers | `backend/app/db/session.py` |
| API client | Single typed fetch surface for all backend calls; ApiError with retryable flag + request-id | `frontend/lib/api.ts` |
| Route shell | Client-side section router mapping `/[section]` to workspace components | `frontend/app/[section]/page.tsx`, `frontend/components/metaradar.tsx` |

## Pattern Overview

**Overall:** Layered monolith with two internal planes — a synchronous request/response REST stack and an asynchronous batch intelligence plane (scheduler + LangGraph pipeline) — sharing one PostgreSQL database.

**Key Characteristics:**
- **Medallion-style persistence:** raw payloads land immutable in `raw_signals_bronze`; the pipeline promotes them to silver `signals` (with embeddings) and gold `developments`/`confluences`. Bronze rows are only marked promoted when silver upserts succeed (`backend/app/workflows/runner.py`, `_persist_state_to_db`).
- **Config-driven behavior:** domain ontology, asset registry, connector query profiles, and scoring thresholds live in `config/haemophilia.yaml`, validated by `backend/app/core/domain_config.py`. Connectors execute YAML query blocks — they never invent queries.
- **Linear deterministic pipeline:** no conditional edges or cycles; exactly 11 nodes executed in fixed order (`backend/app/workflows/graph.py`).
- **Contract-first frontend:** TypeScript types in `frontend/types/api.ts` are synchronized from exported OpenAPI (`contracts/openapi.json`, generated by `scripts/export_openapi.py`); drift is caught by `tests/test_contract_drift.py`.

## Layers

**Presentation (frontend):**
- Purpose: workspace UI, polling-based live data, evidence/provenance display
- Location: `frontend/app/`, `frontend/components/`, `frontend/lib/`
- Depends on: backend REST API through `frontend/lib/api.ts` only
- Used by: end users; root route redirects `/` → `/dashboard` (`frontend/app/page.tsx`)

**API layer:**
- Purpose: HTTP surface, validation, serialization; no business logic beyond serialization helpers (e.g., `_serialize_signal` in `backend/app/api/v1/endpoints/signals.py`)
- Location: `backend/app/main.py` registers routers under `{settings.API_V1_STR}` = `/api/v1`
- Depends on: service layer singletons, ORM models, schemas (`backend/app/schemas/intelligence.py`, `registry.py`)
- Used by: frontend and tests

**Service layer:**
- Purpose: reusable business logic — scoring (`services/scoring.py`), confluence detection (`services/confluence.py`), embeddings (`services/embeddings.py`), HITL calibration (`services/calibration.py`), deduplication (`services/deduplication.py`), PII scrubbing (`services/pii.py`), relevance gating (`services/relevance.py`), red-team rules (`services/redteam.py`), vector search (`services/vector_query.py`)
- Location: `backend/app/services/`
- Depends on: ORM models, providers, db session
- Used by: endpoints, workflow nodes, scheduler

**Intelligence engine (workflow):**
- Purpose: stateful multi-step signal processing via LangGraph
- Location: `backend/app/workflows/`
- Depends on: services, models, providers, optional injected `AsyncSession`
- Used by: `PipelineRunner` invoked by scheduler (on new records) and `/pipeline` / `/ingestion/sync-live` endpoints

**Ingestion plane:**
- Purpose: pull raw data from public APIs into bronze without generating intelligence
- Location: `backend/app/connectors/` (adapters), `backend/app/services/scheduler.py` + `services/ingestion.py` (orchestration)
- Depends on: httpx, domain config, bronze model, dedup service
- Used by: background scheduler (autonomous) and manual sync endpoints (`endpoints/ingestion.py`)

**LLM provider layer:**
- Purpose: capability-checked reasoning backends with local-first policy and privacy classification (`DataClassification` gates what may be sent where)
- Location: `backend/app/providers/base.py`, `factory.py`, `gemma.py`, `grok.py`, `degraded.py`
- Depends on: Ollama sidecar (docker-compose service `ollama`) or transformers locally; xAI API when enabled
- Used by: synthesis/Athena paths in endpoints and nodes

**Data layer:**
- Purpose: relational persistence + vector index
- Location: `backend/app/models/__init__.py` (single module holds every table class), `backend/app/db/session.py`, migrations `backend/alembic/versions/`
- Depends on: SQLAlchemy async engine (asyncpg), pgvector extension
- Used by: everything above

## Data Flow

### Primary Request Path (read)

1. Browser client component calls a typed helper in `frontend/lib/api.ts` (e.g. `getSignals`, `fetchOverview`) — polling driven by `useLiveData` (`frontend/lib/hooks.ts`, default 30s, visibility-aware, abort-safe)
2. `apiFetch` issues `fetch` against `${NEXT_PUBLIC_API_URL}${endpoint}` (`frontend/lib/api.ts:142-195`); errors become `ApiError` carrying status, retryable flag, and `x-request-id`
3. FastAPI endpoint handler queries PostgreSQL via injected `AsyncSession` (`get_db` dependency, `backend/app/db/session.py:31-40`)
4. Rows serialized to pydantic response models; frontend maps raw JSON into UI types via `frontend/lib/mappers.ts`

### Ingestion Flow (background, autonomous)

1. App lifespan starts `SourceScheduler.get_instance().start()` (`backend/app/main.py:43-46`); one asyncio task per connector with startup jitter (`backend/app/services/scheduler.py:90-95`)
2. Worker acquires a PostgreSQL advisory lock derived from `source_id` hash, then calls `IngestionService.run_connectors([source_id])` (`backend/app/services/scheduler.py:114-150`)
3. Connector executes each configured profile (`SourceConnector.run_all_profiles`, `backend/app/connectors/base.py`), applies retries/backoff, and persists verbatim payloads to `raw_signals_bronze` via `check_and_persist_bronze` (`backend/app/services/deduplication.py`)
4. Health telemetry written to `sources` + `source_health_logs` with truthful status precedence `CONFIGURATION_ERROR > FAILED > DEGRADED > NO_NEW_DATA > HEALTHY` (`backend/app/services/ingestion.py:72-90`)
5. If new records were found, the worker triggers `PipelineRunner` (decoupling: ingestion ≠ intelligence execution)

### Intelligence Pipeline Flow

1. `PipelineRunner.run()` creates a `pipeline_runs` row and loads unpromoted bronze records (`backend/app/workflows/runner.py:38-96`)
2. `graph.compile().ainvoke(initial_state)` executes the fixed 11-node chain (`backend/app/workflows/graph.py:45-56`); each node returns channel updates merged by reducers defined in `backend/app/workflows/state.py`
3. Relevance gate filters bronze records first (`node_ingest` → `RelevanceGate.evaluate`, `backend/app/workflows/nodes/ingest.py:77-86`)
4. After `END`, `_persist_state_to_db` upserts developments, signals (embedding + fingerprint conflict target), and confluences; failed signal IDs keep their bronze rows unpromoted for retry (`backend/app/workflows/runner.py:141-369`)
5. `PipelineRun` marked completed with counters (signals_created, duplicates_removed, error_summary)

### Calibration Flow (HITL)

1. Stakeholder submits ratings via `POST /feedback` → `calibration_feedback` rows (`backend/app/api/v1/endpoints/feedback.py`)
2. `POST /calibrate` triggers recalibration using `backend/app/services/calibration.py`, producing `calibration_runs` + updated `scoring_weights` consumed by later scoring/routing

**State Management:**
- Server: stateless request handling; all durable state in PostgreSQL. Process-scoped singletons exist for the scheduler, settings, and service instances (see Architectural Constraints)
- Pipeline: all intermediate data flows through the `MetaRadarState` TypedDict; list channels accumulate via `operator.add`, `validated_signals` uses replacement semantics (`replace_list`) to avoid duplication, dicts merge via `merge_dicts` (`backend/app/workflows/state.py`)
- Client: per-component polling state via `useLiveData`; theme via localStorage-backed `ThemeProvider` (`frontend/components/theme/ThemeProvider.tsx`); no global store (no Redux/Zustand)

## Key Abstractions

**MetaRadarState (pipeline contract):**
- Purpose: canonical typed channels shared by all 11 nodes
- Examples: `backend/app/workflows/state.py`
- Pattern: `TypedDict(total=False)` + `Annotated` reducers; factory `create_initial_state()`

**SourceConnector (ingestion contract):**
- Purpose: uniform adapter interface — profiles from YAML, retry/timeout knobs, truthful `RunStatus` literals, `ProfileRunResult` telemetry
- Examples: `backend/app/connectors/pubmed.py`, `clinical_trials.py`, `fda.py`, `ema.py`, `newsapi.py`
- Pattern: Template Method base class registered as module-level instances in `ALL_CONNECTORS`

**LLMProvider (reasoning contract):**
- Purpose: pluggable summarization/reasoning with capability checks and `DataClassification` privacy gate
- Examples: `backend/app/providers/gemma.py` (local Gemma 3 4B via Ollama), `grok.py` (hosted fallback), `degraded.py` (honest unavailable stub)
- Pattern: Strategy selected by `provider_factory` based on `LLM_PROVIDER` setting

**Synced API contracts:**
- Purpose: eliminate FE/BE drift
- Examples: `contracts/openapi.json` ← `scripts/export_openapi.py` → `frontend/types/api.ts`, enforced by `tests/test_contract_drift.py`
- Pattern: export-and-sync codegen check

## Entry Points

**Unified launcher (primary developer entry):**
- Location: `start.py` (also `setup.py` for setup assistance)
- Triggers: `python start.py [--no-frontend|--no-backend|--no-docker|...]`
- Responsibilities: starts Docker Postgres/Redis, frees occupied ports, applies Alembic migrations, launches uvicorn backend + Next.js frontend, streams logs to `logs/`

**FastAPI application:**
- Location: `backend/app/main.py`
- Triggers: uvicorn; lifespan hook starts/stops `SourceScheduler`
- Responsibilities: middleware (CorrelationId → CORS), registers 10 routers under `/api/v1`, exposes `/docs` and root metadata

**Next.js application:**
- Location: `frontend/app/layout.tsx`, `frontend/app/page.tsx` (redirect to `/dashboard`), dynamic section renderer `frontend/app/[section]/page.tsx`
- Triggers: browser navigation; sections: dashboard, signals, confluence, lifecycles, red-team, missing-signals, developments, intelligence, functions, calibrate, sources, observability, settings

**Docker Compose (full-stack alternative):**
- Location: `docker-compose.yml` — services: postgres (pgvector/pg16), redis:7, ollama (Gemma 3 4B GPU sidecar), backend (+ `backend-gpu` profile), frontend

## Architectural Constraints

- **Threading:** fully async I/O — asyncpg engine, `async_session_factory`, `asyncio.Task` workers; LangGraph invoked with `ainvoke`. No thread pools in app code. Node signature convention: `async def node_x(state: MetaRadarState, session: Optional[AsyncSession] = None)`
- **Global state:** module-level singletons — `settings` (`backend/app/core/config.py:78`), `SourceScheduler._instance` (`backend/app/services/scheduler.py:48`), `ALL_CONNECTORS` pre-instantiated adapters (`backend/app/connectors/__init__.py`), `priority_scorer`, `confluence_engine`, `embedding_service`, `provider_factory` (service modules). Treat these as process-wide; do not mutate at runtime outside their own APIs
- **Distributed execution safety:** concurrent backend replicas coordinate via PostgreSQL advisory locks keyed by MD5 of `metaradar_lock_{source_id}` (`backend/app/db/session.py:43-60`, `backend/app/services/scheduler.py:20-23`)
- **Circular imports:** none observed between layers; dependencies flow strictly downward (api → services/workflows → models). Lazy imports used deliberately inside functions/lifespan (e.g., scheduler imported inside `lifespan`) to avoid import-time DB/model side effects
- **Bronze immutability:** connectors persist verbatim payloads only; intelligence is produced exclusively downstream in workflow nodes (`backend/app/connectors/base.py` docstring D-26)
- **Truthfulness invariants:** synthetic fixtures must be flagged `is_synthetic=True`, `data_mode="test_fixture"`, `provenance_status="fixture"` (`backend/app/workflows/nodes/ingest.py:27-33`); zero-record healthy polls report `NO_NEW_DATA`, never fabricated counts
- **Embedding dimension lock:** `signals.embedding` is `Vector(settings.EMBEDDING_DIMENSION)` = 384 tied to pinned model revision (`backend/app/models/__init__.py:265`, `backend/app/core/config.py:46-49`); changing models requires migration + backfill (`backend/app/services/embeddings_backfill.py`)

## Anti-Patterns

### Adding UI to the monolithic shell component

**What happens:** `frontend/components/metaradar.tsx` is ~2079 lines containing Shell, DashboardPage, LifecyclePage, GenericPage, badges, drawers, and inline widgets.
**Why it's wrong:** any edit to one workspace risks re-render/type-check churn across all of them; merge conflicts concentrate here.
**Do this instead:** create a dedicated directory `frontend/components/<domain>/<Name>Workspace.tsx` (pattern used by `calibration/CalibrationWorkspace.tsx`, `sources/SourcesOperationsWorkspace.tsx`, etc.) and register it in the switch in `frontend/app/[section]/page.tsx`.

### Calling fetch directly from components

**What happens:** ad-hoc `fetch()` in a component bypasses error normalization and contract typing.
**Why it's wrong:** loses `ApiError` semantics (retryable flag, requestId), breaks the synced-contract guarantee, duplicates URL logic.
**Do this instead:** add a typed function to `frontend/lib/api.ts` and consume it via `useLiveData` (`frontend/lib/hooks.ts`).

### Generating intelligence inside connectors

**What happens:** tempting to enrich/classify during fetch to "save a step".
**Why it's wrong:** violates the bronze-immutability design rule and makes ingestion non-replayable/non-idempotent.
**Do this instead:** persist verbatim payload to bronze; put transformations in a workflow node under `backend/app/workflows/nodes/`.

## Error Handling

**Strategy:** fail-soft per unit of work with explicit status surfaces; never fabricate success.

**Patterns:**
- Pipeline nodes catch their own exceptions, append structured entries to the `errors` state channel, set `node_statuses[node] = "FAILED"`, and return partial results (`backend/app/workflows/nodes/ingest.py:127-139`)
- `PipelineRunner` marks the run `failed`/`completed` accordingly and records `error_summary` JSONB (`backend/app/workflows/runner.py:112-139`); per-record persistence failures log warnings and skip bronze promotion so records retry next run
- Scheduler wraps each cycle in try/except, tracking `consecutive_failures` → exponential backoff → circuit-breaker thresholds (`backend/app/services/scheduler.py`)
- Endpoints raise `HTTPException` for bad input; `get_db` commits on success and rolls back on exception (`backend/app/db/session.py:31-40`)
- Frontend normalizes every failure into `ApiError(status, statusText, message, retryable, requestId, endpoint)` (`frontend/lib/errors.ts`, raised in `frontend/lib/api.ts:144-195`); workspaces render `ErrorState`/`EmptyState` common components (`frontend/components/common/`)

## Cross-Cutting Concerns

**Logging:** structlog JSON configured at startup (`configure_structlog(json_logs=True)`, `backend/app/core/logging.py`); `CorrelationIdMiddleware` attaches `x-request-id` echoed by the frontend (`backend/app/core/middleware.py`); stdlib logging elsewhere with `metaradar.*` logger names.

**Validation:** pydantic v2 everywhere — request/response schemas (`backend/app/schemas/intelligence.py`, `registry.py`), settings (`backend/app/core/config.py`), domain YAML (`backend/app/core/domain_config.py`). PII/PHI scrubbing before persistence via `backend/app/services/pii.py`.

**Authentication:** none detected — open local/trusted-network deployment; CORS restricted to configured origins (default `http://localhost:3000`, `backend/app/core/config.py:23`). Do not expose publicly without adding auth.

**Configuration sources:** environment variables (`.env`, loaded by pydantic-settings; `.env.example` documents keys — existence only, contents never committed) + canonical domain YAML (`config/haemophilia.yaml`).

---

*Architecture analysis: 2026-08-23*
