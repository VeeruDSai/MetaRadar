# Testing Patterns

**Analysis Date:** 2026-08-25

## Test Framework & Execution

**Backend Test Suite:**
- Runner: `pytest >= 8.0.0` with `pytest-asyncio` (`asyncio_mode = auto`), `pytest-cov`, and `pytest-httpx`
- Configuration: `pytest.ini` at repo root (`testpaths = tests`, `python_files = test_*.py`, `pythonpath = backend .`)
- Live Marker: `@pytest.mark.live` for tests requiring live third-party network access or live Grok keys (skipped automatically when unconfigured)

**Execution Commands:**
```bash
# Run complete test suite (skipping live external network tests)
pytest -v -m "not live"

# Run fast fail mode
pytest tests/ -x -q

# Run specific domain test
pytest tests/test_provenance.py -v
pytest tests/test_calibration_service.py -v
```

**Frontend Quality Gates:**
Frontend code is validated through executable CI gates (no headless UI runner like jest/vitest, but four strict static and build gates):
```bash
cd frontend

# 1. Strict TypeScript typechecking
pnpm exec tsc --noEmit

# 2. Design token & banned class gate (ensures no hardcoded slate-* / hex)
node ../scripts/check-banned-classes.mjs

# 3. Next.js ESLint flat config
pnpm lint

# 4. Production Turbopack build verification
pnpm build
```

**Contract Synchronization Gate:**
```bash
# Export OpenAPI 3.1 JSON and verify TypeScript definitions are 100% in sync
python scripts/export_openapi.py
git diff --exit-code frontend/types/api.ts
```

## Test Directory Structure (25 Suites)

All test files are organized in the root `tests/` directory:

| Test Suite | Purpose & Coverage |
|------------|-------------------|
| `test_api_endpoints.py` | FastAPI REST API contract verification using httpx ASGITransport |
| `test_calibration_service.py` | Brier score calculation, ECE bins, reliability curves, human decision scoring |
| `test_config.py` | YAML domain configuration loading and validation |
| `test_config_errors.py` | Error handling for missing or malformed configuration |
| `test_confluence_semantics.py` | Multi-source clustering, thematic convergence, contradiction detection |
| `test_connector_health.py` | Connector health status tracking and telemetry logging |
| `test_contract_drift.py` | OpenAPI schema drift verification against TypeScript models |
| `test_e2e_calibration_scenario.py` | End-to-end multi-step calibration scenario and adjustment lifecycle |
| `test_failure_injection.py` | Fault tolerance, network disruption, and corrupted payload resilience |
| `test_foundation.py` | Core foundational checks (dedup, PII scrubbing, domain config) |
| `test_gemma_stream.py` | Token streaming and SSE responses from Gemma local provider |
| `test_ingestion.py` | Bronze-layer connector ingestion, parsing, and deduplication logic |
| `test_intelligence_nodes.py` | Unit coverage across all 11 LangGraph workflow nodes |
| `test_launchers.py` | Environment setup and service launcher verification |
| `test_observability.py` | Health telemetry, system metrics, and scheduler observability endpoints |
| `test_parity_matrix.py` | Feature parity matrix verification against requirements |
| `test_privacy_boundary.py` | PII redaction and Grok cloud fallback privacy boundary verification |
| `test_provenance.py` | Canonical biomedical URL resolution and provenance metadata validation |
| `test_provider_matrix.py` | Provider capability matrix and automatic failover handling |
| `test_providers_live.py` | Real external LLM provider integration test (marked live) |
| `test_redteam_behavior.py` | Adversarial challenge generation and counter-evidence logic |
| `test_retrieval.py` | Hybrid dense vector and metadata filtering retrieval tests |
| `test_signal_decision_refinement.py` | Human feedback and signal decision refinement workflows |
| `test_signals_endpoints.py` | `/api/v1/signals` filtering, pagination, and detail views |
| `test_truthfulness_and_invariants.py` | Anti-hallucination, honest telemetry, and domain invariant tests |
