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
│  Ingest → Validate/PII → NLP Extract │ │  8 Connectors (PubMed, CT.gov,     │
│  → Ontology → Embed → Confluence     │ │  FDA, EMA, NewsAPI, Fierce, ET,    │
│  → Lifecycle → Red Team → Gap        │ │  BioPharma Dive)                   │
│  → Synthesize → Calibrate            │ │  PostgreSQL Advisory Lock Scheduler│
│  `backend/app/workflows/`            │ │  `backend/app/connectors/`         │
│                                      │ │  `backend/app/services/scheduler.py│
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
| **Signal Detail & Explainer** | 4-Question decision view, Evidence Convergence Tree, Priority Score Explainer, Red-Team Counter-factuals | `frontend/components/signals/SignalDetailWorkspace.tsx`, `frontend/components/signals/PriorityScoreExplainer.tsx`, `frontend/components/signals/EvidenceConvergenceWidget.tsx` |
| **Executive Briefing** | Daily top-3 prioritized signals hero card with strategic triage | `frontend/components/signals/SignalList.tsx` |
| **API Client & Mappers** | Type-safe REST client, error mapping, and contract transformers | `frontend/lib/api.ts`, `frontend/lib/mappers.ts` |
| **FastAPI Core** | Application lifecycle, correlation tracing, JSON logging, CORS | `backend/app/main.py`, `backend/app/core/middleware.py` |
| **Signals & Review Router** | Signal retrieval, filtering, 4-question decision data, review status transitions | `backend/app/api/v1/endpoints/signals.py` |
| **Athena Clinical Q&A** | Grounded clinical question answering with SSE token streaming and citation injection | `backend/app/api/v1/endpoints/intelligence.py` |
| **LangGraph Runner** | 11-node stateful workflow execution, error resilience, and state transitions | `backend/app/workflows/runner.py`, `backend/app/workflows/graph.py` |
| **Ingestion Connectors** | Multi-source data retrieval, normalization, and raw Bronze persistence (8 connectors) | `backend/app/connectors/base.py`, `backend/app/connectors/*.py` |
| **Autonomous Scheduler & Governor** | Background connector scheduling with backoff, jitter, advisory locking, and NewsAPI quota protection | `backend/app/services/scheduler.py` |
| **Red-Team Engine** | Contradiction detection against a 19-rule clinical registry | `backend/app/services/redteam.py` |
| **Routing & Authority** | Strategic role assignment, authority hierarchy, score calculation, and leadership escalation | `backend/app/services/routing.py`, `backend/app/services/authority.py`, `backend/app/services/scoring.py` |
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

**Intelligence Processing Flow:**

1. **Ingest Node** (`backend/app/workflows/nodes/ingest.py`): Ingests candidate payloads from Bronze storage into the pipeline state.
2. **Validate & PII Node** (`backend/app/workflows/nodes/validate.py`): Validates schema integrity and sanitizes candidate text through `PIIPHIScrubber`.
3. **NLP Extract Node** (`backend/app/workflows/nodes/nlp_extract.py`): Extracts clinical entities (drugs, targets, trial phases, patient populations).
4. **Medical Ontology Node** (`backend/app/workflows/nodes/ontology.py`): Maps extracted terms against domain configuration (`config/haemophilia.yaml`).
5. **Dense Embedding Node** (`backend/app/workflows/nodes/embed.py`): Generates 384-dimensional FastEmbed dense vectors.
6. **Confluence Clustering Node** (`backend/app/workflows/nodes/confluence.py`): Discovers multi-source temporal clusters and updates confluence scores.
7. **Lifecycle Tracking Node** (`backend/app/workflows/nodes/lifecycle.py`): Maps developmental milestones and updates asset pipelines.
8. **Red-Team Node** (`backend/app/workflows/nodes/redteam.py`): Scans signals against the 19 clinical contradiction rules.
9. **Gap Analysis Node** (`backend/app/workflows/nodes/missing_signal.py`): Detects regulatory and clinical reporting anomalies.
10. **Synthesis Node** (`backend/app/workflows/nodes/synthesize.py`): Generates structured 4-question decision data, executive briefing, and role actions using Gemma 3 / Grok.
11. **Calibration Node** (`backend/app/workflows/nodes/calibrate.py`): Applies stakeholder calibrated scoring weights and finalizes priority scores.

**State Management:**
- Relational state stored in PostgreSQL 16.
- In-memory workflow state passed immutably across LangGraph nodes via `MetaRadarState`.
- Frontend role switcher state stored in browser `sessionStorage`.

## Key Abstractions

**`SourceConnector` (`backend/app/connectors/base.py`):**
- Abstract base class for all 8 data connectors providing Bronze storage persistence, rate-limiting, error logging, and health telemetry.

**`LLMProvider` (`backend/app/providers/base.py`):**
- Unified contract for structured completion and streaming responses across Local Gemma, xAI Grok, and Degraded Factual fallback.

**`MetaRadarState` (`backend/app/workflows/state.py`):**
- TypedDict carrying signal payloads, extracted entities, embeddings, and intermediate analysis across graph nodes.

## Entry Points

**Backend API:**
- Location: `backend/app/main.py`
- Triggers: Uvicorn ASGI server invocation
- Responsibilities: Lifespan management, database connection pool startup, scheduler initialization, CORS, and route mounting.

**Frontend Application:**
- Location: `frontend/app/layout.tsx` & `frontend/app/page.tsx`
- Triggers: Next.js server/browser rendering
- Responsibilities: Global theme providers, shell layout, and radar overview rendering.

**Autonomous Ingestion Runner:**
- Location: `backend/app/services/scheduler.py`
- Triggers: Async background loop started on FastAPI startup
- Responsibilities: Schedules and triggers connectors at domain-configured intervals with advisory locking and quota protection.

## Error Handling

**Strategy:** Multi-tier graceful degradation with structured fallback.

**Patterns:**
- **Provider Fallback:** Local Gemma → xAI Grok (if enabled and gated) → Degraded Factual Deterministic Provider.
- **Database Safety:** Explicit session rollback and advisory lock release in `finally` blocks.
- **Client Error Mapping:** Strongly typed `ApiError` instances with fallback mock/demo data for graceful offline presentations.

## Cross-Cutting Concerns

**Logging:** Structured JSON logging via `structlog` with correlation IDs.
**Security & Privacy:** Automated PII/PHI redaction in logs and LLM prompts via `PIIPHIScrubber` and `backend/app/core/redact.py`.
**Verification:** Contract synchronization gating with automated OpenAPI schema export.

---

*Architecture analysis: 2026-08-27*
