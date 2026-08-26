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

# Run 5-scenario end-to-end demo test harness
python scripts/test_demo_scenarios_e2e.py
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
```

**Patterns:**
- **Arrange-Act-Assert (AAA):** Structure all tests with clear separation between setup, execution, and verification.
- **Transactional Rollback:** Database tests run in isolated transactions that rollback after each test to prevent test cross-contamination.

## Mocking

**Framework:** `unittest.mock` (`AsyncMock`, `MagicMock`) + `pytest-httpx` for HTTP endpoint mocking.

**Patterns:**
```python
# Mocking external HTTP responses with pytest-httpx
def test_pubmed_connector_mock_http(httpx_mock):
    httpx_mock.add_response(
        url="https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
        json={"esearchresult": {"idlist": ["12345678"]}}
    )
```

**What to Mock:**
- External network requests to third-party APIs (PubMed, ClinicalTrials.gov, NewsAPI).
- Long-running cloud LLM completions in deterministic unit tests.

**What NOT to Mock:**
- Local database queries and transactions (use test PostgreSQL or SQLite async dialect).
- Core mathematical calculations (priority scoring, time decay, calibration weights).
- PII/PHI scrubbing regex algorithms.

## Coverage

**Requirements:** High branch coverage across core services, connectors, endpoints, and intelligence nodes.

**View Coverage:**
```bash
pytest --cov=backend/app --cov-report=term-missing
```

## Test Types

**Unit Tests:**
- Fast tests validating pure functions: scoring formulas, PII sanitization, URL validation, and ontology mappings.

**Integration Tests:**
- Testing FastAPI route controllers with active database transactions and Pydantic validation.

**End-to-End Tests:**
- 5-Scenario Demo Journey test harness (`scripts/test_demo_scenarios_e2e.py`) validating the complete lifecycle from ingestion and LangGraph synthesis to UI review and feedback calibration.

---

*Testing analysis: 2026-08-27*
