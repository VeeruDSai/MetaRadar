# Codebase Concerns & Audit State

**Analysis Date:** 2026-08-24

## Resolved in Recent Iterations

**1. NewsAPI Key Configuration & Multi-Path `.env` Resolution (RESOLVED):**
- *Resolution:* `backend/app/core/config.py` now includes multi-path `.env` resolution (`.env`, `../.env`, root `.env`, `backend/.env`) and aliases `NEWS_API_KEY` to `NEWSAPI_KEY`. `start.py` propagates root `.env` variables to child worker processes.

**2. Grok API Key Dynamic Resolution & Resilient Fallback (RESOLVED):**
- *Resolution:* `backend/app/core/config.py` provides `effective_xai_api_key` checking both `XAI_API_KEY` and `GROK_API_KEY`. `GrokProvider` uses a dedicated 60s timeout and safely cascades to BART degraded factual summaries when xAI accounts return permissions or credit exhaustion errors.

**3. Synthetic Provenance URL Sanitization (RESOLVED):**
- *Resolution:* Replaced unresolvable `metaradar.internal` placeholder links with `[TEST FIXTURE (SYNTHETIC BENCHMARK)]` badges across backend serialization and frontend evidence drawers.

**4. Ask Athena Conversational Handling & Threshold Balancing (RESOLVED):**
- *Resolution:* Added conversational greeting handler (`hey`, `hello`, `hi`), balanced vector cosine distance threshold (`< 0.65`), and structured evidence citations.

**5. Root `models/` GGUF Discovery & Inference Orchestration (RESOLVED):**
- *Resolution:* Created root `models/` directory with automatic `.gguf` model discovery in `GemmaProvider`. Added hardware-optimized execution with `llama-cpp-python` (`n_gpu_layers=-1`, `n_threads=os.cpu_count()`, `n_ctx=2048`, `n_batch=512`), robust JSON extraction, and interactive download in `setup.py`. Downloaded `gemma-3-4b-it-Q4_K_M.gguf` (2.48 GB).

**6. Sleek Rectangular Custom Scrollbars (RESOLVED):**
- *Resolution:* Redesigned scrollbar thumbs in `frontend/app/globals.css` with sleek rectangular geometry (`border-radius: 2px`) and glowing indigo/sapphire hover states across dark and light themes.

---

## Remaining Tech Debt & Maintenance Items

**Frontend monolith component:**
- Issue: `frontend/components/metaradar.tsx` contains legacy app shell and navigation utilities.
- Fix approach: Continue modularizing workspaces into `frontend/components/<domain>/`.

**Schema churn around signal identity columns:**
- Issue: Migrations 006, 010, 011 widened signal identity fields.
- Fix approach: Lock identity contract behind `tests/test_contract_drift.py`.

**Inconsistent logging frameworks (scrubbing bypassed):**
- Issue: structlog configured with `_scrub_secrets`, but some modules use stdlib `logging.getLogger`.
- Fix approach: Gradually standardize on `app.core.logging.get_logger`.

**Dead optional spaCy path:**
- Issue: `nlp_extract.py` has optional spaCy fallback.
- Fix approach: Keep fast regex/rule extractor as standard path.

## Security & Architecture Invariants

**Zero Secret Leakage:**
- Multi-path `.env` loading ensures secrets remain strictly local and gitignored.

**Local-First Privacy Gate:**
- Data classification gates external LLM transmissions (`validate_privacy_gate()` in `backend/app/providers/grok.py`), ensuring private data stays strictly on-premise with local GGUF / Gemma.

## Performance Bottlenecks

**New HTTP client created per request attempt:**
- Problem: `_fetch_with_retry` constructs a fresh `httpx.AsyncClient` inside the retry loop — no connection pooling/keep-alive reuse across profiles/runs.
- Files: `backend/app/connectors/base.py` (lines 134–145)
- Improvement path: One long-lived `AsyncClient` per connector instance (as `GrokProvider` already does, `grok.py:48-54`).

**Row-by-row bronze persistence:**
- Problem: `_persist_bronze` awaits `check_and_persist_bronze` sequentially per payload — one round-trip per record.
- Files: `backend/app/connectors/base.py` (lines 214–229), `backend/app/services/deduplication.py`
- Improvement path: Batch insert with `ON CONFLICT DO NOTHING` + conflict count query.

**Full-table ID loads every pipeline run:**
- Problem: `_persist_state_to_db` loads ALL asset IDs and company IDs into Python sets each run just to validate FK references.
- Files: `backend/app/workflows/runner.py` (lines 147–150)
- Improvement path: Query only referenced IDs, or rely on FK constraints handled by existing per-row try/except.

**Sequential connector execution in IngestionService:**
- Problem: `run_connectors` iterates connectors serially; slow sources delay the rest of manual/bulk runs.
- Files: `backend/app/services/ingestion.py` (line 53)
- Mitigation present: background scheduler runs one task per source concurrently (`scheduler.py:90-95`).
- Improvement path: `asyncio.gather` with per-connector isolation.

**Embedding lazy-load race:**
- Problem: `EmbeddingService._get_model` has no lock; concurrent first calls via `run_in_executor` (thread pool) can double-initialize fastembed.
- Files: `backend/app/services/embeddings.py` (lines 50–59, executor offload 81–93)
- Improvement path: `threading.Lock` around first init.

**2,079-line client component re-render surface:**
- Problem: All state lives in `metaradar.tsx`; polling updates re-render whole tree every 30s per workspace.
- Files: `frontend/components/metaradar.tsx`, `frontend/lib/hooks.ts`
- Improvement path: Split state ownership per section (see Tech Debt item 1).

## Fragile Areas

**Signal identity / dedup chain:**
- Files: `backend/app/services/deduplication.py`, `backend/app/workflows/runner.py` (lines 190–197 — comment explicitly warns random-fallback UUIDs break upsert dedup), `backend/app/models/__init__.py` (`uix_signals_fingerprint` unique index)
- Why fragile: Three widening migrations (006/010/011); runner falls back `external_id → fingerprint → random uuid4`; a random fallback inserts a NEW row per run instead of updating.
- Safe modification: Never add new fallback identity branches; preserve `sig:{source}:{ext_id}` format; run `tests/test_contract_drift.py` + `tests/test_ingestion.py` after changes.
- Test coverage: Partial — statement-compilation tests exist; no live-DB dedup test in CI.

**Athena evidence-gate constant:**
- Files: `backend/app/api/v1/endpoints/signals.py` (lines 34–37, `MAX_EVIDENCE_DISTANCE = 0.35`)
- Why fragile: In-code comment says filter and docstring contract "must never drift apart again" — evidence of a past drift bug between documented similarity >= 0.65 and actual cosine-distance filter.
- Safe modification: Change only together with `backend/app/services/vector_query.py` docs and `tests/test_retrieval.py`.

**OpenAPI → TypeScript contract sync:**
- Files: `scripts/export_openapi.py` (664-line generator containing canonical TS template), `frontend/types/api.ts` (generated)
- Why fragile: CI fails if `frontend/types/api.ts` is edited directly (`.github/workflows/ci.yml` "Verify TypeScript Contract Canonical Copy"); template embedded in Python string.
- Safe modification: Edit template in `scripts/export_openapi.py`, regenerate, commit both atomically.

**useLiveData dependency spreading:**
- Files: `frontend/lib/hooks.ts` (lines 128–129: eslint-disable + `[executeFetch, intervalMs, ...deps]`)
- Why fragile: Callers passing inline array literals restart the polling effect every render; disabled lint rule hides this.
- Safe modification: Pass memoized deps or none; verify with profiler after changes.

## Scaling Limits

**raw_signals_bronze grows without bound:**
- Current capacity: Retention setting exists (`RAW_SIGNAL_RETENTION_DAYS: int = 30` in `backend/app/core/config.py` line 52) but is referenced nowhere else — no cleanup job/endpoint deletes aged bronze rows.
- Limit: Table grows forever with 5 connectors cycling at 15–60 min intervals.
- Scaling path: Add retention sweeper honoring the config value.

**Single-process in-memory scheduler/job state:**
- Current capacity: `SourceScheduler` is a module-level singleton (`backend/app/services/scheduler.py:48-61`); backoff/jitter state in process memory only.
- Limit: Multi-instance deployments use advisory locks for mutual exclusion (`try_advisory_lock` in `backend/app/db/session.py`) but status telemetry reflects only that process's view.
- Scaling path: Derive `get_status()` from the persisted fields already written to `sources` (`next_scheduled_run`, `backoff_minutes`, `consecutive_failures`).

**HNSW vector search tuning:**
- Current capacity: HNSW index `signals_embedding_hnsw` from initial migration (`backend/alembic/versions/001_initial_v51_schema.py:196-198`); `hnsw.ef_search` settable at query time (`backend/app/services/vector_query.py:74`).
- Limit: Default ef_search needs retuning past tens of thousands of signals; no maintenance guidance.
- Scaling path: Benchmark recall vs latency; tune ef_search as corpus grows.

## Dependencies at Risk

**Unpinned Python dependencies:**
- Risk: All `>=` constraints in `backend/requirements.txt` (fastapi, sqlalchemy, langgraph, fastembed, pydantic).
- Impact: Fresh CI install or Docker build can break without repo change.
- Migration plan: Pin exact versions; add Dependabot/pip-audit for controlled bumps.

**Undeclared optional dependency (spaCy):**
- Risk: Imported in try/except by `nlp_extract.py` but absent from requirements.
- Impact: Better extraction path silently never activates; ad-hoc install adds GBs of model downloads at import time.
- Migration plan: Declare extras with pinned models or remove branch.

**Frontend heavyweights as direct deps:**
- Risk: `shadcn@^4.8.0` (a CLI) listed as runtime dependency in `frontend/package.json`; framer-motion v13 and recharts v3 are major-new-version lines with zero frontend tests guarding upgrades.
- Impact: Larger installs; breaking upgrades undetected.
- Migration plan: Move `shadcn` to devDependencies; pin majors deliberately.

## Missing Critical Features

**Authentication/authorization:**
- Problem: No auth on any route.
- Blocks: Deployment beyond localhost; audit trails; role integrity of calibration (stakeholder functions spoofable via unauthenticated POSTs to `backend/app/api/v1/endpoints/feedback.py`).

**Data retention enforcement:**
- Problem: `RAW_SIGNAL_RETENTION_DAYS` unused.
- Blocks: Compliance posture for medical-intelligence data; storage cost control.

**API rate limiting:**
- Problem: Unauthenticated mutation endpoints (ingestion trigger, pipeline run, cache clear) have no throttle.
- Blocks: Safe exposure on shared networks.

**Frontend test infrastructure:**
- Problem: No test runner in `frontend/package.json` (no vitest/jest/playwright); zero component/hook/API tests.
- Blocks: Safe refactoring of `metaradar.tsx`, `lib/hooks.ts`, `lib/mappers.ts`.

## Test Coverage Gaps

**Entire frontend:**
- What's not tested: All components, `frontend/lib/api.ts` fetch/error handling, `frontend/lib/mappers.ts` transformations, `frontend/lib/hooks.ts` polling/abort logic.
- Files: everything under `frontend/lib/`, `frontend/components/`, `frontend/app/`
- Risk: Mapper bugs silently corrupt displayed medical intelligence; hook regressions cause duplicate polling.
- Priority: High

**Live-database integration paths (CI):**
- What's not tested: `.github/workflows/ci.yml` runs pytest WITHOUT postgres/redis service containers; DB-dependent tests mock sessions or compile statements (`tests/test_ingestion.py:111-113`). Real upsert behavior (`on_conflict_do_update` in `runner.py:300-321`), advisory locks, and HNSW queries never exercised in CI.
- Files: `backend/app/workflows/runner.py`, `backend/app/db/session.py`, `backend/app/services/vector_query.py`, `.github/workflows/ci.yml`
- Risk: Schema/index drift and SQL errors surface only at manual/live runtime.
- Priority: High — add pgvector service container + marked integration suite.

**Scheduler resilience:**
- What's not tested: Backoff escalation, jitter bounds, advisory-lock contention, silent DB-state-update failure path (`scheduler.py:195-204`).
- Files: `backend/app/services/scheduler.py`, `tests/test_failure_injection.py` (2 tests total)
- Risk: Stalled ingestion loops go unnoticed because failures vanish.
- Priority: Medium

**Privacy boundary depth:**
- What's not tested: Only pattern-positive PII cases asserted (`tests/test_foundation.py` script + `tests/test_privacy_boundary.py`); no tests covering names/narratives that SHOULD be caught but aren't by the regex set, nor end-to-end proof that CONFIDENTIAL payloads never reach external providers under failure injection.
- Files: `backend/app/services/pii.py`, `backend/app/providers/grok.py`, `tests/test_privacy_boundary.py`
- Risk: False confidence in the privacy gate as patterns evolve.
- Priority: Medium

---

*Concerns audit: 2026-08-23*
