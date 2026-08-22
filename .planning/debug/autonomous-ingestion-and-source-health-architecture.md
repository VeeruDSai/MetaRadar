# Debug Session: Continuous Autonomous Ingestion & Source Health Truthfulness Architecture

**Session ID**: `autonomous-ingestion-and-source-health-architecture`  
**Date**: 2026-08-22  
**Status**: `ROOT CAUSE CONFIRMED & PLAN FORMULATED`  
**Related Milestones**: `v5.1-extension`, `v5.2-autonomous-radar`

---

## 1. Symptoms & Problem Statement

### Reported Symptoms
1. **ClinicalTrials.gov degraded false alarm**:
   - `ClinicalTrials.gov` connector transitions from `HEALTHY` to `DEGRADED` whenever a query returns 0 new studies or 0 modified studies, even though the API is completely healthy and reachable.
   - ClinicalTrials.gov refreshes public data Mon–Fri ~9:00 AM ET and provides `dataTimestamp`; absence of new records in a 10-minute window is expected behavior, not degradation.
2. **Missing Autonomous Background Scheduler**:
   - Ingestion is only executed when an operator or the frontend calls `POST /api/v1/ingestion/run` or `POST /api/v1/pipeline/run`.
   - No continuous, independent persistent scheduler or worker exists to poll source APIs at their respective cadence.
3. **Frontend Ingestion Responsibility Coupling**:
   - The UI contains buttons to trigger live ingestion, coupling user browsing to system intelligence freshness.
4. **Adapter-Ready vs. Truly Live Connectors (FDA, EMA)**:
   - FDA and EMA adapters need full multi-feed coverage (openFDA drug endpoints, MedWatch RSS safety feeds, Drug Safety Communications, EMA EPARs, EMA medicine RSS feeds).
5. **Lack of Event/Change Detection & Source Hierarchy**:
   - Connectors ingest flat records without detecting lifecycle change events (`STATUS CHANGE`, `RECRUITMENT CHANGE`, `PRIMARY ENDPOINT CHANGE`, `RESULTS POSTED`, `COMPLETION`, `TERMINATION`).
   - All sources are treated equally without explicit 4-tier authority weighting (`Tier 1: Authoritative`, `Tier 2: High-Value`, `Tier 3: Discovery`, `Tier 4: Lead Only`).
6. **Telemetry & Artifact Hygiene**:
   - Need rich source run history (`run_id`, `connector_id`, `started_at`, `duration_ms`, `records_received`, `records_new`, `records_duplicate`, `cursor_before`, `cursor_after`, etc.).
   - Package manager lockfile duplication (`package-lock.json` alongside `pnpm-lock.yaml`) and legacy `frontend/src/` directory.

---

## 2. Investigation & Code Evidence

### Evidence Item 1: Conflation of "0 New Records" with "DEGRADED"
In [ingestion.py](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/services/ingestion.py#L79-L84):
```python
elif conn_fetched == 0:
    conn_status = "DEGRADED"
    error_msg = "; ".join(r.error_detail for r in conn_results if r.error_detail) or "0 records fetched"
elif conn_new == 0:
    conn_status = "DEGRADED"
    error_msg = "; ".join(r.error_detail for r in conn_results if r.error_detail) or "0 new records accepted (all duplicates or filtered)"
```
**Impact**: If a connector makes a successful HTTP 200 call but finds 0 new records since the last check, the system unconditionally marks the connector `DEGRADED`.

### Evidence Item 2: Connector Health Enum Over-simplification
In [models/__init__.py](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/models/__init__.py) & [health.py](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/api/v1/endpoints/health.py):
The current connector status only handles simple strings (`HEALTHY`, `DEGRADED`, `UNHEALTHY`, `CONFIGURATION_ERROR`, `NEVER_CONNECTED`).
It lacks:
- `CONNECTED` (API reachable)
- `HEALTHY` (API reachable + successful fetch within expected SLA)
- `NO_NEW_DATA` (API reachable + 200 OK + 0 new/changed records)
- `STALE` (connector hasn't run within expected SLA)
- `DEGRADED` (repeated partial failures, high latency, malformed responses)
- `FAILED` (repeated connection, auth, or 5xx failures)

### Evidence Item 3: Lack of In-Process Async Scheduler in Lifespan
In [main.py](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/main.py#L30-L48):
FastAPI `lifespan` initializes logging and domain config, but does not launch an `asyncio.Task` or background job runner (e.g., source scheduler loop with per-source intervals and backoff).

### Evidence Item 4: Legacy Folders & Lockfile Drift
- `frontend/package-lock.json` exists while `frontend/pnpm-lock.yaml` is the canonical lockfile.
- `frontend/src/app/sources/page.tsx` exists with hardcoded placeholder data from legacy iterations, whereas canonical Next.js App Router is located at `frontend/app/`.

---

## 3. Root Cause Analysis

1. **Ingestion Evaluation Logic**: Conflates "no updates from upstream provider" with "connector pipeline failure", leading to false yellow/red alerts on dashboards.
2. **Execution Model**: The backend lacks an integrated background polling worker / autonomous daemon loop with SLA intervals (`CT.gov`: 30–60m, `PubMed`: 60m, `FDA/EMA`: 30m, `News`: 15–30m) and adaptive backoff.
3. **Event Detection Gap**: Pipeline treats studies/articles as static blobs rather than diffing against previous states to generate structured event signals (`STATUS CHANGE`, `ENDPOINTS CHANGED`, etc.).
4. **Source Tiering Gap**: Downstream scoring and confluence do not differentiate Tier 1 Authoritative (FDA, EMA, CT.gov, PubMed) from Tier 3/4 Discovery/Leads.

---

## 4. Remediation Architecture & Phasing

### Phase P0 (Immediate Foundation & Truthfulness)
1. **Truthful Source Health Model**:
   - Refactor `IngestionService` and `SourceConnector._resolve_run_status` to support `CONNECTED`, `HEALTHY`, `NO_NEW_DATA`, `STALE`, `DEGRADED`, `FAILED`, `CONFIGURATION_ERROR`, `NEVER_CONNECTED`.
   - Ensure 0 new records from a successful 200 response yields `NO_NEW_DATA` or `HEALTHY` (with `records_new: 0`), never `DEGRADED`.
2. **Continuous Background Scheduler**:
   - Implement `SourceScheduler` service with source-specific polling intervals, adaptive backoff, and jitter.
   - Start scheduler gracefully inside FastAPI `lifespan` when enabled by configuration (`ENABLE_BACKGROUND_SCHEDULER=True`).
3. **Inspectable Connector Run Telemetry**:
   - Record granular run telemetry for every execution in `source_health_logs` and `connector_state` (`run_id`, `cursor_before`, `cursor_after`, `duration_ms`, `records_fetched`, `records_accepted`, `records_rejected`, `error_detail`).
4. **Repository Hygiene**:
   - Remove `frontend/package-lock.json` and legacy `frontend/src/` directory.

### Phase P1 (Feeds, Hierarchy, & Event Detection)
1. **Finish FDA & EMA Adapters**:
   - FDA: OpenFDA + MedWatch RSS + Drug Safety Communications RSS.
   - EMA: EPARs + Medicines RSS + Orphan designations.
2. **Domain Query Strategy & Event Detection**:
   - Expand `ClinicalTrialsConnector` with structured query expansions and study diffing (detect `STATUS CHANGE`, `RECRUITMENT CHANGE`, `PRIMARY ENDPOINT CHANGE`).
3. **4-Tier Source Hierarchy**:
   - Formalize Tier 1 (Authoritative), Tier 2 (High-Value), Tier 3 (Discovery), Tier 4 (Lead-only) in domain config and scoring/confluence nodes.
4. **Watchlist Matching**:
   - Target assets, NCT IDs, mechanisms, and competitors.

### Phase P2 & P3 (Extended Expansion)
- WHO ICTRP, Europe PMC, Crossref, Congress monitoring, Company IR/Press feeds.
