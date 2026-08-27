# Codebase Concerns

**Analysis Date:** 2026-08-28

## Tech Debt

**Contract & Type Synchronization:**
- Issue: TypeScript interfaces in `frontend/types/api.ts` are generated from OpenAPI schemas (`backend/app/schemas/`). If backend endpoints change without running `python scripts/export_openapi.py`, contract drift can occur.
- Files: `backend/app/schemas/`, `frontend/types/api.ts`, `scripts/export_openapi.py`
- Impact: Potential runtime frontend type mismatches or unhandled response properties.
- Fix approach: Enforce CI contract validation using `tests/test_contract_drift.py` on all pull requests.

**Synthetic Data vs Live Connectors:**
- Issue: Local developer environments operate seamlessly on synthetic seed data (`backend/app/data/synthetic_signals.json`), but live feeds require explicit network API keys (NewsAPI, NCBI).
- Files: `backend/app/db/seed.py`, `backend/app/core/config.py`
- Impact: Developers without third-party API keys may not test live rate-limit handling locally.
- Fix approach: Built-in mock modes and fixture replay fixtures in `tests/test_ingestion.py`.

## Performance Bottlenecks

**Local LLM Inference on CPU:**
- Problem: Running `google/gemma-3-4b-it` (Q4_K_M GGUF) on CPU-only machines takes ~30–60 seconds per synthesis request, whereas CUDA GPU execution completes in ~1.5–3 seconds.
- Files: `backend/app/providers/gemma.py`, `setup.py`, `start.py`
- Cause: Quantized autoregressive token generation without tensor hardware acceleration.
- Improvement path: Ensure CUDA 12.4 wheels are installed via `setup.py` on systems with NVIDIA GPUs, or enable hosted Grok fallback via `ENABLE_GROK_FALLBACK=true`.

**External Biomedical API Rate Quotas:**
- Problem: Unauthenticated PubMed (NCBI) allows only 3 req/sec; free NewsAPI accounts are restricted to 100 requests per day.
- Files: `backend/app/connectors/pubmed.py`, `backend/app/connectors/newsapi.py`, `backend/app/services/scheduler.py`
- Cause: Upstream third-party API constraints.
- Improvement path: The autonomous background scheduler (`backend/app/services/scheduler.py`) implements jitter, exponential backoff, and stateful cursor tracking to prevent 429 quota exhaustion.

## Security Considerations

**Session Security & Production Cookies:**
- Risk: Session cookies in local development default to `SESSION_COOKIE_SECURE=False` to support HTTP `localhost`.
- Files: `backend/app/core/config.py`, `backend/app/api/v1/endpoints/auth.py`
- Current mitigation: Secure cookies enabled when configured for HTTPS environments.
- Recommendations: Ensure `SESSION_COOKIE_SECURE=True` is strictly set in production `.env` and verified in deployment pipelines.

**Third-Party LLM Data Privacy:**
- Risk: Transmitting sensitive internal competitive intelligence to cloud LLM APIs.
- Files: `backend/app/providers/grok.py`, `backend/app/services/pii.py`
- Current mitigation: Local-first inference (Local Gemma 3 4B) keeps data 100% on-premises. If cloud Grok is used, `backend/app/services/pii.py` automatically redacts sensitive names and patient identifiers.
- Recommendations: Maintain strict CI testing on `tests/test_privacy_boundary.py`.

## Fragile Areas

**Multi-Worker Scheduler Execution:**
- Files: `backend/app/services/scheduler.py`, `backend/app/main.py`
- Why fragile: In multi-worker Uvicorn deployments (`uvicorn --workers 4`), in-memory schedulers can trigger duplicate concurrent connector runs if not protected by distributed locks.
- Safe modification: In distributed multi-process environments, use Redis distributed locks (`REDIS_URL`) to ensure single-leader scheduling.
- Test coverage: Tested in `tests/test_ingestion.py` and `tests/test_connector_health.py`.

## Scaling Limits

**Vector Storage Capacity (pgvector):**
- Current capacity: Efficient cosine distance indexing on 384-dimensional dense vectors up to hundreds of thousands of signals.
- Limit: At multi-million signal scales, IVFFlat / HNSW index build times and memory usage increase.
- Scaling path: Partition `signals` table by `published_at` year/quarter and tune HNSW `m` and `ef_construction` index parameters.

## Test Coverage Gaps

**Live Network Integration Testing in CI:**
- What's not tested in standard offline CI: Live external network connections to PubMed, FDA, and EMA are mocked via `pytest-httpx` to ensure fast, deterministic builds.
- Files: `tests/test_ingestion.py`, `scripts/test_live_ingestion_e2e.py`
- Risk: Upstream breaking schema changes in external third-party XML/JSON endpoints could go undetected until runtime.
- Priority: Medium (Mitigated by scheduled staging health runs using `scripts/test_live_ingestion_e2e.py`).

---

*Concerns audit: 2026-08-28*
