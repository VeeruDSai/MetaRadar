<!-- refreshed: 2026-08-24 -->
# Architecture

**Analysis Date:** 2026-08-24

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────┐
│                    Next.js 16 Frontend (React 19)                   │
│   App Router SPA-style shell: app/[section]/page.tsx switch router  │
│   `frontend/components/*`  ·  `frontend/lib/api.ts` (fetch layer)   │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTP JSON (fetch, NEXT_PUBLIC_API_URL)
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend  /api/v1  (:8000)                  │
│                `backend/app/main.py`                                │
├──────────────────┬──────────────────┬───────────────────────────────┤
│  REST Endpoints  │  Source Scheduler│   LangGraph Pipeline          │
│  `app/api/v1/    │  (asyncio,       │   `app/workflows/graph.py`    │
│   endpoints/*`   │   singleton)     │   11 linear nodes             │
│                  │ `app/services/   │   `app/workflows/nodes/*`     │
│                  │  scheduler.py`   │   orchestrated by             │
│                  │                  │   `app/workflows/runner.py`   │
└────────┬─────────┴────────┬─────────┴──────────────┬────────────────┘
         │                  │                        │
         ▼                  ▼                        ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│ Service Layer    │ │ LLM Providers    │ │ Source Connectors        │
│ `app/services/*` │ │ `app/providers/` │ │ `app/connectors/*`       │
│ scoring, routing,│ │ Gemma (Ollama/   │ │ PubMed, ClinicalTrials,  │
│ confluence,      │ │ GGUF) → Grok →   │ │ NewsAPI, OpenFDA, EMA    │
│ embeddings, PII  │ │ BART degraded    │ │ (httpx + retry/backoff)  │
└────────┬─────────┘ └──────────────────┘ └───────────┬──────────────┘
         │                                            │
         ▼                                            ▼
┌─────────────────────────────────────────────────────────────────────┐
│              PostgreSQL 16 + pgvector  (bronze→silver→gold)          │
│   `backend/app/models/__init__.py` (SQLAlchemy 2.0 async)            │
│   raw_signals_bronze → signals (+Vector(384)) → developments/        │
│   confluences/contradictions/watch_items/calibration_*               │
└─────────────────────────────────────────────────────────────────────┘
         ▲                            ▲
         │                            │
┌────────┴───────────┐     ┌──────────┴─────────────┐
│ Ollama sidecar     │     │ Redis 7                │
│ gemma3:4b (GPU)    │     │ redis://localhost:6379 │
│ :11434             │     │ (configured, light use)│
└────────────────────┘     └────────────────────────┘

Domain configuration (single YAML source of truth):
`config/haemophilia.yaml` → loaded by `backend/app/core/domain_config.py`
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app | Route registration, CORS, correlation-ID middleware, lifespan startup/shutdown of scheduler | `backend/app/main.py` |
| REST endpoints | HTTP request/response handling, serialization via Pydantic schemas | `backend/app/api/v1/endpoints/*.py` |
| Shared deps | Optional `X-API-Key` mutation auth + in-memory per-client rate limiting | `backend/app/api/deps.py` |
| Settings | Typed env-driven configuration (pydantic-settings) | `backend/app/core/config.py` |
| Domain config | Loads `config/haemophilia.yaml` into typed Pydantic models (assets, connectors, thresholds, routing matrix) | `backend/app/core/domain_config.py` |
| Logging/redaction | structlog JSON logs, correlation IDs, PII redaction helpers | `backend/app/core/logging.py`, `backend/app/core/middleware.py`, `backend/app/core/redact.py` |
| Connectors | Fetch from 5 public biomedical sources; idempotent bronze persistence; per-profile incremental state; health telemetry | `backend/app/connectors/base.py` + 5 concrete connectors |
| IngestionService | Orchestrates connector runs, aggregates status precedence, writes health logs | `backend/app/services/ingestion.py` |
| SourceScheduler | Singleton asyncio worker per connector; jitter, exponential backoff, PG advisory locks; triggers pipeline only on new data | `backend/app/services/scheduler.py` |
| PipelineRunner | Builds/invokes the LangGraph graph; persists gold entities back to DB; manages `PipelineRun` lifecycle | `backend/app/workflows/runner.py` |
| Workflow nodes | 11 pure-ish async transforms over `MetaRadarState` (ingest→validate→embed→nlp→ontology→confluence→lifecycle→redteam→missing→synthesize→calibrate) | `backend/app/workflows/nodes/*.py` |
| ProviderFactory | Capability-routed LLM execution with privacy-gated fallback chain: Gemma → Grok (if permitted) → Degraded BART | `backend/app/providers/factory.py` |
| Embeddings | fastembed/all-MiniLM-L6-v2, 384-dim vectors stored via pgvector | `backend/app/services/embeddings.py` |
| SQLAlchemy models | All tables in one declarative module (bronze/silver/gold + calibration + audit) | `backend/app/models/__init__.py` |
| Migrations | Alembic revisions 001–012 | `backend/alembic/versions/*.py` |
| Frontend API layer | Typed fetch wrappers, ApiError normalization, response mapping | `frontend/lib/api.ts`, `frontend/lib/errors.ts`, `frontend/lib/mappers.ts` |
| Polling hook | `useLiveData` — visibility-aware, abort-safe interval polling | `frontend/lib/hooks.ts` |
| Workspace shell + pages | Nav shell, dashboard, lifecycle page, generic page (all in one client bundle) | `frontend/components/metaradar.tsx` |
| Workspaces | Per-domain UI (signals, confluence, contradictions, missing-signals, developments, intelligence/Athena, functions, calibration, sources, observability, settings) | `frontend/components/<domain>/*.tsx` |

## Pattern Overview

**Overall:** Layered two-tier web app with an embedded event-driven ingestion subsystem and a linear stateful ML pipeline (LangGraph). Medallion data layering (bronze → silver/gold) inside a single PostgreSQL database.

**Key Characteristics:**
- **Single-process backend**: FastAPI hosts REST API, background scheduler, and pipeline execution in one uvicorn process (`backend/app/main.py` lifespan starts `SourceScheduler.get_instance()`).
- **Config-driven domain**: Almost all business parameters (assets, queries, thresholds, weights, routing matrix) come from `config/haemophilia.yaml`, not code. Connectors "execute config, never invent queries."
- **Honest-telemetry invariant (D-22)**: Health/status endpoints must reflect real state; degraded paths return explicit statuses (`DEGRADED`, `CONFIGURATION_ERROR`, `NO_NEW_DATA`) instead of fabricated values.
- **Privacy gate**: `DataClassification` enum on every LLM call; hosted Grok fallback is blocked for non-public classifications (`backend/app/providers/factory.py`, `backend/app/providers/grok.py`).
- **Idempotent persistence**: Dedup via unique fingerprints/hashes; signals upsert `on_conflict_do_update` on `fingerprint`; bronze rows promoted only after successful silver persistence (`backend/app/workflows/runner.py:346-364`).

## Layers

**Presentation (frontend):**
- Purpose: Decision-intelligence workspace UI
- Location: `frontend/app/` (routes), `frontend/components/` (UI)
- Contains: Server-component route entry, client workspaces, design primitives
- Depends on: `frontend/lib/api.ts` only for data access
- Used by: Users via browser (:3000)

**API layer (backend):**
- Purpose: HTTP surface; validation/serialization only
- Location: `backend/app/api/v1/endpoints/`
- Contains: 10 routers (health, signals, intelligence, registry, observability, cache, pipeline, ingestion, search, feedback)
- Depends on: services, models, db session
- Used by: Frontend and scripts (`scripts/test_live_ingestion_e2e.py`)

**Service layer:**
- Purpose: Business logic (scoring, routing, confluence detection, dedup, embeddings, calibration, PII scrubbing, provenance resolution)
- Location: `backend/app/services/`
- Contains: Classes plus module-level singletons (`priority_scorer`, `confluence_engine`, `embedding_service`)
- Depends on: models, core config/domain_config, providers
- Used by: endpoints, workflow nodes, scheduler

**Workflow/pipeline layer:**
- Purpose: Multi-step intelligence generation with typed shared state
- Location: `backend/app/workflows/` (`state.py`, `graph.py`, `nodes/`, `runner.py`)
- Contains: `MetaRadarState` TypedDict with annotated reducers; 11 nodes; `PipelineRunner` persistence
- Depends on: services, providers, models
- Used by: `pipeline.py` endpoint and `scheduler.py`

**Integration layer:**
- Purpose: External world adapters (sources, LLMs)
- Location: `backend/app/connectors/`, `backend/app/providers/`
- Contains: `SourceConnector` base contract + 5 connectors; `LLMProvider` base + Gemma/Grok/Degraded + factory
- Depends on: httpx, core config, domain config, dedup service
- Used by: scheduler, ingestion service, synthesize/search nodes, endpoints

**Persistence layer:**
- Purpose: Relational storage + vector search + migrations
- Location: `backend/app/db/session.py`, `backend/app/models/__init__.py`, `backend/alembic/`
- Contains: async engine (pool_size=10, max_overflow=20), `get_db` dependency, advisory-lock helpers, 20+ ORM models
- Depends on: PostgreSQL 16 + pgvector
- Used by: everything above

## Data Flow

### Primary Request Path (read)

1. Client component calls typed wrapper (e.g. `fetchSignals`) in `frontend/lib/api.ts:256`
2. `apiFetch` builds URL against `NEXT_PUBLIC_API_URL || http://localhost:8000/api/v1`, normalizes errors to `ApiError` (`frontend/lib/api.ts:151-202`)
3. FastAPI endpoint executes queries via `Depends(get_db)` session (e.g. `backend/app/api/v1/endpoints/signals.py`)
4. ORM result serialized through Pydantic schemas (`backend/app/schemas/intelligence.py`, `backend/app/schemas/registry.py`)
5. Frontend maps raw payloads to view types via mappers (`frontend/lib/mappers.ts`), rendered by workspace components; polling refresh handled by `useLiveData` (`frontend/lib/hooks.ts:21`)

### Ingestion Flow (write, scheduled or manual)

1. Trigger: `POST /api/v1/ingestion/run` (`backend/app/api/v1/endpoints/ingestion.py`) or autonomous `SourceScheduler` worker loop (`backend/app/services/scheduler.py`)
2. Scheduler acquires per-source PG advisory lock (`try_advisory_lock`, `backend/app/db/session.py:43`) to guarantee single execution
3. `IngestionService.run_connectors` iterates `ALL_CONNECTORS` (`backend/app/services/ingestion.py:29`); each connector runs its YAML-defined profiles (`backend/app/connectors/base.py:179-197`)
4. `_fetch_with_retry` does bounded exponential backoff + jitter over httpx (`backend/app/connectors/base.py:133-166`)
5. Payloads persisted idempotently to `raw_signals_bronze` via `check_and_persist_bronze` (`backend/app/services/deduplication.py`); run telemetry written to `source_health_logs` and live `sources` row (`backend/app/connectors/base.py:366-433`)
6. If new records exist, scheduler triggers `PipelineRunner.run` (decoupled ingestion vs intelligence)

### Intelligence Pipeline Flow

1. Entry: `POST /api/v1/pipeline/run` (`backend/app/api/v1/endpoints/pipeline.py:25`) creates `PipelineRunner(session)` and calls `run()` (`backend/app/workflows/runner.py:39`)
2. Runner inserts `PipelineRun(status=running)`, loads unpromoted bronze rows where `pipeline_run_id IS NULL` (`backend/app/workflows/runner.py:71-89`), builds initial state via `create_initial_state` (`backend/app/workflows/state.py:68`)
3. Compiled linear graph executes 11 nodes in order (`backend/app/workflows/graph.py:46-56`): ingest → validate → embed → nlp_extract → ontology_enrich → confluence → lifecycle → redteam → missing_signal → synthesize → calibrate → END
4. `node_synthesize` enforces evidence-sufficiency gate and calls `provider_factory.execute_task` for Four-Question briefs (`backend/app/workflows/nodes/synthesize.py:48`)
5. Runner persists results: Developments (FK-guarded), Signals upserted on fingerprint with fresh embedding + provenance + score breakdown, Confluences; finally promotes processed bronze rows by stamping `pipeline_run_id` — failed rows stay unpromoted for retry (`backend/app/workflows/runner.py:142-366`)
6. `PipelineRun` marked completed/failed with counts and error summary JSONB

### Calibration Feedback Loop

1. User rates a signal → `POST /feedback` stores `CalibrationFeedback` (`backend/app/api/v1/endpoints/feedback.py`)
2. Recalibration recomputes per-function weights → `calibration_runs`/`scoring_weights`/`calibration_history` (`backend/app/services/calibration.py`)
3. Next pipeline run seeds `calibration_weights` into initial state; `node_calibrate` applies them to routing scores (`backend/app/workflows/state.py:58-65`)

**State Management:**
- Backend: no server-side session state; all state in PostgreSQL. In-memory only: scheduler job states, provider HTTP clients, rate-limit buckets (`backend/app/api/deps.py:13`).
- Frontend: local React state per workspace + `useLiveData` polling; no global store, no react-query/redux.
- LangGraph: channel reducers defined in `backend/app/workflows/state.py` — `operator.add` for append-channels, `merge_dicts` for dicts, custom `replace_list` for `validated_signals` (prevents duplicate-append when validate and embed both emit the full list).

## Key Abstractions

**`SourceConnector` (connector contract D-01/D-06):**
- Purpose: Isolated, idempotent, quota-aware, observable source adapter
- Examples: `backend/app/connectors/pubmed.py`, `clinical_trials.py`, `newsapi.py`, `fda.py`, `ema.py`
- Pattern: Template method — base class owns retry, bronze persistence, connector-state I/O, health logging; subclasses implement `fetch_latest()` and `run_profile()` only. Registry list `ALL_CONNECTORS` in `backend/app/connectors/__init__.py`.

**`MetaRadarState` (pipeline contract D-02):**
- Purpose: TypedDict shared blackboard across pipeline nodes
- Example: `backend/app/workflows/state.py:26-51`
- Pattern: Annotated reducers; alias `IntelligenceState` kept for backward compatibility

**`LLMProvider` + `ProviderCapability`:**
- Purpose: Capability-scoped LLM interface with data-classification-aware privacy
- Examples: `backend/app/providers/gemma.py` (dual-engine: Ollama HTTP or llama-cpp GGUF), `grok.py` (hosted xAI), `degraded.py` (extractive/BART summarize-only)
- Pattern: Strategy + Chain-of-responsibility in `ProviderFactory.execute_task` (`backend/app/providers/factory.py:18-47`)

**Pydantic schemas (API contracts):**
- Purpose: Strict request/response DTOs decoupled from ORM models
- Examples: `backend/app/schemas/intelligence.py`, `backend/app/schemas/registry.py`
- Contract sync enforced by test `tests/test_contract_drift.py` against `contracts/openapi.json`

**Domain config (YAML → Pydantic):**
- Purpose: Single source of truth for disease area, assets, connector profiles, thresholds, routing matrix
- Files: `config/haemophilia.yaml` → `backend/app/core/domain_config.py` (`get_domain_config()` cached accessor)

## Entry Points

**FastAPI application:**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app` / Docker / `python start.py`
- Responsibilities: structlog init, domain-config load log, scheduler start/stop in lifespan, middleware + 10 router registrations, root metadata endpoint

**Next.js app:**
- Locations: `frontend/app/layout.tsx` (root layout + theme bootstrap script), `frontend/app/page.tsx` (redirects to `/dashboard`), `frontend/app/[section]/page.tsx` (catch-all section switch → workspace component), `frontend/app/signals/[signalId]/` (signal detail route)
- Triggers: `next dev` / `next start` / Docker

**Process orchestrators (repo root):**
- `setup.py`: zero-config environment bootstrap (deps, Docker backing services, models, migrations, seed)
- `start.py`: unified launcher for Docker backing services + backend + frontend with log tailing and graceful shutdown (Windows-aware `taskkill /T`)

**Infrastructure:**
- `docker-compose.yml`: postgres (pgvector/pgvector:pg16), redis:7, backend (+ optional `gpu` profile variant), frontend, ollama sidecar (`gemma3:4b`, NVIDIA reservation)

## Architectural Constraints

- **Threading:** Single asyncio event loop; concurrency via `asyncio.Task`s (one worker per connector) — no thread pools except implicit model loading. CPU-bound GGUF inference runs synchronously inside `GemmaProvider._generate_with_local_gguf` (`backend/app/providers/gemma.py:87`).
- **Global state:** Module-level singletons exist intentionally: `settings` (`backend/app/core/config.py:106`), `provider_factory` (`backend/app/providers/factory.py:50`), `engine`/`AsyncSessionLocal`/`Base` (`backend/app/db/session.py`), `SourceScheduler._instance` (`backend/app/services/scheduler.py:48`), `ALL_CONNECTORS` instances (`backend/app/connectors/__init__.py:13`). Do not instantiate duplicates.
- **Circular-import avoidance:** Lazy imports are used deliberately (e.g., `SourceScheduler` imported inside `main.py` lifespan; `app.models` imported inside functions in `backend/app/connectors/base.py:381`) — preserve this pattern when adding cross-layer references.
- **Linear pipeline:** The LangGraph graph has no conditional edges; adding branching requires changing `build_graph()` (`backend/app/workflows/graph.py`).
- **Bronze immutability:** Raw payloads persist verbatim (D-23); interpretation happens only downstream in silver `signals` columns (`facts`/`interpretation`/`speculation`).
- **Contract sync:** OpenAPI exported to `contracts/openapi.json` (`scripts/export_openapi.py`); drift is tested (`tests/test_contract_drift.py`) — regenerate after any endpoint/schema change.
- **Approved stack lock:** Next.js 16 + FastAPI + PostgreSQL 16 + local Gemma per `docs/rules/ARCHITECTURE_RULES.md`; do not substitute frameworks.

## Anti-Patterns

### Monolithic model module

**What happens:** Every ORM entity (20+ tables) lives in one file: `backend/app/models/__init__.py` (430 lines), while the `backend/app/models/` package has no other modules.
**Why it's wrong here:** Any model change touches a hot file; merge conflicts likely; unrelated imports pull the full metadata.
**Do this instead:** When touching models, keep edits surgical; a future refactor may split per-aggregate modules re-exported from `__init__.py`. Do not add new tables anywhere else — `Base` comes from `backend/app/db/session.py`.

### Switch-based routing instead of file-based routes

**What happens:** One catch-all route `frontend/app/[section]/page.tsx` maps 13 section strings to components via a `switch`; navigation labels live separately in `frontend/components/metaradar.tsx`.
**Why it's wrong here:** Adding a section requires editing two distant files; no per-section metadata/code-splitting boundaries.
**Do this instead:** Follow the existing convention (register the new case + nav entry), unless migrating wholesale to real nested routes — do not mix both styles.

### God component file

**What happens:** `frontend/components/metaradar.tsx` exports `Shell`, `DashboardPage`, `LifecyclePage`, `GenericPage` and much shared UI from a single 2,300-line client file.
**Why it's wrong here:** Large client bundle, hard review diffs, tangled state.
**Do this instead:** New workspaces go in their own `frontend/components/<domain>/` directory; reuse (don't extend inline) the shell exports.

### Silent-broad excepts around persistence steps

**What happens:** Pipeline persistence wraps each entity insert in `try/except Exception` logging warnings (`backend/app/workflows/runner.py:180,320,343`) so one bad record doesn't kill a run.
**Why it's risky:** Failures degrade quietly; mitigated by `failed_signal_ids` retry logic and `PipelineRun.errors_count` accounting — keep that bookkeeping intact when modifying.
**Do this instead:** Preserve the failure-collection pattern; surface failures through run telemetry rather than swallowing them.

## Error Handling

**Strategy:** Fail loudly at API boundary (HTTPException), fail soft inside pipeline/connectors with structured status reporting; never fabricate healthy state.

**Patterns:**
- Endpoint guards raise `HTTPException` with explicit status codes (`backend/app/api/v1/endpoints/pipeline.py:69`)
- Connector retries bounded with exponential backoff + jitter, final failure raises `ConnectorFetchError` with redacted message (`backend/app/connectors/base.py:22,162-166`)
- Provider chain catches per-provider exceptions and falls through Gemma → Grok → Degraded (`backend/app/providers/factory.py:30-47`); Gemma raises `OllamaUnavailableError` (never-crash contract D-12, `backend/app/providers/gemma.py:48`)
- Pipeline errors accumulate into state `errors` channel + `PipelineRun.error_summary` JSONB
- Frontend normalizes all failures into `ApiError` with retryability hint (`frontend/lib/errors.ts`, `frontend/lib/api.ts:173-201`)

## Cross-Cutting Concerns

**Logging:** structlog JSON configured once at startup (`backend/app/core/logging.py`); correlation ID middleware (`backend/app/core/middleware.py`, `asgi-correlation-id`) propagates `x-request-id` to clients.

**Validation:** Pydantic v2 everywhere — settings (`BaseSettings`), domain YAML models, API DTOs; connectors validate payloads with `RawSignalPayload` (`backend/app/connectors/base.py:26`).

**Authentication:** Optional API-key gate for mutations via `require_mutation_auth` dependency + naive per-IP rate limiter (`backend/app/api/deps.py`); active only when `METARADAR_API_KEY` set. No user accounts/auth roles exist.

**PII/PHI protection:** Scrubbing service (`backend/app/services/pii.py`) and redaction utilities (`backend/app/core/redact.py`) applied to connector params/logs before persistence or emission.

---

*Architecture analysis: 2026-08-24*
