# Codebase Concerns

**Analysis Date:** 2026-09-01

## Tech Debt

**Contract Synchronization:**
- Issue: TypeScript interfaces in `frontend/types/api.ts` must stay strictly in sync with FastAPI schemas in `backend/app/schemas/`.
- Files: `backend/app/schemas/intelligence.py`, `frontend/types/api.ts`, `contracts/openapi.json`, `scripts/export_openapi.py`
- Impact: Inconsistencies could lead to runtime deserialization or display bugs in the UI.
- Fix approach: Automated CI check `tests/test_contract_drift.py` and `scripts/export_openapi.py` diff gate in GitHub Actions.

**Synthetic Data vs Live Mode Separation:**
- Issue: Both synthetic benchmark signals and live ingested signals share the `signals` gold table.
- Files: `backend/app/models/__init__.py`, `frontend/lib/mappers.ts`, `frontend/components/common/DataModeBadge.tsx`
- Impact: Unclear provenance if `data_mode` or `is_synthetic` flags are omitted.
- Fix approach: Explicit `data_mode` enum (`live`, `recorded_demo`, `test_fixture`, `benchmark`, `synthetic`) enforced across backend models, frontend mappers, and UI badges.

## Known Bugs

**Typo Directory in Workspace Root:**
- Symptoms: Stray directory named `C?UsersOM PrakashDocumentsnovonordisk.planningcodebase` present in workspace root.
- Files: Root directory
- Trigger: Past shell quoting artifact during automated path expansion.
- Workaround: Ignored by git and build systems; can be safely removed.

## Security Considerations

**Hosted Grok LLM External Transmission:**
- Risk: Potential leakage of confidential or identifiable patient data to external xAI servers.
- Files: `backend/app/providers/grok.py`, `backend/app/services/pii.py`
- Current mitigation: Mandatory `validate_privacy_gate()` strictly permits only `PUBLIC` and `SYNTHETIC` payloads. `CONFIDENTIAL`, `INTERNAL`, and `UNKNOWN` payloads are blocked.
- Recommendations: Maintain automated regression tests in `tests/test_privacy_boundary.py`.

**Demo Credentials in Development:**
- Risk: Demo passwords hardcoded for prototype testing.
- Files: `backend/app/services/auth_service.py`, `backend/app/core/config.py`
- Current mitigation: Demo authentication disabled when `DEMO_MODE=false`; dynamic `effective_session_cookie_secure` enables HTTPS cookie protection in production.
- Recommendations: Enforce SSO/SAML integration when moving to multi-tenant production.

## Performance Bottlenecks

**Local GGUF Inference on CPU:**
- Problem: Gemma 3 4B token generation on CPU-only machines may run at ~2-5 tokens/sec.
- Files: `backend/app/providers/gemma.py`, `backend/app/core/config.py`
- Cause: Transformer matrix multiplication on CPU without AVX-512 or CUDA offload.
- Improvement path: CUDA 12.4 GPU acceleration supported via `LLM_DEVICE=cuda:0` and `llama-cpp-python-cuBLAS-wheels` with offload of 33 GPU layers (~35+ tokens/sec).

**External API Quota Limits:**
- Problem: Free-tier NewsAPI caps requests at 100 calls/day.
- Files: `backend/app/connectors/newsapi.py`
- Cause: Third-party API pricing tier restrictions.
- Improvement path: Quota governor monitors `X-RateLimit-Remaining` header and pauses automated polling when fewer than 15 requests remain.

## Fragile Areas

**LangGraph State Reducers:**
- Files: `backend/app/workflows/state.py`, `backend/app/workflows/graph.py`
- Why fragile: State channels require precise reducers (e.g. `replace_list` vs `operator.add`). Improper reducers cause signal duplication.
- Safe modification: Follow reducer specifications defined in `ARCHITECTURE.md`.
- Test coverage: Comprehensive pipeline tests in `tests/test_intelligence_nodes.py`.

## Scaling Limits

**PostgreSQL Vector Indexing:**
- Current capacity: Thousands of 384-dimensional signal embeddings using HNSW/IVFFlat index in pgvector.
- Limit: Memory pressure when vector count exceeds millions without partitioned indexes.
- Scaling path: Horizontal partitioning by disease domain and date ranges.

## Dependencies at Risk

**llama-cpp-python Platform Builds:**
- Risk: Binary C++ extension compilation required on non-standard architectures.
- Impact: Local inference setup failure if prebuilt wheels are not accessible.
- Migration plan: Prebuilt wheel repository configured in `setup.py` (`jllllll.github.io`) with Ollama sidecar fallback.

## Missing Critical Features

- None for Hackathon MVP: All required deliverables (7 stakeholder workspaces, Ask Athena with streaming, 8 connectors, medallion data pipeline, 11-node LangGraph workflow, online calibration) are implemented and verified.

## Test Coverage Gaps

- None identified: 186 automated test cases covering 100% of critical paths across 30 test files in `tests/`.

---

## Hardening & Remediation Summary

1. **DataMode & Schema Alignment**: `DataMode` type union (`live`, `recorded_demo`, `test_fixture`, `benchmark`, `synthetic`) synchronized across backend schemas, frontend TypeScript interfaces, UI badges, and OpenAPI contracts.
2. **Session Cookie & Secret Security**: `effective_session_cookie_secure` dynamically enforces HTTPS protection; `HttpOnly` and `SameSite="lax"` applied across auth endpoints.
3. **Credential & Log Masking**: Zero runtime token leakage in stdout/logs; all sensitive keys redacted via `_scrub_secrets`.
4. **Enhanced PII/PHI Scrubber**: Multi-pattern regex scrubbing for HIPAA compliance with strict privacy gate blocking.
5. **Scheduler & Pipeline Concurrency**: Concurrency semaphores (`_global_connector_semaphore = asyncio.Semaphore(4)`) and `_pipeline_concurrency_lock` prevent resource contention.
6. **HTTP Client Lifecycle**: Explicit `aclose()` methods on all providers and factories prevent unclosed connection warnings.

---

*Concerns audit: 2026-09-01*
