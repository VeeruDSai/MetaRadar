# Architecture

**Analysis Date:** 2026-08-25

## System Overview

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       Next.js 16 Frontend (React 19)                        │
│   App Router Workspace Architecture: app/[section]/page.tsx switch router   │
│   Modular Workspaces: components/signals, components/confluence, etc.       │
│   Design Tokens & Modern CSS: app/globals.css (no hardcoded slate / hex)    │
│   Typed API Client: lib/api.ts (strongly typed via types/api.ts)            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP JSON (fetch, NEXT_PUBLIC_API_URL)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend /api/v1 (:8000)                     │
│                         `backend/app/main.py`                               │
├───────────────────┬───────────────────┬─────────────────────────────────────┤
│  REST Endpoints   │  Source Scheduler │   LangGraph Pipeline                │
│  `app/api/v1/     │  (asyncio,        │   `app/workflows/graph.py`          │
│   endpoints/*`    │   singleton)      │   11 linear nodes                   │
│  10 Routers       │  `app/services/   │   `app/workflows/nodes/*`           │
│                   │   scheduler.py`   │   orchestrated by runner.py         │
└─────────┬─────────┴─────────┬─────────┴──────────────────┬──────────────────┘
          │                   │                            │
          ▼                   ▼                            ▼
┌──────────────────┐  ┌──────────────────┐  ┌─────────────────────────────────┐
│ Service Layer    │  │ LLM Providers    │  │ Source Connectors               │
│ `app/services/*` │  │ `app/providers/` │  │ `app/connectors/*`              │
│ 16 domain modules│  │ Gemma (Ollama/   │  │ PubMed, ClinicalTrials, OpenFDA,│
│ (scoring, routing│  │ GGUF) → Grok →   │  │ EMA, NewsAPI                    │
│ calibration, etc)│  │ Degraded BART    │  │ (bounded backoff & retry)       │
└─────────┬────────┘  └──────────────────┘  └──────────────┬──────────────────┘
          │                                                │
          ▼                                                ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                 PostgreSQL 16 + pgvector (Medallion Storage)                │
│   `backend/app/models/__init__.py` (SQLAlchemy 2.0 asyncpg)                 │
│   Bronze: raw_signals_bronze (raw immutable JSON)                           │
│   Silver: signals (+ Vector(384) embeddings)                                │
│   Gold: developments, confluences, contradictions, watch_items, calibration │
└─────────────────────────────────────────────────────────────────────────────┘
          ▲                                       ▲
          │                                       │
┌─────────┴──────────┐                 ┌──────────┴─────────────┐
│ Ollama Sidecar     │                 │ Redis 7                │
│ gemma3:4b (GPU)    │                 │ redis://localhost:6379 │
│ :11434             │                 │ (cache & fast key-val) │
└────────────────────┘                 └────────────────────────┘

Domain configuration (single YAML source of truth):
`config/haemophilia.yaml` → parsed into typed Pydantic models by `backend/app/core/domain_config.py`
```

## Component Responsibilities

| Component | Responsibility | Primary Files |
|-----------|----------------|---------------|
| **FastAPI Core** | Route registration, CORS, request/response middleware, correlation ID tracking, graceful startup/shutdown | `backend/app/main.py`, `backend/app/core/middleware.py` |
| **REST Endpoints** | HTTP route handlers, query validation, and Pydantic serialization across 10 resource routers | `backend/app/api/v1/endpoints/*.py` |
| **Domain Config Engine** | Loads and validates `config/haemophilia.yaml` (assets, queries, thresholds, routing weights) | `backend/app/core/domain_config.py` |
| **Data Connectors** | Fetches raw records from 5 biomedical sources into bronze storage with exponential backoff | `backend/app/connectors/*.py` |
| **Ingestion Service** | Orchestrates connector executions, tracks per-source run status, records health metrics | `backend/app/services/ingestion.py` |
| **Source Scheduler** | Background asyncio worker managing recurring connector runs with PostgreSQL advisory locks | `backend/app/services/scheduler.py` |
| **LangGraph Pipeline** | 11-step directed graph processing silver signals into gold synthesized intelligence | `backend/app/workflows/graph.py`, `runner.py` |
| **LLM Provider Chain** | Multi-tier reasoning: Local Gemma (Ollama/GGUF) → xAI Grok (privacy gated) → Degraded fallback | `backend/app/providers/*.py` |
| **Embeddings Service** | In-process fastembed ONNX MiniLM-L6-v2 vectorizer generating 384-dim dense embeddings | `backend/app/services/embeddings.py` |
| **Calibration Service** | Brier score calculation, Expected Calibration Error (ECE), reliability diagrams, human feedback loop | `backend/app/services/calibration.py` |
| **Provenance Resolver** | Resolves canonical hyperlinks to external authoritative biomedical repositories | `backend/app/services/provenance_urls.py` |
| **Frontend Workspaces** | Specialized UI workspaces (Signals, Confluence, Contradictions, Calibration, Observability) | `frontend/components/**/*.tsx` |
| **API Client** | Strongly typed frontend fetch layer with error normalization and abort controller support | `frontend/lib/api.ts`, `frontend/types/api.ts` |

## Pipeline Flow (11 Linear Nodes)

1. **`ingest`**: Fetches pending signals from `raw_signals_bronze` or falls back to synthetic dataset if configured.
2. **`validate`**: Cleans text, redacts sensitive PII, validates required schema invariants, and flags malformed inputs.
3. **`embed`**: Generates 384-dimensional dense semantic vectors using fastembed CPU ONNX engine.
4. **`nlp_extract`**: Extracts clinical entities (biomarkers, mechanisms, endpoints, company/institution names) via Gemma or heuristic parser.
5. **`ontology_enrich`**: Maps extracted entities to standardized MeSH and domain taxonomy definitions.
6. **`confluence`**: Computes cosine similarity across vector embeddings and groups converging cross-source signals.
7. **`lifecycle`**: Tracks signal trajectory across clinical stages (Discovery, Preclinical, Phase I-III, Approved, Post-market).
8. **`redteam`**: Generates adversarial challenges and counter-evidence hypotheses against high-priority signals.
9. **`missing_signal`**: Evaluates pipeline coverage gaps and identifies potential blind spots or unmonitored assets.
10. **`synthesize`**: Produces executive intelligence briefs, actionable clinical takeaways, and strategic implications.
11. **`calibrate`**: Computes probabilistic calibration confidence scores, Brier penalties, and adjusts for source independence.
