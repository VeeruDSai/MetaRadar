# Testing Patterns

**Analysis Date:** 2026-09-01

## Test Framework

### Runner & Configuration

- **Framework:** `pytest` with `pytest-asyncio`
- **Configuration file:** `pytest.ini` at project root
- **asyncio mode:** `auto` — async test functions run seamlessly across all test suites
- **Test paths:** `tests` directory at project root
- **Python path:** `pythonpath = backend .` configured in `pytest.ini` so `import app.*` works across all tests

**pytest.ini:**
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

### Assertion Library

- **Built-in:** Python `assert` statements throughout
- **Pattern:** `assert response.status_code == 200`, `assert data["role"] == "MEDICAL_AFFAIRS"`, `assert len(items) >= 1`
- **Exception assertions:** `pytest.raises(PermissionError, match="...")` for expected security & validation errors

### Async Testing

- **Decorator:** `@pytest.mark.asyncio` on async test functions
- **Pattern:** `async def test_*()` coroutine test functions
- **HTTP testing:** `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://localhost:8000")` — ASGI in-memory transport for FastAPI without network sockets
- **Database testing:** `AsyncSessionLocal()` context manager for real database sessions; `AsyncMock()` for mocked sessions

### HTTP Mocking

- **ASGI transport:** `ASGITransport(app=app)` direct FastAPI app wrapping
- **MockTransport (httpx):** Used for provider tests that mock HTTP calls to Ollama/xAI/Grok
- **MockResponse custom class:** Simple class with `json()`, `text`, `status_code`, `headers` attributes for connector tests
- **Dependency overrides:** `app.dependency_overrides[get_db] = mock_get_db` and `app.dependency_overrides[get_current_user] = mock_current_user` for route mocking

### Run Commands

```bash
pytest                                    # Run all tests (186 tests)
pytest tests/test_auth.py                 # Run specific test file
pytest -k "test_pubmed"                   # Run tests matching keyword
pytest -m "not live"                      # Run non-live tests (CI default)
pytest --asyncio-mode=auto                # Explicit asyncio mode
```

## Test File Organization

### Location & Structure

All test files reside in `tests/` at the project root:

```
tests/
├── conftest.py                              # Shared fixtures, auto-cleanup, rate bucket reset
├── test_api_endpoints.py                    # Root, health, business endpoint integration tests
├── test_auth.py                             # Auth, CSRF, session, dual timeout tests
├── test_calibration_service.py              # Calibration/feedback service tests
├── test_config.py                           # Config loading tests
├── test_config_errors.py                    # Configuration error tests
├── test_connector_health.py                 # Connector health endpoint tests
├── test_confluence_semantics.py             # Confluence semantic tests
├── test_contract_drift.py                   # OpenAPI contract sync tests
├── test_e2e_calibration_scenario.py         # End-to-end calibration scenarios
├── test_failure_injection.py                # Failure injection tests
├── test_foundation.py                       # Foundation verification (config, dedup, PII, provider)
├── test_gemma_stream.py                     # Gemma streaming tests
├── test_ingestion.py                        # Connector ingestion tests (PubMed, ClinicalTrials, NewsAPI, FDA, EMA)
├── test_intelligence_nodes.py               # LangGraph intelligence node tests
├── test_launchers.py                        # Launcher tests
├── test_login_credentials.py                # Stakeholder login credentials validation
├── test_observability.py                    # Observability endpoint tests
├── test_operational_workspaces.py           # Operational workspace tests
├── test_parity_matrix.py                    # Feature parity manifest validation
├── test_privacy_boundary.py                 # PII scrubbing and privacy gate tests
├── test_providers_live.py                   # Live provider tests (opt-in, marked `live`)
├── test_provider_matrix.py                  # Provider scenario matrix (Cases A-F)
├── test_provenance.py                       # Provenance tests
├── test_rbac.py                             # Role-based access control tests
├── test_redteam_behavior.py                 # Red-team NLP behavior tests
├── test_retrieval.py                        # Embedding, vector query, and provider failure tests
├── test_review_state_machine.py             # FSM state transition and audit log immutability tests
├── test_security.py                         # Security headers, preauth, CSRF, audit log tests
├── test_signal_decision_refinement.py       # Signal decision refinement tests
├── test_signal_routing_workflow.py          # Signal routing workflow tests
├── test_signals_endpoints.py                # Signal CRUD and Athena endpoint tests
└── test_truthfulness_and_invariants.py      # Truthfulness and invariant tests
```

### Naming Conventions

- **Test files:** `test_*.py`
- **Test functions:** `async def test_*()` or `def test_*()`
- **Test markers:** `@pytest.mark.asyncio`, `@pytest.mark.live`

## Test Structure & Patterns

### Async Endpoint Test Pattern (HTTP + Database)

```python
@pytest.mark.asyncio
async def test_rbac_signals_list_scoping():
    async with AsyncSessionLocal() as db:
        sig_med = make_test_signal(signal_id=uuid.uuid4(), ...)
        sig_safe = make_test_signal(signal_id=uuid.uuid4(), ...)
        db.add_all([sig_med, sig_safe])
        await db.commit()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac_med:
        await ac_med.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        res = await ac_med.get("/api/v1/signals")
        assert res.status_code == 200
        items = res.json()["signals"]
        assert all(s["relevant_function"] == "MEDICAL_AFFAIRS" for s in items)
```

### Mocked Database Test Pattern

```python
@pytest.mark.asyncio
async def test_signals_list_empty_database():
    mock_db = AsyncMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result_signals = MagicMock()
    mock_result_signals.scalars.return_value = mock_scalars
    mock_result_count = MagicMock()
    mock_result_count.scalar.return_value = 0
    mock_db.execute.side_effect = [mock_result_signals, mock_result_count]

    async def override_get_db():
        yield mock_db

    async def override_current_user():
        return User(user_id=uuid.uuid4(), ...)

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_current_user
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            res = await ac.get("/api/v1/signals?limit=10&offset=0")
            assert res.status_code == 200
            assert res.json()["signals"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
```

### Database Fixtures & Cleanup

The `tests/conftest.py` autouse fixture resets rate buckets, cleans test-generated records by pattern, and disposes the async engine:

```python
@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_connections():
    _auth_rate_buckets.clear()
    yield
    from app.db.session import AsyncSessionLocal
    from app.models import Signal
    from sqlalchemy import delete, or_
    try:
        async with AsyncSessionLocal() as session:
            test_patterns = ['%Test Signal%', 'S1 Pending', 'S2 In Review']
            conditions = [Signal.title.ilike(p) for p in test_patterns]
            await session.execute(delete(Signal).where(or_(*conditions)))
            await session.commit()
    except Exception:
        pass
    await engine.dispose()
```

## Mocking

### Framework

- **Primary:** `unittest.mock` from Python standard library — `AsyncMock`, `MagicMock`, `patch`, `monkeypatch`
- **HTTP Mocking:** `httpx.MockTransport` for provider & connector testing

### What to Mock

| Target | Mock Approach | Context |
|--------|--------------|---------|
| `get_db` dependency | `app.dependency_overrides[get_db] = mock_get_db` | Endpoint tests (`test_api_endpoints.py`) |
| `get_current_user` dependency | `app.dependency_overrides[get_current_user] = mock_current_user` | Auth & scoping tests |
| External API HTTP responses | `httpx.MockTransport(handler)` | Provider tests (`test_provider_matrix.py`) |
| FastEmbed model | `FakeEmbeddingService()` / `FakeTextEmbedding` | Offline retrieval tests (`test_retrieval.py`) |
| Settings attributes | `monkeypatch.setattr(settings, "KEY", value)` | Fallback & configuration tests |

### What NOT to Mock

- **Pydantic schema validation:** Models are tested with real schemas to catch serialization regressions
- **Security cryptographic primitives:** `bcrypt`, `itsdangerous`, and HMAC operations run real cryptography
- **Audit log database immutability:** Tested with actual SQLAlchemy event listeners and database sessions
- **Review state machine rules:** Validated against real transition tables

## Test Suites & Coverage Matrix

| Suite File | Domain | Test Approach |
|------------|--------|---------------|
| `test_api_endpoints.py` | Root, health, business endpoints | ASGI transport + dependency overrides |
| `test_auth.py` | Login, logout, CSRF, session, dual timeout | ASGI transport + real DB |
| `test_config.py` | App settings, domain config | Direct function calls |
| `test_security.py` | Security headers, preauth, CSRF, audit log immutability | ASGI transport + real DB + raw SQL |
| `test_rbac.py` | Role-based access control, queue isolation | ASGI transport + real DB |
| `test_signals_endpoints.py` | Signal CRUD, Athena endpoint | ASGI transport + mocked DB |
| `test_privacy_boundary.py` | PII scrubbing, privacy gate | Direct class instantiation |
| `test_ingestion.py` | PubMed, ClinicalTrials, NewsAPI, FDA, EMA connectors | `FakeSession` + `MockResponse` + `monkeypatch` |
| `test_foundation.py` | Domain config, dedup, PII scrubber, provider execution | Direct function calls + `MockTransport` |
| `test_provider_matrix.py` | Provider scenarios A-F (gemma, grok, degraded) | `MockTransport` + `monkeypatch` |
| `test_retrieval.py` | Embedding, vector query, node_embed, provider failures | `monkeypatch` + `FakeTextEmbedding` |
| `test_review_state_machine.py` | FSM transitions, audit log immutability | Real DB + ASGI transport |
| `test_calibration_service.py` | Calibration, feedback, watch items | Service layer tests |
| `test_signal_routing_workflow.py` | Signal routing workflow | Workflow tests |
| `test_signal_decision_refinement.py` | Decision refinement | Decision object tests |
| `test_truthfulness_and_invariants.py` | Truthfulness invariants | Invariant verification |
| `test_confluence_semantics.py` | Confluence semantic tests | Semantic verification |
| `test_parity_matrix.py` | Feature parity manifest | JSON/Markdown file validation |
| `test_contract_drift.py` | OpenAPI contract drift | `app.openapi()` comparison |
| `test_connector_health.py` | Connector health endpoint | ASGI transport |
| `test_observability.py` | Observability endpoints | ASGI transport |
| `test_operational_workspaces.py` | Operational workspace tests | Workspace tests |
| `test_e2e_calibration_scenario.py` | End-to-end calibration scenario | E2E scenario |
| `test_failure_injection.py` | Failure injection | Fault injection |
| `test_gemma_stream.py` | Gemma streaming | Streaming tests |
| `test_intelligence_nodes.py` | Intelligence node tests | Node tests |
| `test_launchers.py` | Launcher tests | Launcher tests |
| `test_login_credentials.py` | Stakeholder persona login validation | Credentials tests |
| `test_providers_live.py` | Live provider tests | Live external services (`@pytest.mark.live`) |
| `test_config_errors.py` | Configuration error handling | Error scenario tests |

---

*Testing analysis: 2026-09-01*
