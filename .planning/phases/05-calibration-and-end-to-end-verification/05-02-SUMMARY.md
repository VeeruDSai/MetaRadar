# Plan 05-02 Summary: Curated Hemgenix Demo Dataset, node_calibrate Service Wiring & Scripted E2E Scenario Test

## Overview
Curated the high-fidelity synthetic demo dataset in `data/synthetic_signals.json` reproducing the flagship "Hemgenix 3-Year Durability Shift" scenario across scientific publications, competitor announcements, and congress abstracts. Connected `node_calibrate` to `StakeholderCalibrationService` supporting both live session persistence and in-memory test execution, and implemented the automated scripted end-to-end scenario test in `tests/test_e2e_calibration_scenario.py`.

## Key Changes
- `data/synthetic_signals.json`:
  - Signal 1 (PubMed / NEJM): HOPE-B 3-year durability follow-up of etranacogene dezaparvovec (36.7% mean FIX activity, 64% ABR reduction, secondary antibody titer & FIX decline).
  - Signal 2 (CSL Behring Commercial Announcement): 3-year commercial durability claiming 88% prophylaxis displacement and HEOR congress preparations.
  - Signal 3 (ASH 2026 Congress Abstract): Direct comparative registry analysis benchmarking single-dose AAV gene therapy against subcutaneous non-factor bispecifics (mim8 / concizumab / emicizumab).
- `backend/app/workflows/nodes/calibrate.py`:
  - Added dual execution support: when `session` is provided, automatically uses `StakeholderCalibrationService` to persist feedback, trigger batch recalibration, and update `SignalRouting` and `ScoringWeights`; when `session is None`, executes in-memory gradient calculation for backwards compatibility.
- `backend/app/providers/gemma.py`: Fixed `httpx.Timeout` constructor initialization (`httpx.Timeout(30.0, connect=5.0)`).
- `tests/test_e2e_calibration_scenario.py`:
  - 8-step automated end-to-end scenario test executing ingestion, pipeline convergence, baseline routing, simulated Regulatory persona feedback, batch recalibration, BEFORE vs AFTER comparison (0.88 -> 0.97, CRITICAL priority), heuristic watch-rule suggestion, and `node_missing_signal` evaluation.

## Verification Results
- `pytest tests/test_e2e_calibration_scenario.py -v`: 1 passed (100%).
- `pytest tests/test_intelligence_nodes.py -v`: 17 passed (100%).
- `pytest tests/test_calibration_service.py -v`: 5 passed (100%).
