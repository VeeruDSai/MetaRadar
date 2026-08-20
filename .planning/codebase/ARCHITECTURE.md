<!-- refreshed: 2026-08-20 -->
# Architecture

**Analysis Date:** 2026-08-20

## System Overview

MetaRadar v5.1 is a near-real-time competitive intelligence platform for the haemophilia landscape. It ingests public biomedical signals (PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS), runs them through a stateful LangGraph pipeline, and surfaces role-tailored intelligence briefs to six stakeholder functions (Medical Affairs, Regulatory, Safety, Market Access, Comms, Leadership) via a Next.js workspace UI.

```text
┌──────────────────────────────────────────────────────────────────┐
│                  Next.js 16 Frontend (frontend/)                  │
│  frontend/app/[section]/page.tsx → components/metaradar.tsx       │
│  frontend/lib/api.ts (typed REST client + mappers)                │
│  frontend/lib/hooks.ts (useLiveData polling)                      │
├───────────────────────────────┬──────────────────────────────────┤
│                               │ HTTP /api/v1 (CORS)               │
│                               ▼                                  │
│  FastAPI Backend (backend/app/main.py → uvicorn app.main:app)    │
│  ├─ api/v1/endpoints/*  8 routers (health, signals, pipeline,     │
│  │                       search, feedback, intelligence,          │
│  │                       registry, cache)                         │
│  ├─ schemas/            Pydantic request/response contracts       │
│  ├─ services/           business logic (embedding, vector query,  │
│  │                       calibration, PII scrub, red-team, dedup)  │
│  ├─ workflows/          LangGraph 11-node pipeline + PipelineRunner│
│  ├─ connectors/         5 source adapters (bronze persistence)    │
│  └─ providers/          LLM fallback chain (Gemma→Grok→Degraded)  │
├───────────────────────────────┬──────────────────────────────────┤
│                               ▼                                  │
│  PostgreSQL 16 + pgvector · Redis · Ollama (Gemma) · xAI API     │
│  config/haemophilia.yaml (domain ontology, config-driven)         │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app factory | Creates app, CORS, registers 9 routers, correlation ID middleware, structlog | `backend/app/main.py` |
| Settings singleton | pydantic-settings env config (DB, Redis, LLM, CORS) | `backend/app/core/config.py` |
| Domain config | YAML-driven haemophilia ontology + connector query blocks, cached | `backend/app/core/domain_config.py` → `config/haemophilia.yaml` |
| API endpoints | HTTP surface: signals, overview, athena, search, pipeline, feedback, registry, cache, health, observability | `backend/app/api/v1/endpoints/*.py` |
| Pydantic schemas | Request/response contracts; canonical OpenAPI source | `backend/app/schemas/__init__.py`, `backend/app/schemas/intelligence.py`, `backend/app/schemas/registry.py` |
| SQLAlchemy models | 22 ORM tables (signals, bronze, developments, calibration, watch items, health logs, runs) | `backend/app/models/__init__.py` |
| DB session | Async engine, `get_db` dependency, advisory locks | `backend/app/db/session.py` |
| Alembic migrations | Schema versioning (4 migrations: 001, 002, 003, 004) | `backend/alembic/versions/` |
| Source connectors | 5 adapters implementing `SourceConnector`; config-driven profiles | `backend/app/connectors/` |
| LLM providers | `LLMProvider` base + Gemma (Ollama), Grok (xAI), Degraded BART | `backend/app/providers/` |
| ProviderFactory | Fallback chain orchestrator (singleton) | `backend/app/providers/factory.py` |
| LangGraph state | `MetaRadarState` TypedDict with typed reducers | `backend/app/workflows/state.py` |
| LangGraph graph | 11-node linear pipeline assembly/compile | `backend/app/workflows/graph.py` |
| PipelineRunner | Async orchestrator; PipelineRun DB lifecycle; `ainvoke` execution | `backend/app/workflows/runner.py` |
| Workflow nodes | 11 node functions (ingest → calibrate) | `backend/app/workflows/nodes/` |
| Priority Scoring Service | Deterministic 4-factor scoring (Novelty 25%, Clinical 30%, Regulatory 25%, Recency 20%) | `backend/app/services/scoring.py` |
| Confluence Engine | Multi-source convergence detection (≥3 sources in 48h) | `backend/app/services/confluence.py` |
| Structured Logging | Structlog JSON logging with secret/PII auto-redaction | `backend/app/core/logging.py` |
| Correlation Middleware | X-Request-ID propagation and contextual request tracing | `backend/app/core/middleware.py` |
| Frontend bounded workspaces | Modularized domain workspaces (Signals, Confluence, Contradictions, Missing Signals, Athena, etc.) | `frontend/components/{signals,confluence,contradictions,missing-signals,developments,intelligence,functions,calibration,sources,observability,settings}/` |
| Frontend API client | `apiFetch` wrapper, typed ApiError, correlation ID propagation | `frontend/lib/api.ts`, `frontend/lib/errors.ts`, `frontend/lib/mappers.ts` |
| Frontend hooks | `useLiveData` visibility-aware polling | `frontend/lib/hooks.ts` |
| Frontend types | Auto-generated contract (DO NOT EDIT) | `frontend/types/api.ts` |
| Contract exporter | OpenAPI JSON + TS contract generation | `scripts/export_openapi.py` → `contracts/openapi.json` |
| Launchers | Zero-config setup and multi-process start | `setup.py`, `start.py` |

## Pattern Overview

**Overall:** Layered monolith — Next.js frontend + FastAPI backend + PostgreSQL, with a config-driven LangGraph pipeline at the intelligence core. Single-process backend (no Celery; in-memory pipeline execution per `start.py` banner).

**Key Characteristics:**
- **Config-driven domain logic**: haemophilia ontology, connector query profiles, routing matrix, and lag thresholds all live in `config/haemophilia.yaml`, typed by Pydantic models in `backend/app/core/domain_config.py`. Connectors "execute config — never invent queries" (`backend/app/connectors/base.py:68`).
- **Honest telemetry**: providers report `mode: reasoning | degraded_factual` via `ModelMetadataSchema`; endpoints never fabricate metrics (`backend/app/api/v1/endpoints/signals.py`, `backend/app/providers/degraded.py`).
- **Contract-first API**: FastAPI OpenAPI → `contracts/openapi.json` → `frontend/types/api.ts` (generated, CI-enforced drift check in `.github/workflows/ci.yml:35-40`).
- **Fail-degrade fallback chain**: Local Gemma → Grok (privacy-gated) → Degraded BART (`backend/app/providers/factory.py`); exceptions never crash the pipeline.
- **Single-flight pipeline execution**: `PipelineRunner` uses PostgreSQL advisory locks (`backend/app/db/session.py:43-50`) for scheduled-run protection.

## Layers

**Frontend (Presentation):**
- Purpose: Real-time decision intelligence workspace
- Location: `frontend/`
- Contains: App Router pages (`frontend/app/`), component library (`frontend/components/metaradar.tsx`), API client (`frontend/lib/api.ts`), hooks (`frontend/lib/hooks.ts`), auto-generated types (`frontend/types/api.ts`)
- Depends on: Backend REST API at `NEXT_PUBLIC_API_URL` (default `http://localhost:8000/api/v1`, `frontend/lib/api.ts:31`)
- Used by: Browser users

**API Layer (Controllers):**
- Purpose: HTTP surface; thin orchestration, no business logic
- Location: `backend/app/api/v1/endpoints/`
- Contains: 8 routers — `health.py`, `signals.py`, `pipeline.py`, `search.py`, `feedback.py`, `intelligence.py`, `registry.py`, `cache.py`
- Depends on: `app.schemas`, `app.models`, `app.services`, `app.providers`, `app.workflows.runner`
- Used by: Frontend `frontend/lib/api.ts`, external consumers

**Service Layer (Business Logic):**
- Purpose: Embeddings, hybrid search, calibration math, PII scrubbing, dedup, red-team NLI
- Location: `backend/app/services/`
- Contains: `embeddings.py`, `vector_query.py`, `calibration.py`, `pii.py`, `deduplication.py`, `redteam.py`, `source_independence.py`, `embeddings_backfill.py`
- Depends on: `app.models`, `app.core.config`, `app.providers.base`
- Used by: API endpoints and workflow nodes

**Workflow Layer (Intelligence Engine):**
- Purpose: Stateful multi-stage intelligence processing
- Location: `backend/app/workflows/`
- Contains: `graph.py` (graph assembly), `state.py` (typed state + reducers), `runner.py` (async orchestrator), `nodes/` (11 node functions)
- Depends on: `app.services`, `app.providers`, `app.core.domain_config`, `app.models`
- Used by: `POST /api/v1/pipeline/run` (`backend/app/api/v1/endpoints/pipeline.py`)

**Ingestion Layer (Connectors):**
- Purpose: External source adapters; bronze-tier persistence
- Location: `backend/app/connectors/`
- Contains: `base.py` (abstract `SourceConnector` + `RawSignalPayload`), `pubmed.py`, `clinical_trials.py`, `newsapi.py`, `fda.py`, `ema.py`; registry `__init__.py` (singleton `ALL_CONNECTORS`)
- Depends on: `app.services.deduplication` (bronze persistence), `app.models.ConnectorState`, domain config
- Used by: Scheduled runs (external trigger), health endpoint (`backend/app/api/v1/endpoints/health.py`)

**Provider Layer (LLM Abstraction):**
- Purpose: Unified LLM execution with capability + privacy classification
- Location: `backend/app/providers/`
- Contains: `base.py` (`LLMProvider`, `ProviderCapability`, `DataClassification`), `gemma.py`, `grok.py`, `degraded.py`, `factory.py`
- Depends on: `app.core.config`, `app.schemas.ModelMetadataSchema`
- Used by: Workflow nodes (`node_synthesize`), `/athena` endpoint

**Data Layer (Persistence):**
- Purpose: ORM models, async sessions, migrations, seeding
- Location: `backend/app/models/`, `backend/app/db/`, `backend/alembic/`
- Contains: All SQLAlchemy models in one module (`backend/app/models/__init__.py`), engine + `get_db` (`backend/app/db/session.py`), seed script (`backend/app/db/seed.py`), 3 Alembic migrations (`backend/alembic/versions/`)
- Depends on: PostgreSQL 16 + pgvector, Redis
- Used by: Every layer above

## Data Flow

### Primary Request Path (Frontend → API → DB)

1. Browser hits `http://localhost:3000/<section>` → `frontend/app/page.tsx` redirects to `/dashboard` (`frontend/app/page.tsx:4`) → dynamic route `frontend/app/[section]/page.tsx` dispatches section → page component from `frontend/components/metaradar.tsx` (e.g. `DashboardPage`, line 762)
2. Page components call typed fetchers in `frontend/lib/api.ts` (e.g. `getOverview` → `GET /overview` + `GET /signals?limit=20`, `frontend/lib/api.ts:179-226`), often wrapped in `useLiveData` polling (`frontend/lib/hooks.ts`)
3. FastAPI router handles request, injects `AsyncSession` via `Depends(get_db)` (`backend/app/db/session.py:31-40`), runs SQLAlchemy async queries
4. Response serialized through Pydantic response models (`backend/app/schemas/`) back to JSON
5. Frontend `mapSignal`/`mapSearchResult` mappers convert backend shapes to UI presentation contract (`frontend/lib/api.ts:92-174`)

### Intelligence Pipeline Path (Connectors → Bronze → LangGraph)

1. Connector `run_profile` fetches source data with bounded retry/backoff (`backend/app/connectors/base.py:110-144`), persists via `check_and_persist_bronze` (`backend/app/services/deduplication.py:94`) into `raw_signals_bronze`; deterministic fingerprint dedup + `ConnectorState` incremental cursors (`backend/app/connectors/base.py:211-258`)
2. `POST /api/v1/pipeline/run` → `PipelineRunner.run` (`backend/app/workflows/runner.py:24`) → creates `PipelineRun` DB record → `create_initial_state` (`backend/app/workflows/state.py:68`) → `graph.ainvoke(initial_state)`
3. 11-node linear graph executes: `node_ingest` (reads bronze or synthetic fallback `backend/app/data/synthetic_signals.json`) → `node_validate` (length/English/PII filters, fingerprint dedup) → `node_embed` (fastembed 384-dim) → `node_nlp_extract` (regex + optional spaCy) → `node_ontology_enrich` (maps to domain config) → `node_confluence` (multi-source convergence) → `node_lifecycle` (9-stage FSM) → `node_redteam` (pairwise NLI contradictions) → `node_missing_signal` (silence lag + watch rules) → `node_synthesize` (Four-Question briefs via `provider_factory`) → `node_calibrate` (weight updates) → END
4. `PipelineRunner` marks run `completed | partial | failed` based on `errors` list; returns final state

### Search Path (Semantic Retrieval)

1. `POST /api/v1/search` (`backend/app/api/v1/endpoints/search.py`) → `VectorQueryService.search` (`backend/app/services/vector_query.py:54`)
2. Query text embedded via `embedding_service.embed_text` (fastembed CPU)
3. Transaction-scoped `hnsw.ef_search` set via `set_config(..., is_local=true)`; pgvector cosine-distance query over `signals.embedding` with optional metadata filters (`backend/app/services/vector_query.py:73-96`)

### Ask Athena Path (LLM Synthesis)

1. `POST /api/v1/athena` (`backend/app/api/v1/endpoints/signals.py:240`) → prompt trimmed → `PIIPHIScrubber.scrub` → `DataClassification` computed
2. `provider_factory.execute_task(required_capability=REASON, ...)` (`backend/app/providers/factory.py:18`) — Gemma → Grok (privacy gate) → Degraded BART
3. Degraded mode inspection: `mode == "degraded_factual"` returns factual summary at 45% confidence; else reasoning answer (`backend/app/api/v1/endpoints/signals.py:275-281`)

**State Management:**
- Pipeline state: `MetaRadarState` TypedDict (`backend/app/workflows/state.py`) — accumulate semantics via `operator.add` reducers, replacement semantics via `replace_list` for `validated_signals` (prevents double-append from `node_validate` + `node_embed`), scalar metadata via `merge_dicts`
- Frontend state: per-page React state + `useLiveData` hook (polling every 30s, pauses on hidden tab, AbortController in-flight guard — `frontend/lib/hooks.ts`)
- Persistence: PostgreSQL for all domain data; Redis for cache (flushed via `POST /api/v1/cache/clear`, `backend/app/api/v1/endpoints/cache.py`)

## Key Abstractions

**SourceConnector (abstract base):**
- Purpose: Contract for all external source adapters — idempotent, incremental, quota-aware, observable
- Examples: `PubMedConnector` (`backend/app/connectors/pubmed.py`), `ClinicalTrialsConnector` (`backend/app/connectors/clinical_trials.py`), `NewsAPIConnector` (`backend/app/connectors/newsapi.py`), `OpenFDAConnector` (`backend/app/connectors/fda.py`), `EMARSSConnector` (`backend/app/connectors/ema.py`)
- Pattern: Abstract methods `fetch_latest` / `run_profile`; shared machinery `_fetch_with_retry`, `_persist_bronze`, `_read/_write_connector_state`, `get_status` in `backend/app/connectors/base.py`

**LLMProvider + ProviderFactory:**
- Purpose: Capability-tagged LLM abstraction with a guaranteed fallback chain
- Examples: `GemmaProvider` (`backend/app/providers/gemma.py`, Ollama HTTP `/api/generate`), `GrokProvider` (`backend/app/providers/grok.py`, xAI API + privacy gate), `DegradedProvider` (`backend/app/providers/degraded.py`, summarize-only)
- Pattern: `supports(capability)` capability check; `generate_intelligence(evidence, task, classification)` returns dict with `model_metadata`; factory singleton `provider_factory` at `backend/app/providers/factory.py:49`

**MetaRadarState (TypedDict with reducers):**
- Purpose: Single shared state contract flowing through all 11 nodes
- Pattern: `Annotated[List[...], operator.add]` for accumulating channels; `Annotated[Dict[str, float], merge_dicts]` for weight maps; `replace_list` custom reducer for `validated_signals` (`backend/app/workflows/state.py:13-23`)

**Workflow Node function signature:**
- Purpose: Uniform node contract for LangGraph
- Pattern: `async def node_<name>(state: MetaRadarState, session: Optional[AsyncSession] = None) -> Dict[str, Any]` — returns partial-state dict with `errors` list and `node_statuses`; never raises (catches, logs, returns FAILED status). See `backend/app/workflows/nodes/ingest.py:32`

**DomainConfig (Pydantic):**
- Purpose: Typed view over `config/haemophilia.yaml` — diseases, assets, connectors, routing matrix, lag thresholds; cached in `_domain_config_cache` (`backend/app/core/domain_config.py:117-138`)

**Settings (pydantic-settings):**
- Purpose: Environment config singleton loaded from `.env` (`backend/app/core/config.py:58`); all DB/LLM/CORS knobs

**Frontend API client pattern:**
- Purpose: Typed REST access with retryable-error semantics and honest mappers
- Pattern: `apiFetch<T>` central wrapper (`frontend/lib/api.ts:45`) throwing `ApiError(status, statusText, message, isRetryable)`; pure mapper functions `mapSignal` / `mapSearchResult`; typed fetchers per endpoint

## Entry Points

**Process Launcher (`start.py`):**
- Location: `start.py`
- Triggers: `python start.py [--no-frontend | --no-backend | --no-docker | --port-* | --daemon]`
- Responsibilities: docker compose up postgres/redis, uvicorn backend on 8000, `npm run dev` frontend on 3000, port-conflict cleanup, live telemetry loop, graceful shutdown (`start.py:254-336`)

**Environment Setup (`setup.py`):**
- Location: `setup.py`
- Responsibilities: prerequisite checks (Python ≥3.11, Node, Docker), pip install, npm install, alembic upgrade, DB seed, Ollama model pull (`setup.py` 6-step flow)

**Backend Service (`backend/app/main.py`):**
- Location: `backend/app/main.py`
- Triggers: `uvicorn app.main:app` (via `start.py` or manually, `PYTHONPATH=backend`)
- Responsibilities: app creation, CORS, router registration, lifespan logging of domain config load

**Pipeline Trigger (REST):**
- Location: `backend/app/api/v1/endpoints/pipeline.py:18`
- Triggers: `POST /api/v1/pipeline/run` with optional `PipelineRunRequestSchema`
- Responsibilities: instantiate `PipelineRunner`, execute LangGraph, return `PipelineRunResponseSchema` with counts + node statuses

**Frontend Router:**
- Location: `frontend/app/page.tsx` (redirect), `frontend/app/[section]/page.tsx` (dispatch)
- Triggers: Any `/dashboard`, `/signals`, `/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/intelligence`, `/functions`, `/calibrate`, `/sources`, `/settings` URL
- Responsibilities: `switch (section)` mapping to page components inside `Shell` (`frontend/app/[section]/page.tsx:26-69`)

**Contract Export (`scripts/export_openapi.py`):**
- Location: `scripts/export_openapi.py`
- Triggers: `python scripts/export_openapi.py` (CI enforced in `.github/workflows/ci.yml:35-40`)
- Responsibilities: dump `app.openapi()` → `contracts/openapi.json`; generate `frontend/types/api.ts`

## Architectural Constraints

- **Threading:** Single-threaded asyncio event loop. Blocking CPU work (fastembed inference) is offloaded via `asyncio.get_running_loop().run_in_executor` (`backend/app/services/embeddings.py:61-68`). Ollama/xAI calls are async HTTP.
- **Global state / singletons:** `settings` (`backend/app/core/config.py:58`), `provider_factory` (`backend/app/providers/factory.py:49`), `vector_query_service` (`backend/app/services/vector_query.py:122`), `embedding_service` + module-level `_model` (`backend/app/services/embeddings.py:31,113`), `_domain_config_cache` (`backend/app/core/domain_config.py:117`), `ALL_CONNECTORS` (`backend/app/connectors/__init__.py:13`).
- **Linear pipeline:** The LangGraph graph currently uses only explicit linear edges — no conditional branching (`backend/app/workflows/graph.py:45-56`). Adding conditional routes requires new edges here.
- **No Celery:** Pipeline execution is synchronous-in-process via `PipelineRunner.run` — a `POST /pipeline/run` blocks until the graph completes (`backend/app/api/v1/endpoints/pipeline.py:33-37`).
- **Contract discipline:** `frontend/types/api.ts` is auto-generated and CI fails on drift; never hand-edit it (header `frontend/types/api.ts:1-2`).
- **Single module per layer concern:** All ORM models in `backend/app/models/__init__.py`; all workspace UI components in `frontend/components/metaradar.tsx`.
- **Approved stack:** Next.js 16 + FastAPI + PostgreSQL 16 + Local Gemma per `docs/rules/ARCHITECTURE_RULES.md`; active frontend tree is `frontend/app/` (rule #1) — the `frontend/src/` tree is legacy/stub.

## Anti-Patterns

### Node-count doc drift ("10-node" vs "11-node")

**What happens:** `docs/rules/METARADAR_MASTER_PLAN_v5.0.md`, `.planning/PROJECT.md`, `README.md`, `backend/app/workflows/state.py:29`, and `backend/app/workflows/runner.py:15` describe a "10-node" pipeline, but `backend/app/workflows/graph.py:25-42` builds **11** nodes (ingest, validate, embed, nlp_extract, ontology_enrich, confluence, lifecycle, redteam, missing_signal, synthesize, calibrate). Some files hedge ("Node 2.5" in `backend/app/workflows/nodes/embed.py:2`).
**Why it's wrong:** Confuses readers and planning tools about the true pipeline topology.
**Do this instead:** Refer to the graph as "11-node" everywhere; update docstrings in `backend/app/workflows/state.py` and `backend/app/workflows/runner.py` to match `backend/app/workflows/graph.py`.

### Monolithic frontend component file

**What happens:** All workspace pages (`DashboardPage`, `SignalsPage`, `ConfluencePage`, `LifecyclePage`, `RedTeamPage`, `MissingSignalsPage`, `DevelopmentsPage`, `FunctionsPage`, `SourcesPage`, `SettingsPage`, `IntelligencePage`), the `Shell` layout, `SearchModal`, `SignalDrawer`, and primitives (`Badge`, `Card`) live in one 1892-line file `frontend/components/metaradar.tsx`.
**Why it's wrong:** Any page change risks touching unrelated code; no code-splitting; hard to review and test in isolation.
**Do this instead:** Split per-page components into `frontend/components/pages/<Page>.tsx` with shared primitives in `frontend/components/ui/`, mirroring the existing `frontend/components/ui/button.tsx` pattern.

### Duplicate frontend tree (`frontend/src/`)

**What happens:** A second App Router tree exists at `frontend/src/app/` with one real page (`frontend/src/app/sources/page.tsx`) plus empty dirs (`dashboard`, `signals`, `calibrate`, `developments`, `functions`, `intelligence`), and a re-export stub `frontend/src/types/api.ts` pointing at `frontend/types/api.ts`.
**Why it's wrong:** `ARCHITECTURE_RULES.md:5` declares `frontend/app/` canonical; the `src/` stub creates confusion about where to add pages and which tree Next.js serves.
**Do this instead:** Delete the `frontend/src/` tree (or finish migrating pages into it deliberately); keep `frontend/app/` as the single App Router root.

### Hardcoded evidence / values inside API endpoints

**What happens:** `POST /api/v1/athena` embeds a hardcoded 3-item evidence list (`backend/app/api/v1/endpoints/signals.py:257-261`), and `GET /overview` hardcodes confluence score 75.0 / label / drivers when confluences exist (`backend/app/api/v1/endpoints/signals.py:199-213`).
**Why it's wrong:** The codebase's own standard is "honest telemetry, never fabricate" (D-22); hardcoded values bypass that and decay as real data grows.
**Do this instead:** Source Athena evidence from `VectorQueryService.search` results; compute confluence score from real `confluences` table aggregation in `backend/app/services/` and expose via a service.

### Router prefix inconsistency

**What happens:** `backend/app/main.py:59-66` registers routers at mixed prefix depths: `signals`, `intelligence`, `registry`, `cache`, `pipeline`, `feedback` all at `API_V1_STR` with full paths defined inside router files, while `health` and `search` use sub-prefixes (`/health`, `/search`). This yields endpoints like `POST /api/v1/calibrate` (defined in `feedback.py`) next to `GET /api/v1/health/ready` (defined in `health.py`) — path ownership is spread across files and `main.py` does not make it visible.
**Why it's wrong:** Path discovery requires opening each router file; the API surface is not obvious from the registration site.
**Do this instead:** Standardize — register every router with `prefix=f"{settings.API_V1_STR}"` and define full sub-paths in router files, or move all sub-paths into `main.py` for a single-source route table.

## Error Handling

**Strategy:** Never-crash. Every layer catches exceptions, records structured errors, and degrades gracefully.

**Patterns:**
- Workflow nodes wrap logic in try/except, append `{"node", "error", "timestamp"}` to state `errors`, set `node_statuses[node] = "FAILED"`, and return partial state (e.g. `backend/app/workflows/nodes/ingest.py:86-98`)
- `PipelineRunner` catches fatal graph errors, marks `PipelineRun` failed, and returns initial state with the error appended (`backend/app/workflows/runner.py:95-113`)
- Provider chain: `GemmaProvider` raises `OllamaUnavailableError` → `ProviderFactory` falls through to Grok → Degraded BART; never propagates (`backend/app/providers/factory.py:30-46`)
- API endpoints: `_serialize_signal` try/except per schema parse (`backend/app/api/v1/endpoints/signals.py:30-44`); health connectors degrade to in-memory state when DB is unavailable (`backend/app/api/v1/endpoints/health.py:99-112`); `search.py` maps `SearchError` → HTTP 503
- `get_db` dependency rolls back and re-raises on exception (`backend/app/db/session.py:36-38`)

## Cross-Cutting Concerns

**Logging:** `logging.basicConfig` INFO format `%(asctime)s [%(levelname)s] %(name)s: %(message)s` in `backend/app/main.py:18-21`; per-module `logger = logging.getLogger(__name__)` throughout backend; process logs written to `logs/backend.log` / `logs/frontend.log` by `start.py`.

**Validation:** Pydantic v2 for all API contracts (`backend/app/schemas/`); SQLAlchemy unique partial indexes for dedup (`backend/app/models/__init__.py:221-227`); pydantic-settings for env config; PII/PHI regex scrubber at ingestion and Athena boundaries (`backend/app/services/pii.py`).

**Authentication:** Not implemented — no auth middleware or user sessions in `backend/app/main.py`; roles are simulated (feedback `user_id` field defaults to `"system"` / `"pipeline_agent"`, `backend/app/workflows/nodes/calibrate.py:47`). CORS restricted to configured origins (`backend/app/core/config.py:23-27`).

**Privacy:** Grok privacy gate — only `PUBLIC`/`SYNTHETIC` classifications may reach `api.x.ai` (`backend/app/providers/grok.py:1-7`, `backend/app/providers/factory.py:39`); PII scrubber at `node_validate` and `/athena`.

---

*Architecture analysis: 2026-08-20*
