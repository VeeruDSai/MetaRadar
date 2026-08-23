---
doc_type: codebase-map
focus: quality
analysis_date: 2026-08-23
---

# Testing Strategy & Gates

**Analysis Date:** 2026-08-23

## Framework & Configuration

- **pytest 8** with `pytest-asyncio` (`asyncio_mode = auto`), `pytest-cov`, `pytest-httpx`.
- Config: `pytest.ini` at repo root (`testpaths = tests`, `pythonpath = backend .`).
- Custom marker `live` for live external service verification (e.g. `test_providers_live.py`).
- Fast in-memory testing: all 114 automated unit and integration tests run offline without network dependencies in ~25-30s.

## Test Suite Distribution (23 test modules)

| File | Focus Area |
|---|---|
| `test_observability.py` | Source health state machine, `NO_NEW_DATA` truthful rules, scheduler telemetry |
| `test_ingestion.py` | Connector execution, PII scrubbing, deduplication, incremental cursor state |
| `test_connector_health.py` | Health log logging, unprobed status handling, error detail mapping |
| `test_provenance.py` | Provenance serialization, canonical URL preservation, verbatim bronze payloads |
| `test_intelligence_nodes.py` | 11-node LangGraph execution, entity mapping, synthesis, feedback calibration |
| `test_confluence_semantics.py` | Multi-source convergence and independent confirmation thresholds |
| `test_redteam_behavior.py` | 19-rule contradiction registry and NLI heuristics |
| `test_calibration_service.py` / `test_e2e_calibration_scenario.py` | Role weight recalibration and feedback gradient updates |
| `test_signals_endpoints.py` / `test_api_endpoints.py` | FastAPI endpoint contracts, Athena Q&A, search filters |
| `test_retrieval.py` | 384-dim FastEmbed embeddings, vector search, pgvector integration |
| `test_contract_drift.py` | OpenAPI 3.1 ⇄ `frontend/types/api.ts` synchronization gate |
| `test_parity_matrix.py` | Generated feature parity matrix verification |
| `test_privacy_boundary.py` | Grok privacy gate: non-public data blocking |
| `test_truthfulness_and_invariants.py` | Model metadata, synthetic labeling, correlation ID propagation |
| `test_failure_injection.py` | Fault-tolerance and degraded provider fallbacks |
| `test_config.py` / `test_config_errors.py` | Configuration loading, error surfacing with remediation advice |
| `test_launchers.py` | `setup.py` and `start.py` process lifecycle |
| `test_provider_matrix.py` | Capability matrix across Local Gemma, Grok, and BART |

## Mandatory CI / DoD Verification Gates

```bash
# 1. Banned Tailwind class gate
node scripts/check-banned-classes.mjs

# 2. Frontend ESLint
npm --prefix frontend run lint

# 3. Next.js 16 Production Build & TypeScript Typecheck
npm --prefix frontend run build

# 4. Backend Pytest Suite
pytest tests/ -v -k "not test_database_connection"

# 5. Contract Synchronization
python scripts/export_openapi.py
```

Current test execution status: **114 passed, 1 skipped (live Grok key)**.
