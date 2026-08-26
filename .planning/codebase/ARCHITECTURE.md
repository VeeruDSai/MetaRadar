<!-- refreshed: 2026-08-27 -->
# Architecture

**Analysis Date:** 2026-08-27

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                                │
│  Next.js 16 (App Router) • React 19 • Tailwind CSS v4 CSS Tokens           │
│  9 Dedicated Intelligence Workspaces • Demo Operator Role Context           │
│  `frontend/app/` • `frontend/components/` • `frontend/lib/`                 │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / REST / SSE Stream
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        APPLICATION & ROUTING TIER                           │
│  FastAPI Application • OpenAPI 3.1 Contract • Correlation ID Middleware     │
│  Signals, Review Queue, Athena Q&A, Confluence, Ingestion Endpoints         │
│  `backend/app/api/v1/endpoints/` • `backend/app/core/`                      │
└──────────────────┬──────────────────────────────────────┬───────────────────┘
                   │                                      │
                   ▼                                      ▼
┌──────────────────────────────────────┐ ┌────────────────────────────────────┐
│      11-NODE LANGGRAPH PIPELINE      │ │      INGESTION & SCHEDULER TIER    │
│  Ingest → Validate/PII → NLP Extract │ │  7 Connectors (PubMed, CT.gov,     │
│  → Ontology → Embed → Confluence     │ │  FDA, EMA, NewsAPI, Fierce, ET)    │
│  → Lifecycle → Red Team → Gap        │ │  PostgreSQL Advisory Lock Scheduler│
│  → Synthesize → Calibrate            │ │  `backend/app/connectors/`         │
│  `backend/app/workflows/`            │ │  `backend/app/services/scheduler.py│
└──────────────────┬───────────────────┘ └─────────────────┬──────────────────┘
                   │                                       │
                   └───────────────────┬───────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA & STORAGE LAYER                              │
│  PostgreSQL 16 (Bronze Raw, Signals, Evidence, AuditLog, Weights)           │
│  pgvector (384-dim HNSW Cosine Index) • Redis 7 Cache & Locks               │
│  `backend/app/models/` • `backend/app/db/` • `config/haemophilia.yaml`      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|---|---|---|
| **App Router & Layout** | Shell layout, theme provider, navigation sidebar, demo operator role state | `frontend/app/layout.tsx`, `frontend/components/metaradar.tsx` |
| **Workspaces UI** | Specialized views for Signals, Confluences, Contradictions, Missing Signals, Calibration, Observability | `frontend/components/*/*Workspace.tsx` |
| **API Client & Mappers** | Type-safe REST client, error mapping, and contract transformers | `frontend/lib/api.ts`, `frontend/lib/mappers.ts` |
| **FastAPI Core** | Application lifecycle, correlation tracing, JSON logging, CORS | `backend/app/main.py`, `backend/app/core/middleware.py` |
| **Signals & Review Router** | Signal retrieval, filtering, 4-question decision data, review status transitions | `backend/app/api/v1/endpoints/signals.py` |
| **Athena Clinical Q&A** | Grounded clinical question answering with SSE token streaming and citation injection | `backend/app/api/v1/endpoints/intelligence.py` |
| **LangGraph Runner** | 11-node stateful workflow execution, error resilience, and state transitions | `backend/app/workflows/runner.py`, `backend/app/workflows/graph.py` |
| **Ingestion Connectors** | Multi-source data retrieval, normalization, and raw Bronze persistence | `backend/app/connectors/base.py`, `backend/app/connectors/*.py` |
| **Autonomous Scheduler** | Background connector scheduling with backoff, jitter, and advisory locking | `backend/app/services/scheduler.py` |
| **Red-Team Engine** | Contradiction detection against a 19-rule clinical registry | `backend/app/services/redteam.py` |
| **Routing & Authority** | Strategic role assignment, score calculation, and leadership escalation | `backend/app/services/routing.py`, `backend/app/services/scoring.py` |
| **Provenance Resolver** | Canonical record URL validation, direct article link resolution, landing page blocking | `backend/app/services/provenance_urls.py` |
| **Database Models** | SQLAlchemy 2.0 ORM definitions for Signals, Evidence, AuditLog, and metadata | `backend/app/models/__init__.py` |

## Pattern Overview

**Overall:** Tiered Clean Architecture + Directed Acyclic Graph (DAG) Pipeline + Human-in-the-Loop (HITL) Decision Feedback

**Key Characteristics:**
- **Truthful Provenance Invariant:** Raw payloads are immutably captured in Bronze storage (`raw_signals_bronze`), mapped to normalized evidence excerpts (`evidence`), and linked directly to authoritative primary records.
- **Strict 3-Pillar Separation:** Verbatim primary evidence, AI strategic interpretation, and recommended organizational actions are maintained as distinct data properties.
- **Persistent State Machine with Audit Log:** Signal reviews mutate persistent database records with synchronous `AuditLog` row insertions.

## Layers

**Presentation Layer:**
- Purpose: Delivers responsive workspaces tailored to 6 pharma stakeholder roles.
- Location: `frontend/app/`, `frontend/components/`
- Contains: React 19 Server and Client components, custom Framer Motion animations, Lucide icons.
- Depends on: `frontend/lib/api.ts`, `frontend/types/api.ts`
- Used by: End users, judges, pharma stakeholders.

**Application Tier (FastAPI):**
- Purpose: Exposes validated REST endpoints and SSE streams.
- Location: `backend/app/api/v1/endpoints/`
- Contains: Pydantic schemas, dependency injectors, route controllers.
- Depends on: `backend/app/services/`, `backend/app/models/`, `backend/app/db/`
- Used by: Next.js frontend client, external test harnesses.

**Pipeline & Intelligence Tier (LangGraph):**
- Purpose: Transforms raw biomedical documents into scored, classified, and synthesized decision objects.
- Location: `backend/app/workflows/`
- Contains: Graph builder, state definitions, 11 discrete execution nodes (`ingest`, `validate`, `nlp_extract`, `ontology`, `embed`, `confluence`, `lifecycle`, `redteam`, `missing_signal`, `synthesize`, `calibrate`).
- Depends on: `backend/app/providers/`, `backend/app/services/`
- Used by: `PipelineRunner`, scheduled ingestion worker.

**Data & Persistence Layer:**
- Purpose: Manages relational state, vector embeddings, and domain configurations.
- Location: `backend/app/models/`, `backend/app/db/`, `config/`
- Contains: SQLAlchemy ORM models, session factories, YAML parsers.
- Depends on: PostgreSQL 16, pgvector.
- Used by: Application tier and Pipeline nodes.

## Data Flow

### Primary Ingestion & Pipeline Path

1. **Connector Fetch:** Connector (`backend/app/connectors/*.py`) retrieves raw items from external APIs/RSS feeds.
2. **Bronze Storage:** Verbatim payload is inserted into `raw_signals_bronze` with SHA-256 content hash.
3. **Graph Execution:** `PipelineRunner` initializes `MetaRadarState` and executes the 11-node graph.
4. **Validation & PII:** `validate` node runs `PIIPHIScrubber` to sanitize patient identifiers.
5. **Extraction & Embedding:** `nlp_extract` extracts entities; `embed` generates 384-dim vector with `fastembed`.
6. **Confluence & Red-Team:** `confluence` detects multi-source clustering; `redteam` checks pairwise claim contradictions.
7. **Synthesis & Routing:** `synthesize` invokes Gemma 3 / Grok to generate the 4-question decision object; `routing` assigns priority and primary stakeholder function.
8. **Signal Persistence:** Final signal is committed to `signals` table with `review_status="UNREVIEWED"`.

### Signal Review & Decision Workflow

1. **User Action:** Stakeholder selects action in UI (e.g. "Approve Priority & Route").
2. **API Call:** Frontend sends `POST /api/v1/signals/{id}/review` with operator persona and decision notes.
3. **DB Mutation:** Backend updates `Signal.review_status`, `Signal.reviewed_by`, `Signal.reviewed_at`, and `Signal.review_decision`.
4. **Audit Trail:** Backend synchronously inserts an `AuditLog` row documenting the state transition.
5. **Response:** Updated signal object is returned to UI for optimistic updates and queue re-filtering.

**State Management:**
- Frontend: Local component state + `sessionStorage` for demo operator persona + SWR caching.
- Backend: PostgreSQL ACID transactions with `AsyncSession`.

## Key Abstractions

**`BaseConnector`:**
- Purpose: Abstract base class enforcing standardized fetching, deduplication, and Bronze storage.
- Location: `backend/app/connectors/base.py`
- Pattern: Template Method Pattern.

**`LLMProvider`:**
- Purpose: Unified interface for multi-backend AI reasoning (`LocalGemmaProvider`, `GrokProvider`, `DegradedFactualProvider`).
- Location: `backend/app/providers/base.py`, `backend/app/providers/factory.py`
- Pattern: Strategy & Abstract Factory Pattern.

**`DomainConfig`:**
- Purpose: Extensible YAML-driven domain model defining disease terms, competitor assets, and priority weights.
- Location: `backend/app/core/domain_config.py` (`config/haemophilia.yaml`)
- Pattern: Data Transfer Object & Singleton Configuration.

## Entry Points

**Backend API Entry:**
- Location: `backend/app/main.py`
- Triggers: Uvicorn ASGI server (`uvicorn app.main:app --port 8000`)
- Responsibilities: Initializes structlog, loads domain config, starts `SourceScheduler`, binds middleware and routers.

**Frontend Web Entry:**
- Location: `frontend/app/layout.tsx`, `frontend/app/page.tsx`
- Triggers: Next.js dev or production server (`next start`)
- Responsibilities: Renders root layout, loads theme custom tokens, initializes demo operator persona.

**Development Orchestrators:**
- Location: `setup.py`, `start.py`
- Triggers: CLI execution (`python setup.py`, `python start.py`)
- Responsibilities: Pre-flight dependency check, database initialization, parallel backend/frontend process launcher.

## Architectural Constraints

- **Threading & Async Model:** FastAPI runs on `asyncio` event loop. Long-running CPU-bound embeddings or model downloads execute in executor threads or background workers.
- **Global State:** Database engine and sessionmaker are managed via `backend/app/db/session.py`. Scheduler is a managed singleton (`SourceScheduler.get_instance()`).
- **Circular Imports:** Avoid importing FastAPI endpoint routers inside service layers; all service dependencies are passed via parameters or constructor injection.

## Anti-Patterns

### Anti-Pattern 1: Hardcoded Tailwind Colors & Utilities
**What happens:** Using arbitrary hex codes (e.g. `bg-[#0f172a]`) or hardcoded `text-slate-400`.  
**Why it's wrong:** Breaks dark/light theme adaptability and violates design system consistency.  
**Do this instead:** Use semantic CSS variables (`bg-[var(--surface)]`, `text-[var(--muted-foreground)]`).

### Anti-Pattern 2: Awaiting Synchronous SQLAlchemy Methods
**What happens:** Writing `await session.add(instance)`.  
**Why it's wrong:** `session.add()` is synchronous in SQLAlchemy 2.0 even when using `AsyncSession`. Awaiting it raises runtime `TypeError`.  
**Do this instead:** Call `session.add(instance)` synchronously, then `await session.commit()`.

### Anti-Pattern 3: Generic Portal URLs for Evidence Provenance
**What happens:** Emitting generic homepage URLs (`https://newsapi.org/register`, `https://www.fda.gov`).  
**Why it's wrong:** Violates the Truthful Provenance Invariant by presenting non-evidential landing pages.  
**Do this instead:** Use `resolve_canonical_provenance()` to generate document-specific links or report `missing_url`.

## Error Handling

**Strategy:** Structured hierarchical exception handling with correlation ID tracking.

**Patterns:**
- Custom HTTP error responses via `ApiError` (`frontend/lib/errors.ts`) and FastAPI `HTTPException`.
- Database error rollback: Automatic `await session.rollback()` on transaction failure.
- Ingestion error resilience: Connectors capture errors in `Source.last_error` and `SourceHealthLog` without crashing the scheduler loop.

## Cross-Cutting Concerns

**Logging:** Structured JSON logs via `structlog` with correlation IDs (`X-Correlation-ID`) and automated regex redaction of sensitive patient data.  
**Validation:** Strict input validation via Pydantic v2 schemas across all API boundaries.  
**Authentication:** Persona-driven review tracking with immutable audit logging.

---

*Architecture analysis: 2026-08-27*
