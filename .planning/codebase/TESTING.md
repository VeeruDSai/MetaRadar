# Testing Patterns

**Analysis Date:** 2026-08-24

## Test Framework

**Runner:**
- pytest >= 8.0.0 with pytest-asyncio >= 0.23.0 (asyncio_mode = auto), pytest-cov >= 4.1.0, pytest-httpx >= 0.30.0 (`backend/requirements.txt:14-19`)
- Config: `pytest.ini` (repo root) - `testpaths = tests`, `python_files = test_*.py`, `pythonpath = backend .`, custom marker `live` for tests requiring live external services

**Assertion Library:**
- Plain `assert` statements (pytest idiomatic)

**Run Commands:**
```bash
pytest                 # Run full backend suite from repo root
pytest -v              # Verbose (what CI runs, with PYTHONPATH=backend:.)
pytest -m "not live"   # Skip live-service tests
python tests/test_foundation.py   # Legacy standalone runner (has its own asyncio main)
```

**Frontend has NO unit test framework.** No jest/vitest/playwright config exists under `frontend/`. Frontend quality gates are executable checks instead (`frontend/package.json:9-15`):
```bash
cd frontend
pnpm exec tsc --noEmit           # Typecheck gate
pnpm run check:banned-classes    # Tailwind class gate (scripts/check-banned-classes.mjs)
pnpm lint                        # ESLint
pnpm build                       # Production build gate
```

## CI Pipeline

`.github/workflows/ci.yml` runs on push/PR to `main`, `develop`, `feature/*`:
1. Install `backend/requirements.txt` on Python 3.11
2. `pytest -v` with `PYTHONPATH=backend:.`
3. Contract sync: `python scripts/export_openapi.py` then `git diff --exit-code frontend/types/api.ts` (fails if canonical TS contract was hand-edited)
4. pnpm install + `tsc --noEmit` + `check:banned-classes` + `lint` + `build`

## Test File Organization

**Location:**
- Centralized in `tests/` at repo root (NOT co-located with backend modules). 24 files, ~129 test functions.

**Naming:**
- Files: `test_<domain>.py` (e.g., `tests/test_ingestion.py`, `tests/test_privacy_boundary.py`)
- Functions: `test_<behavior>()`; async tests declared `async def test_...`
- Classes (rare): `Test*` prefix per `pytest.ini`

**Structure:**
```
tests/
├── test_foundation.py               # Core capability verification (config, dedup, PII, providers)
├── test_api_endpoints.py            # HTTP contract via httpx ASGI transport
├── test_signals_endpoints.py        # /signals endpoint specifics
├── test_contract_drift.py           # OpenAPI <-> frontend/types/api.ts sync guard
├── test_failure_injection.py        # Fault tolerance + validation-error correlation IDs
├── test_privacy_boundary.py         # PII scrubbing + external-provider privacy gate
├── test_intelligence_nodes.py       # LangGraph workflow node coverage (17 tests)
├── test_provider_matrix.py          # Provider capability matrix
├── test_providers_live.py           # @pytest.mark.live real API call (skipped without key)
├── test_e2e_calibration_scenario.py # Full-scenario E2E
└── ... (calibration, confluence, retrieval, provenance, observability, launchers, parity matrix)
```

## Test Structure

**Suite organization (flat functions, numbered docstrings for ordered scenarios):**
```python
# Standard file preamble (every test file)
import pytest
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.core.config import settings


@pytest.mark.asyncio
async def test_health_endpoints():
    """Docstring describing the scenario."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"
```
(`tests/test_api_endpoints.py:15-31`)

**Patterns:**
- No fixtures/conftest.py: each file self-bootstraps `sys.path` and constructs clients inline
- Async tests use `@pytest.mark.asyncio` explicitly (also safe due to `asyncio_mode = auto`)
- Multi-step scenarios assert sequentially inside one test with inline comments per step (`tests/test_api_endpoints.py:26-47`)
- Dependency overrides wrapped in `try/finally` to guarantee cleanup:
```python
app.dependency_overrides[get_db] = mock_get_db
try:
    ...
finally:
    app.dependency_overrides.pop(get_db, None)
```
(`tests/test_api_endpoints.py:75-95`)

## Mocking

**Framework:** `unittest.mock` (AsyncMock/MagicMock/patch) + `httpx.MockTransport` + pytest `monkeypatch`

**DB session mocking (FastAPI dependency override):**
```python
mock_db = AsyncMock()
mock_scalars = MagicMock()
mock_scalars.all.return_value = []
mock_res = MagicMock()
mock_res.scalars.return_value = mock_scalars
mock_db.execute.side_effect = [mock_res_count, mock_res_scalars, ...]  # one entry per query, in order

async def mock_get_db():
    yield mock_db
```
(`tests/test_api_endpoints.py:51-70`) - `side_effect` lists must match the exact number/order of DB calls the endpoint makes.

**HTTP provider mocking (inject transport into client):**
```python
def ollama_handler(request):
    return Response(200, json={...})

provider_factory.gemma._client = AsyncClient(
    transport=MockTransport(ollama_handler), base_url="http://ollama-test"
)
```
(`tests/test_foundation.py:66-82`) - swap `_client` on the provider rather than patching network APIs.

**Settings mutation:** `monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)` (`tests/test_privacy_boundary.py:44`)

**Failure injection via test doubles subclassing production base classes:**
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
- Database sessions (always - no live Postgres in unit suite)
- External LLM/provider HTTP endpoints (Ollama/Grok) via MockTransport
- Settings flags via monkeypatch when testing conditional behavior
- Time-sensitive logic uses injected datetimes or synthetic data

**What NOT to Mock:**
- The FastAPI app itself and its middleware chain (correlation-ID behavior is asserted through the real stack - `tests/test_failure_injection.py:57-58`)
- Pure domain services (scoring, PII scrubbing, routing, authority) are tested directly against real implementations (`tests/test_foundation.py:20-56`, `tests/test_privacy_boundary.py:17-41`)
- Never fabricate pass/fail output; honest telemetry extends to tests (root `AGENTS.md` rule 4)

## Live-Service Tests

Marked `@pytest.mark.live` plus env-var-gated skip so CI stays green:
```python
@pytest.mark.live
@pytest.mark.skipif(not os.getenv("LIVE_XAI_KEY"), reason="Requires LIVE_XAI_KEY env var")
async def test_grok_live_structured_output():
    """Real Grok API call -- only runs with LIVE_XAI_KEY set. CI stays green without it."""
```
(`tests/test_providers_live.py:5-8`). Follow this two-marker pattern for any test hitting real external services. A manual live ingestion E2E script also exists at `scripts/test_live_ingestion_e2e.py`.

## Fixtures and Factories

**Test Data:**
- Inline dict literals constructed per-test; no factory libraries, no fixture files
```python
claims = [
    {"claim_id": "c1", "asset": "Hemgenix", "signal_type": "CLINICAL_TRIAL",
     "priority": "HIGH", "source": "PubMed"},
]
```
(`tests/test_foundation.py:51-54`)
- Shared synthetic dataset for pipeline tests: `data/synthetic_signals.json` (loaded by `backend/app/workflows/nodes/ingest.py:15-36`); records must carry `is_synthetic=True` / `data_mode="test_fixture"` tags
- Domain constants asserted against `config/haemophilia.yaml` via `get_domain_config()` (`tests/test_foundation.py:20-26`)

**Location:**
- All inline; shared JSON at repo-root `data/` and `backend/app/data/synthetic_signals.json`

## Coverage

**Requirements:** None enforced. `pytest-cov` is installed but no `--cov` addopts are configured anywhere.

**View Coverage:**
```bash
pytest --cov=backend/app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Pure services and helpers tested by direct import and invocation: scoring math, fingerprinting, PII patterns, authority tiers (`tests/test_foundation.py`, `tests/test_calibration_service.py`, `tests/test_signal_decision_refinement.py`)

**Integration Tests:**
- Full FastAPI app exercised over `httpx.AsyncClient` + `ASGITransport` with mocked DB dependency (`tests/test_api_endpoints.py`, `tests/test_signals_endpoints.py`)
- LangGraph workflow nodes tested with in-memory state dicts and optional mock sessions (`tests/test_intelligence_nodes.py`)

**E2E Tests:**
- Scenario-level suite `tests/test_e2e_calibration_scenario.py` (single multi-step flow)
- Live external E2E kept out of default run via `live` marker / standalone scripts

**Contract Tests:**
- `tests/test_contract_drift.py`: asserts OpenAPI schema contains required paths AND that `frontend/types/api.ts` exports the matching interfaces - the executable half of the contract-sync gate

## Common Patterns

**Async API testing:**
```python
async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
    res = await ac.post("/api/v1/athena", json={"prompt": "..."})
    assert res.status_code == 200
```
Note: project uses `ASGITransport` (not deprecated `AsyncClient(app=...)`).

**Error-path testing:**
```python
with pytest.raises(Exception) as exc_info:
    await failing_connector.fetch_signals()
assert "Simulated connector timeout" in str(exc_info.value)

with pytest.raises(PermissionError):   # privacy gate blocks confidential payloads
    await grok.generate_intelligence(...)
```
(`tests/test_failure_injection.py:34-36`, `tests/test_privacy_boundary.py:63-69`)

**Validation-error assertions include headers:**
```python
res = await ac.post("/api/v1/feedback", json=bad_payload)
assert res.status_code == 422
assert "x-request-id" in res.headers   # correlation ID survives failures
```
(`tests/test_failure_injection.py:55-58`)

**Adding a new backend test (checklist):**
1. Create `tests/test_<area>.py` with the standard sys.path preamble
2. Mark async tests `@pytest.mark.asyncio`
3. Override `get_db` with an `AsyncMock` session inside `try/finally` if hitting endpoints
4. Mock external providers via `MockTransport` injection, never real network
5. Tag anything needing real services with `@pytest.mark.live` + `skipif` env guard
6. Ensure `pytest -v` passes locally before pushing (CI gate: `.github/workflows/ci.yml:29-33`)

---

*Testing analysis: 2026-08-24*
