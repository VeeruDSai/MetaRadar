<!-- refreshed: 2026-08-24 -->
# Architecture

**Analysis Date:** 2026-08-24

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────┐
│                     FRONTEND — Next.js 16 (App Router)                │
│   `frontend/app/layout.tsx` · `frontend/app/[section]/page.tsx`      │
├──────────────────┬───────────────────┬───────────────────────────────┤
│  Shell + Pages   │ Workspace         │ Data Access                   │
│  `frontend/      │ Components        │ `frontend/lib/api.ts`         │
│  components/     │ `frontend/        │ `frontend/lib/mappers.ts`     │
│  metaradar.tsx`  │ components/*`     │ `frontend/lib/hooks.ts`       │
└────────┬─────────┴─────────┬─────────┴──────────────┬────────────────┘
         │                   │                        │
         └───────────────────┴──── REST (JSON) ───────┘
                             ▼
┌──────────────────────────────────────────────────────────────────────┐
│                BACKEND API LAYER — FastAPI (`/api/v1`)                │
│      `backend/app/main.py` → `backend/app/api/v1/endpoints/*`        │
├──────────────────────────────────────────────────────────────────────┤
│  SERVICE LAYER                                                       │
│  `backend/app/services/` — ingestion, scheduler, scoring,            │
│  confluence, embeddings, calibration, deduplication, redteam,        │
│  relevance, pii, provenance_urls, vector_query                       │
├───────────────────────────────┬──────────────────────────────────────┤
│  WORKFLOW ENGINE (LangGraph)  │  PROVIDER LAYER (LLM fallback chain) │
│  `backend/app/workflows/`     │  `backend/app/providers/`            │
│  11-node linear StateGraph    │  Gemma → Grok → Degraded BART        │
├───────────────────────────────┴──────────────────────────────────────┤
│  CONNECTOR LAYER (source adapters)                                   │
│  `backend/app/connectors/` — PubMed, ClinicalTrials.gov, FDA, EMA,   │
│  NewsAPI (bronze-only persistence contract)                          │
└───────────────────────────────┬──────────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────────┐
│  PERSISTENCE                                                          │
│  `backend/app/models/__init__.py` (SQLAlchemy, 22 tables)            │
│  `backend/app/db/session.py` (async engine + advisory locks)          │
│  PostgreSQL 16 + pgvector (384-dim HNSW) · Redis 7                    │
│  Bronze (`raw_signals_bronze`) → Silver (`signals`) → Gold            │
│  (`developments`, `confluences`, ...)                                 │
└──────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app | Router registration, CORS, correlation-ID middleware, lifespan scheduler start/stop | `backend/app/main.py` |
| API endpoints | HTTP request handling, Pydantic serialization per resource | `backend/app/api/v1/endpoints/*.py` |
| Schemas | Request/response contracts; source of OpenAPI export | `backend/app/schemas/__init__.py`, `backend/app/schemas/intelligence.py`, `backend/app/schemas/registry.py` |
| Workflow engine | 11-node LangGraph pipeline assembly and execution | `backend/app/workflows/graph.py`, `backend/app/workflows/runner.py` |
| Pipeline state | TypedDict state contract with channel reducers | `backend/app/workflows/state.py` |
| Intelligence nodes | One file per pipeline stage (`node_ingest` … `node_calibrate`) | `backend/app/workflows/nodes/*.py` |
| Ingestion service | Orchestrates connector profile runs, aggregates telemetry | `backend/app/services/ingestion.py` |
| Scheduler | Autonomous asyncio worker loop per connector with backoff/jitter/advisory locking | `backend/app/services/scheduler.py` |
| Connectors | Source-specific fetch adapters; bronze-only persistence | `backend/app/connectors/base.py` + one file per source |
| Provider factory | LLM capability routing with fallback chain and privacy gate | `backend/app/providers/factory.py` |
| Domain config | YAML-driven haemophilia ontology, connector query profiles, thresholds | `backend/app/core/domain_config.py`, `config/haemophilia.yaml` |
| ORM models | 22-table relational schema incl. pgvector embedding column | `backend/app/models/__init__.py` |
| DB session | Async engine, session factory, `get_db` dependency, advisory locks | `backend/app/db/session.py` |
| Frontend shell | App chrome, nav, section routing switch | `frontend/components/metaradar.tsx`, `frontend/app/[section]/page.tsx` |
| API client | Single typed fetch layer over `/api/v1` | `frontend/lib/api.ts` |
| Live-data hook | Polling with AbortController, visibility pause, in-flight guard | `frontend/lib/hooks.ts` |

## Pattern Overview

**Overall:** Layered monorepo with an embedded workflow engine. FastAPI layered architecture (API → services → models) plus a LangGraph state-machine pipeline for intelligence processing, and a config-driven connector framework for external data acquisition.

**Key Characteristics:**
- **Bronze/Silver/Gold data layering**: raw payloads land immutable in `raw_signals_bronze`; promoted/deduplicated into `signals` (silver) with embeddings; aggregated into gold entities (`developments`, `confluences`, `lifecycle_events`)
- **Config-driven connectors**: connectors execute queries defined in `config/haemophilia.yaml` — they never invent queries (decision refs D-08/D-10)
- **Provider fallback chain**: local Gemma GGUF/Ollama → hosted Grok (privacy-gated by `DataClassification`) → deterministic degraded BART summarizer (`backend/app/providers/factory.py`)
- **Truthful telemetry**: health statuses are explicit enums (`HEALTHY`, `NO_NEW_DATA`, `DEGRADED`, `CONFIGURATION_ERROR`, …); zero-record valid responses are never reported as failures (`backend/app/connectors/base.py` `_run_status_to_health_state`)
- **Contract-synced frontend**: `scripts/export_openapi.py` generates `frontend/types/api.ts` from the canonical template; CI fails on drift

## Layers

**API Layer:**
- Purpose: HTTP surface; validation via Pydantic; no business logic beyond serialization helpers
- Location: `backend/app/api/v1/endpoints/`
- Contains: 10 routers (`health`, `signals`, `intelligence`, `registry`, `observability`, `cache`, `pipeline`, `ingestion`, `search`, `feedback`)
- Depends on: services, models, schemas, `app.db.session.get_db`
- Used by: frontend `lib/api.ts`, CI health checks

**Service Layer:**
- Purpose: Domain capabilities — ingestion orchestration, scheduling, scoring, embeddings, confluence, calibration, deduplication, red-team rules, relevance gating, PII scrubbing, provenance URL resolution, vector search
- Location: `backend/app/services/`
- Contains: module-level singleton engines (e.g., `priority_scorer`, `embedding_service`, `confluence_engine`) and session-scoped services (`IngestionService(session)`)
- Depends on: models, core config, providers
- Used by: API endpoints, workflow nodes, scheduler

**Workflow Layer (LangGraph):**
- Purpose: Stateful 11-node intelligence pipeline
- Location: `backend/app/workflows/` (graph, state, runner) and `backend/app/workflows/nodes/`
- Contains: `build_graph()` compiled `StateGraph(MetaRadarState)`; `PipelineRunner` managing `PipelineRun` DB lifecycle and post-run persistence
- Depends on: services (embeddings, scoring), models
- Used by: `PipelineRunner.run()` invoked from scheduler (after new records) and `api/v1/endpoints/pipeline.py`

**Connector Layer:**
- Purpose: Isolated, idempotent, quota-aware source adapters persisting bronze rows only
- Location: `backend/app/connectors/`
- Contains: abstract `SourceConnector` base (retry/backoff, bronze persistence, connector-state I/O, health logging) plus `PubMedConnector`, `ClinicalTrialsConnector`, `NewsAPIConnector`, `OpenFDAConnector`, `EMARSSConnector` registered in module-level `ALL_CONNECTORS` list (`backend/app/connectors/__init__.py`)
- Depends on: domain config, deduplication service, redaction utilities
- Used by: `IngestionService`

**Provider Layer:**
- Purpose: LLM abstraction with capability checks and classification-based privacy gate
- Location: `backend/app/providers/`
- Contains: `LLMProvider` base (`base.py`), `GemmaProvider`, `GrokProvider`, `DegradedProvider`, `ProviderFactory`
- Depends on: core settings
- Used by: endpoints that need synthesis (e.g., Athena Q&A in `api/v1/endpoints/signals.py`)

**Data Layer:**
- Purpose: Persistence and schema management
- Location: `backend/app/models/__init__.py`, `backend/app/db/session.py`, migrations in `backend/alembic/versions/`
- Contains: 22 SQLAlchemy tables (`PipelineRun`, `Source`, `SourceHealthLog`, `Company`, `Asset`, `ClinicalTrial`, `Development`, `Event`, `LifecycleEvent`, `Confluence`, `RawSignalBronze`, `ConnectorState`, `Evidence`, `Signal`, `Contradiction`, `CalibrationRun`, `CalibrationHistory`, `ScoringWeights`, `SignalRouting`, `CalibrationFeedback`, `WatchItem`, `AuditLog`)
- Depends on: settings (`DATABASE_URL`)
- Used by: everything above

## Data Flow

### Primary Ingestion Path (autonomous)

1. FastAPI lifespan starts `SourceScheduler` singleton (`backend/app/main.py:44-46`)
2. Per-connector asyncio worker acquires PostgreSQL advisory lock, then calls `IngestionService.run_connectors([source_id])` (`backend/app/services/scheduler.py:114-175`)
3. Connector executes YAML-configured profiles via `_fetch_with_retry` (bounded exponential backoff + jitter), deduplicates, persists raw payloads to `raw_signals_bronze`, writes `SourceHealthLog` telemetry (`backend/app/connectors/base.py`)
4. If new records discovered, scheduler triggers `PipelineRunner.run(batch_size=50)` in a fresh session (`backend/app/services/scheduler.py:166-175`)

### Intelligence Pipeline Path (LangGraph)

1. `PipelineRunner.__init__` compiles graph once; `run()` creates a `PipelineRun` row and loads unpromoted bronze records (`backend/app/workflows/runner.py:35-97`)
2. Linear node execution: `node_ingest → node_validate → node_embed → node_nlp_extract → node_ontology_enrich → node_confluence → node_lifecycle → node_redteam → node_missing_signal → node_synthesize → node_calibrate → END` (`backend/app/workflows/graph.py:46-59`)
3. Nodes mutate shared `MetaRadarState` via reducers (`operator.add` for accumulating lists, `merge_dicts` for weights/statuses, `replace_list` for the validated-signals channel) (`backend/app/workflows/state.py:26-52`)
4. `_persist_state_to_db` upserts silver `signals` on `fingerprint` conflict (pgvector embedding included), inserts gold `Development`/`Confluence` rows with FK-validity pre-checks, then marks only successfully persisted bronze rows as promoted (`backend/app/workflows/runner.py:142-366`)

### Read Path (frontend)

1. User opens `/[section]` → server component maps section to workspace component (`frontend/app/[section]/page.tsx:14-74`)
2. Client component calls typed wrapper from `frontend/lib/api.ts` → `apiFetch<T>` against `NEXT_PUBLIC_API_URL || http://localhost:8000/api/v1`
3. `useLiveData` hook polls every 30s, pauses on hidden tab, aborts stale requests (`frontend/lib/hooks.ts`)
4. Raw API payloads normalized through `mapSignal`/mappers (`frontend/lib/mappers.ts`) before render

### Calibration / HITL Path

1. Stakeholder submits feedback via `POST /feedback` (`backend/app/api/v1/endpoints/feedback.py`)
2. Weights recalibration updates role weighting matrices (`backend/app/services/calibration.py`); consumed by `node_calibrate` and priority scoring

**State Management:**
- Backend pipeline state lives entirely in the LangGraph `MetaRadarState` dict during a run; durable state is PostgreSQL only
- Frontend has no global store: local component state + `useLiveData` polling + React Context limited to theming (`frontend/components/theme/ThemeProvider.tsx`)

## Key Abstractions

**MetaRadarState (TypedDict with Annotated reducers):**
- Purpose: Canonical contract for data flowing between pipeline nodes
- Examples: `backend/app/workflows/state.py`
- Pattern: `Annotated[List[T], operator.add]` accumulation channels; custom `replace_list` reducer to prevent duplicate appends when nodes re-emit whole lists; `IntelligenceState` kept as backward-compat alias

**SourceConnector (abstract base class):**
- Purpose: Uniform contract for external source adapters — isolated, idempotent, incrementally runnable, observable
- Examples: `backend/app/connectors/base.py`, subclasses in `backend/app/connectors/pubmed.py` etc.
- Pattern: Template method — base class owns retry/backoff, bronze persistence, connector-state upsert (`connector_state` table keyed on `source_id`+`profile_id`), health log writing; subclasses implement `fetch_latest()` and `run_profile()`

**LLMProvider + ProviderFactory (strategy + chain of responsibility):**
- Purpose: Capability-routed inference with graceful degradation
- Examples: `backend/app/providers/base.py`, `factory.py`
- Pattern: `supports(capability)` gate per provider; `validate_privacy_gate(classification)` blocks hosted calls on non-public data before falling through to degraded mode

**Domain Config (Pydantic models over YAML):**
- Purpose: Single source of truth for disease ontology, canonical assets, connector query profiles, thresholds
- Examples: `backend/app/core/domain_config.py`, `config/haemophilia.yaml`
- Pattern: `get_domain_config()` accessor; connectors read their `ConnectorConfig.profiles` at runtime

**Deterministic Signal Identity:**
- Purpose: Cross-run deduplication
- Examples: fingerprint computed in `backend/app/services/deduplication.py`; silver upsert `on_conflict_do_update(index_elements=["fingerprint"])` in `backend/app/workflows/runner.py:297`

## Entry Points

**Backend API server:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn` via `python start.py`, Docker Compose `backend` service, or manual run
- Responsibilities: structlog init, middleware stack, router registration under `/api/v1`, lifespan-managed scheduler

**Frontend app:**
- Location: `frontend/app/layout.tsx` → `frontend/app/page.tsx` (redirects to `/dashboard`) → `frontend/app/[section]/page.tsx`; detail route `frontend/app/signals/[signalId]/page.tsx`
- Triggers: Next.js dev/build server (port 3000)
- Responsibilities: theme bootstrapping, section-to-workspace routing

**Unified launcher:**
- Location: `start.py` (Docker backing services + migrations + backend + frontend + log streaming); `setup.py` (environment wizard, model download, non-interactive flags)

**Manual pipeline trigger:**
- Location: `backend/app/api/v1/endpoints/pipeline.py` (POST run), `backend/app/api/v1/endpoints/ingestion.py` ("Ingest Data" sync)

## Architectural Constraints

- **Threading:** Fully async single-process (asyncio event loop). Scheduler workers are asyncio tasks inside the FastAPI lifespan — not threads or separate processes. Horizontal multi-instance safety relies on PostgreSQL advisory locks (`pg_try_advisory_lock`, `backend/app/db/session.py:43`)
- **Global state:** Module-level singletons exist throughout: `settings` (`backend/app/core/config.py`), `engine`/`AsyncSessionLocal` (`backend/app/db/session.py`), `provider_factory` (`backend/app/providers/factory.py`), `ALL_CONNECTORS` instances (`backend/app/connectors/__init__.py`), `SourceScheduler.get_instance()` (`backend/app/services/scheduler.py`). Treat these as process-wide singletons when testing
- **Circular imports:** Avoided via deferred imports inside functions (e.g., scheduler imports `IngestionService` and `PipelineRunner` lazily; connector base imports dedup service at module top but domain config lazily). Preserve this pattern when adding cross-layer references
- **Linear graph:** The LangGraph pipeline is strictly linear — no conditional edges or cycles. New logic must fit the sequential node order or extend `state.py` channels deliberately
- **Contract sync gate:** `frontend/types/api.ts` must byte-match output of `scripts/export_openapi.py`; CI enforces this (`.github/workflows/ci.yml`). Never hand-edit `frontend/types/api.ts` — edit the template in the script and regenerate
- **Bronze immutability:** Connectors persist verbatim raw payloads only (D-23/D-26); intelligence generation is exclusively the pipeline's job

## Anti-Patterns

### God component in frontend shell

**What happens:** `frontend/components/metaradar.tsx` (2,249 lines) exports the app `Shell` plus multiple page-level components (`DashboardPage`, `LifecyclePage`, `GenericPage`) in one client bundle.
**Why it's wrong:** Any change to any workspace forces re-evaluation of the whole module; hard to test and review.
**Do this instead:** Follow the extracted-workspace pattern — one directory per domain under `frontend/components/<domain>/XWorkspace.tsx` (see `frontend/components/confluence/ConfluenceWorkspace.tsx`) — for new pages rather than appending to `metaradar.tsx`.

### Broad exception swallowing with warning logs

**What happens:** Persistence loops catch all exceptions and continue (`logger.warning(f"Could not persist ...")`) — see `backend/app/workflows/runner.py:180,321,344`.
**Why it's wrong here:** Intentional partial-failure resilience (failed signals stay unpromoted for retry, tracked via `failed_signal_ids`), but new code copying the pattern without tracking failures can silently drop data.
**Do this instead:** When swallowing exceptions in batch persistence, record the failed entity ID (mirror `runner.py:186-324` failed-tracking pattern) so retries/promotions remain correct.

### Union-typed legacy parameter shims in the API client

**What happens:** `frontend/lib/api.ts` wrappers accept `number | AbortSignal` style unions to stay backward compatible with old call sites (e.g., `getConfluences`).
**Why it's wrong:** Ambiguous signatures propagate to every caller.
**Do this instead:** For new functions, use explicit `(args, signal?: AbortSignal)` signatures like `getHealthReady` (`frontend/lib/api.ts:41`).

## Error Handling

**Strategy:** Fail-per-item with accumulated error reporting; truthful status surfaces; no silent fabrication.

**Patterns:**
- Pipeline nodes append structured error dicts to the `errors` state channel; counts land in `PipelineRun.errors_count` / `error_summary` (`backend/app/workflows/runner.py:113-140`)
- Connector HTTP failures retry with exponential backoff + jitter, then raise `ConnectorFetchError` with PII-redacted message (`redact_text`) (`backend/app/connectors/base.py:133-170`)
- Scheduler tracks consecutive failures and applies capped adaptive backoff (`SCHEDULER_MAX_BACKOFF_MINUTES`) (`backend/app/services/scheduler.py:151-161`)
- API endpoints raise `HTTPException` with explicit status codes; health endpoints degrade honestly instead of inventing status values (`backend/app/api/v1/endpoints/health.py`, `backend/app/connectors/base.py:298-345`)
- Configuration problems are surfaced as `CONFIGURATION_ERROR` states via pure evaluator `configuration_error_for()` (`backend/app/core/config.py:109-120`)

## Cross-Cutting Concerns

**Logging:** structlog JSON logging configured once at startup (`backend/app/core/logging.py`); named loggers per module (`metaradar.main`, `ingestion_service`). Log params pass through `redact_mapping`/`redact_text` (`backend/app/core/redact.py`) to scrub secrets/PII.

**Validation:** Pydantic v2 everywhere — request/response schemas (`backend/app/schemas/`), settings (`pydantic-settings` in `backend/app/core/config.py`), connector payloads (`RawSignalPayload`, `backend/app/connectors/base.py:26-39`). Domain YAML validated into Pydantic models.

**Authentication:** No user auth. Optional API-key setting `METARADAR_API_KEY` exists in settings but mutation endpoints are guarded by rate limiting config (`MUTATION_RATE_LIMIT_PER_MINUTE`); CORS restricted to configured origins (`backend/app/main.py:66-73`). Privacy is enforced at the provider boundary via `DataClassification` privacy gate rather than user identity.

**PII/PHI protection:** Scrubbing service (`backend/app/services/pii.py`) applied pre-persistence; log/error redaction (`backend/app/core/redact.py`); hosted-LLM privacy gate (`backend/app/providers/grok.py`).

---

*Architecture analysis: 2026-08-24*
