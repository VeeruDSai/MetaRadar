---
phase: 05-calibration-and-end-to-end-verification
reviewed: 2026-08-18T14:45:00Z
depth: deep
files_reviewed: 10
files_reviewed_list:
  - backend/app/services/calibration.py
  - backend/app/api/v1/endpoints/feedback.py
  - backend/app/schemas/__init__.py
  - backend/app/workflows/nodes/calibrate.py
  - data/synthetic_signals.json
  - frontend/lib/api.ts
  - frontend/components/metaradar.tsx
  - frontend/app/globals.css
  - tests/test_calibration_service.py
  - tests/test_e2e_calibration_scenario.py
findings:
  critical: 0
  warning: 0
  info: 0
  total: 0
status: resolved
---

# Phase 5: Code Review & Remediation Report

**Reviewed:** 2026-08-18T14:45:00Z  
**Resolved:** 2026-08-18T14:45:00Z  
**Depth:** Deep Architecture & Quality Audit  
**Files Reviewed:** 10  
**Status:** resolved (All 5 review findings identified, remediated, and verified)

---

## Executive Summary

Conducted an end-to-end code review of Phase 5 (Calibration & End-to-End Verification), auditing:
- Stakeholder feedback ingestion and WORM audit logging
- Bounded mathematical batch recalibration ($\alpha=0.05, \text{center}=3.0, \text{clamp}=[0.1, 2.0]$)
- Heuristic regex keyword parsing for proactive watch-rule extraction
- Dual execution paths in `node_calibrate`
- High-fidelity synthetic Hemgenix 3-year durability dataset
- 8-step scripted end-to-end scenario test
- Frontend interactive feedback widget and BEFORE/AFTER comparison readout
- Contract drift and TypeScript type safety

All identified issues were classified, resolved, and verified against all automated gates.

---

## Findings & Applied Remediations

### 1. [CRITICAL] Telemetry Bias: Baseline Priority Hardcoded to "HIGH" in Comparisons
- **File:** `backend/app/services/calibration.py:405`
- **Finding:** In `recalibrate_role`, `BeforeAfterComparisonSchema` was instantiated with hardcoded `baseline_priority="HIGH"`, regardless of the actual underlying baseline score (`base_val`). If `base_val` was low (e.g. 0.35), the comparison diff erroneously claimed the baseline priority was `"HIGH"`.
- **Resolution:** Replaced hardcoded string with dynamic baseline priority calculation using unit weights ($0.6 \cdot \text{base\_val} + 0.4 \cdot 0.8$):
  - $\ge 0.75 \rightarrow \text{"CRITICAL"}$
  - $\ge 0.50 \rightarrow \text{"HIGH"}$
  - $\ge 0.30 \rightarrow \text{"MEDIUM"}$
  - $< 0.30 \rightarrow \text{"LOW"}$
- **Verification:** Unit tests and E2E scenario assertions verify exact computed baseline priorities.

### 2. [WARNING] Input Validation: Unrestricted `stakeholder_function` Strings
- **Files:** `backend/app/schemas/__init__.py:234`, `backend/app/api/v1/endpoints/feedback.py:75`
- **Finding:** Arbitrary string values were accepted for `stakeholder_function` in `FeedbackSubmissionRequest` and the `POST /api/v1/calibrate` query parameter. Submitting non-canonical roles could corrupt database aggregations.
- **Resolution:**
  - Added `@field_validator("stakeholder_function")` to `FeedbackSubmissionRequest` enforcing membership in the 6 canonical roles (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`, `LEADERSHIP`).
  - Added explicit validation in `trigger_recalibration` returning `HTTP_400_BAD_REQUEST` on invalid query parameters.
- **Verification:** Added test cases in `tests/test_calibration_service.py` asserting `422 Unprocessable Entity` and `400 Bad Request` responses on invalid inputs.

### 3. [WARNING] Async Mock Telemetry: Unawaited Coroutine Runtime Warnings in Tests
- **Files:** `tests/test_calibration_service.py`, `tests/test_e2e_calibration_scenario.py`
- **Finding:** Mocking `mock_db = AsyncMock()` caused synchronous SQLAlchemy `session.add()` calls to return coroutines, producing 10 `RuntimeWarning: coroutine was never awaited` warnings during test runs.
- **Resolution:** Explicitly configured `mock_db.add = MagicMock()` across all test fixtures.
- **Verification:** `pytest -v` runs with 0 warnings.

### 4. [WARNING] Frontend Robustness: Non-UUID Signal ID Fallback Guard
- **File:** `frontend/components/metaradar.tsx:979, 1013`
- **Finding:** If a demo or synthetic signal had a non-UUID ID (e.g. `"sig-1"`), sending it directly to `POST /api/v1/feedback` would fail backend Pydantic validation with a `422 Unprocessable Entity`.
- **Resolution:** Added `isValidUuid` regex helper in `SignalDrawer` before constructing the API payload.
- **Verification:** Frontend builds cleanly and handles synthetic signals without runtime 422 exceptions.

### 5. [INFO] Keyword Extraction: Word Boundary Matching in `HeuristicWatchParser`
- **File:** `backend/app/services/calibration.py:83`
- **Finding:** Simple substring searching (`kw in comment_lower`) risked false-positive keyword triggers on partial words.
- **Resolution:** Updated parser to use regex word boundaries `re.search(rf"\b{re.escape(kw)}\b", comment_lower)`.
- **Verification:** Verified in `test_heuristic_watch_parser_matches_keywords`.

---

## Final Verification Telemetry

| Quality Gate | Tool / Command | Telemetry | Status |
| :--- | :--- | :--- | :--- |
| **Backend Unit & Regression** | `pytest -v` | 71 passed, 1 skipped, 0 warnings in 45.59s | **PASSED** |
| **E2E Scenario Execution** | `pytest tests/test_e2e_calibration_scenario.py` | 1 passed (100%) | **PASSED** |
| **Contract Synchronization** | `pytest tests/test_contract_drift.py` | 0 schema drift | **PASSED** |
| **TypeScript Typecheck** | `tsc --noEmit` | 0 errors | **PASSED** |
| **Next.js Production Build** | `npm run build` | Compiled in 1.9s, static pages generated | **PASSED** |
| **ESLint Static Analysis** | `npm run lint` | 0 warnings or errors | **PASSED** |