# Phase 5: Calibration & End-to-End Verification - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 5-calibration-and-end-to-end-verification
**Areas discussed:** Weight-update math, Recalibration trigger & API, Watch-rule from comments, Frontend scope in Phase 5

---

## Weight-update math

| Option | Description | Selected |
|--------|-------------|----------|
| Per-factor weights | relevance_rating → impact_weight, urgency_rating → urgency_weight, action_appropriate → action-affecting logic; matches ScoringWeights columns | ✓ |
| Single composite weight | Keep node_calibrate's one per-function weight (α=0.05, clamp [0.1,2.0]) | |
| Batch recalibration | recalibrate() aggregates all unapplied feedback for a role into one versioned delta | ✓ |
| Online gradient | Each feedback immediately nudges weights | |
| Calibrated priority recompute | priority = w_impact·impact + w_urgency·urgency + w_novelty·novelty with calibrated weights | ✓ |
| Routing-only adjustment | Calibration affects Q3 routing only, priority stays baseline | |
| Neutral 1.0 seed | ScoringWeights initializes all functions to 1.0; calibration is the differentiator | ✓ |
| Matrix-derived seed | Derive initial weights from config/haemophilia.yaml baseline_routing_matrix | |

**User's choice:** Per-factor weights; Batch recalibration; Calibrated priority recompute; Neutral 1.0 seed
**Notes:** All three recommended options selected. Calibration must visibly change priority, routing AND action per FR-2.8.3 expanded scope.

---

## Recalibration trigger & API

| Option | Description | Selected |
|--------|-------------|----------|
| Queue + explicit trigger | Feedback lands in WORM table; recalibration via POST /api/v1/calibrate | ✓ |
| Immediate auto-recalibrate | Each feedback runs recalibration in the same request | |
| Fixed small N + manual | Auto after N rows (e.g., 3) plus manual "Recalibrate now" button | ✓ |
| Manual only | Demo operator calls POST /api/v1/calibrate explicitly every time | |
| Configurable N | Threshold as env var | |
| Rich body + weights GET | {signal_id, stakeholder_function, relevance_rating, urgency_rating, action_appropriate, comments, user_id} + GET /api/v1/calibration/weights | ✓ |
| Minimal SRS-literal body | Strictly {signal_id, role, rating, reason, user_id} | |

**User's choice:** Queue + explicit trigger; Fixed small N + manual; Rich body + weights GET
**Notes:** Rich body selected to honor the per-factor dimensions locked in the weight-math area.

---

## Watch-rule from comments

| Option | Description | Selected |
|--------|-------------|----------|
| Heuristic keyword rules | Deterministic keyword/intent rules over the comment → WatchItem; falls through to manual-review flag | ✓ |
| LLM intent parsing | Use Gemma/Grok to extract watch intent; nondeterministic, provider-dependent | |
| Structured checkboxes only | No free-text magic; structured form fields map 1:1 to WatchItem | |
| Confirm before activate | Watch suggestion appears in BEFORE/AFTER; stakeholder confirms before active | ✓ |
| Auto-activate on recalibration | Recalibration auto-creates WatchItem immediately | |
| Development-linked watch | Attaches to the signal's development/asset chain; reuses watch_items + node_missing_signal | ✓ |
| Signal-scoped only | Standalone watch on the signal card only | |

**User's choice:** Heuristic keyword rules; Confirm before activate; Development-linked watch
**Notes:** Deterministic parser keeps the calibration path free of LLM/provider dependencies. Confirm-before-activate preserves HITL fidelity. Development-linking enables the demo step-6 flow (congress evidence links into the same development chain, watch flips to new_evidence_detected).

---

## Frontend scope in Phase 5

| Option | Description | Selected |
|--------|-------------|----------|
| Backend + minimal feedback UI | StakeholderFeedbackWidget on Q3 role badges + BEFORE/AFTER readout, kept small | ✓ |
| Backend-only, UI deferred to Phase 6 | Full feedback UI lands in Phase 6 doc-to-UI mapping | |
| Full before/after readout | Rating widget + Recalibrate button + baseline-vs-calibrated panel + confidence uplift | ✓ |
| Rating widget only | Just the rating widget + role badge refresh | |
| Curated synthetic dataset | Extend data/synthetic_signals.json with the Hemgenix/mim8/emicizumab durability story | ✓ |
| Live connector pull | Pull live from PubMed/ClinicalTrials/NewsAPI during the demo | |
| Separate demo fixture | Dedicated demo scenario fixture module, not the production fallback | |
| Scripted E2E scenario test | Automated test/script running the full arc; runs in CI / on demand | ✓ |
| Manual demo guide only | Manual walkthrough documented as a release/runbook doc | |

**User's choice:** Backend + minimal feedback UI; Full before/after readout; Curated synthetic dataset; Scripted E2E scenario test
**Notes:** The demo REQUIRES visible calibration (FR-2.8.4/2.8.5, AC-14), so a minimal feedback widget ships in Phase 5 despite ROADMAP listing backend deliverables; full doc-to-UI parity remains Phase 6. Offline reproducibility prioritized over live connector pulls.

---

## the agent's Discretion

- calibration_version format; exact keyword rule set; exact N threshold (~3); delta/learning-rate constants; feedback summary response shape; widget placement in metaradar.tsx; whether the E2E test doubles as the demo runbook and release documentation shape.

## Deferred Ideas

- None — discussion stayed within phase scope.
