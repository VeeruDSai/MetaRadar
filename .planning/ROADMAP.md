# MetaRadar v5.1 — Implementation Roadmap

> **Current Status:** Phase 0 (Baseline Stabilization & Governance) completed & verified. Phase 1 ready for planning and execution.

---

## Phase Structure Overview

```
Phase 0: Baseline Stabilization & Governance (COMPLETED)
   │
   ▼
Phase 1: Ingestion Connectors & Data Pipeline (NEXT)
   │
   ▼
Phase 2: LangGraph 10-Node Intelligence Engine
   │
   ▼
Phase 3: Vector Search & LLM Provider Execution
   │
   ▼
Phase 4: Frontend API Integration & Real-Time Workspace
   │
   ▼
Phase 5: Calibration & End-to-End Verification
```

---

## Phase Details & Goals

### Phase 0: Baseline Stabilization & Governance (Status: COMPLETED)
- **Goal**: Reconcile Next.js 16 + FastAPI 0.115 stack, enforce strict typecheck/lint/build quality gates, build 18-point pytest suite, author Dockerfiles, establish Alembic async scaffold, unify OpenAPI contract at `frontend/types/api.ts`, and set CI governance.
- **Verification**: `pytest -v` (18/18 passed), `tsc` (0 errors), `eslint` (0 errors), `next build` (compiled), `git push origin feature/stabilization-baseline`.

### Phase 1: Ingestion Connectors & Data Pipeline (Status: PLANNED)
- **Goal**: Implement concrete `SourceConnector` adapters for PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, and EMA RSS. Build bronze-layer verbatim payload storage and deterministic deduplication.
- **Key Deliverables**: `backend/app/connectors/pubmed.py`, `clinical_trials.py`, `newsapi.py`, `fda.py`, `ema.py`, deduplication integration, and ingest tests.

### Phase 2: LangGraph 10-Node Intelligence Engine (Status: PLANNED)
- **Goal**: Build stateful 10-node LangGraph pipeline (`node_ingest` through `node_calibrate -> END`) managing `IntelligenceState`.
- **Key Deliverables**: `backend/app/workflows/` package, node functions, state reducers, and workflow unit tests.

### Phase 3: Vector Search & LLM Provider Execution (Status: PLANNED)
- **Goal**: Integrate 384-dim sentence-transformers embedding generation, pgvector HNSW similarity queries, and real Gemma/Grok text synthesis.
- **Key Deliverables**: Embedding service, vector query service, provider execution integration, and retrieval tests.

### Phase 4: Frontend API Integration & Real-Time Workspace (Status: PLANNED)
- **Goal**: Connect Next.js App Router UI (`frontend/lib/api.ts`) to backend `/api/v1` REST endpoints. Render real signals, Ask Athena answers, and portfolio momentum.
- **Key Deliverables**: Live REST client in `frontend/lib/api.ts`, component state updates, and end-to-end UI verification.

### Phase 5: Calibration & End-to-End Verification (Status: PLANNED)
- **Goal**: Implement `StakeholderCalibrationService` for rating feedback, execute the haemophilia demo story (mim8 / Hemgenix durability), and perform final Definition of Done audit.
- **Key Deliverables**: Feedback API, weight adjustment service, demo scenario test, and release documentation.
