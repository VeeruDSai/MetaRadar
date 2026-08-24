# Codebase Concerns

**Analysis Date:** 2026-08-24

## Tech Debt

**Monolithic frontend god-component:**
- Issue: `frontend/components/metaradar.tsx` is a single 2,302-line client component containing the dashboard shell, Athena chat, calibration UI, confluence/contradiction views, cache management, and theme toggling. It holds 27 `useState` hooks and 5 `useEffect` hooks in one component and imports ~20 API functions from `frontend/lib/api.ts`.
- Files: `frontend/components/metaradar.tsx`
- Impact: Any state change re-renders a very large tree; the file is hard to review, test, or modify safely. Several workspace components already exist (`frontend/components/signals/`, `frontend/components/confluence/`, etc.) but the monolith still duplicates orchestration logic.
- Fix approach: Incrementally extract each dashboard section into its own component under `frontend/components/` (pattern already established by `SignalDetailWorkspace.tsx`, `SettingsWorkspace.tsx`), lifting only shared state into context or hooks.

**Oversized endpoint module mixing layers:**
- Issue: `backend/app/api/v1/endpoints/signals.py` (923+ lines) mixes HTTP concerns, ORM-to-Pydantic serialization (`_serialize_signal`), business rules (Athena evidence gate `MAX_EVIDENCE_DISTANCE`), authority/routing resolution, and LLM dispatch.
- Files: `backend/app/api/v1/endpoints/signals.py`
- Impact: High cognitive load; serialization helpers are duplicated per-endpoint; hard to unit test business rules without FastAPI.
- Fix approach: Extract serializers into `backend/app/schemas/converters.py` (or services layer) and move the Athena gate/routing resolution into dedicated services like the existing `backend/app/services/routing.py`.

**Inconsistent logging frameworks:**
- Issue: The app configures `structlog` JSON logging (`backend/app/core/logging.py`, used by `backend/app/core/middleware.py`), but most core modules use stdlib `logging`: `backend/app/services/scheduler.py`, `backend/app/workflows/runner.py`, `backend/app/providers/gemma.py`, `backend/app/connectors/base.py`.
- Files: see above
- Impact: Scheduler/pipeline/provider telemetry bypasses structured correlation-ID logging; two log formats reach stdout.
- Fix approach: Standardize on `structlog.get_logger(...)` across `backend/app/` (middleware already binds request/correlation contextvars).

**Migration churn / historical schema drift:**
- Issue: Migrations 006, 009, 010, 011, 012 exist purely to patch drift between ORM models and DB schema (widened columns, "final_schema_sync", dropped unique constraints). Migration `010_non_unique_signal_identifiers.py` documents that unique constraints on `pmid`/`nct_id`/`regulatory_id`/`canonical_url` previously caused `UniqueViolationError` → `InFailedSQLTransactionError` and **total signal loss during pipeline execution**.
- Files: `backend/alembic/versions/006_widen_signals_external_id.py`, `009_final_schema_sync.py`, `010_non_unique_signal_identifiers.py`, `011_widen_signals_fingerprint.py`, `012_signal_decision_object_fields.py`
- Impact: New environments depend on a long fix-forward chain; drift risk recurs whenever models change without a migration.
- Fix approach: Keep using `tests/test_contract_drift.py`-style checks; consider squashing migrations before next milestone and adding an alembic-vs-models parity test.

**Dual-call-signature compatibility layer in frontend API client:**
- Issue: `frontend/lib/api.ts` exports aliases (`getOverview = fetchOverview`, `getSignals`, `getConfluences`, ...) whose parameters are union types like `filters?: SignalFilterParams | AbortSignal` to support both old and new call styles. Callers must know which variant to use.
- Files: `frontend/lib/api.ts` (~507 lines)
- Impact: Confusing API surface; type unions hide misuse; every new endpoint risks adding another dual signature.
- Fix approach: Migrate callers to one canonical naming convention and delete alias shims.

**In-memory rate limiting and unbounded dict growth:**
- Issue: `backend/app/api/deps.py` keeps rate-limit buckets in a module-level `_rate_buckets: Dict[str, List[float]]` defaultdict keyed by client IP. Buckets for inactive clients are never pruned (only pruned when the same client hits again), state is per-process, and it is lost on restart.
- Files: `backend/app/api/deps.py`
- Impact: Memory growth proportional to distinct client IPs; limit is not enforced consistently with multiple uvicorn workers or behind a proxy (all requests share proxy IP).
- Fix approach: Periodic sweep of stale buckets, or move counters to Redis (already available via `REDIS_URL`).

**Setup/launcher scripts swallow failures:**
- Issue: `setup.py` and `start.py` catch nearly every failure and print `[WARNING] ... Continuing...` (17 broad except handlers in `start.py`, 6 in `setup.py`). Pip/npm/docker/migration/seed failures still end with `[SUCCESS] MetaRadar environment setup complete!`.
- Files: `setup.py`, `start.py`
- Impact: Users can land in a half-configured environment that reports success; violates the project's own honest-telemetry rule (AGENTS.md #4).
- Fix approach: Track step failures and exit non-zero / print a failed-steps summary at the end.

**Mixed package managers and unpinned Python deps:**
- Issue: `frontend/package.json` declares `"packageManager": "pnpm@9.15.5"` but `setup.py` installs frontend deps with `npm install`. All backend requirements are open-ended `>=` constraints with no lockfile.
- Files: `setup.py`, `backend/requirements.txt`, `frontend/package.json`
- Impact: Non-reproducible builds; npm-vs-pnpm mismatch creates duplicate lockfiles/node_modules layouts.
- Fix approach: Pick one frontend package manager (pnpm per package.json) and add a pinned constraints file (e.g., `pip-tools` output) for backend.

## Known Bugs

**Historical: unique-constraint signal loss (fixed in migration 010):**
- Symptoms: `UniqueViolationError` on subsequent signals sharing the same trial/publication/regulatory URL, cascading into `InFailedSQLTransactionError` and loss of all signals in the batch.
- Files: `backend/alembic/versions/010_non_unique_signal_identifiers.py` (documents the bug), `backend/app/workflows/runner.py` (upsert by fingerprint)
- Trigger: Pipeline runs ingesting multiple events for the same `nct_id`/`pmid`/URL — pre-migration-010 databases only.
- Workaround: Fixed by dropping unique indexes; ensure deployed DBs are at head (`alembic upgrade head`).

**Scheduler DB telemetry writes silently dropped:**
- Symptoms: When updating `sources.next_scheduled_run/backoff/failures` fails, the exception is swallowed with bare `except Exception: pass` — no log, no metric.
- Files: `backend/app/services/scheduler.py:203-204`
- Trigger: Transient DB errors during scheduler loop.
- Workaround: None needed functionally (state re-derived next cycle), but observability is lost.

## Security Considerations

**Default credentials committed in compose file:**
- Risk: `docker-compose.yml` hardcodes `POSTGRES_PASSWORD: metaradar_pass` and publishes Postgres (5432) and Redis (6379, no password) to the host. Backend defaults mirror these in `backend/app/core/config.py` (`DATABASE_URL`). A root `.env` file exists locally (gitignored, contents not inspected).
- Files: `docker-compose.yml`, `backend/app/core/config.py`, `.env` (present, gitignored)
- Current mitigation: Comment in config notes these are local-dev defaults; `.gitignore` excludes `.env`; `.env.example` provided without secrets.
- Recommendations: Bind DB/Redis ports to `127.0.0.1` only; set Redis `requirepass`; fail fast in production profile if default password detected.

**Mutations unauthenticated by default:**
- Risk: `require_mutation_auth` in `backend/app/api/deps.py` is a no-op unless `METARADAR_API_KEY` is set — all POST endpoints (ingest, pipeline trigger, feedback, recalibrate, cache clear) are open on localhost deployments.
- Files: `backend/app/api/deps.py`, endpoints under `backend/app/api/v1/endpoints/`
- Current mitigation: Documented as intentional local-dev behavior; optional key + in-memory rate limit exist.
- Recommendations: At minimum warn loudly at startup when mutations are unprotected; consider requiring the key whenever CORS origins include non-localhost.

**CORS wildcard methods with credentials:**
- Risk: `main.py` sets `allow_credentials=True` with `allow_methods=["*"]` for configured origins. Low risk while origins are localhost-only, but becomes dangerous if `CORS_ORIGINS` is widened.
- Files: `backend/app/main.py:66-73`
- Recommendations: Restrict methods to those actually used; keep origin list explicit.

**Regex-only PII/PHI scrubbing:**
- Risk: `PIIPHIScrubber` covers email, phone, SSN, MRN, DOB patterns only (`backend/app/services/pii.py`). Free-text patient names, addresses, narrative clinical details pass through unredacted to LLM prompts (local Gemma by design, but hosted Grok fallback sends data off-device when enabled).
- Files: `backend/app/services/pii.py`, `backend/app/core/redact.py`, `backend/app/providers/grok.py`
- Current mitigation: DataClassification gating (`test_privacy_boundary.py` verifies boundary behavior); Grok fallback disabled by default (`ENABLE_GROK_FALLBACK=False`).
- Recommendations: Add NER-based scrubbing or block hosted-provider calls for CONFIDENTIAL-classified payloads (verify current behavior before relying on it).

**Third-party CUDA wheel index (supply chain):**
- Risk: `setup.py` installs `llama-cpp-python` from a personal community wheel index (`https://jllllll.github.io/llama-cpp-python-cuBLAS-wheels/AVX2/cu124`) with `--force-reinstall`.
- Files: `setup.py` (`setup_llama_cpp`)
- Recommendations: Pin an exact version+hash, or document manual install from official wheels.

## Performance Bottlenecks

**Blocking synchronous LLM inference inside the async event loop:**
- Problem: `GemmaProvider._generate_with_local_gguf` runs llama.cpp synchronously but is called from `async def _generate` (`backend/app/providers/gemma.py:142-150`) without `asyncio.to_thread`. CPU inference takes 30–90s per response (per `setup.py` output).
- Files: `backend/app/providers/gemma.py`, called in request path via `provider_factory.execute_task` at `backend/app/api/v1/endpoints/signals.py:926` (Ask Athena)
- Cause: llama.cpp call holds the GIL and blocks; while it runs, **every other API request stalls**, including health checks Docker relies on.
- Improvement path: Wrap GGUF inference in `await asyncio.to_thread(...)`, or force Ollama sidecar path (already async over HTTP) when available.

**Leading-wildcard ILIKE scans on every keyword search:**
- Problem: `VectorQueryService.search` issues `%query%` ILIKE against `title` and `content` (plus ID columns) — leading wildcards defeat B-tree indexes → sequential scan of `signals`.
- Files: `backend/app/services/vector_query.py:84-105`
- Improvement path: Add `pg_trgm` GIN index on title/content, or restrict substring search to identifier columns and use vector search for text.

**Full-table loads during pipeline persistence:**
- Problem: `_persist_state_to_db` loads every `Asset.asset_id` and `Company.company_id` into Python sets on each pipeline run to validate FKs.
- Files: `backend/app/workflows/runner.py:148-151`
- Cause: Unbounded SELECTs; fine now, degrades linearly with registry growth.
- Improvement path: Validate FKs via DB constraints and catch IntegrityError, or fetch only referenced IDs.

**Frontend polling fan-out:**
- Problem: `useLiveData` hook polls every 30s per consumer; the monolithic `metaradar.tsx` mounts several pollers plus workspace components, multiplying requests.
- Files: `frontend/lib/hooks.ts`, `frontend/components/metaradar.tsx`
- Improvement path: Consolidate polling per resource, share via context/SWR-style cache.

## Fragile Areas

**Pipeline persistence (`_persist_state_to_db`):**
- Files: `backend/app/workflows/runner.py:142-366`
- Why fragile: Per-row `try/except Exception → logger.warning` means silent partial persistence (failed signals vanish from outputs with only a warning); bronze promotion depends on exact bookkeeping of `failed_signal_ids`; upsert identity depends on external_id/fingerprint truncation rules (255 chars).
- Safe modification: Change one persistence section at a time; keep the retry semantics (unpromoted bronze rows are retried next run); run `tests/test_intelligence_nodes.py` and `tests/test_failure_injection.py`.
- Test coverage: Partially covered (`tests/test_failure_injection.py`, `tests/test_truthfulness_and_invariants.py`); no direct test for partial-failure + bronze retry interaction.

**Source scheduler singleton:**
- Files: `backend/app/services/scheduler.py`
- Why fragile: Process-global singleton started in FastAPI lifespan; asyncio task cancellation paths and advisory-lock release must stay paired; backoff math uses `2 ** min(failures, 4)` with mutable job state.
- Safe modification: Preserve advisory-lock acquire/release symmetry; test with `tests/test_connector_health.py` and `tests/test_observability.py`.
- Test coverage: Health/observability tests exist; no test for multi-instance lock contention.

**Provider fallback chain (Gemma → Grok → degraded BART):**
- Files: `backend/app/providers/gemma.py`, `backend/app/providers/grok.py`, `backend/app/providers/degraded.py`, `backend/app/providers/factory.py`
- Why fragile: Silent degradation is a product-honesty requirement (AGENTS.md #4): any change to exception types (`OllamaUnavailableError`) or factory ordering can flip responses into wrong modes without crashing.
- Safe modification: Extend `tests/test_provider_matrix.py`, `tests/test_providers_live.py` (live marker), `tests/test_failure_injection.py` when touching providers.
- Test coverage: Good — matrix + injection tests exist.

**Contract surface between frontend and backend:**
- Files: `frontend/types/api.ts`, `frontend/lib/mappers.ts`, `scripts/export_openapi.py`, `tests/test_contract_drift.py`, `scripts/generate_parity_matrix.py`
- Why fragile: Hand-mirrored TypeScript types vs FastAPI schemas; drift historically required dedicated drift tests and parity scripts to catch.
- Safe modification: Always regenerate OpenAPI export after changing `backend/app/schemas/__init__.py`; run contract-drift tests.

## Scaling Limits

**PostgreSQL single-node with pgvector HNSW:**
- Current capacity: Local dev scale (synthetic seed via `backend/app/db/seed.py`); pool_size=10, max_overflow=20 (`backend/app/db/session.py`).
- Limit: ILIKE scans + full-table FK validation degrade first; HNSW ef_search=40 fine at millions of rows but memory-bound.
- Scaling path: pg_trgm indexes, connection pooling (pgbouncer), read replicas; embeddings backfill already modularized (`backend/app/services/embeddings_backfill.py`).

**Local LLM throughput:**
- Current capacity: One Gemma 3 4B Q4 model; RTX 3050 4GB budget documented in `docker-compose.yml`; CPU mode 30–90s/response.
- Limit: Event-loop blocking (see performance) makes concurrency ≈ 1 for reasoning tasks.
- Scaling path: Async-offload inference, or route through Ollama daemon which handles its own queueing.

## Dependencies at Risk

**Unpinned Python stack:**
- Risk: Every dependency in `backend/requirements.txt` is `>=` (fastapi, sqlalchemy, langgraph>=0.2.0, fastembed, pydantic v2...). Minor releases can break behavior silently.
- Impact: Non-reproducible CI/local environments; LangGraph 0.x API churn is notorious.
- Migration plan: Pin ranges or lockfile; smoke-test upgrades via existing pytest suite (`pytest.ini`).

**Very-new frontend stack:**
- Risk: `next@16.3.0` + React 19 + Tailwind 4 (`frontend/package.json`); `frontend/AGENTS.md` explicitly warns APIs differ from older training data. `shadcn` listed as a runtime dependency though it's primarily a CLI.
- Impact: Breaking-change risk on upgrades; larger install footprint.
- Migration plan: Move `shadcn` to devDependencies; upgrade via minor steps running `next build` + ESLint gates (per `docs/rules/TESTING_STRATEGY.md`).

**llama-cpp-python CUDA wheels:**
- Risk: Installed from third-party index with `--force-reinstall` (see Security).
- Impact: Supply-chain exposure on dev machines.
- Migration plan: Pin version/hashes; prefer official builds or Ollama sidecar.

## Missing Critical Features

**Zero frontend test infrastructure:**
- Problem: No test runner, no config (vitest/jest/playwright), no `*.test.*` files anywhere under `frontend/`; `package.json` scripts only cover dev/build/lint.
- Blocks: Safe refactoring of the 2,300-line `metaradar.tsx` monolith; regression protection for mappers (`frontend/lib/mappers.ts`) that duplicate backend serialization logic.
- Priority: High — backend has 24 test files; frontend has none.

**No production auth story beyond optional API key:**
- Problem: No user identity, sessions, or RBAC anywhere in `backend/app/` or `frontend/lib/`.
- Blocks: Any multi-user or exposed deployment.
- Priority: Medium (acceptable while strictly local; must precede any hosting).

## Test Coverage Gaps

**Frontend (entire surface):**
- What's not tested: All components, `frontend/lib/api.ts` fetch/error handling, `frontend/lib/hooks.ts` polling logic, `frontend/lib/mappers.ts` transformations.
- Files: `frontend/components/**`, `frontend/lib/**`
- Risk: Mapper drift vs backend schemas goes unnoticed until runtime UI bugs.
- Priority: High

**Partial-failure persistence interplay:**
- What's not tested: Signal insert failure → bronze row left unpromoted → retried next run, end-to-end.
- Files: `backend/app/workflows/runner.py:346-364`
- Risk: Regression here silently drops or double-promotes records.
- Priority: High

**Multi-instance scheduler contention:**
- What's not tested: Two processes racing for the same advisory lock (`pg_try_advisory_lock`) — only single-process paths exercised.
- Files: `backend/app/db/session.py:43-60`, `backend/app/services/scheduler.py`
- Risk: Duplicate ingestion cycles if lock handling regresses.
- Priority: Medium

**Rate limiter correctness:**
- What's not tested: No dedicated tests for `mutation_rate_limit` windowing/pruning behavior.
- Files: `backend/app/api/deps.py`
- Risk: False 429s or no limiting under load.
- Priority: Medium

---

*Concerns audit: 2026-08-24*
