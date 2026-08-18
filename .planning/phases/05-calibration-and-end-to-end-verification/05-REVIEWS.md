---
phase: 05
reviewers:
  - codex
  - claude
reviewed_at: 2026-08-18T19:40:00Z
plans_reviewed:
  - 05-01-PLAN.md
  - 05-02-PLAN.md
  - 05-03-PLAN.md
---

# Cross-AI Plan Review — Phase 05: Stakeholder Calibration & End-to-End Verification

## Review Summary

The Phase 5 plan suite establishes a robust, highly coherent, and verifiable human-in-the-loop (HITL) calibration architecture. The division into 2 waves (Wave 1: Calibration Service, API & Contracts; Wave 2: Demo Dataset, E2E Scenario & Frontend Widget) cleanly decouples backend persistence and mathematics from presentation and scenario testing.

---

## Strengths Identified

1. **Strict Baseline Immutability (WORM Architecture)**:
   - Preserves `baseline_primary_function`, `baseline_relevance_scores`, and `baseline_suggested_action` permanently in `signal_routing`, storing calibration adjustments in separate `calibrated_*` columns. This guarantees reproducible, honest BEFORE vs AFTER comparisons without state corruption.
2. **Bounded Mathematical Formulations**:
   - Uses bounded gradient delta updates:
     $$\Delta w = \alpha \cdot (\overline{R} - 3.0), \quad \alpha = 0.05, \quad w \in [0.1, 2.0]$$
     This prevents runaway feedback bias or vanishing weights across iterative sessions.
3. **Deterministic & Cost-Free Watch-Rule Extraction**:
   - Relies on keyword-based heuristic parsing (`"congress"`, `"trial"`, `"durability"`, `"regulatory"`, `"safety"`) rather than non-deterministic LLM prompting, ensuring predictable unit testing, zero privacy-gate boundary leaks, and instant execution.
4. **Complete E2E Demonstration Arc (Hemgenix 3-Year Durability)**:
   - Curates a multi-source story (PubMed 3-yr follow-up + CSL commercial announcement + ASH 2026 comparative abstract) and exercises the entire 8-step arc in `tests/test_e2e_calibration_scenario.py`.
5. **Contract Governance & Strict DoD**:
   - Enforces automatic OpenAPI 3.1 and TypeScript synchronization (`scripts/export_openapi.py` / `test_contract_drift.py`) alongside strict Next.js, ESLint, and Pytest quality gates.

---

## Findings & Plan Refinements

### High Severity

1. **In-Memory vs Persistent Fallback in `node_calibrate` (Plan 05-02)**:
   - *Concern*: Pipeline tests and standalone graph executions often run without an active database session. If `node_calibrate` strictly requires a live database connection, unit tests in `tests/test_intelligence_nodes.py` may fail or require complex DB fixtures.
   - *Recommendation*: Ensure `node_calibrate` checks `if session is not None:` and falls back to in-memory state updates when running disconnected, while utilizing `StakeholderCalibrationService` when an `AsyncSession` is provided.
2. **Watch-Rule Suggestion ID Determinism in Scenario Tests (Plan 05-02)**:
   - *Concern*: Generating random UUIDs for parsed watch rule suggestions can make automated assertions in `test_e2e_calibration_scenario.py` fragile.
   - *Recommendation*: Generate deterministic suggestion hashes from `(signal_id, stakeholder_function, trigger_event)` or assert on structured payload contents rather than raw UUIDs.

### Medium Severity

1. **Frontend Star Rating Accessibility & In-Flight State (Plan 05-03)**:
   - *Concern*: Rapid clicks on star rating buttons could dispatch multiple duplicate feedback submissions.
   - *Recommendation*: Add optimistic visual selection, disable the submit button during in-flight network requests, and show a clear checkmark confirmation toast upon recording.
2. **Calibration History Version Tagging (Plan 05-01)**:
   - *Concern*: Using raw timestamps in version tags can produce long strings (`v1.1724001234`).
   - *Recommendation*: Use standard semver format or clean incremental numbering (e.g. `v1.1.0`, `v1.2.0`) with ISO-8601 audit timestamps in `applied_at`.
3. **Empty Feedback Handling in `/calibrate` Endpoint (Plan 05-01)**:
   - *Concern*: Triggering `/calibrate` when 0 unapplied feedback items exist should not error out or alter existing weights.
   - *Recommendation*: Return status `"no_unapplied_feedback"` with 0 delta and current weights rather than throwing a 400/500 error.

---

## Consensus & Action Matrix

| Plan | Target Refinement | Impact |
| :--- | :--- | :--- |
| **05-01** | Add zero-delta handling for empty feedback in `recalibrate_role`; use semver version strings in `calibration_history`. | Guarantees idempotent calibration API behavior and clean audit trail. |
| **05-02** | Implement dual in-memory / persistent execution paths in `node_calibrate`; enforce deterministic suggestion payload verification. | Prevents unit test regressions and guarantees stable CI runs. |
| **05-03** | Add in-flight button lock and confirmation badge in `StakeholderFeedbackWidget`. | Prevents duplicate feedback submission and improves user experience. |

---

## Verdict

**Status:** `APPROVED` (Ready for Wave 1 execution). All plans meet MetaRadar engineering standards, DoD specifications, and architectural constraints.
