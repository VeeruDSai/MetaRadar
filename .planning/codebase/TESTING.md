# Testing Patterns

**Analysis Date:** 2026-08-24

## Test Framework

**Runner:**
- pytest 8+ with pytest-asyncio (`backend/requirements.txt`)
- Config: `pytest.ini` (repo root) — `asyncio_mode = auto`, `testpaths = tests`, discovery pattern `test_*.py` / `Test*` / `test_*`
- Custom markers: `live` — marks tests requiring live external services (`pytest.ini:8-9`)
- Python 3.11 in CI; local dev may run 3.13

**Assertion Library:**
- Plain `assert` statements (no assertion library)

**Run Commands:**
```bash
pytest -v                      # Run all backend tests (from repo root)
pytest -v -m "not live"        # Exclude live-service tests
python tests/test_foundation.py  # Standalone foundation verification (has __main__ runner)
pnpm exec tsc --noEmit         # Frontend type gate (frontend/)
pnpm lint                      # Frontend lint gate
pnpm run check:banned-classes  # Banned Tailwind class gate
pnpm build                     # Frontend production build gate
```

**Frontend unit-test framework:** None. There are no JS/TS test files and no jest/vitest config. Frontend quality is enforced by the four gates above plus CI contract sync (`.github/workflows/ci.yml`). Do not invent a frontend test setup without adding config deliberately.

## Test File Organization

**Location:**
- All tests centralized in root-level `tests/` directory (flat, no subdirectories). NOT co-located with source.

**Naming:**
- `tests/test_<domain>.py`: `test_api_endpoints.py`, `test_ingestion.py`, `test_calibration_service.py`, `test_contract_drift.py`, `test_failure_injection.py`

**Structure (23 files, ~3,800 lines):**
```
tests/
├── test_foundation.py               # Core capability verification (config, PII, providers)
├── test_api_endpoints.py            # HTTP contract via httpx ASGI transport
├── test_signals_endpoints.py        # /signals filters & serialization
├── test_contract_drift.py           # OpenAPI ↔ TS contract sync guard
├── test_failure_injection.py        # Fault tolerance + validation errors
├── test_truthfulness_and_invariants.py  # Determinism/threshold invariants
├── test_provenance.py               # Provenance URL resolution
├── test_privacy_boundary.py         # PII/PHI scrubbing boundaries
├── test_providers_live.py           # @pytest.mark.live real API calls
└── ... (ingestion, calibration, retrieval, observability, e2e scenarios)
```

**Mandatory boilerplate:** There is NO `conftest.py`. Every test file repeats this path bootstrap at top:
```python
import sys
from pathlib import Path
base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))
from app.main import app   # then app imports AFTER sys.path insert
```
(`tests/test_api_endpoints.py:1-13`). Replicate this header in every new test file.

## Test Structure

**Suite Organization:**
```python
@pytest.mark.asyncio
async def test_business_endpoints():
    mock_db = AsyncMock()
    # ... arrange mocks ...
    async def mock_get_db():
        yield mock_db
    app.dependency_overrides[get_db] = mock_get_db
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/overview")
            assert res.status_code == 200
    finally:
        app.dependency_overrides.pop(get_db, None)
```
(`tests/test_api_endpoints.py:50-95`)

**Patterns:**
- Tests are function-based (no test classes), numbered docstrings when part of a suite narrative: `"""1. Testing DomainConfig loader."""` (`tests/test_foundation.py:20-27`)
- Dependency override of `get_db` with `try/finally` cleanup is THE pattern for DB-backed endpoints — never leave overrides registered
- Invariant tests verify determinism by running the same computation twice and comparing exactly (`tests/test_truthfulness_and_invariants.py:45-52`)
- Multi-scenario tests use inline comments to segment scenarios within one test (`tests/test_connector_health.py`)
- No fixtures/factories; tests construct data inline as plain dicts

## Mocking

**Framework:** `unittest.mock` (`AsyncMock`, `MagicMock`, `patch`) + pytest `monkeypatch` + `httpx.MockTransport`

**Patterns:**

1. *DB session mocking* — chain MagicMock results matching SQLAlchemy execute/scalars call order:
```python
mock_db = AsyncMock()
mock_scalars = MagicMock()
mock_scalars.all.return_value = []
res_scalars = MagicMock(); res_scalars.scalars.return_value = mock_scalars
res_count = MagicMock(); res_count.scalar.return_value = 0
mock_db.execute.side_effect = [res_count, res_count, res_scalars]  # ordered per endpoint queries
```
(`tests/test_api_endpoints.py:51-70`) — `side_effect` ordering must match the exact sequence of `db.execute()` calls inside the endpoint.

2. *Settings mutation* — monkeypatch settings attributes directly:
```python
def test_configuration_error_for_newsapi_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "")
```
(`tests/test_config_errors.py:7-16`)

3. *Module-level patch* — swap connector registries or HTTP clients:
```python
monkeypatch.setattr("app.services.ingestion.ALL_CONNECTORS", [mock_conn])          # tests/test_observability.py:35
patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=side_effect)    # tests/test_ingestion.py:126
provider_factory.gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")  # tests/test_foundation.py:82
```

4. *Fake implementations* — subclass real base classes for behavior tests:
```python
class FlakyTestConnector(SourceConnector):
    source_id: str = "flaky_test_source"
    async def fetch_signals(self, since=None):
        if self.should_fail:
            raise Exception("Simulated connector timeout")
        return []
```
(`tests/test_failure_injection.py:15-27`)

**What to Mock:**
- Database sessions (always — no real Postgres/Redis in unit tests)
- External HTTP APIs via `httpx.MockTransport` or patched `httpx.AsyncClient.get`
- Settings values that gate behavior (API keys, feature flags like `ENABLE_GROK_FALLBACK`)
- LLM provider internals (inject mock `_client` on provider instances)

**What NOT to Mock:**
- The FastAPI app/routing layer itself — exercise real routes through `AsyncClient(ASGITransport(app=app))`
- Pure domain logic (scoring, confluence engine, fingerprinting, PII scrubber) — test it directly for determinism/invariant guarantees (`tests/test_truthfulness_and_invariants.py:23-77`)
- Correlation middleware — assert real `x-request-id` headers appear even on 422 responses (`tests/test_failure_injection.py:44-58`)

## Fixtures and Factories

**Test Data:**
- Inline literal construction only. Domain-realistic haemophilia content strings double as keyword-test fixtures:
```python
title = "Phase 3 clinical trial of recombinant Factor VIII shows significant ABR reduction"
claims = [{"claim_id": "c1", "asset": "Hemgenix", "signal_type": "CLINICAL_TRIAL", ...}]
```
(`tests/test_truthfulness_and_invariants.py:26-27`, `tests/test_foundation.py:51-54`)

**Location:** No fixtures directory, no conftest.py, no factory libraries. Shared canonical payloads live in `data/synthetic_signals.json` / `backend/app/data/synthetic_signals.json`.

## Coverage

**Requirements:** None enforced (pytest-cov installed but no `--cov` flag in CI or pytest.ini).

**View Coverage:**
```bash
pytest --cov=backend/app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Direct service/class invocation: scoring determinism, confluence thresholds, fingerprint generation, PII scrubbing (`tests/test_truthfulness_and_invariants.py`, `tests/test_foundation.py`)

**Integration Tests:**
- Full ASGI request/response cycles against the real FastAPI app with mocked DB dependencies (`tests/test_api_endpoints.py`, `tests/test_signals_endpoints.py`)
- End-to-end scenario flows chaining service + endpoint layers (`tests/test_e2e_calibration_scenario.py`)
- Contract drift detection comparing generated OpenAPI paths AND hand-maintained TS interface names (`tests/test_contract_drift.py:11-41`)

**E2E/Live Tests:**
- `@pytest.mark.live` marker + env-var skipif keeps real-provider tests out of CI runs:
```python
@pytest.mark.live
@pytest.mark.skipif(not os.getenv("LIVE_XAI_KEY"), reason="Requires LIVE_XAI_KEY env var")
async def test_grok_live_structured_output():
```
(`tests/test_providers_live.py:5-19`) — follow this dual-guard pattern for any new live-service test.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_red_team_contradiction_service():
    redteam = RedTeamNLIService()
    flags = await redteam.evaluate_contradictions(claims)
```
(`tests/test_foundation.py:47-57`) — note `asyncio_mode = auto` also permits unmarked bare async defs (`test_config_errors.py:53`), but existing code mostly uses explicit markers; prefer explicit `@pytest.mark.asyncio` for new tests.

**Error Testing:**
```python
# Raised exceptions
with pytest.raises(Exception) as exc_info:
    await failing_connector.fetch_signals()
assert "Simulated connector timeout" in str(exc_info.value)     # tests/test_failure_injection.py:34-36

# HTTP validation errors + telemetry contract
res = await ac.post("/api/v1/feedback", json=bad_payload)
assert res.status_code == 422
assert "x-request-id" in res.headers                            # tests/test_failure_injection.py:55-58

# Configuration error states
assert configuration_error_for("newsapi") is not None           # pattern from tests/test_config_errors.py
```

**Honesty/Truthfulness Testing:**
- A dedicated invariant suite asserts the system never fabricates data: scores must be deterministic, recency must decay monotonically, confluence requires >= 3 distinct sources, empty inputs produce honest empties (`tests/test_truthfulness_and_invariants.py`). Any new scoring/aggregation logic MUST add corresponding invariant tests here.

**CI Gate Order** (`.github/workflows/ci.yml`):
1. `pytest -v` (PYTHONPATH=backend:.)
2. Contract sync: re-run `scripts/export_openapi.py`, fail on `git diff frontend/types/api.ts`
3. Frontend: `tsc --noEmit` → `check:banned-classes` → `eslint .` → `next build`

---

*Testing analysis: 2026-08-24*
