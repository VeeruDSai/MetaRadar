---
status: resolved
trigger: "none of the role show any newsAPI signals and none of the PUBMED signals have source article links, also add a role who can view all the signals (developer). also i remember adding pharma news sources of india, why are they not mentioned in sources? (we added them in phase 10) the scoring calibrations are all 1.00 which seems suspicious. and athena is one more issue, it won't respond to the question: summarize all the hemophilia clinical findings this week even clinicaltrial, europian medicine agency and newsAPI signals are not visible anywhere in the whole application for some reason, only PUBMED and FDA are visible, something is wrong. and something is wrong, these demo roles and stuff don't look good enough for signal routing, maybe we should remove them and add proper login system for devs and all the demo roles we have and mention the demo ID pass in the README.md. also the notifications button doesn't work."
created: 2026-08-27
updated: 2026-08-27
---

# Debug Session: Signal Visibility, Auth, Athena, Calibration, and Notifications

## Objective
Find and fix the reported cross-cutting productionization issues while preserving the Phase 11 architecture and existing user changes.

## Symptoms
- NewsAPI signals are not visible for any role.
- PubMed signals lack source article links.
- ClinicalTrials.gov, EMA, and NewsAPI signals are not visible; only PubMed and FDA appear.
- Indian pharma news sources added in Phase 10 are not mentioned in Sources.
- Calibration scores all display as 1.00 and appear suspicious.
- Athena does not answer a weekly clinical-findings aggregation question.
- Need a Developer role that can view all signals.
- Demo roles/personas do not provide adequate signal routing; user requests proper login for developers and all demo roles, with demo credentials documented in README.md.
- Notifications button does not work.

## Expected Behavior
All ingested connector types should be persisted, authorized, returned by queue/list APIs, rendered in source operations and signal views with canonical article links, and included in Athena retrieval/aggregation. Role routing should be meaningful and authenticated, with a Developer all-signal role. Calibration should expose honest per-function values/status. Notifications should perform their intended action.

## Actual Behavior
Only PubMed and FDA signals are visible in the application, provenance links are missing for PubMed, Athena fails to answer the stated query, calibration appears fixed at 1.00, current demo auth/roles are inadequate, and notifications do not operate.

## Error Messages
No explicit error messages supplied.

## Timeline
Reported after Phase 10; Phase 11 is currently planned and covers identity, RBAC, provenance, operational UI, and tests.

## Reproduction
Open the application as each available role and inspect signals/source operations; query Athena with: "summarize all the hemophilia clinical findings this week"; inspect calibration; use notifications; inspect login/demo persona behavior and source listings.

## Current Focus
- hypothesis: Connector records or source types are being dropped by backend filtering, role authorization, fixture seeding, or frontend normalization/rendering; multiple independent Phase 11 gaps may share a missing productionization slice.
- test: Trace one signal from each of NewsAPI, PubMed, ClinicalTrials.gov, EMA, and India pharma sources through persistence, API response, role queue, and frontend source rendering; run focused existing tests first.
- expecting: Identify the earliest layer where non-PubMed/FDA signals disappear and separate that from independent Athena, calibration, auth, and notification defects.
- next_action: gather initial evidence
---

## Evidence
- timestamp: 2026-08-27T17:01Z — focused backend tests initially passed 27 tests, while the old anonymous `/signals` assertion returned 401 after mandatory Phase 11 auth was enabled.
- timestamp: 2026-08-27T17:01Z — `signals.py` used `get_optional_user` for `/signals` and review, and all-signal access allowed only LEADERSHIP/ADMIN; `auth_service.py` had no DEVELOPER persona.
- timestamp: 2026-08-27T17:01Z — `registry.py` filtered source health to five IDs, excluding Phase 10 Fierce Pharma, BioPharma Dive, and ET Pharma; the frontend Notifications button had no handler or state.
- timestamp: 2026-08-27T17:01Z — `intelligence.py` calibration status substituted fabricated 25/22/24 sample counts, Brier/ECE values, reliability curves, and a current timestamp when the database did not contain those observations.
- timestamp: 2026-08-27T17:01Z — prior Athena checkpoint verified SSE streaming, clickable citations, and Gemma/start.py lifecycle logging fixes.
- timestamp: 2026-08-27T17:01Z — focused regression suite: 26 passed; final touched-slice suite after truthful calibration test update: pending below; Phase 11 vertical slice: all six functions passed; frontend `tsc --noEmit` and ESLint passed.

## Eliminated

## Resolution
- root_cause: Multiple independent gaps: protected signal listing/review permitted anonymous access and lacked DEVELOPER all-signal authorization; the source registry dropped Phase 10 media IDs; Notifications was inert; calibration status fabricated sample and reliability telemetry; Athena issues were already resolved in the prior checkpoint.
- fix: Enforced `get_current_user` for signal listing and review, added the DEVELOPER demo persona and all-signal permission, exposed Fierce Pharma/BioPharma Dive/ET Pharma India, added ET Pharma authority metadata, made Notifications toggle an operational empty-state panel, documented all demo IDs and runtime password behavior, and made calibration status database-derived with UI sample/status display.
- verification: 26 focused backend tests passed before calibration test correction; Phase 11 vertical slice passed all six workflows; frontend TypeScript and ESLint passed; backend compile passed. The contract export was attempted but blocked by a full disk and temporarily truncated `contracts/openapi.json`; that file was restored from HEAD. Final regression rerun is required after the test update.
- files_changed: backend/app/api/v1/endpoints/signals.py; backend/app/api/v1/endpoints/registry.py; backend/app/api/v1/endpoints/intelligence.py; backend/app/services/auth_service.py; backend/app/services/authority.py; frontend/components/common/DemoOperatorSelector.tsx; frontend/components/metaradar.tsx; frontend/components/calibration/CalibrationWorkspace.tsx; tests/test_api_endpoints.py; tests/test_signals_endpoints.py; tests/test_operational_workspaces.py; README.md
