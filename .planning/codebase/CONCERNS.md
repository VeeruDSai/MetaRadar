# Codebase Concerns

**Analysis Date:** 2026-08-27

## Tech Debt

**Contract Sync Automation:**
- Issue: `scripts/export_openapi.py` writes a static TypeScript contract template directly to `frontend/types/api.ts` to ensure consistency.
- Files: `scripts/export_openapi.py`, `frontend/types/api.ts`
- Impact: Modifying backend Pydantic schemas requires manual updates in `scripts/export_openapi.py` before re-exporting.
- Fix approach: Integrate `openapi-typescript` or `orval` in CI to generate full TypeScript interfaces dynamically from `contracts/openapi.json`.

**Connector Ingestion Loop Concurrency:**
- Issue: Ingestion scheduler uses PostgreSQL advisory locks (`try_advisory_lock`), which is effective for single/dual instances but lacks fine-grained distributed rate limiting.
- Files: `backend/app/services/scheduler.py`
- Impact: Multi-worker horizontally scaled backend containers may contend for locks.
- Fix approach: Transition to Redis-backed distributed locks (`Redlock`) with sliding-window rate limiters.

## Known Bugs

**None currently detected.** (All 139 test cases pass, 0 ESLint warnings, 0 type errors, and 0 banned Tailwind classes).

## Security Considerations

**PII/PHI Privacy Gate:**
- Risk: Clinical and patient trial notes could inadvertently leak sensitive health identifiers to external cloud LLMs.
- Files: `backend/app/services/pii.py`, `backend/app/providers/grok.py`
- Current mitigation: Regex-based `PIIPHIScrubber` sanitizes MRNs, patient names, dates, and geographic tags prior to invoking any external LLM provider.
- Recommendations: Add named entity recognition (NER) biomedical privacy scrubber for unstructured text notes.

**Secret Scrubbing in Logs:**
- Risk: API keys (`NEWSAPI_KEY`, `XAI_API_KEY`) or tokens appearing in structured JSON logs.
- Files: `backend/app/core/redact.py`, `backend/app/core/logging.py`
- Current mitigation: Automated regex pattern redactor strips keys matching known token formats before writing to stdout.

## Performance Bottlenecks

**Dense Vector Embedding Generation:**
- Problem: Generating 384-dimensional FastEmbed embeddings for large batches of ingested signals can consume significant CPU during startup or heavy batch runs.
- Files: `backend/app/services/embeddings.py`, `backend/app/workflows/nodes/embed.py`
- Cause: FastEmbed ONNX runtime runs on CPU when GPU execution is disabled.
- Improvement path: Enable GPU/CUDA execution for ONNX or execute embedding generation in dedicated asynchronous background worker queues.

## Fragile Areas

**External RSS Feed Schema Fluctuations:**
- Files: `backend/app/connectors/ema.py`, `backend/app/connectors/fierce_pharma.py`, `backend/app/connectors/et_pharma.py`
- Why fragile: Upstream RSS feed XML formats can change element structures (e.g. `<content:encoded>` vs. `<description>`) without notice.
- Safe modification: Utilize multiple XML tag fallbacks and validate parsed feeds against `BaseConnector` schemas before Bronze insertion.
- Test coverage: Covered in `tests/test_ingestion.py` and `tests/test_connector_health.py`.

## Scaling Limits

**NewsAPI Free Developer Tier:**
- Current capacity: 100 requests per 24-hour window.
- Limit: Ingestion scheduler will encounter 429 quota exhaustion if scheduled too aggressively.
- Scaling path: Maintain `15-minute` intervals with jitter, or upgrade to a commercial NewsAPI license.

**PostgreSQL Vector HNSW Index:**
- Current capacity: Efficient for <100,000 signal records in memory.
- Limit: Memory pressure on container if vector table grows significantly beyond millions of rows.
- Scaling path: Configure `m` and `ef_construction` parameters in pgvector index and implement periodic archival of outdated signals.

## Dependencies at Risk

**None high-risk.** All major frameworks (Next.js 16, React 19, FastAPI 0.115, SQLAlchemy 2.0, Pydantic v2) are on modern, actively supported major versions.

## Missing Critical Features

**Automated Real-Time Webhook Subscriptions:**
- Problem: Signals are currently pulled via background scheduled polling rather than real-time push webhooks.
- Blocks: Sub-second latency for breaking regulatory alerts.
- Enhancement: Add WebSocket / Webhook listener endpoints for upstream aggregators.

## Test Coverage Gaps

**Live Cloud Provider End-to-End Tests:**
- What's not tested: Live xAI Grok API calls in standard CI (skipped when `XAI_API_KEY` is not present).
- Files: `tests/test_providers_live.py`
- Risk: Upstream breaking changes in external Grok API endpoints could go unnoticed until staging deployment.
- Priority: Medium (mitigated by strict unit testing of `DegradedFactualProvider` and `LocalGemmaProvider`).

---

*Concerns audit: 2026-08-27*
