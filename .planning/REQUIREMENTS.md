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

## Phase 8: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening (COMPLETED)

- [x] **REQ-P8-01**: End-to-end source provenance for every displayed signal (provider → raw response → normalized record → DB → Signal → serializer → frontend mapper → SignalCard → EvidenceDrawer → source link).
- [x] **REQ-P8-02**: A single authoritative provenance object that survives backend → API → frontend; no frontend reconstruction from heuristics.
- [x] **REQ-P8-03**: Source-specific identifiers preserved end-to-end (PMID, NCT ID, FDA record ID, EMA item URL, NewsAPI article URL) independent of generated signal IDs.
- [x] **REQ-P8-04**: Evidence inspector with SOURCE PROVENANCE, VERBATIM EVIDENCE, and TRACE sections; "Open Original Source" leaves MetaRadar to the exact record.
- [x] **REQ-P8-05**: Synthetic/test-fixture records unmistakably labeled; no manufactured public URLs for fixtures; `SOURCE URL UNAVAILABLE` shown with reason instead of fabricated URLs.
- [x] **REQ-P8-06**: Sources & Connectors page reports honest ingestion telemetry (HTTP status, records fetched/accepted, last syncs, latency, error, auth state), distinguishing HTTP-reachable from successfully-ingesting.
- [x] **REQ-P8-07**: Missing API credentials reported explicitly (`CONFIGURATION_ERROR: <VAR> missing`, required/optional, official location, steps); no fabricated values or fake placeholder secrets.
- [x] **REQ-P8-08**: Overview/Lifecycles design tokens (typography, spacing, cards, borders, badges, density) extracted and applied as the canonical system to all other workspaces.
- [x] **REQ-P8-09**: Global font consistency — single primary font stack matching Overview/Lifecycles; monospace only for IDs/fingerprints/technical values.
- [x] **REQ-P8-10**: Standardized typography hierarchy (page eyebrow/title/description, section eyebrow/title, card title, body, muted metadata, numeric metric, badge, technical identifier).
- [x] **REQ-P8-11**: Light/dark theme is a single system stored once at the root provider; persists across navigation, refresh, drawers, tab/workspace changes, and direct URLs; no hardcoded colors in components.
- [x] **REQ-P8-12**: Light mode is a real semantic token theme (background, surface, elevated, border, primary/secondary/muted text, accent, success/warning/danger/info, input, hover, selected, overlay, drawer, code/log) — not a dark-invert.
- [x] **REQ-P8-13**: Drawers/modals (EvidenceDrawer, Confluence inspector) use the same typography, surface hierarchy, borders, spacing, buttons, badges, form controls, and theme tokens as Overview/Lifecycles.
- [x] **REQ-P8-14**: Priority score (0.25×Novelty + 0.30×Clinical + 0.25×Regulatory + 0.20×Recency) is one authoritative calculation flowing end-to-end; no silent zero fallback; reasons exposed.
- [x] **REQ-P8-15**: Confluence source-count semantics truthful — backend rule (≥3 distinct source categories) and UI wording agree; no 1-source "convergence".
- [x] **REQ-P8-16**: Confluence contributing evidence signals show title, provider, external ID, publication date, canonical URL, evidence excerpt; backward walk Confluence → signal → source record → original source.
- [x] **REQ-P8-17**: Ingestion observability — per-attempt logs of connector, request, status, latency, records fetched/accepted/rejected, rejection reasons, signals created/updated, errors; no secret logging.
- [x] **REQ-P8-18**: Validation — `pytest tests/`, `npm run lint`, `npm run build` pass; manual light/dark navigation flow across all workspaces, drawers, sources telemetry, settings credentials, direct URL navigation.
- [x] **REQ-P8-19**: No "build passes" acceptance — full provenance, URL, synthetic-labeling, identifier, evidence, scoring, confluence-semantics, health, credential, theme, typography, drawer, and test gates verified (audit A–I).

---

## Phase 9: Real Signal Workflow, NewsAPI Provenance & Pharma RSS Discovery (COMPLETED)

- [x] **REQ-P9-01**: NewsAPI Direct Article URL Passthrough & Provenance Fix.
- [x] **REQ-P9-02**: Signal Review State Machine & DB-Persisted Audit Logging (`POST /signals/{id}/review`).
- [x] **REQ-P9-03**: Fierce Pharma RSS Discovery Connector (`FiercePharmaRSSConnector`).
- [x] **REQ-P9-04**: Economic Times (ET) Pharma RSS Discovery Connector (`ETPharmaRSSConnector`).
- [x] **REQ-P9-05**: BioPharma Dive configured state & escalation trigger logic.

---

## Phase 10: Undeniable Demo Journey, Evidence Convergence & UX Refinement (COMPLETED)

- [x] **REQ-P10-01**: Active BioPharma Dive RSS ingestion connector.
- [x] **REQ-P10-02**: Adaptive NewsAPI quota governor & health telemetry.
- [x] **REQ-P10-03**: Evidence Convergence Tree widget surfacing multi-stream corroboration.
- [x] **REQ-P10-04**: "Why This Signal?" explainer component and Red-Team counter-factuals.
- [x] **REQ-P10-05**: Daily Executive Briefing dashboard & 5-scenario E2E test harness (`scripts/test_demo_scenarios_e2e.py`).

---

## Phase 11: MetaRadar Productionization (COMPLETED)

- [x] **REQ-P11-01**: Identity & Session Management (`users` and `sessions` tables, dual absolute/idle timeouts).
- [x] **REQ-P11-02**: Server-Side RBAC Enforcement on all protected endpoints (`/signals`, `/signals/queue/*`).
- [x] **REQ-P11-03**: Terminal Status (`ACTIONED`) immutability enforcement returning 409 CONFLICT on modification.
- [x] **REQ-P11-04**: Database-Level Append-Only `AuditLog` immutability via SQLAlchemy event listeners.
- [x] **REQ-P11-05**: Pre-Auth Exact-Origin validation & session-bound HMAC CSRF tokens.
- [x] **REQ-P11-06**: E2E 6-Function vertical slice test harness (`scripts/test_e2e_vertical_slice.py`).

---

## Phase 12: Hackathon MVP — Full NN GBS Kick-Off Specification & Alignment (ACTIVE / PLANNED)

> **Source Authority:** `docs/NN GBS Hackathon 2026 — Kick-off.pptx` (Novo Nordisk GBS Problem Statement #3: Haemophilia Intelligence Radar)

### 1. The 4 Practical Questions Framework
- [ ] **REQ-P12-01 [Q1: What changed?]**: Ingest, detect, and classify updates across Haemophilia A (Factor VIII) and Haemophilia B (Factor IX) with concise, factual summaries.
- [ ] **REQ-P12-02 [Q2: Why does it matter?]**: AI assessment of potential impact on patients, competitors (Roche/Chugai, Pfizer, Sanofi, Sobi), the market, and Novo Nordisk.
- [ ] **REQ-P12-03 [Q3: Who should review it?]**: Deterministic routing recommendation to the 6 enterprise functions (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`, `LEADERSHIP`).
- [ ] **REQ-P12-04 [Q4: What action is needed?]**: Strategic recommendation categorization (`Review`, `Monitor`, `Escalate`, `Briefing Update`, `FAQ Preparation`) labeled with `[FACT]`, `[INTERPRETATION]`, and `[SPECULATION]`.

### 2. Pilot Therapy Area & In-Scope Coverage
- [ ] **REQ-P12-05 [Modalities Scope]**: Tracking of Factor therapies, Non-factor therapies, Bispecifics (e.g. emicizumab, NXT007, Mim8), Gene therapies (Hemgenix, Roctavian), and RNAi (fitusiran).
- [ ] **REQ-P12-06 [Congress & Public Sources]**: Ingestion coverage of major medical congresses (ISTH, EAHAD, ASH abstracts), clinical trial registries (ClinicalTrials.gov), health agencies (FDA, EMA), scientific journals (PubMed), and pharma discovery feeds.
- [ ] **REQ-P12-07 [Competitor Tracking]**: Tracking of key competitor movements across Roche/Chugai, Pfizer, Sanofi, Sobi, and Novo Nordisk.
- [ ] **REQ-P12-08 [Strict Out-of-Scope Enforcement]**: Zero use of confidential NN strategy, zero patient-identifiable data (PII/PHI), and zero promotional or external-facing content.

### 3. Stakeholder Learning Model (AI + Human-in-the-Loop Calibration)
- [ ] **REQ-P12-09 [5-Step Learning Loop]**: External signals → AI baseline → NN stakeholder input → Calibrated logic → Better intelligence.
- [ ] **REQ-P12-10 [Baseline vs Calibrated Demonstration]**: Explicit comparison examples in UI and documentation (Trial update routing refinement, Market Access / HEOR payer assessment, Safety / PV review flagging without causality assertion).
- [ ] **REQ-P12-11 [Cross-Functional Approval Workflow]**: Non-leadership roles (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`) can request Leadership approval on critical signals (`POST /signals/{id}/request-approval`).
- [ ] **REQ-P12-12 [Leadership Approval Resolution]**: Executive Leadership reviews pending requests in `PendingApprovalsPanel` on Functions workspace and records binding decisions (`POST /signals/{id}/resolve-approval`) with full `AuditLog` persistence.

### 4. Enterprise Identity & User Experience
- [ ] **REQ-P12-13 [Role-Based Login System]**: Dedicated `/login` page replacing demo dropdown with fixed, documented credentials per role (`MedAffairs2026!`, `Leader2026!`, etc.).
- [ ] **REQ-P12-14 [Interactive 3D ProfileCard]**: Interactive pointer-tracking 3D tilt `ProfileCard` showcasing persona context (Dr. Elena Vance, Marcus Chen, Dr. Sarah Jenkins, etc.) with 1-click credential auto-fill.
- [ ] **REQ-P12-15 [Role-Scoped Signal Queue]**: Automatic scoping ensuring Medical Affairs, Regulatory, Safety, Access, and Comms see their role-specific queue while Leadership accesses cross-functional views.

### 5. Compliance, Guardrails & Success Metrics
- [ ] **REQ-P12-16 [Success Metric 1: 100% Source-Linked]**: Every summary contains direct links and persistent identifiers (`PMID`, `NCT ID`, `FDA ID`, `EMA URL`) with `TRACE` metadata.
- [ ] **REQ-P12-17 [Success Metric 2: ≥ 85% Classification Accuracy]**: Verified against LangGraph 10-node classification test suite.
- [ ] **REQ-P12-18 [Success Metric 3: ≤ 5 Min Signal Identification]**: Prioritized dashboard cards enabling identification of top weekly signals in under 5 minutes.
- [ ] **REQ-P12-19 [Success Metric 4: 0 Confidential/Patient Data]**: Enforced by pre-ingestion PII/PHI scrubber and public-only data sources.
- [ ] **REQ-P12-20 [Success Metric 5: Required Stakeholder Improvement]**: Measurable relevance weight adjustments via Calibration workspace.

### 6. Required Deliverables & Evaluation Rubric (100 Points)
- [ ] **REQ-P12-21 [Deliverables 1–8 Package]**:
  1. Concept note & prototype timeline (in `README.md` and `12-CONTEXT.md`)
  2. Working prototype (FastAPI + Next.js 16)
  3. Sample data schema & source list (OpenAPI contract + Sources telemetry)
  4. Dashboard demo with 4-question signal cards
  5. AI baseline vs stakeholder-calibrated example
  6. Validation metrics & architecture diagram (`docs/SYSTEM_ARCHITECTURE.md`)
  7. Risk & guardrail summary
  8. Final 5–7 slide presentation deck outline (in private `pitch/PITCH.md`)
- [ ] **REQ-P12-22 [Rubric Criterion 1: AI Signal Detection & Classification (20 pts)]**: 10-node LangGraph pipeline, 4-factor priority score, 7 signal categories.
- [ ] **REQ-P12-23 [Rubric Criterion 2: Problem Understanding & Haemophilia Relevance (15 pts)]**: Factor VIII/IX gene therapies, bispecifics (NXT007, Mim8, emicizumab), inhibitor alerts, PDUFA dates.
- [ ] **REQ-P12-24 [Rubric Criterion 3: Source Traceability & Summary Quality (15 pts)]**: 100% source links, TRACE tab, FACT/INTERPRETATION/SPECULATION labels.
- [ ] **REQ-P12-25 [Rubric Criterion 4: Stakeholder Calibration & Learning Loop (15 pts)]**: Per-function feedback loop, weight updates, calibration telemetry.
- [ ] **REQ-P12-26 [Rubric Criterion 5: Cross-Functional Usefulness (10 pts)]**: Approval request workflow (Functional role → Leadership approval → Decision badge).
- [ ] **REQ-P12-27 [Rubric Criterion 6: Dashboard UX & Adoption Potential (10 pts)]**: Dedicated login, role queues, 3D tilt ProfileCards, 9 specialized workspaces.
- [ ] **REQ-P12-28 [Rubric Criterion 7: Compliance, Safety & Governance (10 pts)]**: Append-only AuditLog, server-side RBAC, CSRF protection, session timeouts, PII scrubber.
- [ ] **REQ-P12-29 [Rubric Criterion 8: Scalability Beyond Haemophilia (5 pts)]**: 3-step YAML configuration pivot for Oncology, Diabetes, or Rare Diseases without code rewrites.

---

## Phase 13: Signal UX Simplification (FUTURE — BACKLOG)

- [ ] **REQ-P13-01**: Collapsible technical metadata accordion ("Technical Details" expand).
- [ ] **REQ-P13-02**: Plain-language priority badges ("Act Now / Review Today / Monitor / FYI").
- [ ] **REQ-P13-03**: Guided 3-step first-login onboarding tour.
- [ ] **REQ-P13-04**: Mobile-responsive signal card optimizations.
- [ ] **REQ-P13-05**: "Why am I seeing this?" one-tap routing explainer.
