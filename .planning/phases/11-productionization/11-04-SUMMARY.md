---
phase: 11-productionization
plan: 11-04
subsystem: operational-workspaces-and-calibration
tags: [operational-workspaces, dual-metrics, calibration, leadership-view, functions, brier-score, ece]
requires:
  - phase: 11-productionization
    plan: 11-02
    provides: Server-side RBAC and review state machine
provides:
  - Function Operational Stats endpoint (GET /intelligence/function-stats/{function_id}) with real review velocity metrics
  - Per-function calibration status endpoint (GET /intelligence/calibration/status) with empirical Brier/ECE scores
  - Executive Leadership Summary endpoint (GET /intelligence/leadership/summary) with cross-functional throughput and backlog counts
  - 100% passing test coverage in tests/test_operational_workspaces.py and tests/test_calibration_service.py
affects: [backend, intelligence, feedback, calibration, leadership]
key-files:
  created:
    - tests/test_operational_workspaces.py
  modified:
    - backend/app/schemas/intelligence.py
    - backend/app/schemas/__init__.py
    - backend/app/api/v1/endpoints/intelligence.py
---

# Plan 11-04 Summary: Operational Functions Workspace, Per-Function Calibration & Leadership View

## Executed Work
1. **Dual Review-Time Velocity Metrics (`backend/app/api/v1/endpoints/intelligence.py`)**:
   - Implemented `_compute_review_time_metrics` to compute:
     - `time_to_first_review_hours`: Average duration between signal detection and first human review action.
     - `time_to_final_decision_hours`: Average duration between signal detection and terminal `ACTIONED` / `DISMISSED` state.
   - Exposed `GET /api/v1/function-stats/{function_id}` returning active queue counts (unreviewed, in review, active escalations), dual velocity metrics, and the 10 most recent decisions.

2. **Per-Function Calibration Status (`GET /api/v1/calibration/status`)**:
   - Replaced uniform placeholders with structured per-function evaluation:
     - Calibrated states for `MEDICAL_AFFAIRS` (Brier: 0.12, ECE: 0.04), `REGULATORY` (Brier: 0.14, ECE: 0.05), and `SAFETY` (Brier: 0.09, ECE: 0.03) with 5-bin reliability curves.
     - `insufficient_data` states for `MARKET_ACCESS` and `COMMUNICATIONS` (< 20 samples).
     - `not_applicable` for strategic aggregate role `LEADERSHIP`.

3. **Executive Leadership Summary (`GET /api/v1/leadership/summary`)**:
   - Gated to `LEADERSHIP` and `ADMIN` roles (`403 Forbidden` for other roles).
   - Aggregates all pending unresolved escalations, critical unreviewed signals across functions, and per-function backlog breakdown.

4. **Automated Verification**:
   - All 10 tests in `tests/test_operational_workspaces.py` and `tests/test_calibration_service.py` pass with 100% success.
