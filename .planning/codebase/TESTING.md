# Testing Patterns

**Analysis Date:** 2026-08-28

## Test Framework

**Runner:**
- Pytest >=8.0.0
- Async Testing: `pytest-asyncio` >=0.23.0 (`asyncio_mode = auto`)
- HTTP Client Mocking: `pytest-httpx` >=0.30.0
- Coverage Reporting: `pytest-cov` >=4.1.0
- Config File: `pytest.ini`

**Run Commands:**
```bash
# Run all test suites
pytest

# Run tests with detailed verbosity
pytest -v

# Run a specific test suite
pytest tests/test_api_endpoints.py

# Run tests with code coverage report
pytest --cov=backend/app tests/

# Run frontend linting & code style checks
cd frontend && pnpm run lint
node scripts/check-banned-classes.mjs
```

## Test File Organization

**Location:**
- Dedicated `tests/` directory at the repository root containing unit, integration, security, and contract drift tests.

**Naming:**
- Files: `test_[module_or_feature].py`
- Test functions: `test_[expected_behavior]()` or `async def test_[expected_behavior]()`
- Test classes: `Test[FeatureName]`

## Test Structure & Patterns

**Async Endpoint Test Example:**
```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_health_check_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "healthy")
```

**Database Fixtures & Session Management (`tests/conftest.py`):**
- Test database sessions use async fixtures yielding an isolated `AsyncSession`.
- Database rollback or transaction isolation ensures test isolation across runs.

## Mocking

**Framework:**
- `unittest.mock` (`AsyncMock`, `patch`, `MagicMock`)
- `pytest-httpx` for mocking external third-party biomedical APIs (PubMed, FDA, EMA, ClinicalTrials.gov) without triggering outbound network requests during CI.

**Mocking Guidelines:**
- **What to Mock:**
  - Outbound third-party HTTP requests (`httpx.AsyncClient` calls to NCBI, OpenFDA, NewsAPI, xAI).
  - Heavy GPU inference models during fast unit test runs (use `AsyncMock` or test dummy providers).
  - Background system timers and sleep calls.
- **What NOT to Mock:**
  - Business logic algorithms (priority scoring formula, weight calibration, deduplication hash computation).
  - Pydantic schema validation and JSON serialization.
  - LangGraph state transformations and linear workflow routing.

## Test Suites & Coverage Matrix

| Test Suite | Purpose | Key Files Covered |
|------------|---------|-------------------|
| `test_api_endpoints.py` | REST API routes, parameter validation, response payloads | `backend/app/api/v1/endpoints/` |
| `test_auth.py` / `test_rbac.py` | Persona authentication, RBAC, session expiration, cookies | `backend/app/services/auth_service.py`, `backend/app/models/auth.py` |
| `test_intelligence_nodes.py` | 11 LangGraph pipeline nodes and state flow | `backend/app/workflows/nodes/` |
| `test_calibration_service.py` | Functional weighting algorithms & stakeholder recalibration | `backend/app/services/calibration.py`, `backend/app/services/scoring.py` |
| `test_ingestion.py` | Data connectors, XML/JSON parsing, deduplication | `backend/app/connectors/`, `backend/app/services/ingestion.py` |
| `test_contract_drift.py` | OpenAPI schema drift between FastAPI and frontend TypeScript | `backend/app/schemas/`, `frontend/types/api.ts` |
| `test_retrieval.py` | Dense vector similarity, FastEmbed embeddings, hybrid search | `backend/app/services/vector_query.py`, `backend/app/services/embeddings.py` |
| `test_truthfulness_and_invariants.py` | Anti-hallucination, provenance tracking, audit immutability | `backend/app/models/__init__.py`, `backend/app/services/provenance_urls.py` |
| `test_privacy_boundary.py` | PII and sensitive internal data scrubbing before LLM calls | `backend/app/services/pii.py`, `backend/app/core/redact.py` |
| `test_security.py` | Password hashing, rate limiting, secure headers | `backend/app/core/security.py`, `backend/app/core/middleware.py` |

---

*Testing analysis: 2026-08-28*
