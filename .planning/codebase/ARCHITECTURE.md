# Architecture

**Analysis Date:** 2026-08-30

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                                   │
│  Next.js 16 + React 19 │ frontend/app/layout.tsx │ frontend/components/*    │
│  Routes: /dashboard, /signals/[signalId], /[section]                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                       API & MIDDLEWARE LAYER                                    │
│  FastAPI + CORSMiddleware │ CorrelationIdMiddleware │ SecurityHeadersMiddleware│
│  backend/app/main.py → backend/app/api/v1/endpoints/{signals,athena,...}     │
├─────────────────────────────────────────────────────────────────────────────┤
│                     WORKFLOW & INTELLIGENCE LAYER                                 │
│  LangGraph 11-Node Pipeline │ backend/app/workflows/graph.py                │
│  node_ingest → validate → embed → nlp_extract → ontology_enrich →            │
│  confluence → lifecycle → redteam → missing_signal → synthesize → calibrate  │
├─────────────────────────────────────────────────────────────────────────────┤
│                      DOMAIN & SERVICE LAYER                                     │
│  Business Logic │ backend/app/services/{scoring,routing,ingestion,calibrat...}│
│  Connectors │ backend/app/connectors/{pubmed,fda,ema,newsapi,...}            │
│  Providers │ backend/app/providers/{gemma,grok,degraded}                      │
│  Schemas │ backend/app/schemas/{intelligence,auth,registry}                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                        PERSISTENCE LAYER                                        │
│  PostgreSQL 16 + pgvector │ Redis 7 │ Alembic Migrations │ backend/app/models/ │
│  Bronze → Silver → Gold medallion tables                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                      EXTERNAL INFRASTRUCTURE                                      │
│  Ollama (Gemma 3 4B Q4) │ Docker Compose │ config/ │ models/ │ logs/       │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| **Next.js Frontend** | React 19 UI dashboard, signal review, Athena chat, routing | `frontend/app/`, `frontend/components/` |
| **FastAPI App** | REST API, auth, CORS, correlation ID middleware | `backend/app/main.py` |
| **API Endpoints** | Signal CRUD, Athena synthesis, search, feedback, ingestion, pipeline execution | `backend/app/api/v1/endpoints/` |
| **LangGraph Pipeline** | 11-node intelligence pipeline orchestrating signal processing | `backend/app/workflows/graph.py` |
| **Pipeline Nodes** | Individual processing steps: ingest, validate, embed, NLP, ontology, confluence, lifecycle, redteam, missing_signal, synthesize, calibrate | `backend/app/workflows/nodes/*.py` |
| **State Management** | TypedDict state with annotated reducers for accumulating signal data | `backend/app/workflows/state.py` |
| **Source Connectors** | 8 source adapters (PubMed, FDA, EMA, ClinicalTrials, NewsAPI, FiercePharma, ETPharma, BioPharmaDive) | `backend/app/connectors/*.py` |
| **Provider Factory** | LLM fallback chain: Gemma → Grok → BART Degraded | `backend/app/providers/factory.py` |
| **Gemma Provider** | Local GGUF + Ollama inference with streaming | `backend/app/providers/gemma.py` |
| **Grok Provider** | xAI Grok API with mandatory privacy gate | `backend/app/providers/grok.py` |
| **Degraded Provider** | BART factual fallback when LLM unavailable | `backend/app/providers/degraded.py` |
| **Ingestion Service** | Orchestrates connector runs, bronze persistence, health telemetry | `backend/app/services/ingestion.py` |
| **Scoring Service** | Signal priority scoring with haemophilia-specific keyword weights | `backend/app/services/scoring.py` |
| **Routing Service** | Stakeholder function routing and signal assignment | `backend/app/services/routing.py` |
| **Calibration Service** | Stakeholder feedback-driven weight adjustment | `backend/app/services/calibration.py` |
| **SQLAlchemy Models** | Medallion architecture tables (bronze, silver, gold) | `backend/app/models/__init__.py` |
| **Auth Service** | User authentication, demo seeding, session management | `backend/app/services/auth_service.py` |
| **Deduplication Service** | Fingerprint-based dedup, bronze persistence | `backend/app/services/deduplication.py` |
| **PII Scrubber** | PHI/PII redaction for HIPAA compliance | `backend/app/services/pii.py` |
| **Embedding Service** | pgvector embedding generation and vector queries | `backend/app/services/embeddings.py` |
| **Core Config** | Pydantic settings, environment variables, LLM/hardware config | `backend/app/core/config.py` |
| **Core Middleware** | Correlation ID, security headers | `backend/app/core/middleware.py` |
| **Database Session** | Async SQLAlchemy session factory | `backend/app/db/session.py` |
| **DB Seed** | Synthetic reference data seeding | `backend/app/db/seed.py` |

## Pattern Overview

### Medallion Architecture

The platform uses a three-tier medallion data architecture for signal provenance:

- **Bronze** (`raw_signals_bronze`): Raw ingested payloads with verbatim source data, content hashes, and connector metadata. Immutable append-only records with dedup via `content_hash` and `source_id + external_id` unique constraint.
- **Silver** (`evidence`, `developments`): Extracted and validated evidence items linked to developments. Contains scrubbed content, fingerprinted references, and provenance status.
- **Gold** (`signals`): Final enriched signals with embeddings (`pgvector Vector(384)`), calibration scores, routing metadata, review state, and stakeholder function assignments. This is the primary query surface for the UI.

### Provider Fallback Chain

Intelligence synthesis follows a strict 3-tier fallback chain managed by `ProviderFactory`:

1. **Local Gemma** (primary): `GemmaProvider` — tries local `.gguf` file via `llama-cpp-python`, then Ollama sidecar at `http://localhost:11434`. Never crashes (`OllamaUnavailableError` on failure).
2. **Grok/xAI** (fallback 1): `GrokProvider` — only invoked if `XAI_API_KEY` or `GROK_API_KEY` is configured and `ENABLE_GROK_FALLBACK=true`. Privacy gate enforces `PUBLIC` or `SYNTHETIC` classification only.
3. **BART Degraded** (fallback 2): `DegradedProvider` — factual summarization only when both Gemma and Grok fail. Explicitly disables reasoning and action generation.

### Privacy Gate

The `GrokProvider.validate_privacy_gate()` method blocks external transmission of `CONFIDENTIAL`, `INTERNAL`, or `PATIENT_IDENTIFIABLE` data classifications. Only `PUBLIC` and `SYNTHETIC` data may reach `api.x.ai`. The `PIIPHIScrubber` (`app/services/pii.py`) sanitizes text before any persistence or external transmission.

## Layers

### Layer 1: Presentation

- **Purpose**: Next.js 16 + React 19 UI for signal review, Athena chat, dashboard, and stakeholder workflows
- **Location**: `frontend/app/`, `frontend/components/`
- **Contains**: Root layout, page routing, signal components, Athena workspace, calibration UI, authentication context, theme provider
- **Depends on**: API layer via `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1`
- **Used by**: End users via browser

### Layer 2: API & Middleware

- **Purpose**: FastAPI REST API with authentication, CORS, correlation IDs, and all endpoint routing
- **Location**: `backend/app/main.py`, `backend/app/api/v1/endpoints/`, `backend/app/core/`
- **Contains**: FastAPI app lifecycle, CORS middleware, correlation ID middleware, security headers, 11 endpoint routers (health, auth, signals, pipeline, search, feedback, intelligence, registry, cache, observability, ingestion)
- **Depends on**: Service and workflow layers
- **Used by**: Frontend and external API consumers

### Layer 3: Workflow & Intelligence

- **Purpose**: LangGraph 11-node pipeline executing the complete signal-to-intelligence transformation
- **Location**: `backend/app/workflows/graph.py`, `backend/app/workflows/nodes/`, `backend/app/workflows/state.py`
- **Contains**: `MetaRadarState` TypedDict, compiled `StateGraph`, 11 node functions with typed reducers
- **Depends on**: Models (bronze signals), services (scoring, embeddings, PII), providers (LLM)
- **Used by**: API endpoints via `pipeline` router, and autonomous scheduler

### Layer 4: Domain & Service

- **Purpose**: Business logic, source connectors, LLM providers, schemas, and cross-cutting concerns
- **Location**: `backend/app/services/`, `backend/app/connectors/`, `backend/app/providers/`, `backend/app/schemas/`
- **Contains**: 18 service modules, 8 connector adapters, 4 provider classes, 3 schema modules
- **Depends on**: Models, database session, config
- **Used by**: Workflow nodes and API endpoints

### Layer 5: Persistence

- **Purpose**: Data storage, retrieval, and schema versioning
- **Location**: `backend/app/models/__init__.py`, `backend/app/db/session.py`, Alembic migrations, PostgreSQL 16 + pgvector, Redis 7
- **Contains**: 20+ SQLAlchemy models (Signals, RawSignalBronze, Evidence, Developments, Contradictions, CalibrationRuns, ScoringWeights, AuditLog, etc.), async session factory, connector state tracking
- **Depends on**: PostgreSQL 16 + pgvector for vector search, Redis 7 for caching
- **Used by**: All upper layers

## Data Flow

### Primary Signal Processing Flow

1. **Ingest** (`backend/app/connectors/`): Source connectors (PubMed, FDA, EMA, etc.) fetch data via `_fetch_with_retry` with exponential backoff, PII-scrub payloads, and persist verbatim raw data to `raw_signals_bronze`. The `IngestionService` orchestrates all connectors and records health telemetry.
2. **Validate** (`backend/app/workflows/nodes/validate.py`): Node 2 filters short/non-English text, applies `RelevanceGate`, deduplicates within batch via fingerprint, and scrubs PII.
3. **Embed** (`backend/app/workflows/nodes/embed.py`): Node 2.5 generates 384-dimension embeddings via fastembed CPU and attaches `embedding` + `embedding_model_version` to each signal.
4. **NLP Extract** (`backend/app/workflows/nodes/nlp_extract.py`): Node 4 extracts entities, facts, and key information from validated signals.
5. **Ontology Enrich** (`backend/app/workflows/nodes/ontology.py`): Node 5 enriches signals with ontology concepts and links to developments/assets.
6. **Confluence** (`backend/app/workflows/nodes/confluence.py`): Node 6 detects signal convergence patterns across multiple sources.
7. **Lifecycle** (`backend/app/workflows/nodes/lifecycle.py`): Node 7 maps signals to development lifecycle stages.
8. **Redteam** (`backend/app/workflows/nodes/redteam.py`): Node 8 applies contradiction detection and counterfactual analysis.
9. **Missing Signal** (`backend/app/workflows/nodes/missing_signal.py`): Node 9 identifies gaps in the evidence landscape.
10. **Synthesize** (`backend/app/workflows/nodes/synthesize.py`): Node 10 generates structured intelligence via the LLM provider chain.
11. **Calibrate** (`backend/app/workflows/nodes/calibrate.py`): Node 11 applies stakeholder feedback, adjusts `ScoringWeights` via online gradient update (alpha=0.05), and recalculates role-brief relevance scores.

### Athena Query Flow

1. User submits prompt via `POST /api/v1/athena` or `/api/v1/athena/stream`
2. **PII Scrubbing** (`backend/app/services/pii.py`): Classifies data, scrubs PHI
3. **Evidence Retrieval** (`backend/app/services/vector_query.py`): Hybrid search — pgvector cosine similarity (max distance 0.35) → keyword/lexical fallback → broad landscape fallback
4. **Provider Execution** (`backend/app/providers/factory.py`): Gemma → Grok → BART fallback chain
5. **Response**: Structured JSON with citations, confidence, and `response_type` (`grounded_synthesis`, `insufficient_evidence`, `assistant_intro`)

### Calibration Flow

1. Stakeholder submits feedback via `POST /api/v1/feedback`
2. Feedback persisted to `calibration_feedback` table
3. `node_calibrate` reads feedback, applies online gradient update: `new_weight = round(max(0.1, min(2.0, old_weight + 0.05 * (rating - 3.0))), 3)`
4. Recalculates adjusted relevance scores per role brief
5. Persists to `calibration_runs` and `scoring_weights`; updates `signal_routing`

## Architectural Constraints

- **Threading**: Single-threaded async event loop (FastAPI + asyncio). Worker threads used for llama-cpp-python GGUF inference and streaming bridge. Node.js uses React Server Components.
- **Global state**: `settings` singleton from `backend/app/core/config.py` (Pydantic BaseSettings). `provider_factory` singleton from `backend/app/providers/factory.py`. `SourceScheduler` singleton via `get_instance()`.
- **Audit Log Immutability**: `AuditLog` records are append-only — `before_update` and `before_delete` SQLAlchemy event listeners raise `PermissionError`.
- **Medallion Integrity**: Bronze rows are immutable once persisted. Silver/Gold rows reference bronze via `raw_signal_id` and `signal_id`.
- **Python 3.11+**: Required runtime version.
- **pnpm preferred**: Frontend package manager is pnpm with npm fallback.
- **PostgreSQL 16 + pgvector**: Required for vector similarity search and `JSONB` columns.
- **Docker Compose**: All backing services (Postgres, Redis, Ollama) orchestrated via `docker-compose.yml`.

## Error Handling

**Strategy**: Fail-fast with honest telemetry — never fabricate state, never silently swallow errors.

**Patterns**:
- **Connector errors**: `ConnectorFetchError` with bounded retry/backoff (max 3 retries, base 1.5s). Degrades silently to in-memory state when DB unavailable. Health status maps to canonical enum (`HEALTHY`, `DEGRADED`, `FAILED`, `UNHEALTHY`, `CONFIGURATION_ERROR`).
- **Pipeline node errors**: Each node returns `{errors: [...], node_statuses: {node_name: "FAILED"}}` on exception, allowing LangGraph to continue or terminate cleanly.
- **LLM errors**: `OllamaUnavailableError` raised by GemmaProvider triggers automatic fallback chain. `GrokUnavailableError` triggers BART degraded mode. Never crashes the pipeline.
- **Validation errors**: FastAPI `HTTPException` with explicit status codes (400, 403, 409, 422). State transition FSM with `VALID_TRANSITIONS` map.
- **Audit log**: `PermissionError` raised on any update/delete attempt (append-only invariant).
- **Degraded mode**: When no LLM available, `DegradedProvider` returns factual summary with `mode: "degraded_factual"` and confidence=45.0.

## Anti-Patterns

### Fabricated State in Health Checks

**What happens**: Connectors returning fabricated `last_success` or `quota_remaining` when the database is unavailable.

**Why it's wrong**: Violates honest telemetry principle — system reports false health.

**Do this instead**: Degrade silently to in-memory state. `SourceConnector.get_status()` falls back to `self.last_success` and `self.quota_remaining` when DB read fails (see `backend/app/connectors/base.py:302-345`).

### Silent Error Swallowing in Pipeline

**What happens**: Pipeline nodes catching exceptions and returning empty data without error tracking.

**Why it's wrong**: Errors become invisible, pipeline appears to succeed when it failed.

**Do this instead**: Each node appends to the `errors` list with node name, error message, and timestamp. State `node_statuses` dict tracks per-node status explicitly.

### Mixed Rereducer Semantics in LangGraph State

**What happens**: Using `operator.add` reducer for lists that should be replaced, causing duplicated signals.

**Why it's wrong**: LangGraph always applies the channel reducer to incoming values. `operator.add` on lists appends, producing duplicates.

**Do this instead**: Use `replace_list` reducer for `validated_signals` (see `backend/app/workflows/state.py:13-23`) and `operator.add` only for accumulating channels like `raw_signals` and `errors`.

## Cross-Cutting Concerns

**Logging**: `structlog` for structured JSON logging throughout the backend. `configure_structlog(json_logs=True)` in main.py.

**Validation**: Pydantic models for schemas, `validate_state_transition` FSM for review state machine, privacy gate for data classification.

**Authentication**: FastAPI dependency injection (`get_current_user`, `get_optional_user`), session-based auth with CSRF protection, demo mode with persona switching.

**PII/PHI Scrubbing**: `PIIPHIScrubber` applied before bronze persistence, before Grok API transmission, and before Athena query processing.

**Caching**: Redis 7 used for cache management endpoints (`backend/app/api/v1/endpoints/cache.py`).

---

*Architecture analysis: 2026-08-30*
