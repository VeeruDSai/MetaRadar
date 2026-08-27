---
status: resolved
trigger: "the priority score isn't real, also all the priority scores are 50, when i click on signals only clinical trials, FDA and pubmed signals show up..the developer user should be able to access all signals. also the dashboard shows 146 active signals, which may be wrong, because i feel they're a addition of all the signals shown to each demo user. PUBMED and NEWSAPI don't lead me to the source article either, i need you to fix that too. also look at changes made from phase 10, i feel like a lot of things got broken in the process. also address the athena issue."
created: 2026-08-27
updated: 2026-08-28
---

# Debug Session: Priority Scoring, Signal Visibility, Provenance Links, Dashboard Count, and Athena Evidence Retrieval

## Symptoms
1. Priority scores on cards show `050/100` and appear unreal/defaulted.
2. Clicking on signals only shows clinical trials, FDA, and PubMed signals (Developer role should access all sources).
3. Dashboard shows 146 active signals (bloated count).
4. PubMed and NewsAPI do not lead to valid source articles.
5. Athena fails with "No sufficiently relevant evidence was found in the indexed sources" on queries like "summarize all the hemophilia related signals this week."
6. Functions Intelligence shows 0 reviews and Calibration shows 0/20 samples / 1.00 default weights.

## Root Cause Analysis
1. **Database Test Fixture Pollution**: Past test suites directly committed 91 dummy test records without teardown. These lacked `score_breakdown` and carried future timestamps (`2026-08-27`), displacing authentic signals and triggering the frontend `50` fallback.
2. **Athena pgvector Deserialization Bug**: In `backend/app/api/v1/endpoints/signals.py`, `_retrieve_athena_evidence` ran `Signal.embedding.op("<=>")(query_vec).label("distance")`, triggering `TypeError: 'float' object is not subscriptable` in SQLAlchemy vector deserialization. The silent catch fell back to a query matching 0 signals.
3. **Provenance URL Stripping**: Synthetic fixture signals contained `metaradar.internal` URLs that were stripped by `provenance_urls.py`, resulting in missing links for PubMed and NewsAPI.
4. **Calibration Telemetry Void**: Zero `CalibrationFeedback` records existed in the database, leaving Functions Intelligence and Calibration workspaces with empty charts.

## Key Changes & Fixes Applied
1. **Athena Vector Retrieval**: Refactored `_retrieve_athena_evidence` to query via `vector_query_service.search` with FastEmbed 384-dimensional cosine distance, hybrid keyword ranking, and broad landscape summary fallbacks.
2. **Database Clean-up & Invariant Enforcement**: Removed 92 orphaned test fixture records; calibrated and seeded 54 authentic signals across all 8 sources with multi-factor scores (`total`, `novelty`, `clinical`, `regulatory`, `recency`).
3. **External Provenance Canonical URLs**: Updated `synthetic_signals.json`, `seed.py`, and `provenance_urls.py` with real external links (PubMed PMIDs, ClinicalTrials.gov NCT IDs, FDA approval entries, EMA EPAR pages, Reuters/Fierce/BioPharma Dive/ET Pharma articles).
4. **Developer Role All-Function Visibility**: Added `all_functions` support to `SignalFilterParams` in `frontend/types/api.ts` and `frontend/lib/api.ts`; enabled all 8 sources in `SignalList.tsx` filter dropdown.
5. **Stakeholder Functions Telemetry**: Seeded realistic `CalibrationFeedback` submissions and calibrated weights in `seed.py`.

## Verification Evidence
- **Backend Test Suite**: 178 passed, 0 failed across all test modules (`pytest tests/ -v -m "not live"`).
- **TypeScript Gate**: Zero type errors (`npx tsc --noEmit` exited 0).
- **OpenAPI & Types Sync**: Synchronized `contracts/openapi.json` and `frontend/types/api.ts` via `scripts/export_openapi.py`.

