# MetaRadar v5.1 — Project Requirements & Scope Matrix

> **Status:** Milestone v5.1 Completed & Fully Verified across all 7 phases (Phases 0–6).

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

## Phase 1: Ingestion Connectors & Data Pipeline (COMPLETED)

- [x] **REQ-P1-1**: Implement concrete NCBI PubMed (E-utilities) `SourceConnector` adapter with `httpx` async client and rate limiting.
- [x] **REQ-P1-2**: Implement concrete ClinicalTrials.gov API v2 `SourceConnector` adapter with incremental query filtering.
- [x] **REQ-P1-3**: Implement concrete NewsAPI `SourceConnector` adapter with developer quota handling.
- [x] **REQ-P1-4**: Implement concrete OpenFDA & EMA RSS feed connector adapters.
- [x] **REQ-P1-5**: Implement deterministic deduplication & source-independence classifier before vector embedding.
- [x] **REQ-P1-6**: Persist verbatim raw payloads to `raw_signals_bronze` table with content hash verification.

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

## Phase 3: Real Vector Search & LLM Provider Execution (COMPLETED)

- [x] **REQ-P3-1**: Generate real 384-dimensional embeddings (`sentence-transformers/all-MiniLM-L6-v2`) for signals.
- [x] **REQ-P3-2**: Execute pgvector HNSW cosine similarity search (`signals.embedding`) for candidate matching.
- [x] **REQ-P3-3**: Wire local Gemma 3 4B inference on GPU/CPU for real text reasoning.
- [x] **REQ-P3-4**: Validate xAI Grok API integration with strict `validate_privacy_gate` enforcement.

---

## Phase 4: Frontend API Integration & Real-Time Workspace (COMPLETED)

- [x] **REQ-P4-1**: Wire Next.js frontend (`frontend/lib/api.ts`) to backend REST API (`/api/v1/signals`, `/overview`, `/athena`).
- [x] **REQ-P4-2**: Render live signal feed with severity filtering, priority badges, and evidence drawers.
- [x] **REQ-P4-3**: Connect Ask Athena prompt interface to backend `/api/v1/athena` endpoint.
- [x] **REQ-P4-4**: Render real-time portfolio momentum charts and confluence radar visualizations.

---

## Phase 5: Calibration & End-to-End Verification (COMPLETED)

- [x] **REQ-P5-1**: Implement `StakeholderCalibrationService` for rating feedback & weight adjustment.
- [x] **REQ-P5-2**: Execute end-to-end demo story (mim8 / emicizumab / Hemgenix durability data).
- [x] **REQ-P5-3**: Verify DoD matrix (all tests passing, 0 type errors, 0 lint warnings, clean build).

---

## Phase 6: Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers (COMPLETED)

- [x] **REQ-P6-1**: Implement read-only intelligence endpoints (`/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/sources`) and server-side signal query filters (`/signals`).
- [x] **REQ-P6-2**: Implement living `FEATURE_PARITY_MATRIX.md` generated from JSON manifest with 100% in-scope compliance.
- [x] **REQ-P6-3**: Replace all generic placeholders with 8 dedicated Next.js intelligence & registry pages in `frontend/components/metaradar.tsx`.
- [x] **REQ-P6-4**: Implement `FilterBar` (expandable multi-filter drawer) and `CacheClearModal` (Redis cache flush with toast feedback).
- [x] **REQ-P6-5**: Implement automated zero-config `setup.py` and production-grade process launcher `start.py` (NO Celery - A1 compliant).

---

## Phase 8: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening (PLANNED)

- [ ] **REQ-P8-01**: End-to-end source provenance for every displayed signal (provider → raw response → normalized record → DB → Signal → serializer → frontend mapper → SignalCard → EvidenceDrawer → source link).
- [ ] **REQ-P8-02**: A single authoritative provenance object that survives backend → API → frontend; no frontend reconstruction from heuristics.
- [ ] **REQ-P8-03**: Source-specific identifiers preserved end-to-end (PMID, NCT ID, FDA record ID, EMA item URL, NewsAPI article URL) independent of generated signal IDs.
- [ ] **REQ-P8-04**: Evidence inspector with SOURCE PROVENANCE, VERBATIM EVIDENCE, and TRACE sections; "Open Original Source" leaves MetaRadar to the exact record.
- [ ] **REQ-P8-05**: Synthetic/test-fixture records unmistakably labeled; no manufactured public URLs for fixtures; `SOURCE URL UNAVAILABLE` shown with reason instead of fabricated URLs.
- [ ] **REQ-P8-06**: Sources & Connectors page reports honest ingestion telemetry (HTTP status, records fetched/accepted, last syncs, latency, error, auth state), distinguishing HTTP-reachable from successfully-ingesting.
- [ ] **REQ-P8-07**: Missing API credentials reported explicitly (`CONFIGURATION_ERROR: <VAR> missing`, required/optional, official location, steps); no fabricated values or fake placeholder secrets.
- [ ] **REQ-P8-08**: Overview/Lifecycles design tokens (typography, spacing, cards, borders, badges, density) extracted and applied as the canonical system to all other workspaces.
- [ ] **REQ-P8-09**: Global font consistency — single primary font stack matching Overview/Lifecycles; monospace only for IDs/fingerprints/technical values.
- [ ] **REQ-P8-10**: Standardized typography hierarchy (page eyebrow/title/description, section eyebrow/title, card title, body, muted metadata, numeric metric, badge, technical identifier).
- [ ] **REQ-P8-11**: Light/dark theme is a single system stored once at the root provider; persists across navigation, refresh, drawers, tab/workspace changes, and direct URLs; no hardcoded colors in components.
- [ ] **REQ-P8-12**: Light mode is a real semantic token theme (background, surface, elevated, border, primary/secondary/muted text, accent, success/warning/danger/info, input, hover, selected, overlay, drawer, code/log) — not a dark-invert.
- [ ] **REQ-P8-13**: Drawers/modals (EvidenceDrawer, Confluence inspector) use the same typography, surface hierarchy, borders, spacing, buttons, badges, form controls, and theme tokens as Overview/Lifecycles.
- [ ] **REQ-P8-14**: Priority score (0.25×Novelty + 0.30×Clinical + 0.25×Regulatory + 0.20×Recency) is one authoritative calculation flowing end-to-end; no silent zero fallback; reasons exposed.
- [ ] **REQ-P8-15**: Confluence source-count semantics truthful — backend rule (≥3 distinct source categories) and UI wording agree; no 1-source "convergence".
- [ ] **REQ-P8-16**: Confluence contributing evidence signals show title, provider, external ID, publication date, canonical URL, evidence excerpt; backward walk Confluence → signal → source record → original source.
- [ ] **REQ-P8-17**: Ingestion observability — per-attempt logs of connector, request, status, latency, records fetched/accepted/rejected, rejection reasons, signals created/updated, errors; no secret logging.
- [ ] **REQ-P8-18**: Validation — `pytest tests/`, `npm run lint`, `npm run build` pass; manual light/dark navigation flow across all workspaces, drawers, sources telemetry, settings credentials, direct URL navigation.
- [ ] **REQ-P8-19**: No "build passes" acceptance — full provenance, URL, synthetic-labeling, identifier, evidence, scoring, confluence-semantics, health, credential, theme, typography, drawer, and test gates verified (audit A–I).
