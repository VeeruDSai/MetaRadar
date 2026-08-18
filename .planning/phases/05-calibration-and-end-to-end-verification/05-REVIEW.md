---
phase: 05-calibration-and-end-to-end-verification
reviewed: 2026-08-18T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - backend/app/api/v1/endpoints/feedback.py
  - backend/app/main.py
  - backend/app/providers/gemma.py
  - backend/app/schemas/__init__.py
  - backend/app/services/calibration.py
  - backend/app/workflows/nodes/calibrate.py
  - contracts/openapi.json
  - data/synthetic_signals.json
  - docs/release/v5.1_RELEASE_NOTES.md
  - frontend/app/globals.css
  - frontend/components/metaradar.tsx
  - frontend/lib/api.ts
  - frontend/types/api.ts
  - scripts/export_openapi.py
  - tests/test_calibration_service.py
  - tests/test_e2e_calibration_scenario.py
findings:
  critical: 2
  warning: 9
  info: 6
  total: 17
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-08-18
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed the Phase 5 calibration loop implementation at standard depth: the persistent `StakeholderCalibrationService` (WORM feedback, batch recalibration, semver history, watch-rule parsing), the four new API endpoints, the `node_calibrate` rewrite, the frontend `StakeholderFeedbackWidget` + BEFORE/AFTER comparison, the synthetic demo dataset, the OpenAPI/TS contract chain, and both test files. Generated artifacts (`contracts/openapi.json`, `frontend/types/api.ts`) were verified for consistency with `scripts/export_openapi.py` and the FastAPI routes — they are in sync, including the new endpoints and `FeedbackSubmissionRequest.user_id` field. `docs/release/v5.1_RELEASE_NOTES.md` was checked for accuracy and contains several factual claims contradicted by the implementation (see CR-01 note, WR-01, IN-04).

The core service has two serious defects: (1) feedback is never marked as applied, so every recalibration re-applies **all** historical feedback and the weights drift monotonically to the clamp — contradicting the locked D-02 "unapplied feedback" semantics; (2) the BEFORE/AFTER comparison fabricates the baseline priority ("HIGH" hardcoded for every signal) and uses an invented priority formula that omits the novelty term mandated by locked decision D-03 — a direct violation of AGENTS.md rule 4 (no fabricated telemetry). The `action_appropriate` feedback dimension (D-01) is collected but has zero effect on any output, and the D-10 watch-item integration is not wired: `node_missing_signal` never reads the `watch_items` table, and the E2E test's step 8 asserts an unrelated success.

## Critical Issues

### CR-01: Feedback is never marked as applied — repeated recalibration re-applies all historical feedback, causing unbounded weight drift

**File:** `backend/app/services/calibration.py:144-150, 229-235`
**Issue:** `CalibrationFeedback` has no `applied`/`consumed` marker, and `recalibrate_role()` selects **all** feedback rows for a role (`select(CalibrationFeedback)` with no status filter) and re-aggregates them on every trigger. D-02 and D-06 lock "aggregates ALL **unapplied** feedback for a role" with a fixed small-N trigger. Consequences:

- Every "Recalibrate now" click re-applies the same feedback rows: with relevance 5.0, the weight receives +0.10 on each click until it pins at the 2.0 clamp, even when no new feedback was submitted. The version bumps on every click too.
- `unapplied_count` (line 144) counts **all** rows for the role, so it never decreases; `recalibration_triggered` (line 150) is permanently `True` for that role after the 3rd submission.
- `node_calibrate`'s session branch (calibrate.py:53-54) calls `recalibrate_role()` on every pipeline run, re-applying all accumulated feedback and bumping the version each run.

No test covers repeated recalibration, so the drift is invisible to the suite.
**Fix:** Add an `applied_at`/`applied` column to `CalibrationFeedback` (models/__init__.py), filter recalibration queries with `WHERE applied = false`, and mark rows applied (or record which `CalibrationHistory` consumed them) inside `recalibrate_role` after aggregation. Update the `unapplied_count` query to use the same filter.

### CR-02: Fabricated BEFORE/AFTER telemetry — hardcoded baseline priority and an invented priority formula that deviates from locked decision D-03

**File:** `backend/app/services/calibration.py:377, 405`
**Issue:** Two fabrications in the comparison path, both displayed as real data in the UI:

1. `baseline_priority="HIGH"` is hardcoded for **every** comparison (line 405). The actual signal priority is never read (`SignalRouting` has no baseline priority column and the service never joins `Signal.priority`). The UI's "BASELINE ROUTING → Priority: HIGH" badge is therefore always wrong for any signal whose real baseline priority is not HIGH.
2. The calibrated priority formula `0.6 * (base_val * w_imp) + 0.4 * (0.8 * w_urg)` (line 377) invents an urgency constant `0.8` that is not derived from any urgency score, and omits the novelty term that locked decision D-03 explicitly specifies: "priority is recomputed as `w_impact·impact + w_urgency·urgency + w_novelty·novelty`". The 0.75/0.50/0.30 thresholds are arbitrary.

This violates AGENTS.md rule 4 ("No Fabricated Telemetry or Behavior") in the flagship demo story, and the E2E test (test_e2e_calibration_scenario.py:151) asserts against the fabricated formula, cementing it.
**Fix:** Persist/read the actual baseline priority (e.g., join `Signal.priority` or add a `baseline_priority` column populated by the routing node) and recompute priority with the D-03 formula using the real impact/urgency/novelty scores and per-function calibrated weights. Update the E2E assertions accordingly.

## Warnings

### WR-01: `user_id` is collected but silently discarded — release-note provenance claim is false

**File:** `backend/app/services/calibration.py:129-138`; `backend/app/schemas/__init__.py:239`
**Issue:** `FeedbackSubmissionRequest.user_id` (default `"demo_user"`) is accepted and forwarded by `node_calibrate` (calibrate.py:47), but `submit_feedback` never stores it — the `CalibrationFeedback` model has no `user_id` column. The release notes (v5.1_RELEASE_NOTES.md:11) claim feedback preserves "full provenance (`user_id`, timestamp, star ratings 1-5, comments)". The identifier is silently dropped — a provenance/audit data loss for a WORM table.
**Fix:** Add a `user_id` column to `CalibrationFeedback` and persist `req.user_id`, or remove the field from the schema, the TS contract, and the release-notes claim.

### WR-02: `action_appropriate` feedback dimension has zero effect — D-01's third mapping is unimplemented

**File:** `backend/app/services/calibration.py:387-390, 131-138`
**Issue:** D-01 locks `action_appropriate → action-affecting logic` and FR-2.8.3 requires the action to visibly change. The field is stored but never read anywhere: `calibrated_suggested_action` is a static template string with no conditional on `action_appropriate`, and the weights are only driven by `relevance_rating`/`urgency_rating`. A stakeholder answering "action is NOT appropriate" produces an identical, arguably MORE aggressive calibrated action ("Immediate high-priority briefing").
**Fix:** Implement action-affecting logic — e.g., when `action_appropriate` is False, downgrade or replace the calibrated action text (and/or gate the weight delta), and surface that change in the BEFORE/AFTER comparison.

### WR-03: GET `/api/v1/calibration/weights` mutates the database — read endpoint with write side effects

**File:** `backend/app/services/calibration.py:184-203`
**Issue:** `get_weights()` creates six `ScoringWeights` rows and calls `session.commit()` inside a GET handler (feedback.py:101-110). Worse, `recalibrate_role()` calls `get_weights()` mid-transaction, so seeding commits before the weight updates and history insert. If recalibration subsequently fails, seeded weight rows persist while the history/feedback application rolls back — leaving `scoring_weights` out of sync with `calibration_history`.
**Fix:** Seed rows without committing inside `get_weights` (accumulate adds and let the caller commit), or move seeding into an explicit upsert at the start of `recalibrate_role`.

### WR-04: Error paths render as success toasts in the calibration widget

**File:** `frontend/components/metaradar.tsx:992-993, 1004-1005, 1191-1196`
**Issue:** `handleFeedbackSubmit` and `handleRecalibrate` write failure strings into `feedbackSuccess`, which is rendered in the `.feedback-toast` div with a green `CheckCircle2` icon and success styling. Users see a green checkmark next to "Failed to record feedback. Please check backend connection." — a failure presented as success.
**Fix:** Introduce a separate `feedbackError` state rendered with danger styling, or make the toast tone conditional on success/error.

### WR-05: BEFORE/AFTER panel shows recalibration results for ALL signals, not the selected signal

**File:** `frontend/components/metaradar.tsx:1207`; `backend/app/services/calibration.py:348-354`
**Issue:** `recalibrate_role` returns comparisons for **every** `SignalRouting` row in the DB (no signal filter), and `SignalDrawer` renders the entire `recalResult.comparisons` list inside the currently-open signal's drawer. For a single-role recalibration every comparison's `stakeholder_function` is the requested role — so the drawer displays that role's recalibrated scores for unrelated signals.
**Fix:** Filter comparisons by the drawer's `signal.signal_id` client-side, or accept a `signal_id` parameter on `POST /api/v1/calibrate`.

### WR-06: `stakeholder_function`/`signal_id` unvalidated — rogue weight rows and misleading 500s

**File:** `backend/app/services/calibration.py:259-299`; `backend/app/api/v1/endpoints/feedback.py:36-44`
**Issue:** `FeedbackSubmissionRequest.stakeholder_function` is a free string, not constrained to the six canonical functions. Feedback for an arbitrary function (e.g., `"HACKER"`) is accepted, and recalibration then creates `ScoringWeights` rows for that function (line 291-299), polluting the canonical weight set and the summary aggregation. A `signal_id` that doesn't exist raises an `IntegrityError` at commit, which the endpoint's catch-all converts to a 500 "Failed to record stakeholder feedback" instead of a 4xx.
**Fix:** Constrain `stakeholder_function` with a `Literal`/`Enum` over `CANONICAL_FUNCTIONS` in the schema; catch `IntegrityError` and map to 400/404 in the endpoint.

### WR-07: Confirmed watch items are never consumed — D-10 integration missing; E2E step 8 asserts an unrelated success

**File:** `backend/app/services/calibration.py:468-491`; `backend/app/workflows/nodes/missing_signal.py:37-40`; `tests/test_e2e_calibration_scenario.py:174-194`
**Issue:** `confirm_watch_item` writes a `WatchItem` row, but `node_missing_signal` only inspects in-memory state (`developments`, `lifecycle_events`, `redteam_flags`, `scored_signals`) — the `watch_items` table is never queried, and the 5-state lifecycle is computed purely from state. The confirmed watch rule therefore has no effect on monitoring. The E2E test's step 8 calls `node_missing_signal` with hand-built state and asserts only `node_statuses == SUCCESS` — this passes regardless of whether any watch item exists, so the D-10 loop is asserted but not verified.
**Fix:** Load active `WatchItem`s (via DB session or passed state) inside `node_missing_signal` and evaluate monitoring windows against them; make the E2E assertion check that the confirmed watch item drives the watch evaluation (e.g., expected-event window derived from the confirmed rule).

### WR-08: Auto-recalibration trigger (D-06) is not implemented — `recalibration_triggered` is dead signaling

**File:** `backend/app/services/calibration.py:150,158`
**Issue:** D-06 locks "auto-recalibrate after N unapplied feedback rows for a role, plus a 'Recalibrate now' button". The service only sets the `recalibration_triggered` boolean; no code in the backend or frontend ever acts on it, and the underlying count never resets (CR-01). The manual button works, but the auto trigger never fires.
**Fix:** After resolving CR-01, invoke `recalibrate_role` (or enqueue it) when `unapplied_count >= N`, or remove the flag and the D-06 auto claim.

### WR-09: `CalibrationHistory` stores only the partial weight matrix — versioned-state reconstruction is impossible

**File:** `backend/app/services/calibration.py:332-344`
**Issue:** The history snapshot records only the functions updated in the current run (`updated_weights_list`). When recalibrating a single role — or when only some roles have feedback — earlier versions' full matrices are not preserved, so a consumer cannot reconstruct the complete system state at `v1.0.1` despite the release notes claiming immutable "active weight matrices" per version.
**Fix:** Snapshot the full matrix per version: merge `active_weights` with the updated weights before writing `CalibrationHistory.weights`.

## Info

### IN-01: Dead variable — `weights_modified` computed but never used

**File:** `backend/app/services/calibration.py:254, 277-278`
**Issue:** `weights_modified` is set when weights change but never read; a neutral-feedback recalibration still writes a history entry and bumps the version.
**Fix:** Use it to short-circuit history/version writes when no weight changed, or remove it.

### IN-02: Unused imports in `calibration.py`

**File:** `backend/app/services/calibration.py:5, 15`
**Issue:** `Any` (typing) and `Signal` (models) are imported but never referenced in the file.
**Fix:** Remove both imports.

### IN-03: `node_calibrate`'s persistent-session branch is unreachable in the graph

**File:** `backend/app/workflows/nodes/calibrate.py:30-56`
**Issue:** LangGraph invokes `node_calibrate(state)` with a single positional argument (graph.py:43), so `session` is always `None` in production and the persistence branch (submit feedback + `recalibrate_role()`) can only execute when called directly — meaning the "node_calibrate rewritten to persist via the service" integration point (CONTEXT code_context) is effectively dead in pipeline runs.
**Fix:** Wire a session into the graph node invocation (e.g., factory/closure in `build_graph`) or remove the dead branch.

### IN-04: Release notes factual inaccuracies

**File:** `docs/release/v5.1_RELEASE_NOTES.md:17, 13`
**Issue:** (a) "Regex Keyword Pattern Matcher" — `HeuristicWatchParser` uses substring matching, not regex; (b) "monitoring time windows (30-180 days)" — `KEYWORDS_MAP` includes 270-day windows (regulatory/label/filing); (c) "recording who triggered the run" — `CalibrationHistory` has no trigger-user field; (d) semver example "v1.1.0" — only patch-level bumps are implemented.
**Fix:** Align release-note wording with the implementation.

### IN-05: Debug artifact and silent failure in watch confirmation

**File:** `frontend/components/metaradar.tsx:1023`
**Issue:** `handleConfirmWatch` logs failures only via `console.error` and gives the user no feedback; combined with the zero-UUID fallback for missing `development_id` (line 1013, which triggers an FK violation → 500), a failed confirmation is invisible.
**Fix:** Surface the failure in the UI; validate `development_id` before submitting.

### IN-06: `/feedback/summary` returns only roles with feedback, contradicting its docstring

**File:** `backend/app/services/calibration.py:427-466`; `backend/app/api/v1/endpoints/feedback.py:55-56`
**Issue:** The endpoint docstring claims aggregation "across all six canonical stakeholder functions", but `get_summary` groups by functions present in `calibration_feedback` — roles with zero feedback are absent from the response.
**Fix:** Union the canonical function list into the aggregation, or correct the docstring.

---

_Reviewed: 2026-08-18_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_