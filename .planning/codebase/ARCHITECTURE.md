<!-- refreshed: 2026-08-28 -->
# Architecture

**Analysis Date:** 2026-08-28

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────────────┐
│                   Next.js 16 + React 19 Frontend Client                          │
│                   `frontend/app/` & `frontend/components/`                       │
├──────────────────────────┬───────────────────────────┬───────────────────────────┤
│    Athena Intelligence   │    Signals & Detail View  │  Domain Workspaces        │
│   `components/intelligence` `components/signals`     │ `components/calibration`  │
│   `components/auth`      │  `components/common`      │ `components/confluence`   │
└─────────────┬────────────┴─────────────┬─────────────┴─────────────┬─────────────┘
              │                          │                           │
              │ REST / JSON (API Base: /api/v1 via `frontend/lib/api.ts`)
              ▼                          ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                     FastAPI Application Gateway & Routing                        │
│                           `backend/app/main.py`                                  │
├──────────────────────────────────────────────────────────────────────────────────┤
│  Middlewares: CorrelationIdMiddleware, SecurityHeadersMiddleware, CORS           │
│  Routers: /health, /auth, /signals, /intelligence, /ingestion, /search, etc.     │
└─────────────┬──────────────────────────┬───────────────────────────┬─────────────┘
              │                          │                           │
              ▼                          ▼                           ▼
┌──────────────────────────┐ ┌──────────────────────────┐ ┌────────────────────────┐
│ Autonomous Scheduler     │ │ LangGraph Pipeline (11N) │ │ LLM Provider Factory   │
│ `services/scheduler.py`  │ │ `workflows/graph.py`     │ │ `providers/factory.py` │
└─────────────┬────────────┘ └───────────┬──────────────┘ └──────────┬─────────────┘
              │                          │                           │
              ▼                          ▼                           ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                 Domain Services, Ontology & Logic Layer                          │
│                        `backend/app/services/`                                   │
│  - domain_config.py (`config/haemophilia.yaml`)  - deduplication & pii scrubbing │
│  - scoring.py & calibration.py                   - vector_query.py & embeddings  │
│  - redteam.py & confluence.py                    - authority.py & routing.py     │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                        Data Storage & Indexing Layer                             │
│                  `backend/app/models/` & `backend/app/db/`                       │
├────────────────────────────────────────┬─────────────────────────────────────────┤
│ PostgreSQL 16 + pgvector (AsyncPG)     │ Redis 7 In-Memory Cache                 │
│ - Raw Bronze: raw_signals_bronze       │ - Session token verification            │
│ - Gold: signals, evidence, developments│ - Rate limiting counters                │
│ - Embeddings: pgvector 384d index      │ - Fast query result caching             │
│ - Immutable Append-Only: audit_log     │                                         │
└────────────────────────────────────────┴─────────────────────────────────────────┘
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| API Entry & Routing | Application lifecycle, middleware setup, router mounting | `backend/app/main.py` |
| Settings & Config | Environment variables, defaults, rate limits, connector validation | `backend/app/core/config.py` |
| Domain Ontology | Loads disease areas, targets, assets, competitors, mechanisms | `backend/app/core/domain_config.py` |
| Pipeline Orchestrator | Compiles and executes the 11-node LangGraph intelligence pipeline | `backend/app/workflows/graph.py` |
| Pipeline State | Canonical state schema for signals moving through LangGraph | `backend/app/workflows/state.py` |
| LLM Factory | Routes reasoning requests to Gemma (GGUF/Ollama), Grok (xAI), or BART | `backend/app/providers/factory.py` |
| Background Scheduler | Autonomous cron polling of external connectors with jitter and backoff | `backend/app/services/scheduler.py` |
| Vector Engine | FastEmbed text embedding generation (`all-MiniLM-L6-v2`) | `backend/app/services/embeddings.py` |
| Vector Query | Performs cosine similarity and hybrid keyword-vector retrieval | `backend/app/services/vector_query.py` |
| Calibration Engine | Adjusts scoring weights per stakeholder function from user feedback | `backend/app/services/calibration.py` |
| Red Team Engine | Generates counterfactual arguments and adversarial signal challenges | `backend/app/services/redteam.py` |
| Confluence Engine | Correlates cross-source signals into unified development events | `backend/app/services/confluence.py` |
| Database Models | Declarative SQLAlchemy 2.0 models and vector columns | `backend/app/models/__init__.py` |
| Auth & RBAC | Session management, password hashing, demo login, user roles | `backend/app/services/auth_service.py` |
| Frontend Shell | Root layout, theme injection, navigation sidebar, dynamic routing | `frontend/app/layout.tsx` |
| API Client | Unified typed REST client handling authentication, errors, responses | `frontend/lib/api.ts` |
| TypeScript Types | Strongly typed interfaces mirroring backend Pydantic models | `frontend/types/api.ts` |

## Pattern Overview

**Overall:** Modular Multi-Tiered Layered Architecture with Event-Driven Ingestion and Graph-Based Intelligence Processing.

**Key Characteristics:**
- **Separation of Concerns:** Strict isolation between API routing (`app/api/`), business services (`app/services/`), workflow graphs (`app/workflows/`), database persistence (`app/models/`), and frontend views (`frontend/components/`).
- **Medallion Data Architecture (Bronze/Silver/Gold):**
  - Bronze: `raw_signals_bronze` preserves verbatim unmodified payloads from external APIs.
  - Silver: `evidence` and `developments` store parsed, validated, and normalized records.
  - Gold: `signals` stores enriched decision objects with vector embeddings, calibration scores, and suggested actions.
- **Provider Fallback & Privacy Gate:** Local-first LLM inference (Local Gemma 3 4B) ensures sensitive pharmaceutical CI data never leaves the local environment unless explicitly configured for hosted Grok with automated PII scrubbing.

## Layers

**1. Presentation Layer (`frontend/`):**
- Purpose: Delivers responsive, high-aesthetic UI for executive decision intelligence.
- Location: `frontend/app/`, `frontend/components/`
- Contains: Next.js App Router pages, React 19 Client components, Framer Motion animations, Recharts, Lucide icons.
- Depends on: Backend REST API (`/api/v1/*`).

**2. API & Middleware Layer (`backend/app/api/`, `backend/app/core/`):**
- Purpose: HTTP request validation, correlation ID tracking, security headers, authentication, error serialization.
- Location: `backend/app/main.py`, `backend/app/api/v1/endpoints/`, `backend/app/core/middleware.py`
- Contains: FastAPI router functions with Pydantic v2 request/response models.
- Depends on: Business services and database sessions.

**3. Workflow & Intelligence Layer (`backend/app/workflows/`):**
- Purpose: Orchestrates multi-step signal processing, NLP extraction, entity linking, vector embedding, and counterfactual validation.
- Location: `backend/app/workflows/graph.py`, `backend/app/workflows/nodes/`
- Contains: 11 LangGraph state transformation nodes.
- Depends on: Domain configuration and service providers.

**4. Domain & Service Layer (`backend/app/services/`):**
- Purpose: Core business logic, relevance scoring algorithms, stakeholder calibration, red-team analysis, scheduling.
- Location: `backend/app/services/`
- Contains: Pure Python algorithms, vector math, connector scrapers.
- Depends on: SQLAlchemy models and LLM providers.

**5. Persistence Layer (`backend/app/models/`, `backend/app/db/`):**
- Purpose: Reliable relational and vector persistence with strict transaction boundaries.
- Location: `backend/app/db/session.py`, `backend/app/models/`
- Contains: PostgreSQL 16 tables, pgvector vector indices, Redis client.

## Data Flow

### Primary Signal Processing Flow (Ingestion to Gold Signal)

1. **Ingestion Trigger:** Autonomous scheduler (`backend/app/services/scheduler.py`) or manual API trigger (`POST /api/v1/ingestion/run`) invokes connector (`backend/app/connectors/pubmed.py`).
2. **Bronze Storage:** Verbatim response payload is stored in `raw_signals_bronze` (`backend/app/models/__init__.py:176`).
3. **LangGraph Pipeline Execution (`backend/app/workflows/runner.py`):**
   - `node_ingest` -> Parses raw payload.
   - `node_validate` -> Evaluates content hashes, deduplicates against existing records (`services/deduplication.py`).
   - `node_embed` -> Generates 384d dense vector (`services/embeddings.py`).
   - `node_nlp_extract` -> Extracts medical entities (drugs, targets, trial phases, endpoints).
   - `node_ontology_enrich` -> Matches against `config/haemophilia.yaml`.
   - `node_confluence` -> Groups related signals into multi-source developments (`services/confluence.py`).
   - `node_lifecycle` -> Updates asset clinical stage (Phase 1/2/3/Approved).
   - `node_redteam` -> Evaluates risk, bias, counter-evidence (`services/redteam.py`).
   - `node_missing_signal` -> Detects missing competitor milestones or latency gaps.
   - `node_synthesize` -> Invokes Gemma LLM for executive "What Changed & Why It Matters" synthesis.
   - `node_calibrate` -> Computes function-specific priority score (Impact x Urgency x Novelty) (`services/scoring.py`).
4. **Gold Storage & Indexing:** Enriched record committed to `signals` table with pgvector embedding.
5. **UI Presentation:** Next.js frontend fetches updated signals (`frontend/app/signals/page.tsx`) and renders real-time alerts.

### Calibration & Stakeholder Feedback Flow

1. User submits relevance and urgency feedback via UI (`frontend/components/calibration/CalibrationWorkspace.tsx`).
2. Endpoint `POST /api/v1/feedback` stores row in `calibration_feedback` (`backend/app/api/v1/endpoints/feedback.py`).
3. Calibration Service recalculates functional weights in `scoring_weights` (`backend/app/services/calibration.py`).
4. Signals re-ranked dynamically reflecting stakeholder priority.

## Architectural Constraints

- **Single Source of Truth for Schemas:** Backend Pydantic models in `backend/app/schemas/` define the API contract; frontend types in `frontend/types/api.ts` must stay synchronized (verified via `scripts/generate_parity_matrix.py` and `tests/test_contract_drift.py`).
- **Data Privacy & LLM Boundary:** Sensitive internal queries must never hit external cloud LLMs without automated PII scrubbing. Local Gemma-3-4B is the primary default reasoning engine.
- **Audit Immutability:** The `audit_log` table is append-only. SQLAlchemy event listeners explicitly reject all UPDATE and DELETE operations.
- **Async Database IO:** All database interactions in FastAPI handlers must use `AsyncSession` to prevent blocking the async event loop.

## Error Handling

**Strategy:** Fail-safe, graceful degradation across connectors and inference engines.

**Patterns:**
- **Connector Isolation:** If PubMed or OpenFDA encounters a 429/500 error, `SourceHealthLog` logs the failure, increments exponential backoff, and continues running other active connectors without interrupting the pipeline.
- **LLM Tier Fallback:** Local Gemma GGUF -> Ollama API -> Hosted Grok API -> Extractive BART Summarizer (`backend/app/providers/factory.py`).
- **API Error Formatting:** Standardized error responses with HTTP status codes and correlation IDs.

---

*Architecture analysis: 2026-08-28*
