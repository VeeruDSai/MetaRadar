---
doc_type: codebase-map
focus: quality
analysis_date: 2026-08-22
---

# Testing

**Analysis Date:** 2026-08-22

## Framework & Configuration

- **pytest 8** with `pytest-asyncio` (`asyncio_mode = auto` — async tests need no decorator, though some files still use `@pytest.mark.asyncio`), `pytest-cov`, `pytest-httpx`.
- Config: `pytest.ini` at repo root — `testpaths = tests`, `pythonpath = backend .`, custom marker `live` for tests requiring live external services (e.g. `test_providers_live.py`, skipped without `XAI_API_KEY`; STATE.md reports "114 Passed, 1 Skipped (Live Grok Key)").
- Tests live at repo root `tests/` (NOT `backend/tests/`). Each file inserts `backend/` into `sys.path` manually.
- Frontend has **no unit-test runner** — verification is lint + strict TSC + production build + banned-class gate.

## Test Files (23)

| File | Area |
|---|---|
| `test_foundation.py` | DomainConfig loader, fingerprint/chunking, PII scrubber, red-team rules, provider factory + degraded mode. NOTE: script-style (`asyncio.run(run_tests())`) — pytest collects nothing from it; run standalone |
| `test_api_endpoints.py` | FastAPI via `httpx.AsyncClient(ASGITransport(app=app))`; dependency-overridden DB with `AsyncMock` side-effect queues |
| `test_signals_endpoints.py` | `/signals`, `/overview` contract behavior |
| `test_intelligence_nodes.py` | LangGraph node units (confluence/lifecycle/redteam/etc.) |
| `test_confluence_semantics.py` | Confluence independence/threshold semantics |
| `test_redteam_behavior.py` | 19-rule contradiction registry behavior |
| `test_calibration_service.py` / `test_e2e_calibration_scenario.py` | Weight recalibration BEFORE/AFTER |
| `test_ingestion.py` / `test_connector_health.py` | Connector runs, health telemetry |
| `test_retrieval.py` | Vector search/pgvector queries |
| `test_contract_drift.py` | OpenAPI ⇄ `frontend/types/api.ts` sync gate |
| `test_parity_matrix.py` | Generated feature-parity matrix consistency |
| `test_privacy_boundary.py` | Grok privacy gate: non-public data never leaves machine |
| `test_truthfulness_and_invariants.py` | model_metadata presence, synthetic labeling invariants |
| `test_provenance.py` | Provenance traceability columns/endpoints (Phase 8) |
| `test_failure_injection.py` | Fault-tolerance: connector/API/model failure paths |
| `test_config.py` / `test_config_errors.py` | Settings loading + CONFIGURATION_ERROR surfacing |
| `test_launchers.py` | `setup.py`/`start.py` argument handling |
| `test_observability.py` | Activity/source-health endpoints |
| `test_provider_matrix.py` | Capability matrix across providers |

## Patterns

- **In-memory ASGI testing** — no live server needed: `AsyncClient(transport=ASGITransport(app=app), base_url="http://test")`.
- **DB mocking over test databases**: endpoints tested by overriding `app.dependency_overrides[get_db]` with `AsyncMock` sessions whose `execute` side-effects return queued result stubs (`MagicMock().scalars().all()` chains). Fast, but couples tests to query counts/order — brittle when adding queries to an endpoint.
- **HTTP mocking**: `pytest-httpx` for connector unit tests (no real external calls); live behavior behind `live` marker instead.
- **Behavioral assertions**: truthfulness/provenance suites assert *labels and metadata* exist, not just status codes.
- **E2E**: `scripts/test_live_ingestion_e2e.py` for real-source ingestion smoke; pipeline E2E covered via API tests with mocked providers.

## Mandatory Verification Gates (Definition of Done — `docs/rules/TESTING_STRATEGY.md`)

```bash
node scripts/check-banned-classes.mjs        # 0 violations
npm --prefix frontend run lint               # 0 warnings/errors
npm --prefix frontend run build              # strict TS + Next 16 build passes
pytest tests/ -x -q                          # full suite green
python scripts/export_openapi.py             # contract sync clean (no diff on types/api.ts)
```

Latest recorded state (`.planning/STATE.md`, Phase 08 close): all gates green — 114 passed / 1 skipped.

---

*Mapped as part of full-repo codebase analysis: 2026-08-22*
