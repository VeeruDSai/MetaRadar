# Codebase Concerns

**Analysis Date:** 2026-08-20

## Tech Debt

**Frontend monolith — `frontend/components/metaradar.tsx`:**
- Issue: A single 2029-line client component file exports 21 components including 13 full page components (`DashboardPage`, `SignalsPage`, `ConfluencePage`, `LifecyclePage`, `RedTeamPage`, `MissingSignalsPage`, `DevelopmentsPage`, `FunctionsPage`, `SourcesPage`, `SettingsPage`, `IntelligencePage`, `SignalDrawer`, `GenericPage`) plus shared UI (`Shell`, `Badge`, `Card`, `SectionTitle`, `SearchModal`, `SignalRow`, `FilterBar`, `CacheClearModal`). All polling, state, charts (recharts), and modal logic live in one file.
- Impact: Any edit risks regression across all 13 pages; no component-level testing possible; re-renders cascade; the file is the single largest maintenance surface in the repo.
- Fix approach: Split into `frontend/components/pages/*.tsx` (one file per page) and `frontend/components/ui/*.tsx`, then add component tests.

**Dead legacy frontend tree — `frontend/src/app/` and `frontend/src/types/`:**
- Issue: The entire `frontend/src/` tree is dormant legacy code per `docs/audits/REPOSITORY_BASELINE_AUDIT.md` ("LEGACY / DORMANT — INACTIVE"). It contains only `frontend/src/app/sources/page.tsx` (31 lines with stale hardcoded claims, e.g. `"Synthetic Demo Set ... 500 Signals Loaded"` — the actual dataset has 3 entries) and a re-export shim `frontend/src/types/api.ts`.
- Impact: Confusing duplicate App Router roots (`frontend/app/` vs `frontend/src/app/`); stale fabricated claims can be mistaken for live status.
- Fix approach: Delete `frontend/src/app/` (keep the contract shim only if CI contract sync still needs it, otherwise move the export into `frontend/types/api.ts`).

**Dead code — `frontend/lib/mock-data.ts`:**
- Issue: Never imported anywhere in the codebase (verified by grep). Ships fabricated signals (`SIG-2481`, `SIG-2478`, ...) with invented scores/confidence in the repo.
- Impact: Confusing for future work; violates the "no fabricated data" principle if ever accidentally wired in.
- Fix approach: Delete the file.

**Dual package managers — `frontend/package-lock.json` + `frontend/pnpm-lock.yaml`:**
- Issue: Both lockfiles are committed. `frontend/package.json` declares `packageManager: pnpm@9.15.5`, CI uses pnpm (`pnpm install --frozen-lockfile=false`), the Dockerfile uses pnpm, but `start.py:233,241` launches the frontend with `npm run dev` — which resolves against the npm lockfile.
- Impact: Two divergent dependency graphs; npm runs may install different versions than pnpm; `--frozen-lockfile=false` in `.github/workflows/ci.yml:55` allows drift.
- Fix approach: Pick pnpm everywhere; delete `frontend/package-lock.json`; use `--frozen-lockfile` in CI and Dockerfile.

**Unpinned Python dependencies — `backend/requirements.txt`:**
- Issue: Every package uses `>=` (e.g. `fastapi>=0.110.0`, `langgraph>=0.2.0`, `fastembed>=0.4.0`); no lockfile (no requirements.lock, poetry, or pip-tools).
- Impact: Non-reproducible builds; CI and prod can silently install breaking versions; the recent `langgraph 0.x` API churn is a live risk.
- Fix approach: Pin exact versions or generate a lockfile (`pip-compile`); verify `pytest` after any bump.

**Frontend type-safety erosion — `frontend/lib/api.ts` and `frontend/lib/hooks.ts`:**
- Issue: Despite `"strict": true` in `frontend/tsconfig.json`, `mapSignal(raw: any)` (`frontend/lib/api.ts:92`), several `any[]` payload types (`api.ts:182,207,245,267`), and `deps: any[]` in `frontend/lib/hooks.ts:24`. One `eslint-disable-next-line react-hooks/exhaustive-deps` at `frontend/lib/hooks.ts:128`.
- Impact: The UI presentation layer (`mapSignal`) is untyped against the API contract; malformed backend payloads flow through silently.
- Fix approach: Type `mapSignal` against the generated contract `frontend/types/api.ts` (currently 374 hand-rolled lines) or a partial-typed mapper.

**Stale codebase map — `.planning/codebase/`:**
- Issue: Git status shows `.planning/codebase/ARCHITECTURE.md`, `CONCERNS.md`, `CONVENTIONS.md`, `INTEGRATIONS.md`, `STRUCTURE.md`, `TESTING.md` deleted; only `STACK.md` remains (modified).
- Impact: Phase planner/executor lose codebase context; this document is part of the remediation.

## Known Bugs

**Recalibration double-applies historical feedback — `backend/app/services/calibration.py`:**
- Symptoms: `recalibrate_role` (line 218) queries ALL `CalibrationFeedback` rows (`fb_query = select(CalibrationFeedback)` at line 230) with no applied/unapplied filter, and feedback is never marked applied. Every recalibration re-applies the same feedback history, compounding weight drift toward the feedback mean.
- Files: `backend/app/services/calibration.py:230-236`
- Trigger: Call `POST /calibrate` twice with feedback present.
- Workaround: None — the `unapplied_count` returned by `submit_feedback` (line 145-151) also counts lifetime totals, so `recalibration_triggered` fires on cumulative feedback, not pending feedback.
- Fix: Add an `applied` boolean / `applied_at` column to `calibration_feedback` (migration 004) and filter `recalibrate_role` to unapplied rows, then mark them applied.

**Write-during-read — `backend/app/services/calibration.py:get_weights`:**
- Symptoms: `GET /calibration/weights` auto-inserts missing `ScoringWeights` rows (lines 183-201) — a GET endpoint mutates the database.
- Impact: Unexpected DB writes from a read path; complicates read-replica scaling and cache layers.
- Fix: Seed weights in the startup/seed path instead; make `get_weights` read-only.

**Synthetic data silently enters the live pipeline — `backend/app/workflows/nodes/ingest.py:76-78`:**
- Symptoms: When `raw_signals_bronze` is empty, `node_ingest` falls back to `data/synthetic_signals.json` without labeling the rows as synthetic in pipeline state. Downstream nodes (`node_nlp_extract`, `node_synthesize`, `node_redteam`) process them as real signals, and results are persisted to `signals`.
- Files: `backend/app/workflows/nodes/ingest.py:15-29,76-78`; `data/synthetic_signals.json` (3 entries)
- Impact: Violates the "no fabricated telemetry" governance rule (AGENTS.md); users see synthetic intelligence presented as analyzed fact.
- Fix: Tag fallback rows with `source_type: "synthetic"` + `is_synthetic: true` in state, propagate the flag through persistence, and surface it in the UI (`Signal` schema).

**Seed data is indistinguishable from live analysis — `backend/app/db/seed.py`:**
- Symptoms: The seed script inserts `Signal` rows with hardcoded `score_breakdown` totals (e.g. `{"total_score": 88, ...}` at line 255, `94` at line 267), Confluence rows with hardcoded `signal_count=4`/`signal_count=3` (lines 186-196) that don't match actual signal counts, and Contradictions with hardcoded `confidence=0.89`/`0.78` (lines 199-218) never computed by the red-team engine. No `is_synthetic` marker on any seeded row.
- Impact: The dashboard shows these as real signals/scores/confluences; the claims are already stale (e.g. "PDUFA action date scheduled for late 2026", "primary completion as June 2026" — today is Aug 2026).
- Fix: Mark all seeded rows synthetic, or move them to the `raw_signals_bronze` + labeled fallback path instead of direct `signals` inserts.

**Hardcoded evidence in `/athena` — `backend/app/api/v1/endpoints/signals.py:257-261`:**
- Symptoms: The evidence list passed to the LLM is three static strings ("Hemgenix 3-year durability shows sustained FIX levels at 36.5%", "Alhemo European rollout expanded to 14 centers", "Qfitlia sub-q monthly dosing approved in Japan"), and `evidence_count=len(evidence)` (line 285) is reported to the UI.
- Impact: Answers are not grounded in the actual database; `evidence_count` is fabricated relative to real data.
- Fix: Query real `Signal`/`Evidence` rows via vector search and pass genuine evidence.

**Hardcoded confluence score — `backend/app/api/v1/endpoints/signals.py:198-213`:**
- Symptoms: When any confluences exist, `/overview` returns `confluence_score = 75.0` and hardcoded drivers `["Clinical trial readouts", "Payer & regulatory filings"]` — not computed from data.
- Impact: Misleading score presented as computed intelligence.
- Fix: Compute from actual Confluence/Signal aggregations or return `null` with an "uncomputed" label.

**Fabricated excerpt text in `/red-team` — `backend/app/api/v1/endpoints/intelligence.py:158-159`:**
- Symptoms: `claim_a_excerpt=f"Primary evidence claim for {c.claim_a_id}"` and `claim_b_excerpt=f"Contradicting evidence claim for {c.claim_b_id}"` — placeholder strings presented as evidence excerpts.
- Impact: The UI drawer shows text that is not the actual claim.
- Fix: Store and return real excerpts, or drop the fields.

**Heuristic confidence presented as model confidence — `backend/app/api/v1/endpoints/intelligence.py:193`:**
- Symptoms: `/missing-signals` computes `confidence = min(0.95, 0.5 + (0.05 * (overdue // 10)))` — an arithmetic heuristic surfaced as a confidence score in the API response.
- Impact: Users interpret it as model-derived confidence.
- Fix: Rename to `overdue_confidence` or return `null` with an explicit heuristic label.

**`/cache/clear` reports success without clearing — `backend/app/api/v1/endpoints/cache.py:16-32`:**
- Symptoms: Returns `status="cleared"` even when `REDIS_URL` is unset ("in-memory cache clear simulated", line 28) and always reports `keys_cleared=0`.
- Impact: Misleading operational telemetry; the Settings page toast claims "Server cache cleared successfully" regardless.
- Fix: Report `cache_unavailable` when Redis is unreachable; count keys or drop the field.

## Security Considerations

**Default database credentials baked into code — `backend/app/core/config.py:19` and `docker-compose.yml:8,41,72`:**
- Risk: `DATABASE_URL` defaults to `postgresql+asyncpg://metaradar:metaradar_pass@localhost:5432/metaradar` and compose hardcodes `POSTGRES_PASSWORD: metaradar_pass`. If deployed without env override, the DB is exposed with a known credential. Flagged as `H8` in `docs/audits/CONCERNS_VERIFICATION_MATRIX.md` ("Dev credentials should be changed in production .env") — unaddressed.
- Files: `backend/app/core/config.py:19`, `docker-compose.yml:8,41,72`
- Current mitigation: `Settings` reads `.env` via pydantic-settings.
- Recommendations: Fail fast at startup if `DATABASE_URL` still contains `metaradar_pass` outside dev; use docker secrets or env injection for compose.

**`start.py` force-kills arbitrary processes by port — `start.py:91-138`:**
- Risk: `free_port_if_in_use` runs `netstat -ano`, matches any `LISTENING` line containing the port, and executes `taskkill /F /T /PID` — killing the entire process tree of ANY process on ports 3000/8000 without verifying it belongs to MetaRadar.
- Files: `start.py:100-121` (win32 branch)
- Current mitigation: Skips PID equal to `os.getpid()` only.
- Recommendations: Verify the owning process command line contains `metaradar|uvicorn|next` before killing; or fail with a clear message instead of killing.

**Zero authentication on all API endpoints:**
- Risk: Every endpoint in `backend/app/api/v1/endpoints/` (`signals`, `search`, `intelligence`, `registry`, `cache`, `pipeline`, `feedback`, `health`) is unauthenticated. `POST /cache/clear` can flush Redis; `POST /pipeline/run` can trigger expensive LLM pipeline executions (resource-abuse/DoS vector); `POST /feedback` can poison calibration data. This is a medical-competitive-intelligence platform with no identity layer.
- Files: all endpoint modules under `backend/app/api/v1/endpoints/`; CORS config `backend/app/core/config.py:23`
- Current mitigation: CORS default restricts browsers to `http://localhost:3000`; `allow_methods=["*"]`, `allow_headers=["*"]`, `allow_credentials=True` in `backend/app/main.py:49-56`.
- Recommendations: Add API-key or OIDC auth middleware; at minimum protect `/cache/clear` and `/pipeline/run`; scope CORS methods/headers.

**PII/PHI scrubber heuristic coverage — `backend/app/services/pii.py:5-11`:**
- Risk: Only 5 regex patterns (email, phone, SSN, MRN, DOB). Custom clinical formatting (dates without DOB prefix, international IDs, names) passes through to external providers.
- Files: `backend/app/services/pii.py`
- Current mitigation: Privacy gate in `backend/app/providers/grok.py:56-70` blocks non-PUBLIC/SYNTHETIC classification from reaching xAI; scrubbing happens pre-persistence in connectors.
- Recommendations: Expand pattern set (H1 residual risk in `docs/audits/CONCERNS_VERIFICATION_MATRIX.md`); add a test corpus of clinical formats.

## Performance Bottlenecks

**N+1 queries in overview and confluence endpoints:**
- Problem: `/overview` runs a per-development COUNT query (`backend/app/api/v1/endpoints/signals.py:181-183`) plus ~8 sequential aggregations on every load; `/confluence` runs a per-row signals query (`backend/app/api/v1/endpoints/intelligence.py:55-61`).
- Files: `backend/app/api/v1/endpoints/signals.py:145-224`, `backend/app/api/v1/endpoints/intelligence.py:52-71`
- Cause: ORM row iteration with per-row queries instead of joins/group-by.
- Improvement path: Single grouped query with `func.count` + `GROUP BY development_id`; join signals in `/confluence`.

**Synchronous heavy pipeline inside an HTTP request — `backend/app/api/v1/endpoints/pipeline.py:25-53`:**
- Problem: `POST /pipeline/run` executes the full 11-node LangGraph pipeline (including local LLM inference via Gemma/Ollama) synchronously in the request handler with no timeout, background task, or job queue.
- Impact: Requests can hang for minutes; uvicorn workers blocked; no retry/idempotency semantics beyond the advisory-lock helper that is never used (see below).
- Improvement path: Fire-and-forget with a background task + status polling (the `pipeline_runs` table and `/pipeline/status/{id}` endpoint already exist).

**Frontend 30-second polling with parallel fetches — `frontend/lib/hooks.ts` + `frontend/components/metaradar.tsx`:**
- Problem: `useLiveData` (default 30s interval) drives every dashboard widget; `getOverview` (`frontend/lib/api.ts:179-226`) additionally fetches `/signals?limit=20` in parallel on each tick. `SettingsPage` exposes cadence options but the value is never persisted or applied to widgets (`frontend/components/metaradar.tsx:1473-1475,1530-1539` — `pollingInterval` state is dead).
- Impact: Continuous DB load from an idle dashboard; every missed backend field is masked by `?? 0` defaults in `frontend/lib/api.ts:188-224`.
- Improvement path: Use the settings value; debounce; server-side cache with Redis (currently Redis is unused for caching — only `/health/ready` ping and `/cache/clear` touch it).

**`/health/models` instantiates an LLM provider per poll — `backend/app/api/v1/endpoints/health.py:64-75`:**
- Problem: Every call constructs `GemmaProvider()` and performs a real HTTP GET to Ollama `/api/tags`; the frontend polls this endpoint.
- Improvement path: Cache availability for ~10s; reuse a module-level client.

## Fragile Areas

**`_load_synthetic_fallback` path resolution — `backend/app/workflows/nodes/ingest.py:17-20`:**
- Why fragile: Two hardcoded relative paths (`parents[3]` and `parents[4]`) — breaks on any file relocation; only the existence is asserted in `tests/test_e2e_calibration_scenario.py:47-48`.
- Safe modification: Resolve via project root constant; move to a loader module.

**Provider fallback chain — `backend/app/providers/factory.py:18-46`:**
- Why fragile: Any exception in Gemma silently falls through to Grok (if enabled) then BART degraded mode; `GrokProvider.generate_summary` (`backend/app/providers/grok.py:117-128`) defaults to `DataClassification.UNKNOWN` which the privacy gate always rejects — a latent always-failing method. `ModelMetadataSchema` hardcodes `fallback_reason="gemma_unavailable"` (`grok.py:171`) even when Grok was the primary provider in `xai` mode.
- Safe modification: Keep the chain but log each fallback step with reasons; fix `generate_summary` classification; compute `fallback_reason` honestly.
- Test coverage: `tests/test_provider_matrix.py`, `tests/test_providers_live.py` (the latter skipped without `LIVE_XAI_KEY`).

**Windows-centric launcher — `start.py`:**
- Why fragile: `taskkill`/`netstat` (win32 branch) and `lsof`/`kill -9` (non-win32) with no ownership verification; log file handles opened at `start.py:206,239` are never closed; `--daemon` returns immediately with no supervision.
- Safe modification: See security section for kill-by-port; use `contextlib` or subprocess `stdout=` file handles that are closed.

**Dead infrastructure helpers — `backend/app/db/session.py:43-60`:**
- `try_advisory_lock` / `release_advisory_lock` are never called; `PipelineRunner` (`backend/app/workflows/runner.py`) does not prevent concurrent runs. The `AuditLog` model (`backend/app/models/__init__.py:308`) is defined but never written. Redis is provisioned (`docker-compose.yml:20-32`) but no code caches anything.
- Impact: Single-execution protection, audit trail, and caching are promised-but-absent; concurrent `/pipeline/run` calls can double-process the same bronze rows (mitigated only by the un-persisted `pipeline_run_id` check in `ingest.py:54-56`).

## Scaling Limits

**Pipeline execution:**
- Current capacity: In-memory, sequential, single-process LangGraph; `batch_size` default 50 (`backend/app/workflows/runner.py:27`); no Celery/ARQ/queue.
- Limit: LLM inference per signal makes batches slow; HTTP-triggered runs block workers.
- Scaling path: Background task queue + worker process; batch embedding with `fastembed`; precompute overview aggregations.

**Database access pattern:**
- Current: Async SQLAlchemy pool `pool_size=10, max_overflow=20` (`backend/app/db/session.py:14-16`).
- Limit: N+1 queries and unauthenticated repeated pipeline triggers will saturate connections first.
- Scaling path: Aggregation views/materialized summary tables; Redis caching of `/overview` with `last_sync` invalidation.

**Vector search:**
- Current: `EMBEDDING_DIMENSION=384` fixed; pgvector in Postgres 16 (`backend/app/core/config.py:46-49`); `backend/app/services/vector_query.py` has no direct unit test (only indirectly through retrieval tests).
- Limit: No index health check; embedding backfill (`backend/app/services/embeddings_backfill.py`) untested.
- Scaling path: Verify HNSW index on `signals.embedding`; test backfill idempotency.

## Dependencies at Risk

**`langgraph>=0.2.0` (`backend/requirements.txt:16`):**
- Risk: Unpinned 0.x API; graph construction in `backend/app/workflows/graph.py:30-56` may break on minor bumps.
- Impact: Full pipeline broken on bad upgrade.
- Migration plan: Pin exact tested version; add a graph-compile smoke test.

**Python version drift — 3.11 vs 3.13:**
- Risk: CI (`actions/setup-python` `3.11` in `.github/workflows/ci.yml:22`) and `backend/Dockerfile:1` (`python:3.11-slim`) use 3.11; local caches (`tests/__pycache__/*cpython-313*`) show 3.13 in dev.
- Impact: Behavior differences surface only after merge.
- Migration plan: Align dev tooling to 3.11 or upgrade CI/Dockerfile to 3.13.

**`next: 16.3.0` + `react: ^19` + `framer-motion: ^13` + `recharts: ^3.10` (`frontend/package.json`):**
- Risk: Next 16 is a recent major; `react ^19` and `framer-motion ^13` permit minor drift; `shadcn` CLI (`^4.8.0`) is shipped as a runtime dependency though it is a dev tool.
- Impact: Turbopack/App Router changes can break the `[section]` dynamic route pattern (`frontend/app/[section]/page.tsx`).
- Migration plan: Exact-pin react/framer-motion; move `shadcn` to devDependencies.

## Missing Critical Features

**Authentication/authorization:** Entire API surface is open (see Security). Blocks any real deployment behind a corporate network.
**Frontend tests:** Zero test files exist under `frontend/` — the entire Next.js UI (including the 2029-line monolith) has no automated verification. CI runs only `tsc`/`eslint`/`build` (`.github/workflows/ci.yml:52-58`).
**Background job queue:** Pipeline runs block HTTP; no retry/scheduling beyond the unused advisory-lock helpers.
**Real caching:** Redis is provisioned but unused for reads; `/cache/clear` clears nothing meaningful.
**Observability of pipeline nodes:** `node_statuses` exist in state but no metrics/OTEL export; `docs/OBSERVABILITY_STANDARDS.md` exists as policy only.

## Test Coverage Gaps

**Frontend (entire UI):**
- What's not tested: All components/pages in `frontend/components/metaradar.tsx`, `frontend/lib/api.ts` mappers, `frontend/lib/hooks.ts` polling.
- Files: `frontend/components/metaradar.tsx`, `frontend/lib/api.ts`, `frontend/lib/hooks.ts`
- Risk: The monolith refactor, mapper changes (`mapSignal`), and polling behavior can regress unnoticed.
- Priority: High

**Calibration service:**
- What's not tested: The double-apply bug path (recalibrate twice), write-during-read in `get_weights`, semver fallback branch (`backend/app/services/calibration.py:324-330`).
- Files: `backend/app/services/calibration.py`
- Risk: Weight drift and version corruption in production.
- Priority: High

**Workflow ingest fallback:**
- What's not tested: `_load_synthetic_fallback` labeling; fallback path resolution; concurrent-run protection.
- Files: `backend/app/workflows/nodes/ingest.py`
- Risk: Synthetic signals silently analyzed as real.
- Priority: High

**Untested modules (no direct test import):**
- `backend/app/services/embeddings_backfill.py`, `backend/app/api/v1/endpoints/pipeline.py` (only via TestClient smoke), `backend/app/providers/degraded.py` internals, `backend/app/workflows/runner.py` failure branches (DB persistence failure paths at `runner.py:52-54,85-86,104-105`).
- Risk: Backfill idempotency and pipeline crash paths unverified.
- Priority: Medium

**Live providers:**
- What's not tested: `tests/test_providers_live.py` is skipped without `LIVE_XAI_KEY` env; Ollama/Gemma weight loading requires local GPU/CPU runtime (C2 in `docs/audits/CONCERNS_VERIFICATION_MATRIX.md`).
- Priority: Medium

---

*Concerns audit: 2026-08-20*