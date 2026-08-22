# Phase 08 Plan 02: Source Honesty, Connector Observability & Confluence Semantics Summary

## Executed Work
1. **Missing Credential State Machine & Pure Config Evaluator:**
   - Implemented `configuration_error_for(source_id: str) -> Optional[str]` in [`backend/app/core/config.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/core/config.py) evaluating missing or placeholder credentials (`NEWSAPI_KEY`, `XAI_API_KEY`) without database side effects.
   - Updated [`backend/app/connectors/newsapi.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/connectors/newsapi.py) to set `status = "configuration_error"` and return `ProfileRunResult(status="CONFIGURATION_ERROR", error_detail=config_err)` when credentials are absent or placeholders.
   - Updated [`backend/app/api/v1/endpoints/health.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/api/v1/endpoints/health.py), [`backend/app/api/v1/endpoints/registry.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/api/v1/endpoints/registry.py), and [`backend/app/api/v1/endpoints/observability.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/api/v1/endpoints/observability.py) to return `connector_status = "CONFIGURATION_ERROR"` and real database telemetry.

2. **Source Telemetry & Minimum-Records Health Invariant:**
   - Updated `SourceConnector._persist_health_log` in [`backend/app/connectors/base.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/connectors/base.py) to use default `http_status = None` (unprobed connector renders `—`, never fake 200).
   - Updated `IngestionService.run_connectors` in [`backend/app/services/ingestion.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/services/ingestion.py) to enforce the minimum-records rule:
     - Precedence: `CONFIGURATION_ERROR` > `UNHEALTHY` > `DEGRADED` > `HEALTHY`.
     - 0 records fetched -> `DEGRADED` with `"0 records fetched"`.
     - 0 new records accepted -> `DEGRADED` with `"0 new records accepted"`.
     - `HEALTHY` only when ≥1 record fetched AND accepted.
   - Updated [`backend/app/api/v1/endpoints/ingestion.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/api/v1/endpoints/ingestion.py) to use correct `SourceHealthLog` columns (`log.id`, `log.last_error`).

3. **Truthful Multi-Source Confluence Semantics & Backward Trace:**
   - Updated `ConfluenceEngine` in [`backend/app/services/confluence.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/services/confluence.py) and pipeline node in [`backend/app/workflows/nodes/confluence.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/workflows/nodes/confluence.py) to enforce ≥3 distinct independent source providers (`source_id` e.g. PubMed, ClinicalTrials.gov, OpenFDA, EMA, NewsAPI, ASH Congress). Multiple signals from the same provider do not meet convergence threshold.
   - Removed fabricated `75.0` / `3` fallbacks across [`backend/app/api/v1/endpoints/signals.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/api/v1/endpoints/signals.py) (`/overview`), [`backend/app/api/v1/endpoints/intelligence.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/backend/app/api/v1/endpoints/intelligence.py) (`/confluence`, `/confluence/{id}/inspect`), and [`frontend/lib/api.ts`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/lib/api.ts).

4. **Frontend Workspaces & OpenAPI Contract Synchronization:**
   - Synchronized OpenAPI schemas and TypeScript contracts via [`scripts/export_openapi.py`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/scripts/export_openapi.py) -> [`frontend/types/api.ts`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/types/api.ts).
   - Updated [`frontend/components/sources/SourcesOperationsWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/sources/SourcesOperationsWorkspace.tsx): renders `CONFIGURATION_ERROR` badge in danger tone with actionable `.env` setup guide, renders honest HTTP statuses (`—` when unprobed), and uses semantic design tokens.
   - Updated [`frontend/components/confluence/ConfluenceWorkspace.tsx`](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/confluence/ConfluenceWorkspace.tsx): updated threshold copy to "≥3 distinct independent source providers", rendered `SOURCE URL UNAVAILABLE` in monospace for non-URL evidence, and styled with semantic tokens.

## Verification Evidence
- `pytest tests/test_config_errors.py tests/test_connector_health.py tests/test_observability.py tests/test_confluence_semantics.py tests/test_provenance.py tests/test_truthfulness_and_invariants.py -v`: 30/30 passed.
- Full pytest suite `pytest tests/ -x -q`: 114 passed, 1 skipped (0 failures).
- Frontend lint `npm --prefix frontend run lint`: 0 errors.
- Frontend build `npm --prefix frontend run build`: Next.js 16 + Turbopack compiled in 907ms with 0 type errors.
