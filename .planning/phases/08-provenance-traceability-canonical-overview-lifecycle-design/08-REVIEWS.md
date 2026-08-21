---
phase: 08
reviewers: [codex]
reviewed_at: 2026-08-20T18:38:54Z
plans_reviewed:
  - 08-01-PLAN.md
  - 08-02-PLAN.md
  - 08-03-PLAN.md
---

# Cross-AI Plan Review — Phase 08: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening

## Codex Review (OpenAI Codex CLI — `gpt-5.6-terra`)

### Summary
The phase has a strong truthfulness-first strategy: it starts at connector payloads, removes fabricated backend/frontend values, makes operational telemetry explicit, then standardizes UI presentation. The wave ordering is sensible (`08-01 → 08-02 → 08-03`), but the plans need tighter integration testing, a resolved definition of “independent source,” and broader provenance coverage beyond the primary signals route. Overall, the implementation is feasible but high-risk due to its cross-cutting schema, contract, ingestion, and UI changes.

### Strengths
- The plans correctly target the real provenance break at the bronze-to-signal transformation. Current ingestion invents `CLINICAL_TRIAL` and loses provenance fields in `backend/app/workflows/nodes/ingest.py:61-77`.
- Removing runner URL fabrication is essential. Current persistence manufactures PubMed, ClinicalTrials, and openFDA API URLs in `backend/app/workflows/runner.py:207-215`, including an API endpoint incorrectly treated as a source URL.
- Plan 08-01 appropriately removes serializer-side score recomputation and confidence fabrication currently present in `backend/app/api/v1/endpoints/signals.py:59-102` and `signals.py:134`.
- The migration/backfill is narrowly scoped and avoids relabeling all historical rows as live.
- Plan 08-02 correctly addresses known false telemetry: registry emits fabricated `LIVE` in `backend/app/api/v1/endpoints/registry.py:81`, and the Sources UI displays fabricated `200 OK` in `SourcesOperationsWorkspace.tsx:178`.
- Plan 08-03’s static banned-class gate is a useful regression control. The current surface has widespread hardcoded theme pairs, including `EvidenceDrawer.tsx:61-245`.
- The plans explicitly include security controls for evidence rendering and source links: React text rendering, `https` scheme validation, and `noopener noreferrer`.

---

### Plan 08-01 — Provenance End-to-End

#### Concerns
- **HIGH — Tests do not exercise the claimed end-to-end chain.** Most described tests directly insert `Signal` rows and call `GET /signals`. That verifies serialization, not connector parsing → bronze persistence → `node_ingest` → runner upsert. The actual defect is upstream in `ingest.py:61-77`, so direct inserts can pass while the pipeline remains broken.
- **HIGH — “Every displayed signal” is broader than this route.** The plan fixes `/signals`, SignalCard, and EvidenceDrawer, but signal-like data also appears in overview/intelligence/confluence paths. For example, overview constructs separate response objects in `backend/app/api/v1/endpoints/intelligence.py:124-156`. A provenance audit must enumerate every API DTO and UI consumer.
- **HIGH — `recorded_demo` is collapsed into `TEST FIXTURE`.** Phase requirements explicitly distinguish `live`, `recorded_demo`, and `test_fixture`. The proposed badge logic maps `recorded_demo` to `TEST FIXTURE`, losing a required semantic distinction.
- **MEDIUM — “Verbatim evidence” conflicts with scrubbed evidence.** Connector actions use scrubbed abstracts/descriptions as `evidence_text`. That is safe, but it is transformed evidence, not verbatim. The contract should state whether `evidence_text` is “source-derived, PII/PHI-scrubbed excerpt,” and TRACE should disclose the scrubber transformation.
- **MEDIUM — Migration backfill may cause a long transaction.** Updating historical `signals` rows with `LIKE` predicates can produce write amplification and locks on a production-sized table. The plan lacks an operational migration strategy.
- **MEDIUM — Missing/noncanonical provider URLs need a structured reason.** A free-text `provenance_status` is insufficient to distinguish “provider has no stable record page,” “fixture,” “missing provider field,” and “unsafe/unvalidated URL.”

#### Suggestions
- Add true integration tests for each connector: parse fixture → persist `RawSignalBronze` → run `node_ingest` and runner → assert the stored row and API output.
- Make provenance a typed nested schema/object rather than only parallel optional fields. This reduces drift between serializer, OpenAPI, mapper, card, drawer, and confluence evidence.
- Preserve all three display states explicitly: `LIVE INTELLIGENCE`, `RECORDED DEMO`, `TEST FIXTURE` / `SYNTHETIC`.
- Add a URL-state enum/reason contract, e.g. `available`, `fixture`, `provider_url_unavailable`, `missing_provider_url`, `invalid_url`.
- Run migration backfills in batches or document expected lock/runtime and verify upgrade/downgrade against a representative populated database.

---

### Plan 08-02 — Source Honesty & Observability

#### Concerns
- **HIGH — The confluence rule is semantically unresolved.** User decisions say “distinct source categories/types,” while the plan changes the rule to distinct `source_id`. These are not necessarily equivalent. A `source_id` might identify a connector, a provider, or a record, and the plan must establish one canonical independence taxonomy before changing engine, node, API copy, and tests.
- **HIGH — `configuration_error_for()` should not persist DB state from configuration code or a GET path.** The proposed helper both evaluates environment configuration and “persists” it onto `Source`. `config.py` should remain side-effect-free; persistence belongs in an explicit service with an async session/transaction. Otherwise health reads may unexpectedly write data and have inconsistent lifecycle behavior.
- **HIGH — xAI configuration is omitted.** The directive requires `XAI_API_KEY` to be reported when Grok fallback is enabled. The plan’s helper only handles NewsAPI, so REQ-P8-07 is incomplete.
- **HIGH — Logging a request URL can leak secrets.** The plan asks for request URLs in structlog. Query-string tokens and signed URLs are secrets even if the field name is not sensitive. Existing scrubbing must be verified to sanitize URL query parameters, headers, and nested raw data—not merely named keys.
- **MEDIUM — The status boundary lacks a fuller state model.** “Fetched and accepted at least one” is a good HEALTHY criterion, but the plan should specify deterministic precedence for timeout, auth failure, configuration error, partial failure, stale success, and exceptions after fetching.
- **MEDIUM — Health tests still rely too much on direct database setup.** They should include mocked connector attempts that demonstrate actual status propagation from transport result through `SourceHealthLog`, Source, endpoints, and UI DTOs.
- **MEDIUM — Confluence evidence contract changes are under-specified.** The plan changes the inspector, but does not explicitly list the response schema/type that gains provenance fields. It risks an untyped ad hoc payload.

#### Suggestions
- Define `independent_source_category` centrally—likely provider/connector category—and use that exact normalized field in the engine, node, API, UI copy, and tests. Add tests for three records from one provider versus three providers.
- Keep `configuration_error_for()` pure. Add an explicit reconciliation/update service invoked during startup, ingestion attempts, or an administrative refresh.
- Extend configuration reporting for `XAI_API_KEY` conditional on `ENABLE_GROK_FALLBACK`; clearly classify public connectors and optional rate-limit keys.
- Redact URLs before logging: retain scheme/host/path template or an approved endpoint label, strip query/fragment, and never log request headers or raw payloads.
- Add a status precedence table and corresponding parameterized tests: `CONFIGURATION_ERROR > UNHEALTHY/auth-or-transport failure > DEGRADED/zero accepted > HEALTHY`.

---

### Plan 08-03 — Canonical Design System

#### Concerns
- **HIGH — Scope does not meet the stated “all components/drawers/modals” gate.** The plan sweeps nine workspace files, but current violations also exist in shared components such as `EmptyState.tsx:21-38` and `ErrorState.tsx:75-115`. A final all-components gate would fail or require undocumented exclusions.
- **HIGH — The static checker is incomplete for the user directive.** It scans `.tsx` line-by-line and skips comment-only lines, but does not robustly cover multiline JSX/class strings, inline style objects, CSS files, dynamically constructed classes, or hardcoded colors outside the chosen class patterns.
- **MEDIUM — The plan forbids `globals.css` changes while requiring complete semantic theme tokens.** That is safe only if an audit proves every required token already exists and works in both themes. Otherwise this self-imposed non-goal conflicts with REQ-P8-12.
- **MEDIUM — Theme persistence has no automated browser-level verification.** Lint/build and grep cannot prove localStorage persistence across refresh, direct URLs, route changes, and drawer state. The human checkpoint is valuable but should not be the sole protection against regression.
- **MEDIUM — Settings credential display lacks a defined data-loading path.** Plan 08-03 assumes it can consume the Plan 08-02 payload, but does not specify which endpoint/hook supplies it, loading/error handling, or authorization behavior.
- **LOW — The global-font assertion needs an auditable source of truth.** “Arial/Helvetica/sans-serif” should be validated against the canonical dashboard/lifecycles implementation rather than assumed.

#### Suggestions
- Begin with an inventory generated by the checker over all `frontend/components/**/*.tsx`, then explicitly classify every exception. Include `common/`, confluence, Sources, EvidenceDrawer, and any modal/inspector in the sweep.
- Expand the gate to scan `.tsx`, `.ts`, and CSS for forbidden literals; detect `style={{...}}`, `#hex`, `rgb()`, unsupported palette classes, and hardcoded dark/light pairs. Add fixture-based tests for multiline and comment behavior.
- Add Playwright/browser tests for theme switching and drawer behavior.
- Define the Settings API call and UI state explicitly, including `CONFIGURATION_ERROR`, unavailable telemetry, loading, and request failure.
- Add a final `pytest tests/ -x -q` execution in this plan’s completion gate, not only frontend lint/build.

---

## Cross-Plan Dependency Concerns
- **HIGH — Contract churn needs a single ownership point.** Plans 08-01 and 08-02 both regenerate OpenAPI/types. Ensure 08-02 starts from the committed 08-01 generated contract and fails on drift; do not permit manual conflict resolution in `frontend/types/api.ts`.
- **HIGH — Provenance must be complete before confluence evidence uses it.** Plan 08-02 should explicitly require Plan 08-01’s migration to be applied and its full pipeline integration tests—not merely its unit/API tests—to be green.
- **MEDIUM — Manual checkpoints are correctly blocking, but too late to reveal design failures.** Add automated route/contract tests before the final human walkthroughs so reviewers spend time validating usability rather than discovering missing payload fields.
- **MEDIUM — Phase documentation synchronization is absent.** The phase charter calls for synchronized planning/codebase documentation, but none of the three plans updates those artifacts.

---

## Consensus Summary & Actionable Recommendations

### Agreed Strengths
1. **Accurate Root-Cause Targeting**: Direct identification of the bronze-to-signal data dropping in `node_ingest.py` and URL fabrication in `runner.py`.
2. **Elimination of Artificial Telemetry**: Removal of fake `LIVE` connector badges, hardcoded `200 OK` statuses, and serialized re-scoring.
3. **Hard Structural Gates**: CI-compatible static checkers and strict anti-fabrication invariants.

### Agreed High-Priority Concerns & Fixes for `/gsd-plan-phase 08 --reviews`
1. **Full Pipeline Integration Tests in 08-01**: Must test from connector fixture → `RawSignalBronze` → `node_ingest` → `PipelineRunner` upsert → DB → API → Frontend, rather than direct `Signal` DB row inserts.
2. **Three-Way DataMode Badge Fidelity**: Ensure `live`, `recorded_demo`, and `test_fixture`/`synthetic` remain three distinct first-class UI badges rather than collapsing `recorded_demo` into `test_fixture`.
3. **Canonical Confluence Independence Taxonomy in 08-02**: Formalize whether confluence counts distinct `source_id`, provider category, or connector identifier, and enforce this identically across backend node, SQL queries, and UI copy.
4. **Pure Side-Effect-Free Config Helpers**: `configuration_error_for()` must remain pure; DB persistence of health state belongs strictly within the async ingestion/health service during ingestion runs.
5. **Include xAI Grok Credential Reporting**: Include `XAI_API_KEY` (when `ENABLE_GROK_FALLBACK=true`) in the missing credential evaluation matrix alongside `NEWSAPI_KEY`.
6. **URL & Query Parameter Sanitization in Observability Logging**: Explicitly scrub query strings and auth tokens from logged endpoint URLs before structured JSON emission.
7. **Complete Shared Component Sweep in 08-03**: Expand banned class sweep beyond the 9 workspaces to include all shared components in `frontend/components/common/` (`EmptyState.tsx`, `ErrorState.tsx`, modals, drawers).
