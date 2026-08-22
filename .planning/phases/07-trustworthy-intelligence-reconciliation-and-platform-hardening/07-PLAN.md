---
phase: 07
plan: "01"
title: Trustworthy Intelligence Reconciliation, Observability Upgrade, Modular Frontend Refactor & Platform Hardening
status: COMPLETE
completed_at: 2026-08-20T19:25:00Z
wave: 1
depends_on: []
files_modified:
  - docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md
  - backend/alembic/versions/004_phase7_truthfulness_and_provenance.py
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
Research Document: [.planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-RESEARCH.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-RESEARCH.md)  
Peer Review: [.planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md)
</reference_specification>

<review_incorporation>
Incorporated findings from 07-REVIEWS.md:
1. **Async Relationship Safety:** In all intelligence read queries (`get_confluence_alerts`, `get_red_team_contradictions`, `get_missing_signals`, `get_lifecycle_timelines`), use explicit outer joins or batching to prevent `MissingGreenlet` exceptions under asyncpg.
2. **Graceful Legacy Model Serialization:** In `_serialize_signal()`, gracefully handle legacy records with missing `data_mode` or `score_breakdown` by returning explicit default `data_mode="live"` and `scoring_status="not_computed"`, never raising unhandled validation errors.
3. **Recency Calculation Null Guards:** In `PriorityScoringService`, guard against missing published dates (`hours_since_published is None`) by returning `None` (mapped to `"not_computed"` in API serialization), preventing division by zero or NaN errors.
4. **Contextvar Propagation for Background Tasks:** Bind `pipeline_run_id` to `structlog.contextvars` in `PipelineRunner.run()` and ensure background tasks inherit context via `contextvars.copy_context()`.
5. **Non-Blocking Telemetry Persistence:** In connector `run_profile()`, persist `SourceHealthLog` records cleanly within the run transaction without blocking bronze record staging.
6. **Client-Side Mount Guards:** Ensure all extracted client components in `frontend/components/` declare `"use client"` and include `useMounted` checks before accessing browser APIs or `localStorage` to eliminate SSR hydration mismatches.
7. **Clean Migration Reversibility:** Author full `upgrade()` and `downgrade()` methods in `004_phase7_truthfulness_and_provenance.py` for database rollback safety.
</review_incorporation>

<threat_model>
ASVS Level 1 & Enterprise Intelligence Threat Assessment:
- **T-07-01 (Fabricated Telemetry & Deceptive AI Output):** Hardcoded confidence scores or synthetic excerpts misleading clinical or regulatory leadership. Mitigation: Enforce mandatory provenance IDs, real mathematical scoring formulas with breakdowns, typed confidence enums, and zero static evidence fallbacks.
- **T-07-02 (Silent Synthetic Data Infiltration):** Synthetic test fixtures poisoning production vector indexes or live decision streams. Mitigation: Explicit `DataMode` tags (`live`, `recorded_demo`, `test_fixture`) and visible UI badges.
- **T-07-03 (State Mutation on Read Requests):** Vulnerability where `GET /calibrate` mutates weight records. Mitigation: Strict REST idempotency where `GET` is purely read-only and mutations require transactional `POST /api/v1/calibration/run`.
- **T-07-04 (Error Concealment & Unobservable Failures):** Network or parser failures masked behind empty UI cards. Mitigation: Structured JSON logs, correlation IDs (`X-Request-ID`), and standard `ErrorState` components with retry buttons.
- **T-07-05 (Contract Drift & Dynamic Type Bypass):** Loose `any` types in frontend mappers causing deserialization crashes. Mitigation: Fully typed DTO mappers and automated OpenAPI sync validation.
</threat_model>

<must_haves>
- Complete all 12 Non-Negotiable Product Principles.
- Execute all 36 Phases of the intelligence audit and hardening spec in a single, uninterrupted wave.
- Zero hardcoded scores, zero fake "LIVE" badges, zero placeholder claims.
- Real priority scoring with breakdown (`Novelty`, `Clinical`, `Regulatory`, `Recency`).
- Real confluence clustering across $\ge 3$ sources in 48h windows with calculation versions.
- Real pgvector cosine retrieval for Athena and real claim citations for Red-Team.
- Real connector health status tracking (`HEALTHY`, `DEGRADED`, `STALE`, `RATE_LIMITED`, `AUTH_FAILED`, `ERROR`, `DISABLED`, `NEVER_CONNECTED`).
- Structured JSON logging with `structlog`, correlation IDs (`X-Request-ID`), and Activity Stream workspace.
- Modularized frontend under `frontend/components/` by bounded context, eliminating monolithic files.
- Reusable `EvidenceDrawer`, `ErrorState`, and `EmptyState` components.
- Automated tests for all invariants and failure-injection scenarios passing 100%.
- Synchronized codebase map documentation in `.planning/codebase/*.md`.
</must_haves>

<tasks>

<task id="07-01-T1">
<title>Audit Codebase for Fabricated Telemetry, Placeholders & Stale Documentation</title>
<read_first>
- backend/app/api/v1/endpoints/intelligence.py
- backend/app/api/v1/endpoints/signals.py
- frontend/lib/mock-data.ts
- frontend/components/metaradar.tsx
- docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md
</read_first>
<action>
1. Search repository for hardcoded scores, confidence floats, mock excerpts, and static "LIVE" strings.
2. Verify confirmed bugs:
   - `intelligence.py:158-159` placeholder excerpts.
   - `intelligence.py:193` fake confidence heuristic.
   - `frontend/lib/mock-data.ts` hardcoded signals and confluence score 78.
3. Document exact remediation mappings in the execution log.
</action>
<verify>
All placeholder occurrences documented with verified line numbers and replacement strategy.
</verify>
</task>

<task id="07-01-T2">
<title>Author Migration 004 & Update Database Models/Schemas with Provenance, DataMode & Health</title>
<read_first>
- backend/alembic/versions/003_contradictions_scoring.py
- backend/app/models/__init__.py
- backend/app/schemas/__init__.py
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-RESEARCH.md
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md
</read_first>
<action>
1. Author `backend/alembic/versions/004_phase7_truthfulness_and_provenance.py` implementing both `upgrade()` and `downgrade()` (per Review Finding 7):
   - `signals`: `data_mode` (default 'live'), `is_synthetic` (default false), `confidence_type`, `confidence_rationale`.
   - `contradictions`: `claim_a_excerpt`, `claim_b_excerpt`, `claim_a_evidence_id`, `claim_b_evidence_id`, `confidence_type`.
   - `calibration_feedback`: `is_applied` (default false), `applied_at`, `calibration_run_id`.
   - `sources`: `connector_status` (default 'NEVER_CONNECTED'), `last_attempted`, `latency_ms`, `records_fetched`, `records_accepted`, `records_rejected`, `http_status`.
   - Create table `source_health_logs` (id, source_id, pipeline_run_id, checked_at, connector_status, http_status, latency_ms, records_fetched, records_accepted, records_rejected, last_error, error_code).
   - Create table `calibration_runs` (run_id, triggered_at, completed_at, status, feedback_count, previous_weights, new_weights, affected_functions, reason, scoring_version).
2. Update `backend/app/models/__init__.py` with `SourceHealthLog`, `CalibrationRun`, and new model attributes.
3. Update `backend/app/schemas/` to define `DataMode`, `ConfidenceType`, `ScoreBreakdownSchema`, `SourceHealthItem`, and `CalibrationRunSchema`.
</action>
<acceptance_criteria>
`python -c "from app.models import Signal, Confluence, Contradiction, CalibrationRun, SourceHealthLog; print('Models verified')"` exits with code 0.
</acceptance_criteria>
<verify>
`python -c "from app.models import Signal, Confluence, Contradiction, CalibrationRun, SourceHealthLog; print('Models verified')"`
</verify>
</task>

<task id="07-01-T3">
<title>Implement Real Priority Scoring, Confluence & Confidence Typing Services</title>
<read_first>
- backend/app/services/calibration.py
- backend/app/services/source_independence.py
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-RESEARCH.md
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md
</read_first>
<action>
1. Implement `backend/app/services/scoring.py` with `PriorityScoringService`:
   - Inputs: `ScoreInput(novelty_distance, clinical_keywords_found, regulatory_keywords_found, hours_since_published)`.
   - Null Guards (per Review Finding 3): If `hours_since_published is None` or `novelty_distance is None`, return `None` (mapped to `scoring_status: "not_computed"` in serialization).
   - Weights: Novelty 25%, Clinical 30%, Regulatory 25%, Recency 20% (72h half-life decay).
2. Implement `backend/app/services/confluence.py` with multi-source clustering across $\ge 3$ independent source types in 48-hour windows, entity matching, and `calculation_version`.
3. Implement `ConfidenceType` enum (`extraction`, `classification`, `heuristic`, `model`, `human`) and enforce explicit type declaration across all schemas.
</action>
<acceptance_criteria>
`python -c "from app.services.scoring import priority_scorer, ScoreInput; res = priority_scorer.score(ScoreInput(0.8, 2, 1, 12.0)); assert res is not None; print('Scorer verified:', res.total)"` passes.
</acceptance_criteria>
<verify>
`python -c "from app.services.scoring import priority_scorer, ScoreInput; res = priority_scorer.score(ScoreInput(0.8, 2, 1, 12.0)); assert res is not None; print('Scorer verified:', res.total)"`
</verify>
</task>

<task id="07-01-T4">
<title>Hardwire Athena RAG Evidence Retrieval & Red-Team Verbatim Contradiction Excerpts</title>
<read_first>
- backend/app/api/v1/endpoints/intelligence.py
- backend/app/api/v1/endpoints/signals.py
- backend/app/services/vector_query.py
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md
</read_first>
<action>
1. In `backend/app/services/athena.py` / `signals.py`, query pgvector HNSW index over chunked `Evidence` records (`Signal.embedding.op('<=>')(query_embedding) < 0.28`); return `[FACT]`, `[INFERENCE]`, `[SUGGESTION]` labeled responses with source links. Return honest `"No sufficiently relevant evidence was found in the indexed sources to answer this question."` on empty retrieval.
2. In `backend/app/api/v1/endpoints/intelligence.py`, fix `get_red_team_contradictions`: fetch verbatim content from `Signal.content` or `Evidence` for `claim_a_id` and `claim_b_id` using async joins (per Review Finding 1); remove `"Primary evidence claim..."` strings completely.
3. In `backend/app/api/v1/endpoints/intelligence.py`, fix `get_missing_signals`: remove fake `confidence` float and introduce explicit `overdue_heuristic_score` + 6-state FSM (`WITHIN_WINDOW`, `DUE`, `OVERDUE`, `SATISFIED`, `SUPPRESSED`, `INSUFFICIENT_DATA`).
</action>
<acceptance_criteria>
`pytest tests/test_redteam_behavior.py tests/test_retrieval.py -v` passes without placeholder strings.
</acceptance_criteria>
<verify>
`pytest tests/test_redteam_behavior.py tests/test_retrieval.py -v`
</verify>
</task>

<task id="07-01-T5">
<title>Implement Structured Observability, Correlation IDs & Real Connector Health Tracking</title>
<read_first>
- backend/app/connectors/base.py
- backend/app/workflows/runner.py
- backend/app/main.py
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-RESEARCH.md
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md
</read_first>
<action>
1. Implement `backend/app/core/logging.py` configuring `structlog` with JSON rendering, ISO timestamps, stack info, and automatic PII/secret scrubbing (`_scrub_secrets`).
2. Implement `backend/app/core/middleware.py` with `CorrelationIdMiddleware` reading or generating `X-Request-ID`, propagating to structlog contextvars and response headers, and logging request duration.
3. In `backend/app/workflows/runner.py`, bind `pipeline_run_id` at inception and ensure asyncio task spawning preserves contextvars via `contextvars.copy_context()` (per Review Finding 4).
4. In `backend/app/connectors/base.py` and adapters (PubMed, ClinicalTrials, NewsAPI, OpenFDA, EMA), track real connection health, latency, HTTP response codes, and persist each run to `SourceHealthLog` without blocking bronze staging (per Review Finding 5).
5. Implement `backend/app/api/v1/endpoints/observability.py` with `GET /api/v1/observability/activity` and `GET /api/v1/sources/health`.
6. Register routers in `backend/app/main.py`.
</action>
<acceptance_criteria>
FastAPI app logs structured JSON with `request_id` and registers `/api/v1/observability/activity` and `/api/v1/sources/health`.
</acceptance_criteria>
<verify>
`pytest tests/test_api_endpoints.py -v`
</verify>
</task>

<task id="07-01-T6">
<title>Fix Calibration Lifecycle & Ensure Idempotent Read-Only GET Endpoints</title>
<read_first>
- backend/app/api/v1/endpoints/feedback.py
- backend/app/services/calibration.py
</read_first>
<action>
1. In `backend/app/api/v1/endpoints/calibration.py` / `feedback.py`, make `GET /api/v1/calibration` purely read-only (returning current weights, run history, and pending feedback count without database mutation).
2. Implement `POST /api/v1/calibration/run` to execute calibration exclusively over unapplied feedback (`is_applied == False`), create an immutable `CalibrationRun` record, and mark feedback items as `applied` with `calibration_run_id`.
</action>
<acceptance_criteria>
`pytest tests/test_calibration_service.py tests/test_e2e_calibration_scenario.py -v` passes verifying idempotent runs.
</acceptance_criteria>
<verify>
`pytest tests/test_calibration_service.py tests/test_e2e_calibration_scenario.py -v`
</verify>
</task>

<task id="07-01-T7">
<title>Modularize Frontend Architecture by Bounded Context & Build Error/Evidence Components</title>
<read_first>
- frontend/components/metaradar.tsx
- frontend/lib/api.ts
- frontend/lib/mock-data.ts
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-RESEARCH.md
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md
</read_first>
<action>
1. Delete `frontend/lib/mock-data.ts` after verifying and replacing all import references with live typed API client hooks.
2. Build reusable common components with client mount guards (per Review Finding 6):
   - `frontend/components/common/ErrorState.tsx` (human message, correlation ID copy button, retry trigger, technical diagnostics).
   - `frontend/components/common/EmptyState.tsx` (explicit empty state with context).
   - `frontend/components/common/EvidenceDrawer.tsx` (full provenance, source URL, timestamps, calculation history).
   - `frontend/components/common/DataModeBadge.tsx` (`LIVE DATA` vs `RECORDED DEMO DATA`).
3. Deconstruct `metaradar.tsx` into domain packages under `frontend/components/`:
   - `signals/`, `confluence/`, `contradictions/`, `missing-signals/`, `developments/`, `intelligence/`, `functions/`, `calibration/`, `sources/`, `observability/`, `settings/`.
4. Implement `frontend/lib/mappers.ts` and `frontend/lib/errors.ts` eliminating all `any` types and handling legacy null fields gracefully (per Review Finding 2).
</action>
<acceptance_criteria>
Frontend compiles with `tsc --noEmit` with zero type errors and clean modular imports.
</acceptance_criteria>
<verify>
`npm --prefix frontend run build`
</verify>
</task>

<task id="07-01-T8">
<title>Hardwire All 10 Next.js Workspaces with 8 Canonical UI States & Task-Oriented Navigation</title>
<read_first>
- frontend/app/layout.tsx
- frontend/components/layout/Navigation.tsx
- docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md
</read_first>
<action>
1. Wire all workspace routes:
   - `frontend/app/page.tsx` (Overview)
   - `frontend/app/signals/page.tsx` (Signals)
   - `frontend/app/confluence/page.tsx` (Confluences)
   - `frontend/app/contradictions/page.tsx` (Red-Team Contradictions)
   - `frontend/app/missing-signals/page.tsx` (Missing Signals)
   - `frontend/app/developments/page.tsx` (Developments)
   - `frontend/app/intelligence/page.tsx` (Athena AI)
   - `frontend/app/functions/page.tsx` (Stakeholder Functions)
   - `frontend/app/calibration/page.tsx` (Calibration Workspace)
   - `frontend/app/sources/page.tsx` (Sources Operations)
   - `frontend/app/activity/page.tsx` (System Activity Stream)
   - `frontend/app/settings/page.tsx` (Settings)
2. Ensure every workspace handles all 8 canonical states: `loading`, `success`, `empty`, `stale`, `degraded`, `unavailable`, `error`, `not_computed`.
3. Implement task-oriented navigation layout (Overview, Intelligence, Analysis, Workflows, System).
</action>
<acceptance_criteria>
Every workspace renders truthfully without placeholder numbers or broken states.
</acceptance_criteria>
<verify>
`npm --prefix frontend run build && npm --prefix frontend run lint`
</verify>
</task>

<task id="07-01-T9">
<title>Synchronize OpenAPI Contract, TypeScript Types & Export Artifacts</title>
<read_first>
- scripts/export_openapi.py
- contracts/openapi.json
- frontend/types/api.ts
- tests/test_contract_drift.py
</read_first>
<action>
1. Update `scripts/export_openapi.py` with all new schemas (`SourceHealthLog`, `CalibrationRun`, `ActivityLogItem`, `ConfidenceType`, `DataMode`, `ScoreBreakdown`).
2. Regenerate `contracts/openapi.json` and `frontend/types/api.ts`.
3. Verify zero drift with `pytest tests/test_contract_drift.py`.
</action>
<acceptance_criteria>
`pytest tests/test_contract_drift.py -v` exits with code 0 with 0 contract drift.
</acceptance_criteria>
<verify>
`python scripts/export_openapi.py && pytest tests/test_contract_drift.py -v`
</verify>
</task>

<task id="07-01-T10">
<title>Add Invariant Tests, Failure-Injection Suite & Verify 100% Quality Gates</title>
<read_first>
- tests/test_api_endpoints.py
- tests/test_retrieval.py
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-RESEARCH.md
- .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-REVIEWS.md
</read_first>
<action>
1. Write `tests/test_truthfulness_and_invariants.py`:
   - Invariant 1: Zero synthetic data enters live mode.
   - Invariant 2: Priority and Confluence scores are calculated deterministically; null returned when uncomputed.
   - Invariant 3: Confidence types and rationales are explicitly typed.
   - Invariant 4: Athena answers use real retrieved evidence; empty retrieval returns explicit failure string.
   - Invariant 5: Contradiction excerpts are verbatim source citations, not placeholder strings.
   - Invariant 6: Calibration feedback is applied exactly once (`is_applied == True`).
   - Invariant 7: GET endpoints never mutate database state.
2. Write `tests/test_failure_injection.py` with `pytest-httpx`:
   - Simulate PubMed and ClinicalTrials timeouts -> verifies DEGRADED/ERROR status in `SourceHealthLog`.
   - Simulate NewsAPI 429 rate limit -> verifies RATE_LIMITED state and retry telemetry.
   - Simulate Redis unavailable -> verifies graceful fallback response.
   - Verify correlation ID preservation on 500 error responses.
3. Run full verification suite: `pytest`, `npm --prefix frontend run build`, `npm --prefix frontend run lint`.
</action>
<acceptance_criteria>
100% test pass rate across all unit, invariant, failure-injection, contract, and build verification gates.
</acceptance_criteria>
<verify>
`pytest tests/ -v && npm --prefix frontend run build`
</verify>
</task>

<task id="07-01-T11">
<title>Synchronize Codebase Map Documentation & Generate Final Implementation Report</title>
<read_first>
- .planning/codebase/ARCHITECTURE.md
- .planning/codebase/CONCERNS.md
- .planning/codebase/CONVENTIONS.md
- .planning/codebase/INTEGRATIONS.md
- .planning/codebase/STACK.md
- .planning/codebase/STRUCTURE.md
- .planning/codebase/TESTING.md
</read_first>
<action>
1. Update all files in `.planning/codebase/` reflecting the actual codebase:
   - `ARCHITECTURE.md`: Document structured logging, correlation IDs, `PriorityScoringService`, `SourceHealthLog`, `CalibrationRun`.
   - `CONCERNS.md`: Move resolved placeholder/telemetry concerns to Resolved section; record any remaining future items.
   - `CONVENTIONS.md`: Document `DataMode`, `ConfidenceType`, structured logging conventions, and error UX guidelines.
   - `INTEGRATIONS.md`: Document real connector health telemetry and pgvector cosine distance retrieval.
   - `STACK.md`: Update dependencies (`structlog`, `asgi-correlation-id`, `pytest-httpx`).
   - `STRUCTURE.md`: Document modular `frontend/components/` structure and new backend service/endpoint modules.
   - `TESTING.md`: Document invariant tests and failure-injection strategy.
2. Produce comprehensive Final Implementation Report with before/after comparison table, fixed problems, and exact validation commands.
</action>
<acceptance_criteria>
Codebase map files accurately reflect the live implementation and documentation is 100% reconciled.
</acceptance_criteria>
<verify>
`git status` confirms all planning and codebase documentation updated and synchronized.
</verify>
</task>

</tasks>

<artifacts_produced>
### Artifacts this phase produces
- Canonical Specification: `docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md`
- Phase Planning, Research & Reviews: `.planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/`
- Migration: `backend/alembic/versions/004_phase7_truthfulness_and_provenance.py`
- Backend Modules: `scoring.py`, `confluence.py`, `observability.py`, `logging.py`, `middleware.py`
- Frontend Modules: `frontend/components/{signals,confluence,contradictions,missing-signals,developments,intelligence,functions,calibration,sources,observability,settings,common}/`
- Invariant & Failure Injection Tests: `tests/test_truthfulness_and_invariants.py`, `tests/test_failure_injection.py`
- Reconciled Codebase Map: `.planning/codebase/*.md`
</artifacts_produced>
