# Phase 5: Calibration & End-to-End Verification - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement the persistent human-in-the-loop (HITL) Stakeholder Calibration Loop and complete the end-to-end demo story. Deliver:

1. **REQ-P5-1** — `StakeholderCalibrationService` for rating feedback & weight adjustment: feedback API (`POST /api/v1/feedback`, `GET /api/v1/feedback/summary`, `POST /api/v1/calibrate`, `GET /api/v1/calibration/weights`), per-factor batch weight recalibration with versioned baseline preservation, and watch-rule generation from feedback comments.
2. **REQ-P5-2** — Execute the end-to-end demo story (mim8 / emicizumab / Hemgenix durability data): a curated synthetic demo dataset reproducing the "Hemgenix 3-year durability shift" scenario, a scripted E2E scenario test driving the full arc (ingest → pipeline → baseline routing → feedback → recalibrate → BEFORE/AFTER → watch rule), and a minimal frontend calibration UI.
3. **REQ-P5-3** — Final Definition of Done audit: all executable quality gates green (pytest, tsc, eslint, next build, contract sync, docker compose config, CI) plus release documentation.

The calibration loop must produce a **visible BEFORE → stakeholder feedback → AFTER** comparison for the same signal (baseline never overwritten), change priority/routing/action/watch (expanded scope FR-2.8.3), and use persona-driven simulated feedback (never real organizational data).

</domain>

<decisions>
## Implementation Decisions

### Weight-update math
- **D-01:** **Per-factor weight updates** — `relevance_rating` → `impact_weight`, `urgency_rating` → `urgency_weight`, `action_appropriate` → action-affecting logic, matching the existing `scoring_weights` columns. Calibration can move priority AND routing independently.
- **D-02:** **Batch recalibration** — `StakeholderCalibrationService.recalibrate(role)` aggregates ALL unapplied feedback for a role into one versioned weight delta (per FR-2.9.2's reproducible BEFORE→AFTER and Master Plan §14.10 versioned history). Replaces `node_calibrate`'s online-gradient-per-feedback behavior.
- **D-03:** **Calibrated priority recompute** — priority is recomputed as `w_impact·impact + w_urgency·urgency + w_novelty·novelty` using per-function calibrated weights, so priority, routing AND action visibly change from one feedback set (FR-2.8.3 expanded scope).
- **D-04:** **Neutral 1.0 seed** — `ScoringWeights` initializes every function to 1.0 (current defaults); calibration is the ONLY differentiator between functions. The `baseline_routing_matrix` in `config/haemophilia.yaml` continues to drive initial primary/secondary routing and is NOT overridden by seed weights.

### Recalibration trigger & API
- **D-05:** **Queue + explicit trigger** — feedback always lands in the append-only WORM `calibration_feedback` table. Recalibration fires only via `POST /api/v1/calibrate` (manual button, or auto after small fixed N). One versioned BEFORE/AFTER per trigger.
- **D-06:** **Fixed small N (e.g., 3) + manual** — auto-recalibrate after N unapplied feedback rows for a role, plus a "Recalibrate now" button for the demo stage. Deterministic for a hackathon.
- **D-07:** **Rich feedback body + weights GET** — `POST /api/v1/feedback` accepts `{signal_id, stakeholder_function, relevance_rating, urgency_rating, action_appropriate, comments, user_id}` (honoring the three per-factor dimensions); `GET /api/v1/feedback/summary` aggregates per-role accuracy/ratings/trend; new `GET /api/v1/calibration/weights` exposes current weights. All contract changes flow through `scripts/export_openapi.py`. — **Reversibility:** costly — the feedback/calibrate endpoints and summary response are public API surface; undoing requires reverting the endpoint, exported OpenAPI contract, and generated TS types.

### Watch-rule from comments
- **D-08:** **Heuristic keyword rules** — deterministic keyword/intent rules parse feedback comments (e.g., "watch", "congress", "disclosure", "upcoming", "trial") into a structured `WatchItem` suggestion. Zero LLM dependency; non-matching comments fall through to a manual-review flag. — **Reversibility:** costly — the watch-rule parser and its output shape feed the calibration demo; a rewrite would change both the suggestion format and the confirmation UI.
- **D-09:** **Confirm before activate** — a parsed watch-rule suggestion appears in the calibration BEFORE/AFTER result; the stakeholder confirms it via the UI/API before the `WatchItem` is created/activated. Keeps the human-in-the-loop intact.
- **D-10:** **Development-linked watch** — the watch rule attaches to the signal's development/asset chain (`source_event → development → expected_event_type → monitoring window → responsible_function`), reusing the existing `watch_items` table and `node_missing_signal` monitoring. Later congress evidence links into the SAME development chain via confluence and flips status to `new_evidence_detected` (demo scenario step 6).

### Frontend scope & demo
- **D-11:** **Backend + minimal feedback UI** — Phase 5 includes a minimal `StakeholderFeedbackWidget` on Q3 role badges (rating stars + optional comment + submit + confirmation banner), because the demo REQUIRES visible calibration (FR-2.8.4/2.8.5, AC-14). Kept deliberately small; the full doc-to-UI parity sweep remains Phase 6.
- **D-12:** **Full BEFORE/AFTER readout** — the calibration UI shows the rating widget + "Recalibrate" button + a baseline-vs-calibrated comparison panel (priority/function/action) + confidence uplift (e.g., "Regulatory 92% — up from 88% after calibration"), satisfying AC-14 and demo scenario step 8. Driven by the `signal_routing` baseline vs calibrated columns. — **Reversibility:** costly — tied to the canonical signal_routing contract and the exported TS types.
- **D-13:** **Curated synthetic demo dataset** — extend `data/synthetic_signals.json` with the Haemophilia demo story (PubMed paper on Hemgenix 3-year durability + CSL Behring press release + congress abstract + mim8/emicizumab/Hemgenix durability data) so the E2E scenario is reproducible offline, following the existing synthetic fallback pattern. Explicitly labeled synthetic (honest telemetry).
- **D-14:** **Scripted E2E scenario test** — an automated test/script running the full arc: ingest demo signals → pipeline run → baseline routing → submit persona feedback → recalibrate → assert BEFORE/AFTER change → watch rule created & confirmed. Runs in CI / on demand; this is the "demo scenario test" ROADMAP deliverable.

### the agent's Discretion
- `calibration_version` format (existing default `v1.0.0`; follow Master Plan §14.10 versioning).
- Exact keyword rule set for the watch-rule parser.
- Exact N threshold value (small, ~3).
- Delta/learning-rate constants (existing `node_calibrate` uses α=0.05, center baseline 3.0, clamp [0.1, 2.0] — keep or tune).
- Feedback summary response shape details and trend aggregation.
- Exact placement of the feedback widget within `frontend/components/metaradar.tsx` Q3 badges.
- Whether the E2E scenario test also doubles as the demo runbook, and the shape of the release documentation deliverable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Specifications (ROADMAP-mandated for Phase 5)
- `docs/2_SRS_Software_Requirements_Specification.md` §2.8 (Stakeholder Calibration Loop: FR-2.8.1 feedback submission, FR-2.8.2 summary, FR-2.8.3 expanded recalibration scope + mandatory BEFORE/AFTER demo, FR-2.8.4 simulated personas, FR-2.8.5 confidence display), §2.9.2 (Calibration Versioning — baseline never overwritten, train/test on separate records), §4.1 (API endpoint table), §3.5 (model-agnostic local AI context)
- `docs/METARADAR_MASTER_PLAN_v5.0.md` §3 (MVP scope), §9 (Demo Scenario — The Hemgenix 3-Year Durability Shift: full 8-step story), §12 (Domain Research), §14.10 (Scoring & Calibration Versioning — per-signal baseline vs calibrated), §14.2 (entity tables incl. `calibration`)
- `docs/4_UI_DESIGN_DOCUMENT.md` §15.3 (Stakeholder Feedback Widget — posts to `/api/v1/feedback`, N-row trigger, watch-for-next calibration demo), §15 (Four-Question display), §3/§4 (component hierarchy & data flow), §2 (scope note: HITL calibration loop)
- `docs/rules/DEFINITION_OF_DONE.md` — the full DoD gate list REQ-P5-3 verifies

### Engineering rules (quality gates & governance)
- `docs/rules/ENGINEERING_STANDARDS.md` — type safety, honest execution telemetry, no fabricated behavior
- `docs/rules/TESTING_STRATEGY.md` — mandatory executable testing gates (pytest, tsc, eslint, next build, contract sync)
- `docs/rules/ARCHITECTURE_RULES.md` — approved Next.js 16 + FastAPI + PostgreSQL 16 + Local Gemma stack (no silent architecture changes)
- `docs/rules/DATA_AND_PRIVACY_STANDARDS.md` — data classification & privacy boundary (Grok gate not involved in calibration path; simulated persona feedback only)
- `docs/rules/RELEASE_PROCESS.md` — release verification & deployment readiness (release documentation deliverable)

### Contract governance
- `contracts/openapi.json` — OpenAPI 3.1 schema snapshot; drift gate compares against it
- `frontend/types/api.ts` — canonical generated TS contract; MUST be regenerated via `scripts/export_openapi.py`, not hand-edited
- `scripts/export_openapi.py` — OpenAPI JSON + TypeScript contract generator; must stay 0-drift

### Domain & configuration
- `config/haemophilia.yaml` — `functions` list (six canonical stakeholder functions), `baseline_routing_matrix` (initial primary/secondary routing, unchanged by calibration per D-04)

### Existing code implementing the contracts
- `backend/app/models/__init__.py` — `CalibrationHistory`, `ScoringWeights` (impact/urgency/novelty per function), `SignalRouting` (baseline + calibrated columns + calibration_version), `CalibrationFeedback` (rich fields), `WatchItem` (5-state lifecycle), `AuditLog`
- `backend/app/workflows/nodes/calibrate.py` — `node_calibrate` (in-memory online gradient; Phase 5 replaces with persistent batch recalibration via the service)
- `backend/app/workflows/nodes/missing_signal.py` — `node_missing_signal` (watch monitoring consumer; new watch rules feed in)
- `backend/app/api/v1/endpoints/signals.py`, `health.py`, `pipeline.py`, `search.py` — endpoint patterns for new `feedback.py`/`calibrate` endpoints
- `backend/app/core/config.py` — env-driven `Settings` (new calibration config keys land here if needed)
- `data/synthetic_signals.json` — existing synthetic fallback dataset; extend with the demo story (D-13)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **DB schema already anticipates Phase 5:** `ScoringWeights` (per-function impact/urgency/novelty), `CalibrationFeedback` (relevance/urgency/action_appropriate/comments — exactly the rich body), `CalibrationHistory` (versioned weights JSONB — WORM audit), `SignalRouting` (baseline + calibrated side-by-side + calibration_version), `WatchItem` (5-state lifecycle). No migration needed for the core loop.
- **`node_calibrate` gradient math** (α=0.05, center baseline 3.0, clamp [0.1, 2.0]) — reusable as the batch delta function inside `StakeholderCalibrationService`.
- **`node_missing_signal`** — existing watch monitoring with the 5-state lifecycle; new watch rules created by calibration are consumed here.
- **Async FastAPI + Pydantic v2 + async SQLAlchemy patterns** across existing endpoints/services — model new feedback/calibrate endpoints and the service on these.
- **`config/haemophilia.yaml` `functions`** — canonical six stakeholder function IDs (MEDICAL_AFFAIRS, REGULATORY, SAFETY, MARKET_ACCESS, COMMUNICATIONS, LEADERSHIP).

### Established Patterns
- **Contract governance:** any new/changed endpoint MUST flow through `scripts/export_openapi.py` → `contracts/openapi.json` → `frontend/types/api.ts` to keep the contract-drift pytest green (D-07, D-12).
- **Strict quality gates:** `tsc --noEmit` 0 errors, ESLint flat config 0 errors, `next build` clean, `pytest -v` passing (REQ-P5-3).
- **Honest telemetry (AGENTS.md):** no fabricated behavior; demo data explicitly labeled synthetic (D-13); WORM append-only for `calibration_feedback`.
- **Async everything + fail-degrade design** — calibration endpoints must never take the whole app down.
- **Phase 4 hand-rolled frontend client** (`frontend/lib/api.ts`) — new feedback/calibrate/weights calls follow the same mapper + `useLiveData` polling pattern; no new data-fetching library.

### Integration Points
- New `backend/app/services/calibration.py` (`StakeholderCalibrationService`) — the core deliverable; consumed by new endpoints and by `node_calibrate` (persistence wiring).
- `node_calibrate` rewritten to persist via the service: update `ScoringWeights`, write `CalibrationHistory`, upsert `SignalRouting` calibrated columns, and create confirmed `WatchItem`s (D-08/09/10).
- New endpoints `backend/app/api/v1/endpoints/feedback.py` (+ `POST /api/v1/calibrate`, `GET /api/v1/calibration/weights`); registered in `main.py` (repo has no `router.py`).
- Frontend: Q3 role badges in `frontend/components/metaradar.tsx` gain the `StakeholderFeedbackWidget` + BEFORE/AFTER readout; `frontend/lib/api.ts` gains the three calibration calls.
- E2E demo test in `tests/` drives the full scenario arc (D-14), reusing the synthetic fallback dataset.

</code_context>

<specifics>
## Specific Ideas

- **The demo story is THE presentation:** Master Plan §9 "Hemgenix 3-year durability shift" — three signals (PubMed paper + CSL press release + congress abstract) → confluence → lifecycle (post-market durability tracking) → red-team → missing-signal → watch → four questions → calibrate. The calibration demo MUST reproduce BEFORE → feedback → AFTER for the same signal (FR-2.9.2) and visibly change priority, routing, action, and watch (FR-2.8.3).
- **User-locked choices:** per-factor weights; batch recalibration; calibrated priority recompute; neutral 1.0 seed; queue + explicit trigger; fixed small N + manual; rich feedback body + weights GET; heuristic keyword rules (not LLM) for watch parsing; confirm-before-activate watch; development-linked watch; minimal feedback UI in Phase 5; curated synthetic dataset; scripted E2E scenario test.
- **Six stakeholder functions (canonical):** Medical Affairs, Regulatory, Safety/PV, Market Access, Medical Communications, Leadership — personas only, simulated feedback (Master Plan §11.3).
- **Calibration never involves the external-LLM privacy gate** — it operates on internal ratings/weights; the watch parser is deterministic (D-08), so no provider dependency.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 5-Calibration & End-to-End Verification*
*Context gathered: 2026-08-18*
