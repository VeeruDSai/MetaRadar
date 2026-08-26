# Testing Patterns

**Analysis Date:** 2026-08-27

## Test Framework

**Runner:**
- Pytest 8.0.0+ (`pytest-asyncio` 0.23.0+, `pytest-cov` 4.1.0+, `pytest-httpx` 0.30.0+)
- Config: `pytest.ini`

**Assertion Library:**
- Native Python `assert` with rich pytest diff reporting

**Run Commands:**
```bash
# Run all backend unit and integration tests (excluding live network calls)
pytest tests/ -v -m "not live"

# Run fast fail-fast test execution
pytest tests/ -x -q

# Run coverage audit with report
pytest tests/ --cov=backend/app --cov-report=term-missing

# Run specific test module
pytest tests/test_provenance.py -v
```

## Test File Organization

**Location:**
- Dedicated `tests/` directory at the repository root

**Naming:**
- Files: `test_<module_or_feature>.py`
- Test functions: `test_<behavior_under_test>()`
- Async test functions: `async def test_<behavior_under_test>()`

**Structure:**
```
tests/
├── test_api_endpoints.py                 # REST API endpoints & payload serialization
├── test_calibration_service.py           # HITL feedback & dynamic weight adjustments
├── test_config.py                        # Settings parsing & default resolution
├── test_config_errors.py                 # Pure configuration error evaluation
├── test_confluence_semantics.py          # Multi-source temporal clustering
├── test_connector_health.py              # Connector status precedence & registration
├── test_contract_drift.py                # OpenAPI schema parity with TypeScript
├── test_e2e_calibration_scenario.py      # End-to-end feedback-to-routing lifecycle
├── test_failure_injection.py             # Resilience during provider outages
├── test_foundation.py                    # Database connection & migration sanity
├── test_gemma_stream.py                  # SSE streaming token delivery
├── test_ingestion.py                     # Source ingestion & Bronze deduplication
├── test_intelligence_nodes.py            # LangGraph 11-node pipeline step verification
├── test_launchers.py                     # setup.py and start.py orchestration
├── test_observability.py                 # Ingestion health telemetry & JSON logs
├── test_parity_matrix.py                 # Feature and documentation parity matrix
├── test_privacy_boundary.py              # PII/PHI scrubber & Grok gate isolation
├── test_provenance.py                    # Canonical URL truthfulness & link resolution
├── test_provider_matrix.py               # Local Gemma vs. Grok fallback matrix
├── test_providers_live.py                # Optional live network provider tests
├── test_redteam_behavior.py              # Contradiction rule evaluation (Rules A-S)
├── test_retrieval.py                     # pgvector 384-dim semantic & hybrid search
├── test_signal_decision_refinement.py    # Authority hierarchy & decision objects
├── test_signal_routing_workflow.py       # Review state machine & immutable AuditLog
└── test_truthfulness_and_invariants.py   # Determinism, secret scrubbing, scoring
```

## Test Structure

**Suite Organization:**
```python
import pytest
from httpx import AsyncClient
from app.models import Signal, AuditLog
from app.services.routing import route_signal

@pytest.mark.asyncio
async def test_signal_review_workflow_and_audit_trail(client: AsyncClient, db_session):
    # Arrange: Create initial test signal
    signal = Signal(
        title="Roche Announces Hemlibra Phase III Data",
        signal_type="trial_readout",
        disease="Haemophilia A",
        review_status="UNREVIEWED",
        priority="HIGH"
    )
    db_session.add(signal)
    await db_session.commit()

    # Act: Submit review action
    payload = {
        "operator_role": "Medical Affairs",
        "action_taken": "APPROVE_PRIORITY",
        "notes": "Reviewed against Roche readout",
        "resulting_action": "Schedule ad-board review"
    }
    response = await client.post(f"/api/v1/signals/{signal.signal_id}/review", json=payload)

    # Assert: Verify response and persistent database state
    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "REVIEWED"
    assert data["reviewed_by"] == "Medical Affairs"
```

## Mocking

**Framework:** `unittest.mock` (`AsyncMock`, `patch`) and `pytest-httpx` for HTTP intercepting.

**What to Mock:**
- External third-party HTTP endpoints (ClinicalTrials.gov, PubMed, NewsAPI, EMA RSS)
- Cloud LLM network calls (xAI Grok API)
- Time-based decay functions when testing deterministic scoring invariants

**What NOT to Mock:**
- Local database queries: Run against real PostgreSQL / AsyncSession or transactional rollback fixtures
- PII/PHI Scrubbing rules: Test real regex expressions against realistic patient payloads
- State machine transitions: Test real database mutations and ORM relationship updates

## Fixtures and Factories

**Test Fixtures:**
- `client`: Async HTTP test client configured with FastAPI `app`
- `db_session`: Async database session with automatic transaction cleanup
- `clean_sources`: Resets source telemetry and connector states between tests
- Location: `tests/conftest.py` or module-level pytest fixtures

## Coverage

**Requirements:** High coverage on core intelligence algorithms (routing, contradiction detection, PII scrubbing, canonical URL resolution, review state transitions).

**View Coverage:**
```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Types

**Unit Tests:**
- Fast, isolated checks for pure functions (`scoring.py`, `provenance_urls.py`, `pii.py`, `redact.py`).

**Integration Tests:**
- Ingestion pipeline runs, LangGraph node transitions, FastAPI endpoints, and database state machines.

**Invariant & Determinism Tests:**
- Specialized invariant test suites (`test_truthfulness_and_invariants.py`, `test_contract_drift.py`) ensuring no synthetic data leaks into live mode, zero banned CSS classes, and strict type synchronization.

## Common Patterns

**Async Testing:**
```python
@pytest.mark.asyncio
async def test_async_service_operation():
    result = await my_async_service()
    assert result is not None
```

**Error & Edge-Case Testing:**
```python
@pytest.mark.asyncio
async def test_invalid_review_transition_rejected(client: AsyncClient):
    response = await client.post("/api/v1/signals/invalid-uuid/review", json={})
    assert response.status_code == 404
```

---

*Testing analysis: 2026-08-27*
