# Testing Patterns

**Analysis Date:** 2026-08-30

## Test Framework

### Runner & Configuration

- **Framework:** `pytest` with `pytest-asyncio`
- **Configuration file:** `pytest.ini` at project root
- **asyncio mode:** `auto` — all async test functions run without requiring `@pytest.mark.asyncio` decorator (though most tests still use it explicitly)
- **Test paths:** `tests` directory at project root
- **Python path:** `tests` and `.` (project root) — set via `pythonpath = backend .` so `import app.*` works

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

- **Built-in:** `assert` statements throughout — no separate assertion library
- **Pattern:** `assert response.status_code == 200`, `assert data["role"] == "MEDICAL_AFFAIRS"`, `assert len(items) >= 1`
- **Exception assertions:** `pytest.raises(PermissionError, match="...")` for expected exceptions
- **Type assertions:** `assert isinstance(value, type)` used occasionally

### Async Testing

- **Decorator:** `@pytest.mark.asyncio` on all async test functions
- **Pattern:** `async def test_*()` — coroutine test functions
- **HTTP testing:** `httpx.AsyncClient(transport=ASGITransport(app=app), base_url="...")` — ASGI transport for testing FastAPI apps without running a server
- **Database testing:** `AsyncSessionLocal()` context manager for real database sessions; `AsyncMock()` for mocked database sessions

### HTTP Mocking

- **ASGI transport:** `ASGITransport(app=app)` wraps the FastAPI app directly — no HTTP server needed
- **MockTransport (httpx):** Used for provider tests that need to mock HTTP calls to Ollama/xAI/Grok — e.g., `AsyncClient(transport=MockTransport(handler), base_url="...")`
- **MockResponse custom class:** Simple class with `json()`, `text`, `status_code`, `headers` attributes used in connector tests
- **Dependency overrides:** `app.dependency_overrides[get_db] = mock_get_db` and `app.dependency_overrides[get_current_user] = mock_current_user` to inject mock dependencies into FastAPI routes

### Coverage

- **Coverage tool:** Not explicitly configured — no `pytest-cov` or coverage config visible in `pytest.ini`
- **Coverage commands:** Not defined in `package.json` scripts or `pytest.ini`

### Run Commands

```bash
pytest                                    # Run all tests
pytest tests/test_auth.py                 # Run specific test file
pytest -k "test_pubmed"                   # Run tests matching keyword
pytest --asyncio-mode=auto                # Explicit asyncio mode
```

No `pytest-cov` coverage command configured. No watch mode configured. No separate integration/E2E test command defined.

## Test File Organization

### Location & Structure

All test files live in a single `tests/` directory at the project root. There are no subdirectories for test categories.

```
tests/
├── conftest.py                              # Shared fixtures, cleanup
├── test_api_endpoints.py                    # Root, health, business endpoint integration tests
├── test_auth.py                             # Auth, CSRF, session, login tests
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
├── test_observability.py                    # Observability endpoint tests
├── test_operational_workspaces.py           # Operational workspace tests
├── test_parity_matrix.py                    # Feature parity manifest validation
├── test_privacy_boundary.py                 # PII scrubbing and privacy gate tests
├── test_providers_live.py                   # Live provider tests (opt-in, marked `live`)
├── test_provider_matrix.py                  # Provider scenario matrix (Cases A-F)
├── test_provenance.py                       # Provenance tests
├── test_rbac.py                             # Role-based access control tests
├── test_redteam_behavior.py                 # Red-team NLP behavior tests
├── test_review_state_machine.py             # FSM state transition and audit log immutability tests
├── test_retrieval.py                        # Embedding, vector query, and provider failure tests
├── test_security.py                         # Security headers, preauth, CSRF, audit log tests
├── test_signal_decision_refinement.py       # Signal decision refinement tests
├── test_signal_routing_workflow.py          # Signal routing workflow tests
├── test_signals_endpoints.py                # Signal CRUD and Athena endpoint tests
├── test_truthfulness_and_invariants.py      # Truthfulness and invariant tests
```

### Naming Conventions

- **Test files:** `test_*.py` — e.g., `test_auth.py`, `test_signals_endpoints.py`
- **Test functions:** `async def test_*()` for async tests, `def test_*()` for synchronous tests — e.g., `test_password_hashing_and_verification`, `test_rbac_signals_list_scoping`
- **Test classes:** `Test*` pattern supported by pytest config but rarely used; most tests are standalone functions
- **Test markers:** `@pytest.mark.asyncio` on async tests; `@pytest.mark.live` for tests requiring external services

## Test Structure & Patterns

### Async Endpoint Test Pattern (HTTP + Database)

The most common test pattern exercises an endpoint through ASGI transport with real database interaction:

```python
@pytest.mark.asyncio
async def test_rbac_signals_list_scoping():
    # 1. Seed database with test data using AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        sig_med = make_test_signal(signal_id=uuid.uuid4(), ...)
        sig_safe = make_test_signal(signal_id=uuid.uuid4(), ...)
        db.add_all([sig_med, sig_safe])
        await db.commit()

    # 2. Make authenticated request through ASGI transport
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

When the database is mocked, `app.dependency_overrides` replaces FastAPI dependencies:

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
            assert data["signals"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)
```

### Database Fixtures & Cleanup

The `tests/conftest.py` provides a single autouse fixture that runs after every test:

```python
@pytest_asyncio.fixture(autouse=True)
async def cleanup_db_connections():
    _auth_rate_buckets.clear()  # Clear rate limit state
    yield
    # Delete all test-created signals by title pattern
    from app.db.session import AsyncSessionLocal
    from app.models import Signal
    from sqlalchemy import delete, or_
    try:
        async with AsyncSessionLocal() as session:
            test_patterns = [
                '%Test Signal%', 'S1 Pending', 'S2 In Review', ...
            ]
            conditions = [Signal.title.ilike(p) for p in test_patterns]
            await session.execute(delete(Signal).where(or_(*conditions)))
            await session.commit()
    except Exception:
        pass
    await engine.dispose()
```

### Provider Mocking Pattern

Provider tests mock the HTTP client directly on the provider instance:

```python
def ollama_handler(request):
    return Response(200, json={...model response...})

gemma = GemmaProvider()
gemma._client = AsyncClient(transport=MockTransport(ollama_handler), base_url="http://ollama-test")
result = await gemma.generate_intelligence(evidence=[...], task="...", classification=DataClassification.PUBLIC)
```

### Monkeypatch Pattern

`monkeypatch.setattr()` is used to temporarily modify settings or module attributes:

```python
monkeypatch.setattr(settings, "ENABLE_GROK_FALLBACK", True)
monkeypatch.setattr(settings, "LLM_PROVIDER", "xai")
monkeypatch.setattr("app.providers.gemma.find_local_gguf_model", lambda: None)
```

### Custom Test Double Patterns

- **`MockResponse`:** `json_data`, `text`, `status_code`, `headers` attributes; `json()` method returns `json_data`
- **`FakeResult`:** `scalar_one_or_none()`, `scalars()`, `all()`, `first()` methods; mimics SQLAlchemy result objects
- **`FakeSession`:** In-memory `AsyncSession` stand-in; tracks `insert_params`, `seen_external_ids`, `executed`, `commit_count`; `side_effects` list consumed per `execute()` call; `select_result` returned for `Select` statements

## Mocking

### Framework

- **Primary:** `unittest.mock` from stdlib — `AsyncMock`, `MagicMock`, `patch`, `monkeypatch`
- **HTTP mocking:** `httpx.MockTransport` — provides a handler function that returns `httpx.Response` objects
- **No external mocking libraries:** No `pytest-mock`, `mock`, or similar dependencies

### What to Mock

| Target | Mock Approach | File Context |
|--------|--------------|--------------|
| `get_db` dependency | `app.dependency_overrides[get_db] = mock_get_db` | Endpoint tests (`test_api_endpoints.py`, `test_signals_endpoints.py`) |
| `get_current_user` dependency | `app.dependency_overrides[get_current_user] = mock_current_user` | Endpoint tests |
| Database session | `AsyncMock()` with `mock_db.execute.side_effect = [...]` | Tests needing DB behavior without real DB |
| HTTP calls to external APIs | `patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=...)` | Connector tests (`test_ingestion.py`) |
| `httpx.AsyncClient` transport | `MockTransport(handler)` | Provider tests (`test_provider_matrix.py`, `test_retrieval.py`) |
| Provider `_client` attribute | `gemma._client = AsyncClient(transport=MockTransport(...))` | Provider tests |
| `app.providers.gemma.find_local_gguf_model` | `monkeypatch.setattr(...)` | Retrieval/provider tests |
| `settings.*` attributes | `monkeypatch.setattr(settings, "KEY", value)` | Provider, connector, privacy tests |
| Embedding model | `monkeypatch.setattr(embeddings_module, "TextEmbedding", lambda name: fake)` | Retrieval tests |
| `app.workflows.nodes.embed.embedding_service` | `monkeypatch.setattr("...", FakeEmbeddingService())` | Workflow node tests |
| `_auth_rate_buckets` | `_auth_rate_buckets.clear()` in conftest | Auth/rate limit tests |

### What NOT to Mock

- **Pydantic schema validation:** Schemas are tested implicitly through endpoint tests — do not mock the schema models themselves
- **Real HTTP calls in CI:** Tests marked with `@pytest.mark.live` are explicitly for live external services and excluded from standard CI runs (see `test_providers_live.py`)
- **Database engine disposal:** The `engine.dispose()` call in conftest cleanup ensures proper resource cleanup — never mock the engine itself in standard tests
- **Auth token hashing:** `hash_password`, `verify_password`, `sign_session_token` are tested with real implementations, not mocked
- **CSRF token generation/verification:** `generate_session_bound_csrf` and `verify_session_bound_csrf` are tested with real HMAC operations

## Test Suites & Coverage Matrix

### Suite Overview

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
| `test_providers_live.py` | Live provider tests | Live external services (`@pytest.mark.live`) |
| `test_config_errors.py` | Configuration error handling | Error scenario tests |

### Coverage Areas

- **Auth & Security:** Login, logout, CSRF, session management, password hashing, origin validation, rate limiting, audit log immutability
- **Signal CRUD:** List, detail, review, decision object, audit history, routing
- **Athena Intelligence:** Query endpoint, streaming endpoint, evidence retrieval, grounding
- **Health & Observability:** Liveness, readiness, models, connectors, activity logs
- **Connectors/Ingestion:** PubMed, ClinicalTrials, NewsAPI, FDA, EMA — parsing, dedup, quota, incremental state
- **Provider Matrix:** Local Gemma, Grok fallback, BART degraded mode, capability routing
- **RBAC:** Role-scoped signal listing, function queue isolation, ACTIONED permission gate
- **Review State Machine:** Valid transitions, terminal state locking, escalation/resolution lifecycle
- **Privacy:** PII/PHI scrubbing patterns, privacy gate enforcement, external bypass prevention
- **Embeddings & Retrieval:** 384-dim vector generation, batch embedding, vector query, keyword fallback
- **Calibration:** Feedback submission, weight recalibration, stakeholder function profiles
- **Contract & Parity:** OpenAPI schema drift detection, TypeScript/frontend type contract sync, feature parity manifest validation
- **Foundation:** Domain config loading, dedup fingerprinting, chunking, red-team contradiction evaluation
- **Connector Health:** Status reporting, configuration error detection, quota tracking
