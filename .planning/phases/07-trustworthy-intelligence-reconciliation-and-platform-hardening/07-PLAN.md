---
phase: 07
plan: "01"
title: Trustworthy Intelligence Reconciliation, Observability Upgrade, Modular Frontend Refactor & Platform Hardening
wave: 1
depends_on: []
files_modified:
  - docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md
  - backend/app/models/signal.py
  - backend/app/models/intelligence.py
  - backend/app/models/calibration.py
  - backend/app/models/source.py
  - backend/app/models/__init__.py
  - backend/app/schemas/signals.py
  - backend/app/schemas/intelligence.py
  - backend/app/schemas/calibration.py
  - backend/app/schemas/registry.py
  - backend/app/schemas/observability.py
  - backend/app/schemas/__init__.py
  - backend/app/core/logging.py
  - backend/app/core/middleware.py
  - backend/app/services/scoring.py
  - backend/app/services/confluence.py
  - backend/app/services/red_team.py
  - backend/app/services/athena.py
  - backend/app/services/calibration.py
  - backend/app/connectors/base.py
  - backend/app/connectors/pubmed.py
  - backend/app/connectors/clinical_trials.py
  - backend/app/connectors/newsapi.py
  - backend/app/connectors/openfda.py
  - backend/app/connectors/ema_rss.py
  - backend/app/workflows/state.py
  - backend/app/workflows/nodes/nlp_extract.py
  - backend/app/workflows/nodes/confluence.py
  - backend/app/workflows/nodes/red_team.py
  - backend/app/workflows/nodes/athena_synthesis.py
  - backend/app/api/v1/endpoints/signals.py
  - backend/app/api/v1/endpoints/intelligence.py
  - backend/app/api/v1/endpoints/calibration.py
  - backend/app/api/v1/endpoints/registry.py
  - backend/app/api/v1/endpoints/observability.py
  - backend/app/main.py
  - scripts/export_openapi.py
  - contracts/openapi.json
  - frontend/types/api.ts
  - frontend/lib/api.ts
  - frontend/lib/errors.ts
  - frontend/lib/mappers.ts
  - frontend/components/layout/Shell.tsx
  - frontend/components/layout/Navigation.tsx
  - frontend/components/common/ErrorState.tsx
  - frontend/components/common/EmptyState.tsx
  - frontend/components/common/EvidenceDrawer.tsx
  - frontend/components/signals/SignalCard.tsx
  - frontend/components/signals/SignalList.tsx
  - frontend/components/confluence/ConfluenceWorkspace.tsx
  - frontend/components/contradictions/ContradictionWorkspace.tsx
  - frontend/components/missing-signals/MissingSignalsWorkspace.tsx
  - frontend/components/developments/DevelopmentsWorkspace.tsx
  - frontend/components/intelligence/AthenaWorkspace.tsx
  - frontend/components/functions/FunctionsWorkspace.tsx
  - frontend/components/calibration/CalibrationWorkspace.tsx
  - frontend/components/sources/SourcesOperationsWorkspace.tsx
  - frontend/components/observability/ActivityStreamWorkspace.tsx
  - frontend/components/settings/SettingsWorkspace.tsx
  - frontend/app/page.tsx
  - frontend/app/signals/page.tsx
  - frontend/app/confluence/page.tsx
  - frontend/app/contradictions/page.tsx
  - frontend/app/missing-signals/page.tsx
  - frontend/app/developments/page.tsx
  - frontend/app/intelligence/page.tsx
  - frontend/app/functions/page.tsx
  - frontend/app/calibration/page.tsx
  - frontend/app/sources/page.tsx
  - frontend/app/activity/page.tsx
  - frontend/app/settings/page.tsx
  - tests/test_truthfulness_and_invariants.py
  - tests/test_failure_injection.py
  - tests/test_contract_drift.py
  - tests/test_api_endpoints.py
  - .planning/codebase/ARCHITECTURE.md
  - .planning/codebase/CONCERNS.md
  - .planning/codebase/CONVENTIONS.md
  - .planning/codebase/INTEGRATIONS.md
  - .planning/codebase/STACK.md
  - .planning/codebase/STRUCTURE.md
  - .planning/codebase/TESTING.md
autonomous: true
requirements_addressed:
  - REQ-P7-AUDIT-AND-DISCREPANCIES
  - REQ-P7-SYNTHETIC-GOVERNANCE
  - REQ-P7-PROVENANCE-DATA-MODEL
  - REQ-P7-PRIORITY-SCORING-ENGINE
  - REQ-P7-CONFLUENCE-ENGINE
  - REQ-P7-CONFIDENCE-SEMANTICS
  - REQ-P7-ATHENA-EVIDENCE-TRUTH
  - REQ-P7-RED-TEAM-INTEGRITY
  - REQ-P7-MISSING-SIGNALS-FSM
  - REQ-P7-OPERATIONAL-SOURCES
  - REQ-P7-STRUCTURED-OBSERVABILITY
  - REQ-P7-CORRELATION-TRACING
  - REQ-P7-SYSTEM-ACTIVITY-UI
  - REQ-P7-ERROR-UX-RESILIENCE
  - REQ-P7-FRONTEND-MODULARIZATION
  - REQ-P7-CALIBRATION-IDEMPOTENCY
  - REQ-P7-PURE-GET-ENDPOINTS
  - REQ-P7-WORKSPACES-HARDENING
  - REQ-P7-FAILURE-INJECTION-TESTS
  - REQ-P7-CODEBASE-MAP-SYNC
---

# Plan 07-01: Trustworthy Intelligence Reconciliation & Platform Hardening (Single-Wave Unified Execution)

<objective>
Execute a comprehensive codebase audit, data-truthfulness reconciliation, intelligence pipeline correction, observability upgrade, frontend modular refactor, invariant test hardening, and codebase-map update across MetaRadar v5.1 in a single, uninterrupted execution wave.

Transform MetaRadar into a fully truthful, verified, and transparent competitive intelligence platform where every metric, score, source health status, confidence rating, and evidence citation is computed, traceable to bronze ingestion records, and resilient to failure.
</objective>

<reference_specification>
Primary Reference: [docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md)
</reference_specification>

<threat_model>
ASVS Level 1 & Enterprise Intelligence Threat Assessment:
- **T-07-01 (Fabricated Telemetry & Deceptive AI Output):** Hardcoded confidence scores or synthetic excerpts misleading clinical or regulatory leadership. Mitigation: Enforce mandatory provenance IDs, real mathematical scoring formulas with breakdowns, typed confidence enums, and zero static evidence fallbacks.
- **T-07-02 (Silent Synthetic Data Infiltration):** Synthetic test fixtures poisoning production vector indexes or live decision streams. Mitigation: Explicit `DataMode` tags (`live`, `recorded_demo`, `test_fixture`) and visible UI badges.
- **T-07-03 (State Mutation on Read Requests):** Vulnerability where `GET /calibrate` mutates weight records. Mitigation: Strict REST idempotency where `GET` is purely read-only and mutations require transactional `POST /api/v1/calibration/run`.
- **T-07-04 (Error Concealment & Unobservable Failures):** Network or parser failures masked behind empty UI cards. Mitigation: Structured JSON logs, correlation IDs (`X-Request-ID`), and standard `ErrorState` components with retry buttons.
- **T-07-05 (Contract Drift & Dynamic Type Bypass):** Loose `any` types in frontend mappers causing deserialization crashes. Mitigation: Fully typed DTO mappers and automated OpenAPI sync validation.
</threat_model>

<must_haves>
- Complete 12 Non-Negotiable Product Principles.
- All 36 Phases of the intelligence audit and hardening spec executed without pausing between sub-stages.
- Zero hardcoded scores, zero fake "LIVE" badges, zero placeholder claims.
- Real priority scoring with breakdown (`Novelty`, `Clinical`, `Regulatory`, `Recency`).
- Real confluence clustering across $\ge 3$ sources in 48h windows with calculation versions.
- Real pgvector cosine retrieval for Athena and real claim citations for Red-Team.
- Real connector health status tracking (`HEALTHY`, `DEGRADED`, `STALE`, `RATE_LIMITED`, `AUTH_FAILED`, `ERROR`, `DISABLED`, `NEVER_CONNECTED`).
- Structured JSON logging, correlation IDs, and Activity Stream workspace.
- Modularized frontend under `frontend/components/` by bounded context, eliminating monolithic files.
- Reusable `EvidenceDrawer`, `ErrorState`, and `EmptyState` components.
- Automated tests for all invariants and failure-injection scenarios passing 100%.
- Synchronized codebase map documentation in `.planning/codebase/*.md`.
</must_haves>

<tasks>

<task id="07-01-T1">
<title>Audit Codebase for Fabricated Telemetry, Placeholders & Stale Documentation</title>
<action>
1. Search repository for hardcoded scores, confidence floats, mock excerpts, and static "LIVE" strings.
2. Produce an internal Discrepancy Matrix (Documented vs Actual vs Expected vs Required Fix).
3. Identify dead code, unused mock files (`frontend/lib/mock-data.ts`), and duplicate route trees.
</action>
<verify>
All placeholder occurrences documented with their replacement strategy in the audit log.
</verify>
</task>

<task id="07-01-T2">
<title>Update Database Models & Schemas with Provenance, DataMode & Calibration Lifecycle</title>
<action>
1. In `backend/app/models/` and `schemas/`, add `DataMode` (`live`, `recorded_demo`, `test_fixture`), `is_synthetic`, `provenance_status`, `scoring_version`, `score_breakdown`, `calculation_version`, and `pipeline_run_id` to `Signal`, `Confluence`, `Contradiction`, `WatchItem`, and `Evidence`.
2. Implement `CalibrationRun` model to track immutable calibration executions (`run_id`, `applied_at`, `previous_weights`, `new_weights`, `affected_functions`, `reason`).
3. Add `SourceHealthLog` model to persist real connector telemetry (`status`, `latency_ms`, `records_fetched`, `records_accepted`, `records_rejected`, `last_error`, `http_status`, `checked_at`).
4. Ensure all datetime fields use timezone-aware UTC.
</action>
<verify>
`python -c "from app.models import Signal, Confluence, Contradiction, CalibrationRun, SourceHealthLog; print('Models verified')"`
</verify>
</task>

<task id="07-01-T3">
<title>Implement Real Priority Scoring, Confluence & Confidence Typing Services</title>
<action>
1. Implement `backend/app/services/scoring.py` with multi-factor Priority Scoring formula and explicit score breakdown. Return `null` / `not_computed` if required inputs are missing.
2. Implement `backend/app/services/confluence.py` with dynamic multi-source clustering across $\ge 3$ sources in 48-hour windows, entity matching, and calculation versioning.
3. Define canonical `ConfidenceType` enum (`extraction`, `classification`, `heuristic`, `model`, `human`) with explicit calculation rationale.
</action>
<verify>
Unit tests for scoring and confluence calculation passing with deterministic outputs.
</verify>
</task>

<task id="07-01-T4">
<title>Hardwire Athena RAG Evidence Retrieval & Red-Team Verbatim Contradiction Excerpts</title>
<action>
1. In `backend/app/services/athena.py`, query pgvector HNSW index over chunked `Evidence` records; return `[FACT]`, `[INFERENCE]`, `[SUGGESTION]` labeled responses with source links. Return honest "No sufficiently relevant evidence found" on empty retrieval.
2. In `backend/app/services/red_team.py`, populate `claim_a_excerpt` and `claim_b_excerpt` from actual linked `Evidence` records; eliminate all `"Primary evidence claim..."` placeholders.
3. In `backend/app/services/missing_signals.py`, implement explicit watch lifecycle: `WITHIN_WINDOW`, `DUE`, `OVERDUE`, `SATISFIED`, `SUPPRESSED`, `INSUFFICIENT_DATA`.
</action>
<verify>
Athena and Red-Team integration tests pass with real evidence references.
</verify>
</task>

<task id="07-01-T5">
<title>Implement Structured Observability, Correlation IDs & Real Connector Health Tracking</title>
<action>
1. Implement `backend/app/core/logging.py` providing JSON structured logging with `request_id`, `trace_id`, `pipeline_run_id`, `component`, `duration_ms`, and automatic PII/secret scrubbing.
2. Implement `backend/app/core/middleware.py` injecting `X-Request-ID` and `X-Correlation-ID`.
3. In `backend/app/connectors/base.py` and connector adapters (PubMed, ClinicalTrials, NewsAPI, OpenFDA, EMA), track real connection health, latency, HTTP response codes, rate limits, and persist to `SourceHealthLog`.
4. Expose `GET /api/v1/observability/activity` and `GET /api/v1/sources/health` endpoints.
</action>
<verify>
Log output conforms to JSON schema and correlation IDs propagate across endpoints.
</verify>
</task>

<task id="07-01-T6">
<title>Fix Calibration Lifecycle & Ensure Idempotent Read-Only GET Endpoints</title>
<action>
1. In `backend/app/api/v1/endpoints/calibration.py`, make `GET /api/v1/calibration` purely read-only (returning current weights and run history).
2. Implement `POST /api/v1/calibration/run` to execute calibration over pending unapplied feedback, create an immutable `CalibrationRun`, and mark feedback as `applied`.
</action>
<verify>
GET requests do not mutate weight records; calibration runs are idempotent and auditable.
</verify>
</task>

<task id="07-01-T7">
<title>Modularize Frontend Architecture by Bounded Context & Build Error/Evidence Components</title>
<action>
1. Deconstruct monolithic components into modular packages under `frontend/components/`: `signals/`, `confluence/`, `contradictions/`, `missing-signals/`, `developments/`, `intelligence/`, `functions/`, `calibration/`, `sources/`, `observability/`, `settings/`, `common/`.
2. Build reusable `EvidenceDrawer` with full provenance, source URLs, timestamps, and calculation history.
3. Build reusable `ErrorState` component with human-readable message, correlation ID copy button, retry trigger, and expandable technical details.
4. Build `ActivityStream` workspace displaying live system telemetry and expandable error logs.
5. In `frontend/lib/mappers.ts`, eliminate all `any` types and enforce strict DTO mapping from generated types.
</action>
<verify>
Next.js compiles with zero TypeScript errors (`tsc --noEmit`) and clean component imports.
</verify>
</task>

<task id="07-01-T8">
<title>Hardwire All 10 Next.js Workspaces with 8 Canonical UI States & Task-Oriented Navigation</title>
<action>
1. Wire all workspace pages: Overview, Signals, Confluence, Contradictions, Missing Signals, Developments, Athena Intelligence, Functions, Calibration, Sources, Activity, and Settings.
2. Ensure every page handles all 8 canonical states: `loading`, `success`, `empty`, `stale`, `degraded`, `unavailable`, `error`, `not_computed`.
3. Add prominent `RECORDED DEMO DATA` vs `LIVE DATA` badges.
4. Implement task-oriented navigation layout (Overview, Intelligence, Analysis, Workflows, System).
</action>
<verify>
Every workspace renders truthfully without placeholder numbers or broken states.
</verify>
</task>

<task id="07-01-T9">
<title>Synchronize OpenAPI Contract, TypeScript Types & Export Artifacts</title>
<action>
1. Update `scripts/export_openapi.py` with all new schemas (`SourceHealthLog`, `CalibrationRun`, `ActivityLogItem`, `ConfidenceType`, `DataMode`).
2. Regenerate `contracts/openapi.json` and `frontend/types/api.ts`.
3. Verify zero drift with `pytest tests/test_contract_drift.py`.
</action>
<verify>
`python scripts/export_openapi.py && pytest tests/test_contract_drift.py` passes with 0 drift.
</verify>
</task>

<task id="07-01-T10">
<title>Add Invariant Tests, Failure-Injection Suite & Verify 100% Quality Gates</title>
<action>
1. Write `tests/test_truthfulness_and_invariants.py` verifying:
   - Zero synthetic data enters live mode.
   - Priority and Confluence scores are calculated deterministically.
   - Confidence types and rationales are populated.
   - Athena answers use retrieved evidence.
   - Contradiction excerpts are verbatim source citations.
   - Calibration feedback is applied exactly once.
   - GET endpoints never mutate data.
2. Write `tests/test_failure_injection.py` simulating:
   - External connector timeouts and 429 rate limits.
   - Database/Redis disconnection handling.
   - LLM provider fallback and degraded mode.
   - Correlation ID preservation on error.
3. Run full verification suite: `pytest`, `npm --prefix frontend run build`, `npm --prefix frontend run lint`.
</action>
<verify>
100% test pass rate across all unit, invariant, failure-injection, and build verification gates.
</verify>
</task>

<task id="07-01-T11">
<title>Synchronize Codebase Map Documentation & Generate Final Verification Report</title>
<action>
1. Update all files in `.planning/codebase/`:
   - `ARCHITECTURE.md`
   - `CONCERNS.md`
   - `CONVENTIONS.md`
   - `INTEGRATIONS.md`
   - `STACK.md`
   - `STRUCTURE.md`
   - `TESTING.md`
2. Produce comprehensive Final Implementation Report with before/after comparison table, fixed problems, and exact validation commands.
</action>
<verify>
Codebase map files accurately reflect the live implementation and documentation is 100% reconciled.
</verify>
</task>

</tasks>

<artifacts_produced>
### Artifacts this phase produces
- Canonical Specification: `docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md`
- Phase Planning: `.planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/`
- Backend Modules: `scoring.py`, `confluence.py`, `observability.py`, `logging.py`, `middleware.py`
- Frontend Modules: `frontend/components/{signals,confluence,contradictions,missing-signals,developments,intelligence,functions,calibration,sources,observability,common}/`
- Invariant & Failure Injection Tests: `tests/test_truthfulness_and_invariants.py`, `tests/test_failure_injection.py`
- Reconciled Codebase Map: `.planning/codebase/*.md`
</artifacts_produced>
