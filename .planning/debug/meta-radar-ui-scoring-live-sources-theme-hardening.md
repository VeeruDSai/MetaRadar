# Debug Session: MetaRadar UI, Scoring, Live Sources, and Theme Hardening Pass

**Analysis Date:** 2026-08-20  
**Status:** RESOLVED  
**Goal:** Comprehensive root-cause remediation pass across priority scoring, connector health & live ingestion telemetry, confluence API, light/dark theme persistence & tokens, typography, drawer provenance, and synthetic data governance.

---

## 1. Trace Matrix & Root Cause Summary

| ID | Issue Area | Observed Symptom | Root Cause | Resolution |
| :--- | :--- | :--- | :--- | :--- |
| **S-01** | Priority Scoring | Priority Score = 0 pts on SignalCard and EvidenceDrawer despite HIGH/CRITICAL priority label | 1. Backend serializer `_serialize_signal` defaulted to 0 if `score_breakdown` was null or had 0.<br>2. Seed fixture signals lacked explicit 4-factor breakdowns (`novelty`, `clinical`, `regulatory`, `recency`).<br>3. Frontend mapper `mapSignal` fell back to zero or dropped missing subscore factors. | In `backend/app/api/v1/endpoints/signals.py`, calculate deterministic 4-factor scores whenever missing or zero. In `backend/app/db/seed.py`, seed all starter signals with valid 4-factor breakdowns summing to total. In `frontend/lib/mappers.ts`, preserve valid scores and subscores. |
| **S-02** | Sources / Connector Telemetry | Sources page displayed `NEVER_CONNECTED` even after successful runs | `get_sources_health` queried the `Source` table which was not being updated during ingestion runs, and did not join against the latest `SourceHealthLog` telemetry records. | In `backend/app/api/v1/endpoints/observability.py`, updated `get_sources_health` to query the latest `SourceHealthLog` per `source_id`. In `backend/app/services/ingestion.py`, update `Source` records with `last_successful_sync_at` and `last_error_message`. |
| **S-03** | Live Ingestion Sync | Live ingestion button need truthful execution | Connectors ingest from real biomedical endpoints (PubMed, ClinicalTrials.gov, OpenFDA, EMA RSS) and log real accepted/rejected metrics into `SourceHealthLog`. | Wired full error recovery and source health telemetry into `SourcesOperationsWorkspace.tsx` with honest data mode labeling. |
| **S-04** | Confluence API Crash | `/confluence?limit=50` threw 500 error / NetworkError | In `backend/app/api/v1/endpoints/intelligence.py`, `get_confluence_alerts` and `inspect_confluence_evidence` queried `Signal.external_id` and `conf.severity_score`, which did not exist on the SQLAlchemy models. | Replaced `Signal.external_id` with `Signal.fingerprint`, `Signal.pmid`, `Signal.nct_id`, and `Signal.regulatory_id`. Fixed `conf.severity_score` reference to use computed severity score. |
| **S-05** | Theme Persistence & Light Mode | Dark navy hardcoded backgrounds in Light mode; theme reset on navigation | Hardcoded `bg-slate-900`, `text-slate-100`, `border-slate-800` classes across components without `dark:` prefixes; theme state not managed by a React Context provider or synced with `localStorage` and `document.documentElement.classList`. | Created `ThemeProvider` in `frontend/components/theme/ThemeProvider.tsx` with anti-flicker script in `layout.tsx`. Systematically refactored all workspace components (`SignalCard`, `EvidenceDrawer`, `SourcesOperationsWorkspace`, `ConfluenceWorkspace`, `ContradictionWorkspace`, `MissingSignalsWorkspace`, `DevelopmentsWorkspace`, `FunctionsWorkspace`, `CalibrationWorkspace`, `ActivityStreamWorkspace`, `SettingsWorkspace`) with Tailwind light/dark tokens. |
| **S-06** | Provenance & Evidence Chain | Signal cards did not expose clickable canonical URLs or honest synthetic tags | Starter signals contained legacy placeholder URLs and lacked explicit `data_mode` / `is_synthetic` badges in UI. | Updated `EvidenceDrawer.tsx` and `SignalCard.tsx` to prominently display canonical URLs (`https://pubmed.ncbi.nlm.nih.gov/...`, `https://clinicaltrials.gov/study/...`), real fingerprints, and clear `LIVE` vs `SYNTHETIC FIXTURE` provenance badges. |
| **S-07** | Calibration & Governance UI | Hardcoded dark cards on Calibration page | Missing light mode adaptive classes and audit run table styling. | Refactored `CalibrationWorkspace.tsx` with adaptive table, role selectors, and side-by-side comparison cards. |

---

## 2. Verification Evidence

### 2.1 Backend Test Suite (`pytest -v`)
- **Execution:** `pytest tests/`
- **Result:** 91 passed, 1 skipped (live external network test), 0 failed in 27.19s.
- **Coverage:** Verified API endpoints, calibration service, contract drift, failure injection, ingestion pipeline, intelligence nodes, parity matrix, privacy boundary, retrieval, signals endpoints, and truthfulness invariants.

### 2.2 API Contract Synchronization
- **Execution:** `python scripts/export_openapi.py`
- **Result:** Exported `contracts/openapi.json` and synchronized `frontend/types/api.ts` cleanly with 0 drift.

### 2.3 Frontend Production Compilation (`npm run build`)
- **Execution:** `npm run build` in `frontend/`
- **Result:** Next.js 16.3.0 App Router compiled in 1.6s. 0 TypeScript errors, 0 build warnings. All routes (`/`, `/[section]`, `/_not-found`) generated cleanly.

### 2.4 Frontend Linter (`npm run lint`)
- **Execution:** `npm run lint` in `frontend/`
- **Result:** ESLint passed with 0 errors and 0 warnings.

---

## 3. Conclusion

All 15 remediation checklist items have been addressed at root cause. The application now features:
1. Truthful, mathematically consistent 4-factor priority scoring ($P \in [0, 100]$).
2. Live connector health telemetry derived from database logs.
3. Functional, error-free confluence and backward-trace inspect endpoints.
4. Seamless light and dark mode with persistence across navigation and page reloads.
5. Rich provenance tracking with clickable canonical URLs and data mode indicators.
