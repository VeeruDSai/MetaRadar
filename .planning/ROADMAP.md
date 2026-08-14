# MetaRadar v5.1 — Implementation Roadmap

> **Current Status:** Phase 0 (Baseline Stabilization & Governance) completed & verified. Phase 1 ready for planning and execution.  
> **Specification Authority:** Fully aligned with `docs/rules/` (Canonical Operating Standards), `docs/METARADAR_MASTER_PLAN_v5.0.md`, `docs/10_ARCHITECTURE_HARDENING_REPORT.md`, `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`, and `docs/4_UI_DESIGN_DOCUMENT.md`.

---

## Phase Structure & Document Mapping Overview

```
Phase 0: Baseline Stabilization & Governance (COMPLETED)
   │ └── Aligned with: docs/10_ARCHITECTURE_HARDENING_REPORT.md & docs/rules/*
   ▼
Phase 1: Ingestion Connectors & Data Pipeline (NEXT)
   │ └── Aligned with: Master Plan §4.1, SDD §2.1, & SRS §3.1
   ▼
Phase 2: LangGraph 10-Node Intelligence Engine
   │ └── Aligned with: Master Plan §4, SDD §2.3, & SRS §3.2
   ▼
Phase 3: Vector Search & LLM Provider Execution
   │ └── Aligned with: Master Plan §13-§14, SDD §2.4, & Hardening Report §5
   ▼
Phase 4: Frontend API Integration & Real-Time Workspace
   │ └── Aligned with: UI Design Doc §4, Master Plan §3, & Hardening Report §6
   ▼
Phase 5: Calibration & End-to-End Verification
     └── Aligned with: Master Plan §3 & §12, SRS §3.5, & Definition of Done
```

---

## Phase Details & Document Alignment

### Phase 0: Baseline Stabilization & Governance (Status: COMPLETED)

- **Goal**: Reconcile Next.js 16 + FastAPI 0.115 stack, enforce strict typecheck/lint/build quality gates, build 18-point pytest suite, author Dockerfiles, establish Alembic async scaffold, unify OpenAPI contract at `frontend/types/api.ts`, and set CI governance.
- **Specification Alignment**:
  - `docs/rules/ENGINEERING_STANDARDS.md`
  - `docs/rules/DEFINITION_OF_DONE.md`
  - `docs/rules/TESTING_STRATEGY.md`
  - `docs/10_ARCHITECTURE_HARDENING_REPORT.md`
- **Verification**: `pytest -v` (18/18 passed), `tsc` (0 errors), `eslint` (0 errors), `next build` (compiled), `git push origin feature/stabilization-baseline`.

### Phase 1: Ingestion Connectors & Data Pipeline (Status: PLANNED)

- **Goal**: Implement concrete `SourceConnector` adapters for PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, and EMA RSS. Build bronze-layer verbatim payload storage (`raw_signals_bronze`) and deterministic deduplication (`generate_fingerprint`).
- **Specification Alignment**:
  - `docs/METARADAR_MASTER_PLAN_v5.0.md` (§4.1 Ingestion & Validation)
  - `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` (§2.1 Data Ingestion Architecture)
  - `docs/2_SRS_Software_Requirements_Specification.md` (§3.1 Data Acquisition)
- **Key Deliverables**: `backend/app/connectors/pubmed.py`, `clinical_trials.py`, `newsapi.py`, `fda.py`, `ema.py`, deduplication integration, and ingest tests.

### Phase 2: LangGraph 10-Node Intelligence Engine (Status: COMPLETED)

- **Goal**: Build stateful 10-node LangGraph pipeline (`node_ingest` through `node_calibrate -> END`) managing `IntelligenceState`.
- **Specification Alignment**:
  - `docs/METARADAR_MASTER_PLAN_v5.0.md` (§4 Pipeline & §12 Domain Rules)
  - `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` (§2.3 Workflow State Machine)
  - `docs/8_CORRECTED_UNIFIED_PLAN.md` (§3 Pipeline Architecture)
- **Key Deliverables**: `backend/app/workflows/` package (state, graph, runner, 10 node modules), `backend/app/api/v1/endpoints/pipeline.py`, synthetic fallback dataset, and 17-point unit test suite.
- **Verification**: `pytest -v` (51/51 passed), `tsc` (0 errors), `eslint` (0 errors), `next build` (compiled), `contracts/openapi.json` synchronized.

### Phase 3: Vector Search & LLM Provider Execution (Status: IN PROGRESS — Plan 03 executed, verification pending)

- **Goal**: Integrate 384-dim sentence-transformers embedding generation, pgvector HNSW similarity queries (`signals_embedding_hnsw`), and ProviderFactory execution (Local Gemma 3 4B -> Grok privacy-gated fallback -> BART degraded mode).
- **Specification Alignment**:
  - `docs/METARADAR_MASTER_PLAN_v5.0.md` (§13 Reasoning Layer & §14 Hardening)
  - `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` (§2.4 Provider Abstraction)
  - `docs/rules/DATA_AND_PRIVACY_STANDARDS.md`
- **Key Deliverables**: Embedding service, vector query service, provider execution integration, and retrieval tests.
- **Plan 03 (Tracer) — COMPLETE** (commits `ae657db`..`7278508`): fastembed EmbeddingService, `node_embed` (11-node pipeline), pgvector hybrid `VectorQueryService` + `POST /api/v1/search`, real Ollama-backed Gemma 3 4B, real xAI Grok client, honest `/health/models`, CLI backfill, Ollama docker-compose service. Gates: 61 passed + 1 skipped (live), 0 contract drift, compose validated.
- **Remaining in phase**: Phase 3 VERIFICATION.md (live Ollama Gemma on GPU, live Grok with `LIVE_XAI_KEY`, pgvector search against running Postgres + HNSW index).

### Phase 4: Frontend API Integration & Real-Time Workspace (Status: PLANNED)

- **Goal**: Connect Next.js App Router UI (`frontend/lib/api.ts`) to backend `/api/v1` REST endpoints (`/signals`, `/overview`, `/athena`). Render real signals, Ask Athena answers, and portfolio momentum.
- **Specification Alignment**:
  - `docs/4_UI_DESIGN_DOCUMENT.md` (§3 Component Hierarchy & §4 Data Flow)
  - `docs/METARADAR_MASTER_PLAN_v5.0.md` (§3 Four-Question Decision Interface)
  - `docs/rules/ARCHITECTURE_RULES.md`
- **Key Deliverables**: Live REST client in `frontend/lib/api.ts`, component state updates, and end-to-end UI verification.

### Phase 5: Calibration & End-to-End Verification (Status: PLANNED)

- **Goal**: Implement `StakeholderCalibrationService` for rating feedback, execute the haemophilia demo story (mim8 / emicizumab / Hemgenix durability data), and perform final Definition of Done audit.
- **Specification Alignment**:
  - `docs/METARADAR_MASTER_PLAN_v5.0.md` (§3 MVP Scope & §12 Domain Research)
  - `docs/2_SRS_Software_Requirements_Specification.md` (§3.5 Calibration Loop)
  - `docs/rules/DEFINITION_OF_DONE.md`
- **Key Deliverables**: Feedback API, weight adjustment service, demo scenario test, and release documentation.
