# Testing Patterns

**Analysis Date:** 2026-08-23

## Test Framework

**Runner:**
- pytest 8.x + pytest-asyncio (asyncio_mode = auto) - `backend/requirements.txt`
- Config: `pytest.ini` at repo root
  - `testpaths = tests`, `python_files = test_*.py`, `python_classes = Test*`, `python_functions = test_*`
  - `pythonpath = backend .`
  - Custom marker: `live` - "mark test as requiring live external services"
- pytest-cov and pytest-httpx installed (`backend/requirements.txt`) though no coverage threshold is configured

**Assertion Library:**
- Plain `assert` statements (pytest style); no BDD layers

**Run Commands:**
```bash
pytest                      # Run all backend tests (from repo root)
pytest -v                   # Verbose (CI uses this)
pytest tests/test_ingestion.py            # Single file
pytest tests/test_calibration_service.py::test_heuristic_watch_parser_matches_keywords   # Single test
pytest -m "not live"        # Exclude live-service tests (default run already skips them via skipif)
python tests/test_foundation.py           # Standalone foundation verification script (not a pytest suite)
```

**Frontend Quality Gates (no unit test runner):**
```bash
cd frontend
pnpm exec tsc --noEmit          # Typecheck gate
pnpm run check:banned-classes   # Tailwind banned-class gate (scripts/check-banned-classes.mjs)
pnpm lint                       # ESLint gate
pnpm build                      # Production build gate
```

CI executes all gates in one job: `.github/workflows/ci.yml` (pytest, then `python scripts/export_openapi.py` + `git diff --exit-code frontend/types/api.ts` contract check, then the four frontend gates).

## Test File Organization

**Location:**
- All backend tests centralized in repo-root `tests/` directory; never co-located with source. No `conftest.py` exists - each file is self-contained.
- No frontend component/lib tests exist anywhere (`frontend/` has zero `*.test.*` / `*.spec.*` files and no jest/vitest/playwright config).

**Naming:**
- `test_<domain>.py` mirroring backend domain areas:
  - API layer: `tests/test_api_endpoints.py`, `tests/test_signals_endpoints.py`, `tests/test_connector_health.py`
  - Services: `tests/test_calibration_service.py`, `tests/test_confluence_semantics.py`, `tests/test_retrieval.py`, `tests/test_intelligence_nodes.py`
  - Ingestion/connectors: `tests/test_ingestion.py` (largest, ~694 lines)
  - Cross-cutting guarantees: `tests/test_privacy_boundary.py`, `tests/test_provenance.py`, `tests/test_truthfulness_and_invariants.py`, `tests/test_contract_drift.py`, `tests/test_parity_matrix.py`, `tests/test_failure_injection.py`
  - Live-only: `tests/test_providers_live.py`

**Structure:**
```
tests/
  test_<domain>.py     # sys.path bootstrap -> imports -> inline test doubles -> fixture constants -> test functions
```

## Test Structure

**Suite Organization:**
Every test file starts with an identical bootstrap header, then imports app modules:

```python
import sys
from pathlib import Path

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app          # noqa: E402
from app.db.session import get_db # noqa: E402
```

Tests are flat module-level functions (no test classes). Section banner comments group related scenarios:

```python
# --------------------------------------------------------------------------- #
# T-P1-01 / T-P1-02 - PubMed
# --------------------------------------------------------------------------- #
@pytest.mark.asyncio
async def test_pubmed_connector():
    ...
```

**Patterns:**
- Async tests declared with `@pytest.mark.asyncio` even though asyncio_mode is auto - follow this explicit-marker convention
- Arrange-Act-Assert within each function; multiple related endpoint hits per test are acceptable (e.g. `test_health_endpoints` in `tests/test_api_endpoints.py` checks three endpoints in one test)
- Scenario-based naming: `test_e2e_hemgenix_durability_shift_scenario` (`tests/test_e2e_calibration_scenario.py`)
- Requirement traceability IDs in comments/banners (`T-P1-xx`) matching `REQ-P1-xx` docstrings in source

## Mocking

**Framework:** `unittest.mock` (AsyncMock, MagicMock, patch) plus hand-written fake classes.

**Patterns:**

Database session mocking for service-layer tests (`tests/test_calibration_service.py`):
```python
mock_db = AsyncMock()
mock_db.add = MagicMock()

res_count = MagicMock()
res_count.scalar_one.return_value = 3
mock_db.execute.return_value = res_count
# or sequenced results:
mock_db.execute.side_effect = [res_weights, res_hist]

service = StakeholderCalibrationService(mock_db)
resp = await service.submit_feedback(req)
assert mock_db.commit.called
```

HTTP mocking so connector tests never touch the network (`tests/test_ingestion.py`):
```python
def mock_http_get(side_effect):
    """Patches httpx.AsyncClient.get so connector tests never touch the network."""
    return patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=side_effect)
```

API testing via ASGI transport with dependency override, cleaned up in finally (`tests/test_api_endpoints.py`):
```python
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

Environment/config manipulation uses pytest's built-in `monkeypatch` fixture (`tests/test_config_errors.py`, `tests/test_connector_health.py`).

**Hand-written test doubles** live inline per file (no shared helpers module):
- `FakeSession` / `FakeResult` - in-memory AsyncSession stand-ins that emulate insert unique constraints, capture compiled params, expose `insert_params` / `commit_count` inspection attributes (`tests/test_ingestion.py`)
- `MockResponse` - httpx response stand-in with `.json()` / `.text` / `.status_code` / `.headers`
- Helper accessors like `bronze_insert_params(session)` filter captured inserts by column presence

**What to Mock:**
- External HTTP APIs (PubMed E-utilities, ClinicalTrials, NewsAPI, FDA, EMA RSS) - always mocked in CI
- The DB session (AsyncMock or FakeSession) - real Postgres is not started for unit tests
- Provider LLM backends except in `@pytest.mark.live` tests

**What NOT to Mock:**
- Pure domain logic under test (scoring math, confluence windows, fingerprint generation, PII scrubber regexes) - tested directly against real implementations
- The FastAPI app itself - exercised through real routing via ASGITransport, only `get_db` overridden
- Mock/synthetic data must be explicitly labeled per `docs/rules/ENGINEERING_STANDARDS.md`; tests assert on labeling fields such as `data_mode == "test_fixture"` and `is_synthetic` flags (see `tests/test_provenance.py::test_synthetic_fallback_tagging`)

## Fixtures and Factories

**Test Data:**
Module-level constants hold canned payloads close to their consuming tests:

```python
PUBMED_ESEARCH = {"esearchresult": {"idlist": ["11111111", "22222222"]}}

PUBMED_EFETCH_XML = """<?xml version="1.0"?>
<PubmedArticleSet> ... </PubmedArticleSet>"""
```
(`tests/test_ingestion.py`)

Pydantic request models double as data factories:
```python
req = FeedbackSubmissionRequest(
    signal_id=uuid.uuid4(),
    stakeholder_function="REGULATORY",
    relevance_rating=5,
    ...
)
```

SQLAlchemy model instances built directly for row fixtures (`ScoringWeights(...)`, `CalibrationFeedback(...)` in `tests/test_calibration_service.py`).

Shared reference data comes from the real domain config: `config/haemophilia.yaml` loaded via `get_domain_config()` (asset lists, confluence thresholds), asserted in `tests/test_foundation.py` and `tests/test_config.py`. Repo fixture files also exist at `data/synthetic_signals.json`.

**Location:**
- Inline within each test module; no `fixtures/` directory, no factory libraries (no factory_boy/faker)

## Coverage

**Requirements:** None enforced - pytest-cov is installed but no `--cov` flag or threshold is wired into CI.

**View Coverage:**
```bash
pytest --cov=backend/app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Dominant type: services/engines/connectors against mocked session + mocked HTTP (~117 test functions across 23 files, ~3.7k lines total)
- Pure-function tests without mocks: scoring, dedup fingerprints, PII patterns (`tests/test_confluence_semantics.py`, `tests/test_privacy_boundary.py::test_pii_scrubber_patterns`)

**Integration Tests:**
- In-process API integration via `httpx.AsyncClient(transport=ASGITransport(app=app))` with dependency overrides - no network server spawned
- Pipeline-level integration with mocked externals: provenance flow through pubmed pipeline (`tests/test_provenance.py`), LangGraph node behavior (`tests/test_intelligence_nodes.py`)
- Full scenario E2E in-memory: `tests/test_e2e_calibration_scenario.py` (feedback submission through recalibration)

**Live Tests:**
- Gated behind custom marker AND env-var skipif so CI stays green (`tests/test_providers_live.py`):
```python
@pytest.mark.live
@pytest.mark.skipif(not os.getenv("LIVE_XAI_KEY"), reason="Requires LIVE_XAI_KEY env var")
async def test_grok_live_structured_output(): ...
```
- Manual live E2E script outside pytest collection: `scripts/test_live_ingestion_e2e.py`

**Contract Tests:**
- `tests/test_contract_drift.py` asserts OpenAPI paths exist and canonical `frontend/types/api.ts` exports required interfaces
- `tests/test_parity_matrix.py` validates `docs/manifests/feature_parity_manifest.json` structure, endpoint wiring, and matrix sync

## Special Verification Scripts

- `tests/test_foundation.py`: standalone async verification script (print/assert loop, `asyncio.run(run_tests())`). Contains zero `test_*` functions, so pytest imports it harmlessly but collects nothing from it. Run manually: `python tests/test_foundation.py`. Listed as quality gate #3 in `docs/rules/TESTING_STRATEGY.md`.
- `tests/test_launchers.py` exercises `setup.py` / `start.py` via subprocess `--help` and tmp_path utilities.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_service_method():
    mock_db = AsyncMock()
    service = StakeholderCalibrationService(mock_db)
    resp = await service.submit_feedback(req)
    assert resp.status == "recorded"
```

**Error Testing:**
```python
# Configuration errors as values, not raised exceptions (tests/test_config_errors.py)
def test_configuration_error_for_newsapi_missing_key(monkeypatch):
    monkeypatch.setattr(settings, "NEWSAPI_KEY", None)
    assert configuration_error_for("newsapi") is not None

# Failure injection: malformed payloads and connector exceptions drive resilience paths
async def test_malformed_feedback_payload_validation(): ...   # tests/test_failure_injection.py
async def test_connector_failure_logging_and_resilience(): ...
```

**Observability Rule Testing:**
- Health/degradation rules verified with monkeypatched ingestion results (`tests/test_observability.py`: zero-records and all-duplicates scenarios must surface degraded status, healthy when records accepted)

---

*Testing analysis: 2026-08-23*
