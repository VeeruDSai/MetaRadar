---
status: resolved
trigger: "/gsd-debug why are most signals in signals tab 'test fixture' and not 'live intelligence'? Ingested 39 newsapi + 1 pubmed records, but signals tab showed 0 live signals."
created: 2026-08-29
updated: 2026-08-29
---

# Debug Session: Bronze Record Content Normalization & Promotion to Live Signals

## Symptoms
1. On platform startup and sync, live connectors (such as NewsAPI and PubMed) successfully ingested 40+ bronze records into `raw_signals_bronze`.
2. However, the Signals page rendered 100% "test fixture" synthetic signals, and zero live intelligence signals were created.
3. Database inspection revealed 444 bronze records in `raw_signals_bronze`, but only 3 live signals in `signals` (and 111 synthetic fixture signals).

## Root Cause Analysis
1. **Schema Mismatch Between Connector Payloads and `node_validate`**:
   - Each live connector stores text under source-specific keys:
     - `pubmed` stores abstract in `"abstract"` / `"abstract_raw"`.
     - `newsapi` stores body in `"description"` / `"article"` / `"evidence_text"`.
     - `clinical_trials` stores descriptions in `"study"`.
     - `biopharmadive` / `fda` store summary in `"description"` / `"evidence_text"`.
   - `node_validate` checked `content = str(sig.get("content") or "").strip()` and `if len(content) < 50: continue`.
   - Because `raw_payload` did not have an explicit `"content"` key, `content` evaluated to empty string `""` (0 chars), causing `node_validate` to silently discard 100% of all real ingested bronze signals.
   - When the bronze batch resulted in 0 validated signals, the pipeline finished with `signals_created = 0` while still stamping `pipeline_run_id` on the bronze records.
   - The only signals that ever passed `node_validate` were from `synthetic_signals.json` (which had hardcoded `"content"` keys).

## Key Changes & Fixes Applied
1. **Payload Normalization in [backend/app/workflows/runner.py](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/workflows/runner.py)**:
   - When querying `raw_signals_bronze`, extracts and sets `"content"` from `"abstract"`, `"description"`, `"evidence_text"`, `"study"`, or `"title"`.
   - Populates `"is_synthetic": False` and `"data_mode": "live"`.
2. **Defensive Extraction in [backend/app/workflows/nodes/validate.py](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/workflows/nodes/validate.py)**:
   - Evaluates `content` fallback hierarchy across `content -> abstract -> description -> evidence_text -> study -> title`.
   - Preserves `is_synthetic` and `data_mode` on validated signal dictionaries.
3. **Reset and Batch Promotion of Bronze Records**:
   - Cleared stale `pipeline_run_id` stamps from previously dropped bronze records.
   - Ran pipeline promotion to convert live bronze records into live intelligence signals.

## Verification Evidence
- **Database Telemetry**: Live signals increased from 3 to 28+ verified live signals with `is_synthetic: False` and `data_mode: "live"`.
- **Node Tests**: 17/17 passed (`pytest tests/test_intelligence_nodes.py -v`).
- **Frontend Typecheck**: `npx tsc --noEmit` passed with 0 errors.
