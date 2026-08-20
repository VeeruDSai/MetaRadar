# Testing Patterns

**Analysis Date:** 2026-08-20

## Test Framework

**Runner:**
- pytest (>= 8.0.0 per `backend/requirements.txt`) with `pytest-asyncio` and `pytest-cov`
- Config: `pytest.ini` at repo root
  ```ini
  [pytest]
  asyncio_mode = auto
  testpaths = tests
  python_files = test_*.py
  python_classes = Test*
  python_functions = test_*
  pythonpath = backend .
  markers =
      live: mark test as requiring live external services
  ```

**Assertion Library:**
- Plain `assert` statements — no `assertpy`, `expect`, or pytest-assertions plugins. Complex numeric expectations are computed inline: `assert comp.calibrated_relevance_score == round(min(1.0, 0.88 * 1.10), 2)` (`tests/test_e2e_calibration_scenario.py` line 149)

**Mocking Library:**
- stdlib `unittest.mock` (`AsyncMock`, `MagicMock`, `patch`) — no `pytest-mock` plugin in requirements; the `monkeypatch` fixture is used for settings/module attribute mutation

**Run Commands:**
```bash
pytest                    # run all tests (testpaths=tests), no DB/services required
pytest -v                 # verbose (CI uses this)
pytest -m "not live"      # exclude live external-service tests
pytest tests/test_ingestion.py   # single file
python tests/test_foundation.py  # standalone async verification script (NOT collected as a test)
```
- CI (`.github/workflows/ci.yml`) runs `pytest -v` with `PYTHONPATH: backend:.`, then verifies OpenAPI↔TypeScript contract sync, then `tsc --noEmit`, `pnpm lint`, `pnpm build`

## Test File Organization

**Location:**
- **All backend tests live in the root `tests/` directory** — co-location is NOT used. `pytest.ini` sets `testpaths = tests`
- Every test module starts with the same import bootstrap so `app.*` imports resolve without installing the package:
  ```python
  base_dir = Path(__file__).resolve().parents[1]
  sys.path.insert(0, str(base_dir / "backend"))
  ```
  (redundant with `pythonpath = backend .` but consistently kept in every file)

**Naming:**
- Files: `test_<subject>.py` — `test_ingestion.py`, `test_calibration_service.py`, `test_retrieval.py`, `test_api_endpoints.py`
- Functions: `test_<behavior>[_<condition>]` — `test_calibration_service_recalibrate_role_bounded_math`, `test_newsapi_quota_exhaustion`
- One test file per bounded context, not per module

```
tests/
├── test_api_endpoints.py             # core endpoint smoke tests (root, health, overview, athena)
├── test_calibration_service.py       # calibration service unit + endpoint API tests
├── test_config.py                    # domain config + settings defaults
├── test_contract_drift.py            # OpenAPI ↔ frontend types contract sync
├── test_e2e_calibration_scenario.py  # scripted end-to-end scenario (real PipelineRunner)
├── test_foundation.py                # standalone verification script (asyncio.run)
├── test_ingestion.py                 # connector + bronze persistence + dedup + source independence
├── test_intelligence_nodes.py        # workflow state contract, graph, per-node behavior
├── test_launchers.py                 # setup.py / start.py CLI smoke tests
├── test_parity_matrix.py             # feature parity manifest ↔ OpenAPI wiring
├── test_privacy_boundary.py          # PII/PHI scrubber + Grok privacy gate
├── test_provider_matrix.py           # provider fallback matrix via MockTransport
├── test_providers_live.py            # opt-in live xAI calls (marker: live)
├── test_redteam_behavior.py          # red-team service rules + caching
├── test_retrieval.py                 # embeddings, vector query, provider failure behavior
└── test_signals_endpoints.py         # signals/overview/athena endpoints with empty-DB mocks
```

## Test Structure

**Suite Organization:**

Backend unit/service tests use function-scoped `@pytest.mark.asyncio` tests; `asyncio_mode = auto` in `pytest.ini` means `async def test_*` functions are runnable without the marker, but the explicit marker is the dominant convention:

```python
@pytest.mark.asyncio
async def test_calibration_service_submit_feedback():
    mock_db = AsyncMock()
    mock_db.add = MagicMock()

    res_count = MagicMock()
    res_count.scalar_one.return_value = 3
    mock_db.execute.return_value = res_count

    service = StakeholderCalibrationService(mock_db)
    resp = await service.submit_feedback(req)
    assert resp.status == "recorded"
    assert resp.unapplied_count == 3
    assert mock_db.commit.called
```
(`tests/test_calibration_service.py` lines 70-96)

**Patterns:**
- **Arrange → Act → Assert** with comments staging each query result before `mock_db.execute.side_effect = [...]`
- **Sequenced DB mocks**: `mock_db.execute.side_effect = [res_weights, res_hist, res_feedback, ...]` — order matters and comments document which query each result satisfies (`tests/test_calibration_service.py` lines 181-187)
- **Teardown**: API tests use `try/finally` with `app.dependency_overrides.pop(get_db, None)` — never leak overrides between tests (`tests/test_api_endpoints.py` lines 70-90)
- **Sync tests wrap async calls** in `asyncio.run(...)` when testing pure async functions outside pytest-asyncio (seen in `tests/test_retrieval.py`, `tests/test_foundation.py`)

## Mocking

**Framework:** stdlib `unittest.mock` + `monkeypatch` fixture + httpx `MockTransport`/`ASGITransport`.

**Pattern 1 — FastAPI dependency override for endpoint tests:**
```python
mock_db = AsyncMock()
...
async def override_get_db():
    yield mock_db

app.dependency_overrides[get_db] = override_get_db
try:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/v1/signals?limit=10&offset=0")
        assert res.status_code == 200
finally:
    app.dependency_overrides.pop(get_db, None)
```
(`tests/test_signals_endpoints.py` lines 14-41)

**Pattern 2 — httpx MockTransport for provider HTTP:**
```python
def ollama_handler(request):
    return Response(200, json={...})

gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")
result = await gemma.generate_intelligence(...)
```
(`tests/test_provider_matrix.py` lines 18-48). Connection-refused behavior uses a handler that raises `httpx.ConnectError` (`tests/test_retrieval.py` lines 173-196).

**Pattern 3 — `patch` on httpx client methods for connectors:**
```python
def mock_http_get(side_effect):
    """Patches httpx.AsyncClient.get so connector tests never touch the network."""
    return patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=side_effect)

with mock_http_get([esearch_resp, esearch_resp, efetch_resp]):
    result = await connector.run_profile(session, "haemophilia_clinical")
```
(`tests/test_ingestion.py` lines 124-127). Asserting "no network call happened" uses `side_effect=AsyncMock(side_effect=AssertionError(...))` + `patched.assert_not_awaited()` (lines 337-343).

**Pattern 4 — `monkeypatch` for settings and module singletons:**
```python
monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
monkeypatch.setattr(settings, "NEWSAPI_KEY", "test-key")
monkeypatch.setattr("app.workflows.nodes.embed.embedding_service", FakeEmbeddingService())
```

**Pattern 5 — in-memory test doubles:**
- `FakeSession` — a full `AsyncSession` stand-in that emulates Insert/Select handling, unique-constraint behavior, and captures compiled params (`tests/test_ingestion.py` lines 72-121). This is the preferred double for connector tests (deeper than `AsyncMock`).
- `FakeResult` — stubs `scalar_one_or_none` / `scalars().all()` / `first()` (`tests/test_ingestion.py` lines 54-69)
- `FakeTextEmbedding` / `FakeEmbeddingService` — minimal model doubles yielding deterministic 384-dim vectors (`tests/test_retrieval.py`)
- `MockResponse` — minimal httpx Response replacement with `.json()` / `.text` / `.status_code` (`tests/test_ingestion.py` lines 43-51)

**What to Mock:**
- The database session (always — no test hits a real Postgres; the DB is exercised via Alembic/seed scripts, not unit tests)
- All outbound HTTP (httpx methods, clients)
- Embedding/model boundaries (`TextEmbedding` factory, module-level `embedding_service`)
- Settings via `monkeypatch.setattr(settings, ...)`

**What NOT to Mock:**
- Domain logic — e.g. `HeuristicWatchParser.parse`, weight math (delta/clamp), PII scrubber regexes, `_resolve_run_status` are asserted against real implementations (`tests/test_calibration_service.py`, `tests/test_ingestion.py` lines 616-632)
- The LangGraph pipeline — `test_e2e_calibration_scenario.py` runs the real `PipelineRunner` over `data/synthetic_signals.json`
- OpenAPI schema — `test_contract_drift.py` calls the real `app.openapi()`

## Fixtures and Factories

**Test Data:**
- Inline fixture dicts at module top, named `UPPER_SNAKE_CASE` — `PUBMED_ESEARCH`, `PUBMED_EFETCH_XML`, `CT_PAGE_1`, `NEWS_ARTICLE`, `FDA_RESULT`, `EMA_RSS_XML` (`tests/test_ingestion.py`)
- Small builder helpers for parametrized payloads: `make_payload(external_id="NDA761234", title=..., **overrides)` (`tests/test_ingestion.py` lines 431-454), `_ct_study(...)` (line 223)
- Real ORM model instances constructed inline for mock-query results: `ScoringWeights(...)`, `CalibrationFeedback(...)`, `CalibrationHistory(version="v1.0.0")` (`tests/test_calibration_service.py`)

**Location:**
- `data/synthetic_signals.json` is the curated demo dataset used by the e2e scenario (`tests/test_e2e_calibration_scenario.py` line 47)
- No `conftest.py` and no shared fixtures file detected — each test module bootstraps its own imports and doubles

## Coverage

**Requirements:** None enforced. `pytest-cov` is installed (`backend/requirements.txt`) but `pytest.ini` has no `--cov` args or thresholds, and CI (`ci.yml`) does not run coverage. Quality gates are instead: all tests green + contract sync + tsc + eslint + `next build` (`docs/rules/TESTING_STRATEGY.md`).

**View Coverage:**
```bash
pytest --cov=app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Service logic (`tests/test_calibration_service.py`, `tests/test_redteam_behavior.py`)
- Connectors with fully mocked HTTP (`tests/test_ingestion.py`)
- Providers and fallback matrix (`tests/test_provider_matrix.py`, `tests/test_retrieval.py`)
- Workflow nodes and state contract (`tests/test_intelligence_nodes.py`)
- PII/PHI scrubber and privacy gate (`tests/test_privacy_boundary.py`)

**Integration Tests:**
- Full FastAPI app via `ASGITransport` + dependency override for DB (`tests/test_api_endpoints.py`, `tests/test_signals_endpoints.py`, `tests/test_calibration_service.py` `test_feedback_endpoints_api`)
- Contract sync: `tests/test_contract_drift.py` asserts `app.openapi()` contains all paths AND that `frontend/types/api.ts` contains the expected interfaces
- Parity matrix wiring: `tests/test_parity_matrix.py` asserts every `WIRED` manifest feature exists in `contracts/openapi.json`
- Launcher smoke tests execute `setup.py --help` / `start.py --help` as subprocesses (`tests/test_launchers.py`)

**E2E Tests:**
- One scripted scenario: `tests/test_e2e_calibration_scenario.py` — loads `data/synthetic_signals.json`, runs the real 10-node `PipelineRunner`, submits feedback, recalibrates, confirms a watch item, evaluates `node_missing_signal`. Fully hermetic (mocked DB only at the persistence boundary).
- `tests/test_foundation.py` is a standalone `asyncio.run(run_tests())` script with print-based PASS markers; it is the "Backend Unit & Capability Verification" gate in `docs/rules/TESTING_STRATEGY.md` and is invoked directly, not collected by pytest (it has no `test_` functions).

**Live (opt-in):**
- `tests/test_providers_live.py` — real xAI API call, gated by both the `live` marker and `@pytest.mark.skipif(not os.getenv("LIVE_XAI_KEY"), ...)` so CI stays green without credentials

**Frontend:**
- **No frontend test framework exists** — no jest/vitest/playwright config, no `*.test.ts(x)` / `*.spec.ts(x)` files. Frontend verification is typecheck + lint + production build only (`tsc --noEmit`, `eslint .`, `next build`). Contract correctness is covered indirectly by `tests/test_contract_drift.py`.

## Common Patterns

**Async Testing:**
- `@pytest.mark.asyncio` on every async test (explicit despite `asyncio_mode = auto`)
- `asyncio.run(...)` inside sync tests for isolated async calls (`tests/test_retrieval.py`)
- Async mocks: `AsyncMock()` for sessions/clients; `async def override_get_db(): yield mock_db` for DI overrides
- Assert `patched.assert_not_awaited()` to prove a code path never makes a network call (`tests/test_ingestion.py` line 343)

**Error Testing:**
```python
def test_gemma_raises_on_connection_refused():
    gemma = GemmaProvider()
    gemma._client = _refused_transport()

    with pytest.raises(OllamaUnavailableError):
        asyncio.run(gemma.generate_intelligence(...))
```
(`tests/test_retrieval.py` lines 180-189). Also: `with pytest.raises(PermissionError)` for privacy-gate violations (`tests/test_privacy_boundary.py` line 53), and `with pytest.raises(GrokUnavailableError)` when API key is missing (`tests/test_retrieval.py` lines 199-208).

**HTTP status assertions:**
- `200` success, `201` created (`tests/test_calibration_service.py` lines 240, 280), `400` domain validation, `422` schema validation (`tests/test_calibration_service.py` lines 253, 269)

**Degradation / honesty assertions:**
- Assert status enums and honest metadata: `result.status == "DEGRADED"`, `result.error_detail == "NewsAPI daily quota exhausted"`, `meta["fallback_used"] is False`, `meta["reasoning_available"] is False` (`tests/test_ingestion.py` line 341, `tests/test_provider_matrix.py` lines 47-48, `tests/test_foundation.py` lines 79-81)

---

*Testing analysis: 2026-08-20*
