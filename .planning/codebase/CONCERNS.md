# Codebase Concerns

**Analysis Date:** 2026-08-27

## Tech Debt

**Contract Sync Automation:**
- Issue: `scripts/export_openapi.py` exports OpenAPI 3.1 schema from FastAPI and synchronizes TypeScript contracts into `frontend/types/api.ts`.
- Files: `scripts/export_openapi.py`, `frontend/types/api.ts`, `contracts/openapi.json`
- Impact: Complex nested schema additions require executing `python scripts/export_openapi.py` after backend model edits.
- Fix approach: Integrate `openapi-typescript` in CI pipeline to automatically regenerate TypeScript types on backend schema changes.

**Distributed Multi-Node Locking:**
- Issue: Ingestion scheduler uses PostgreSQL advisory locks (`try_advisory_lock`), which is reliable for single or dual replicas.
- Files: `backend/app/services/scheduler.py`
- Impact: If scaled to dozens of worker containers, database connection pool lock acquisition overhead could increase.
- Fix approach: Support Redis-backed distributed locks (`Redlock`) with fine-grained per-source rate limiters.

## Known Bugs

**None currently detected.**
- All 141 automated pytest test cases pass cleanly (1 live provider test skipped when offline).
- Frontend passes ESLint with 0 warnings.
- 0 banned Tailwind classes or unauthorized hex colors detected across all 31 UI component files.

## Security Considerations

**PII/PHI Privacy Gate:**
- Risk: Clinical study notes or patient trial data could inadvertently leak identifiers to external cloud LLMs.
- Files: `backend/app/services/pii.py`, `backend/app/providers/grok.py`
- Current mitigation: Regex-based `PIIPHIScrubber` sanitizes MRNs, patient names, dates, and geographic tags prior to invoking any external LLM provider.
- Recommendations: Supplement regex filters with biomedical Named Entity Recognition (NER) models for unstructured text notes.

**Secret Scrubbing in Logs:**
- Risk: API keys (`NEWSAPI_KEY`, `XAI_API_KEY`) or tokens appearing in structured JSON logs.
- Files: `backend/app/core/redact.py`, `backend/app/core/logging.py`
- Current mitigation: Automated regex pattern redactor strips keys matching known token formats before writing to stdout.

## Performance Bottlenecks

**Dense Vector Embedding Generation:**
- Problem: Generating 384-dimensional FastEmbed embeddings for large batches of ingested signals consumes CPU when run in the main process.
- Files: `backend/app/services/embeddings.py`, `backend/app/workflows/nodes/embed.py`
- Cause: FastEmbed ONNX runtime runs on CPU by default when GPU execution is not configured.
- Improvement path: Enable CUDA execution for ONNX or execute embedding generation in asynchronous background worker queues.

## Fragile Areas

**External RSS Feed Schema Fluctuations:**
- Files: `backend/app/connectors/ema.py`, `backend/app/connectors/fierce_pharma.py`, `backend/app/connectors/et_pharma.py`, `backend/app/connectors/biopharma_dive.py`
- Why fragile: Upstream RSS feed XML formats can change element structures (e.g. `<content:encoded>` vs. `<description>`) without notice.
- Safe modification: Utilize multiple XML tag fallbacks and validate parsed feeds against `BaseConnector` schemas before Bronze insertion.
- Test coverage: Covered in `tests/test_ingestion.py` and `tests/test_connector_health.py`.

## Scaling Limits

**NewsAPI Free Developer Tier:**
- Current capacity: 100 requests per 24-hour window.
- Limit: Automatic polling could exhaust developer quotas during multi-day demo periods.
- Current mitigation: NewsAPI Quota-Awareness Governor (`backend/app/services/scheduler.py`) automatically pauses background polling when fewer than 15 requests remain, preserving quota for interactive demonstrations.
- Scaling path: Upgrade to a commercial NewsAPI license for production high-volume streaming.

**PostgreSQL Vector HNSW Index:**
- Current capacity: Highly efficient for <100,000 signal records in memory.
- Limit: Memory pressure on database container if vector table grows significantly beyond millions of rows.
- Scaling path: Fine-tune `m` and `ef_construction` parameters in pgvector index and implement periodic archival of outdated signals.

## Dependencies at Risk

**None high-risk.** All major frameworks (Next.js 16, React 19, FastAPI 0.115, SQLAlchemy 2.0, Pydantic v2, FastEmbed, LangGraph) are on modern, actively supported major versions.

## Missing Critical Features

**Automated Real-Time Push Webhooks:**
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
