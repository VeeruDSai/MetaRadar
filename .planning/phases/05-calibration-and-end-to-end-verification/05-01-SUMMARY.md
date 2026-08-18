# Plan 05-01 Summary: Stakeholder Calibration Service, WORM Feedback API & Contract Synchronization

## Overview
Implemented the persistent `StakeholderCalibrationService` in `backend/app/services/calibration.py` and connected the FastAPI `/api/v1` feedback and calibration endpoints (`/feedback`, `/feedback/summary`, `/calibrate`, `/calibration/weights`, `/watch-items/confirm`). Implemented bounded batch weight recalibration ($\alpha=0.05, \text{center}=3.0, \text{clamp}=[0.1, 2.0]$), immutable baseline routing preservation in `signal_routing`, deterministic heuristic keyword watch-rule parsing (`HeuristicWatchParser`), and zero-drift OpenAPI/TypeScript contract synchronization.

## Key Changes
- `backend/app/schemas/__init__.py`: Added explicit Pydantic schemas:
  - `FeedbackSubmissionRequest`, `FeedbackSubmissionResponse`
  - `RoleWeightSchema`, `CalibrationWeightsResponse`
  - `WatchRuleSuggestionSchema`, `BeforeAfterComparisonSchema`, `RecalibrateResponse`
  - `FeedbackRoleSummarySchema`, `FeedbackSummaryResponse`
  - `ConfirmWatchItemRequest`, `ConfirmWatchItemResponse`
- `backend/app/services/calibration.py`:
  - `HeuristicWatchParser`: Deterministic regex/keyword scanner extracting expected congress/trial/durability events and monitoring windows (90/180/270 days) without external LLMs.
  - `StakeholderCalibrationService`: Manages append-only WORM `calibration_feedback`, versioned semver `calibration_history`, `scoring_weights`, `signal_routing` recomputation, and `watch_items` creation.
- `backend/app/api/v1/endpoints/feedback.py`: FastAPI router implementing all 5 calibration and feedback routes.
- `backend/app/main.py`: Registered `feedback.router` under prefix `/api/v1`.
- `scripts/export_openapi.py`: Regenerated `contracts/openapi.json` and `frontend/types/api.ts` (0 schema drift).
- `tests/test_calibration_service.py`: Added 5 unit and integration tests covering parser heuristics, feedback submission, weight seeding, bounded math recalibration, and API endpoints.

## Verification Results
- `pytest tests/test_calibration_service.py -v`: 5 passed (100%).
- `pytest tests/test_contract_drift.py -v`: 1 passed (0 schema drift).
- `scripts/export_openapi.py`: Clean export to `contracts/openapi.json` and `frontend/types/api.ts`.
