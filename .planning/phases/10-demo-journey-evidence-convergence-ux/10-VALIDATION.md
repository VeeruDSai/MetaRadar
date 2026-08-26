---
phase: 10
slug: demo-journey-evidence-convergence-ux
status: planned
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-27
---

# Phase 10 — Validation Strategy

> Verification matrix, Nyquist compliance gates, and test strategy for Phase 10 (Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement).

---

## Executable Verification Gates

| Gate ID | Target / Focus | Command | Passing Criteria |
|:---|:---|:---|:---:|
| **GATE-10-01** | Backend Test Suite | `pytest tests/ -v -m "not live"` | 100% tests pass (140+ tests), 0 failures |
| **GATE-10-02** | BioPharma Dive Connector Test | `pytest tests/test_connector_health.py -v -k "biopharmadive"` | BioPharma Dive passes parsing & registration |
| **GATE-10-03** | NewsAPI Quota Governor Test | `pytest tests/test_connector_health.py -v -k "quota"` | Quota threshold state transitions verified |
| **GATE-10-04** | Tailwind CSS Token Gate | `node scripts/check-banned-classes.mjs` | 0 violations across all frontend files |
| **GATE-10-05** | Next.js 16 Production Build | `npm --prefix frontend run build` | 0 TypeScript errors, clean Turbopack build |
| **GATE-10-06** | Contract Parity Sync | `python scripts/export_openapi.py` | `contracts/openapi.json` & `api.ts` synced |

---

## 5 Brutal Real-World Verification Scenarios

```
Scenario A: Full Signal Journey
Ingest Signal ──► Calculate Priority ──► Route to Queue ──► Demo Operator Review ──► Persist Action ──► Verify AuditLog

Scenario B: Evidence Convergence
Fierce/ET Discovery ──► ClinicalTrials.gov Validation ──► Confluence Detection ──► Convergence Tree UI Rendered

Scenario C: Idle Sync
Connector Runs ──► 0 New Records ──► Status = HEALTHY (NO_NEW_DATA) ──► No Error Logged

Scenario D: Graceful Outage
Simulate Feed Timeout ──► Status = DEGRADED ──► Scheduler Continues Other 7 Feeds Unaffected

Scenario E: Provenance Invariant
Scan All Rendered Links ──► 0 Generic Portals (newsapi.org/register, fda.gov, ema.europa.eu blocked)
```

---

## Requirement Traceability Matrix

| Req ID | Description | Verifying Test / Check |
|:---|:---|:---|
| **REQ-P10-01** | `BioPharmaDiveRSSConnector` parses `biopharmadive.com/feeds/news/` and filters by keywords | `tests/test_connector_health.py` |
| **REQ-P10-02** | BioPharma Dive registered in `haemophilia.yaml` under `tier_3_discovery` with active status | `tests/test_ingestion.py` |
| **REQ-P10-03** | Adaptive NewsAPI quota governor in `SourceScheduler` throttles polling when quota < 40 | `tests/test_connector_health.py` |
| **REQ-P10-04** | Source health endpoints and UI expose `quota_remaining` for quota-limited connectors | `tests/test_api_endpoints.py` |
| **REQ-P10-05** | `EvidenceConvergenceWidget` renders multi-source convergence with authoritative vs discovery badges | `npm --prefix frontend run build` |
| **REQ-P10-06** | "Why This Signal?" explainer breaks down additive priority score factors | `npm --prefix frontend run build` |
| **REQ-P10-07** | "What Could Invalidate This?" displays Red-Team counter-factual criteria | `npm --prefix frontend run build` |
| **REQ-P10-08** | `SignalCard` and `SignalDetailWorkspace` render explicit source hierarchy badges | `node scripts/check-banned-classes.mjs` |
| **REQ-P10-09** | Dashboard hero view provides daily executive intelligence briefing metrics | `npm --prefix frontend run build` |
| **REQ-P10-10** | Zero hardcoded Tailwind colors or banned utility classes in new components | `node scripts/check-banned-classes.mjs` |
| **REQ-P10-11** | All 5 brutal validation scenarios (A–E) pass end-to-end | `tests/test_signal_routing_workflow.py` |
