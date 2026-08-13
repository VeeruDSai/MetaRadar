# MetaRadar v5.1 — Project Requirements & Scope Matrix

> **Status:** Baseline Stabilization & Governance (Phase 0) Completed & Verified. Phases 1–5 ready for execution planning.

---

## Phase 0: Baseline Hardening & Quality Governance (COMPLETED)

- [x] **REQ-P0-1**: Reconcile frontend stack to Next.js 16.3.0, React 19, Tailwind 4, Framer Motion 13, Recharts 3, Base UI / shadcn.
- [x] **REQ-P0-2**: Establish native ESLint 10 flat config (`eslint.config.mjs`) and strict TypeScript build checking (`ignoreBuildErrors: false`).
- [x] **REQ-P0-3**: Scaffold async Alembic migration environment (`alembic.ini`, `env.py`, `script.py.mako`).
- [x] **REQ-P0-4**: Author multi-stage container Dockerfiles (`backend/Dockerfile`, `frontend/Dockerfile`) and validate `docker compose config`.
- [x] **REQ-P0-5**: Implement PII/PHI scrubber (`PIIPHIScrubber`) and 19-rule Red-Team registry (`RedTeamNLIService` Rules A–S).
- [x] **REQ-P0-6**: Implement honest health & readiness endpoints (`/health`, `/health/ready`, `/health/models`, `/health/connectors`).
- [x] **REQ-P0-7**: Unify OpenAPI contract pipeline to `contracts/openapi.json` and canonical generated `frontend/types/api.ts`.
- [x] **REQ-P0-8**: Build 18-point `pytest` backend test suite (`tests/`) covering config, endpoints, provider matrix Cases A–F, PII scrubbing, privacy gate, and contract drift.
- [x] **REQ-P0-9**: Establish GitHub Actions CI workflow (`.github/workflows/ci.yml`) with least-privilege token access (`permissions: contents: read`).
- [x] **REQ-P0-10**: Establish repo-wide operating rules in `docs/rules/`, `AGENTS.md`, and `GEMINI.md`.

---

## Phase 1: Ingestion Connectors & Data Pipeline

- [ ] **REQ-P1-1**: Implement concrete NCBI PubMed (E-utilities) `SourceConnector` adapter with `httpx` async client and rate limiting.
- [ ] **REQ-P1-2**: Implement concrete ClinicalTrials.gov API v2 `SourceConnector` adapter with incremental query filtering.
- [ ] **REQ-P1-3**: Implement concrete NewsAPI `SourceConnector` adapter with developer quota handling.
- [ ] **REQ-P1-4**: Implement concrete OpenFDA & EMA RSS feed connector adapters.
- [ ] **REQ-P1-5**: Implement deterministic deduplication & source-independence classifier before vector embedding.
- [ ] **REQ-P1-6**: Persist verbatim raw payloads to `raw_signals_bronze` table with content hash verification.

---

## Phase 2: LangGraph 10-Node Intelligence Engine (COMPLETED)

- [x] **REQ-P2-1**: Implement `IntelligenceState` TypedDict state contract with reducers.
- [x] **REQ-P2-2**: Build `node_ingest` and `node_validate` nodes for raw payload processing & PII scrubbing.
- [x] **REQ-P2-3**: Build `node_nlp_extract` and `node_ontology_enrich` nodes mapping entities against `config/haemophilia.yaml`.
- [x] **REQ-P2-4**: Build `node_confluence` node for 48h / ≥3 signal type alignment detection.
- [x] **REQ-P2-5**: Build `node_lifecycle` node executing the 9-stage asset state machine.
- [x] **REQ-P2-6**: Build `node_redteam` node running 19-rule pairwise contradiction checks.
- [x] **REQ-P2-7**: Build `node_missing_signal` node for stakeholder WATCH rule monitoring.
- [x] **REQ-P2-8**: Build `node_synthesize` node invoking the `ProviderFactory` (Gemma / Grok / BART) to generate Four-Question briefs.
- [x] **REQ-P2-9**: Build `node_calibrate` node terminating at `END` with auditable routing updates.

---

## Phase 3: Real Vector Search & LLM Provider Execution

- [ ] **REQ-P3-1**: Generate real 384-dimensional embeddings (`sentence-transformers/all-MiniLM-L6-v2`) for signals.
- [ ] **REQ-P3-2**: Execute pgvector HNSW cosine similarity search (`signals.embedding`) for candidate matching.
- [ ] **REQ-P3-3**: Wire local Gemma 3 4B inference on GPU/CPU for real text reasoning.
- [ ] **REQ-P3-4**: Validate xAI Grok API integration with strict `validate_privacy_gate` enforcement.

---

## Phase 4: Frontend API Integration & Real-Time Workspace

- [ ] **REQ-P4-1**: Wire Next.js frontend (`frontend/lib/api.ts`) to backend REST API (`/api/v1/signals`, `/overview`, `/athena`).
- [ ] **REQ-P4-2**: Render live signal feed with severity filtering, priority badges, and evidence drawers.
- [ ] **REQ-P4-3**: Connect Ask Athena prompt interface to backend `/api/v1/athena` endpoint.
- [ ] **REQ-P4-4**: Render real-time portfolio momentum charts and confluence radar visualizations.

---

## Phase 5: Calibration & End-to-End Verification

- [ ] **REQ-P5-1**: Implement `StakeholderCalibrationService` for rating feedback & weight adjustment.
- [ ] **REQ-P5-2**: Execute end-to-end demo story (mim8 / emicizumab / Hemgenix durability data).
- [ ] **REQ-P5-3**: Verify DoD matrix (all tests passing, 0 type errors, 0 lint warnings, clean build).
