---
phase: "06"
slug: full-doc-to-ui-mapping-feature-synchronization-automated-setup-py-and-start-py-launchers
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-18
validated: 2026-08-18
---

# Phase 06 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (Backend & Contracts) + TypeScript/Next.js compiler (Frontend) |
| **Config file** | `pytest.ini` / `frontend/package.json` |
| **Quick run command** | `pytest tests/test_contract_drift.py tests/test_api_endpoints.py tests/test_parity_matrix.py tests/test_launchers.py -v` |
| **Full suite command** | `pytest tests/ -v && npm --prefix frontend run build` |
| **Estimated runtime** | ~20 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_contract_drift.py tests/test_api_endpoints.py -v`
- **After every plan wave:** Run `pytest tests/ -v && npm --prefix frontend run build`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|:---|:---:|:---:|:---|:---|:---|:---:|:---|:---:|:---:|
| 06-01-01 | 01 | 1 | UI-PARITY-READS | T-06-01 | Read-only SQL sanitization | unit | `pytest tests/test_api_endpoints.py -k "intelligence or reads" -v` | ✅ | ✅ green |
| 06-01-02 | 01 | 1 | SIGNAL-FILTERS | T-06-02 | Safe parameter validation | unit | `pytest tests/test_signals_endpoints.py -v` | ✅ | ✅ green |
| 06-01-03 | 01 | 1 | CACHE-CLEAR | T-06-03 | Controlled cache invalidation | integration | `pytest tests/test_api_endpoints.py -k "cache_clear" -v` | ✅ | ✅ green |
| 06-01-04 | 01 | 1 | CONTRACT-EXPORT | — | Zero OpenAPI contract drift | regression | `pytest tests/test_contract_drift.py -v` | ✅ | ✅ green |
| 06-02-01 | 02 | 2 | PARITY-MANIFEST | — | Verified doc-to-code mapping | regression | `pytest tests/test_parity_matrix.py -v` | ✅ | ✅ green |
| 06-02-02 | 02 | 2 | INTEL-PAGES-UI | — | Type-safe React components | build | `npm --prefix frontend run build` | ✅ | ✅ green |
| 06-02-03 | 02 | 2 | GENERIC-REPLACE | — | No GenericPage regressions | build | `npm --prefix frontend run build` | ✅ | ✅ green |
| 06-03-01 | 03 | 3 | SETUP-PY | T-06-04 | Safe environment generation | cli | `pytest tests/test_launchers.py -k "setup" -v` | ✅ | ✅ green |
| 06-03-02 | 03 | 3 | START-PY | T-06-05 | Graceful process teardown | cli | `pytest tests/test_launchers.py -k "start" -v` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_parity_matrix.py` — automated parity matrix verification test
- [x] `docs/manifests/feature_parity_manifest.json` — baseline feature parity manifest
- [x] `scripts/generate_parity_matrix.py` — manifest to markdown generator script
- [x] `tests/test_launchers.py` — automated process launcher tests

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live Process Supervision & Graceful SIGTERM | START-PY | Interactive process orchestration | Run `python start.py`, verify table rendered in terminal, send Ctrl+C, ensure all child processes exit cleanly. |
| Ollama Model Auto-Pull | SETUP-PY | Heavy weight download test | Run `python setup.py --skip-models` and verify model check step. |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-18

---

## Validation Audit (2026-08-18)

| Metric | Count | Percentage |
|---|---|---|
| **Total Tasks Audited** | **9** | **100%** |
| **Gaps Found** | **0** | **0%** |
| **Automated Verification Pass Rate** | **9 / 9** | **100%** |
| **Pytest Full Suite Pass Rate** | **80 / 80** | **100%** |
| **Next.js 16 Build Status** | **Clean (0 errors)** | **100%** |
| **Nyquist Compliance** | **TRUE** | **100%** |
