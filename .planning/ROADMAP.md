# MetaRadar v5.1 — Implementation Roadmap

> **Current Status:** Phase 6 (Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers) COMPLETED & VERIFIED.  
> **Specification Authority:** Fully aligned with `docs/rules/` (Canonical Operating Standards), `docs/METARADAR_MASTER_PLAN_v5.0.md`, `docs/10_ARCHITECTURE_HARDENING_REPORT.md`, `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`, and `docs/4_UI_DESIGN_DOCUMENT.md`.

---

## Phase Structure & Document Mapping Overview

```
Phase 0: Baseline Stabilization & Governance (COMPLETED)
   │ └── Aligned with: docs/10_ARCHITECTURE_HARDENING_REPORT.md & docs/rules/*
   ▼
Phase 1: Ingestion Connectors & Data Pipeline (COMPLETED)
   │ └── Aligned with: Master Plan §4.1, SDD §2.1, & SRS §3.1
   ▼
Phase 2: LangGraph 10-Node Intelligence Engine (COMPLETED)
   │ └── Aligned with: Master Plan §4, SDD §2.3, & SRS §3.2
   ▼
Phase 3: Vector Search & LLM Provider Execution (COMPLETED)
   │ └── Aligned with: Master Plan §13-§14, SDD §2.4, & Hardening Report §5
   ▼
Phase 4: Frontend API Integration & Real-Time Workspace (COMPLETED)
   │ └── Aligned with: UI Design Doc §4, Master Plan §3, & Hardening Report §6
   ▼
Phase 5: Calibration & End-to-End Verification (COMPLETED)
   │ └── Aligned with: Master Plan §3 & §12, SRS §3.5, & Definition of Done
   ▼
Phase 6: Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers (COMPLETED)
     └── Aligned with: docs/4_UI_DESIGN_DOCUMENT.md, docs/10_ARCHITECTURE_HARDENING_REPORT.md, setup/start automation
```

---

## Phase Details & Document Alignment

### Phase 0: Baseline Stabilization & Governance (Status: COMPLETED)
- **Goal**: Reconcile Next.js 16 + FastAPI stack, enforce strict typecheck/lint/build quality gates, build 18-point pytest suite, author Dockerfiles, establish Alembic async scaffold, unify OpenAPI contract at `frontend/types/api.ts`, and set CI governance.

### Phase 1: Ingestion Connectors & Data Pipeline (Status: COMPLETED)
- **Goal**: Implement concrete `SourceConnector` adapters for PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, and EMA RSS. Build bronze-layer verbatim payload storage (`raw_signals_bronze`) and deterministic deduplication (`generate_fingerprint`).

### Phase 2: LangGraph 10-Node Intelligence Engine (Status: COMPLETED)
- **Goal**: Build stateful 10-node LangGraph pipeline (`node_ingest` through `node_calibrate -> END`) managing `IntelligenceState`.

### Phase 3: Vector Search & LLM Provider Execution (Status: COMPLETED)
- **Goal**: Integrate 384-dim sentence-transformers embedding generation, pgvector HNSW similarity queries (`signals_embedding_hnsw`), and ProviderFactory execution (Local Gemma 3 4B -> Grok privacy-gated fallback -> BART degraded mode).

### Phase 4: Frontend API Integration & Real-Time Workspace (Status: COMPLETED)
- **Goal**: Connect Next.js App Router UI (`frontend/lib/api.ts`) to backend `/api/v1` REST endpoints (`/signals`, `/overview`, `/athena`, `/search`, `/health/ready`). Render real signals, Ask Athena answers, ⌘K hybrid vector search, and portfolio momentum with 30s visibility-aware polling.

### Phase 5: Calibration & End-to-End Verification (Status: COMPLETED)
- **Goal**: Implement `StakeholderCalibrationService` for rating feedback, execute the haemophilia demo story (mim8 / emicizumab / Hemgenix durability data), and perform final Definition of Done audit.

### Phase 6: Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers (Status: COMPLETED)
- **Goal**: Perform comprehensive doc-to-UI feature parity audit and implementation across all buttons, controls, and workflows specified in `docs/` (UI Design Doc, SRS, SDD, Architecture Hardening Report). Create automated `setup.py` (automated dependency verification, environment orchestration, migrations, seed data, Ollama model setup) and `start.py` (single-command unified launcher with live health-check telemetry).
- **Accomplishments & Verification**:
  - `06-01-PLAN.md` (Wave 1): Read-only intelligence endpoints (`/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/sources`), server-side signal query filters, `POST /api/v1/cache/clear` Redis endpoint, OpenAPI contract synchronization.
  - `06-02-PLAN.md` (Wave 2): `docs/manifests/feature_parity_manifest.json` and `scripts/generate_parity_matrix.py` -> `docs/FEATURE_PARITY_MATRIX.md` (100% compliance); `tests/test_parity_matrix.py`; `FilterBar` & `CacheClearModal` components; 8 dedicated Next.js intelligence pages in `frontend/components/metaradar.tsx` replacing all generic placeholders; Next.js 16 build passing cleanly.
  - `06-03-PLAN.md` (Wave 3): `backend/app/db/seed.py`, zero-config `setup.py` launcher, production-grade `start.py` process orchestrator (NO Celery - A1 compliant), `tests/test_launchers.py`.
  - Full suite verification: `pytest tests/ -v` (80 passed, 1 skipped live, 0 failures), `npm run build` (compiled cleanly).
