# Codebase Concerns

**Analysis Date:** 2026-08-24

## Tech Debt

**Frontend monolith component:**
- Issue: `frontend/components/metaradar.tsx` is a 2,249-line single client file containing ~15 distinct components (app shell/nav, command palette, dashboard KPIs, signal filters, cache controls, settings panel, Athena Q&A, calibration form). It is also the most-churned file in recent history (8 of last 8 commits are `fix(ui)` touching it).
- Files: `frontend/components/metaradar.tsx`
- Impact: Merge-conflict hotspot; untestable in isolation; any edit risks unrelated regressions across all 13 workspaces.
- Fix approach: Extract each inner component into `frontend/components/<domain>/` alongside the existing workspace components (e.g., `AthenaWorkspace.tsx`, `CalibrationWorkspace.tsx`). Move shared filter state into a hook under `frontend/lib/hooks.ts`. Do this incrementally per workspace.

**Backward-compat API shim layer in frontend:**
- Issue: `frontend/lib/api.ts` maintains dual naming (`getOverview = fetchOverview`, etc.) and five overloads that sniff `AbortSignal` in the first parameter position (`getSignals`, `getConfluences`, `getLifecycles`, `getRedTeamContradictions`, `getMissingSignals`, `getDevelopments` at lines 41–133). The positional sniffing breaks silently if a caller passes options objects.
- Files: `frontend/lib/api.ts`
- Impact: Confusing call surface; new code can pick either name; type errors surface late.
- Fix approach: Migrate all callers to the canonical `(args, signal)` signatures, then delete aliases and AbortSignal-sniffing overloads.

**Pervasive `any` in the API client despite strict TS:**
- Issue: `fetchOverview` parses `apiFetch<any>`, `mapSearchResult(r: any)`, `triggerIngestionRun(): Promise<any>`, `inspectConfluence(): Promise<any>` — response shapes are unchecked at these boundaries even though `frontend/types/api.ts` is CI-synced from OpenAPI.
- Files: `frontend/lib/api.ts` (lines 135–147, 208–254, 515–550)
- Impact: Contract drift gate protects `frontend/types/api.ts` but not these inline `any` mappings; backend renames reach production as `undefined` fields at runtime.
- Fix approach: Type every `apiFetch<T>` call with the generated types from `frontend/types/api.ts`; keep mappers as the only `unknown → typed` boundary.

**Silent exception swallowing in scheduler/runner:**
- Issue: Most of the 88 broad `except Exception` blocks log correctly, but two swallow entirely: `scheduler.py:203-204` (`except Exception: pass` around DB next-run update) and `runner.py:138-139` (`except Exception: pass` around PipelineRun failure-status update).
- Files: `backend/app/services/scheduler.py`, `backend/app/workflows/runner.py`
- Impact: Observability blind spots exactly where failure telemetry matters most (violates the project's own ENGINEERING_STANDARDS "logged exceptions" rule fixed on 2026-08-23).
- Fix approach: Replace both `pass` bodies with `logger.warning(..., exc_info=True)`.

**Dual frontend lockfiles + loose CI install:**
- Issue: Both `frontend/package-lock.json` and `frontend/pnpm-lock.yaml` exist while `package.json` declares `packageManager: pnpm@9.15.5`; CI runs `pnpm install --frozen-lockfile=false` (`.github/workflows/ci.yml`), so installs are non-deterministic and npm lockfile drifts.
- Files: `frontend/package-lock.json`, `frontend/pnpm-lock.yaml`, `.github/workflows/ci.yml`
- Impact: "Works locally, differs in CI" class of bugs; no reproducible dependency resolution.
- Fix approach: Delete `package-lock.json`, switch CI to `--frozen-lockfile`.

**Misplaced runtime dependency:**
- Issue: `shadcn` (a CLI tool) is listed under runtime `dependencies` in `frontend/package.json`.
- Files: `frontend/package.json`
- Impact: Bloated installs; risk of accidental imports of CLI internals.
- Fix approach: Move to `devDependencies` or remove if unused.

## Known Bugs

**Live connector endpoints returning errors (observed live):**
- Symptoms: OpenFDA query syntax returns HTTP 404 for some queries; EMA RSS (`https://www.ema.europa.eu/en/medicines/rss`) returns 404/429. System records honest `UNHEALTHY`/`DEGRADED` telemetry rather than fabricating data.
- Files: `backend/app/connectors/fda.py`, `backend/app/connectors/ema.py`
- Trigger: Run `IngestionService.run_connectors(["fda", "ema"])` against live APIs (evidence in `.planning/debug/live-ingestion-provenance-and-end-to-end-validation.md`).
- Workaround: None — 2 of 5 sources may persistently yield no live data until query syntax/endpoint is corrected. Backoff logic caps retries via `SCHEDULER_MAX_BACKOFF_MINUTES`.

**Previously fixed (2026-08-23) — verify stays fixed:**
- Grok provider missing stdlib/typing imports (`NameError`) — fixed in `backend/app/providers/grok.py`.
- `tests/test_foundation.py` uncollectable by pytest — refactored to standard pytest functions.
- `scripts/apply_phase7_migrations.py` stamped stale revision `004_phase7_truthfulness` instead of head `011_widen_fingerprint`.
- Full history in `.planning/debug/concerns-md-audit-fixes.md`, `.planning/debug/docker-backend-connection-failure.md` (Docker daemon race, missing Alembic tables 003, seed FK flush order, Windows cp1252 emoji crash), and `.planning/debug/frontend-eaddrinuse-exit-code-1.md` (orphaned node.exe requiring `taskkill /F /T`).

## Security Considerations

**Mutation auth is opt-in (open by default):**
- Risk: Every mutation endpoint (ingest, pipeline, recalibrate, feedback, cache clear, watch-item confirm) is unauthenticated when `METARADAR_API_KEY` is unset — the shipped default.
- Files: `backend/app/api/deps.py` (lines 16–27), `backend/app/core/config.py` (line 35)
- Current mitigation: Intentional local-dev posture, documented in docstring; rate limiting active.
- Recommendations: Add a startup warning log when mutations are unauthenticated; consider failing closed (env-gated) for any non-localhost bind.

**In-memory rate limiter — per-process and unbounded:**
- Risk: `_rate_buckets` module-level dict grows one key per client IP forever (entries pruned only when that client requests again); limits don't apply across uvicorn workers/replicas.
- Files: `backend/app/api/deps.py` (lines 13, 30–44)
- Current mitigation: Adequate for single-process local dev.
- Recommendations: Move counters to Redis (already a dependency); add periodic eviction of stale buckets.

**Default database credentials in committed defaults:**
- Risk: `DATABASE_URL` default embeds `metaradar:metaradar_pass` (`backend/app/core/config.py` line 30) — documented dev-only, but deploys that skip `.env` inherit known creds.
- Files: `backend/app/core/config.py`, `.env.example`
- Current mitigation: `.env` gitignored; `docker-compose.yml` provisions matching local creds only.
- Recommendations: Log a hard warning when defaults are used with a non-localhost host.

**Heuristic PII scrubbing:**
- Risk: `PIIPHIScrubber` uses regex patterns only; unusual formats (custom MRN schemes, free-text names) pass through. Already flagged in `docs/audits/CONCERNS_VERIFICATION_MATRIX.md` (H1).
- Files: `backend/app/services/pii.py`
- Current mitigation: Privacy gate blocks anything not explicitly classified `PUBLIC`/`SYNTHETIC` from leaving the host (`backend/app/providers/grok.py`); secret scrubbing via `backend/app/core/redact.py` covers logs and query params.
- Recommendations: Expand pattern coverage before enabling any hosted provider by default; keep `ENABLE_GROK_FALLBACK=false` default.

**Secret hygiene status:** No hardcoded secrets found in tracked source; `.env` gitignored; GGUF weights (2.3 GB `models/gemma-3-4b-it-Q4_K_M.gguf`) gitignored via `/models/*` rule in `.gitignore`.

## Performance Bottlenecks

**Event-loop-blocking GGUF inference:**
- Problem: `_generate_with_local_gguf` runs synchronous llama-cpp inference directly inside `async def _generate` without executor offload — the entire FastAPI event loop stalls for the full generation (seconds+), freezing health checks and all concurrent requests.
- Files: `backend/app/providers/gemma.py` (lines 87–148)
- Cause: `self._llama_instance(...)` is CPU/GPU-bound synchronous code awaited nowhere. Contrast with correct pattern in `backend/app/services/embeddings.py` (`run_in_executor`).
- Improvement path: Wrap in `asyncio.get_running_loop().run_in_executor(None, ...)` exactly like `EmbeddingService._embed_sync`.

**Filesystem model scan on every LLM call:**
- Problem: `find_local_gguf_model()` globs `models/` twice per generation (once to execute, once for the metadata tag at `gemma.py:145,238`).
- Files: `backend/app/providers/gemma.py`
- Improvement path: Resolve once at startup/init; invalidate only on config change.

**Sequential per-signal embeddings during persistence:**
- Problem: `_persist_state_to_db` awaits `embedding_service.embed_signal(sig)` one signal at a time inside the insert loop — N+1 pattern when `embed_batch` exists.
- Files: `backend/app/workflows/runner.py` (line 207), `backend/app/services/embeddings.py` (line 87)
- Improvement path: Pre-compute all embeddings with one `embed_batch(texts)` call before the insert loop.

**Full-table ID loads for FK validation:**
- Problem: Persistence loads every `Asset.asset_id` and `Company.company_id` into Python sets to guard FK violations.
- Files: `backend/app/workflows/runner.py` (lines 148–151)
- Cause: Unbounded `select` with no limit — fine now, degrades linearly with catalog growth.
- Improvement path: Validate against seeded domain IDs from `config/haemophilia.yaml` or use FK-error-driven retry per row.

## Fragile Areas

**OpenAPI contract sync chain:**
- Files: `scripts/export_openapi.py`, `contracts/openapi.json`, `frontend/types/api.ts`, `.github/workflows/ci.yml`
- Why fragile: `frontend/types/api.ts` is generated; editing it by hand fails CI (`git diff --exit-code`). Template lives in a Python script — easy to miss.
- Safe modification: Always edit the TS template inside `scripts/export_openapi.py`, then run `python scripts/export_openapi.py`; verify with `pytest tests/test_contract_drift.py`.
- Test coverage: Covered by `tests/test_contract_drift.py`.

**Alembic ↔ ORM lockstep:**
- Files: `backend/alembic/versions/001_*.py` through `011_widen_signals_fingerprint.py`, `backend/app/models/__init__.py`
- Why fragile: History shows models drifting from migrations (003 emergency migration added `contradictions`, `calibration_history`, `scoring_weights`; stale stamp bug in `scripts/apply_phase7_migrations.py`).
- Safe modification: After any `backend/app/models/__init__.py` change, autogenerate a revision and run `alembic upgrade head` against a real Postgres before committing; never hand-stamp versions.

**Bronze promotion retry mechanics:**
- Files: `backend/app/workflows/runner.py` (lines 157, 190, 330, 346–364)
- Why fragile: Retry-on-failure depends on exact 36-char UUID string checks and on `failed_signal_ids` bookkeeping; malformed IDs fall back to fresh random UUIDs which break dedup upserts across runs.
- Safe modification: Preserve the "only promote persisted rows" invariant (comment block at lines 346–350) when touching persistence; add tests for malformed-ID paths.
- Test coverage: Partial — see `tests/test_ingestion.py`, `tests/test_provenance.py`; no direct test of failed-signal retry.

**Windows-specific launcher:**
- Files: `start.py` (taskkill process-tree kill, TCP port polling), `backend/app/db/seed.py` (`sys.stdout.reconfigure(encoding='utf-8')`)
- Why fragile: Two prior incidents traced here (Docker daemon race; orphaned node.exe EADDRINUSE). Cross-platform behavior (Linux/macOS cleanup path) less exercised.
- Safe modification: Keep `wait_for_backing_service` polling before backend launch; preserve crash-log tail printing.

## Scaling Limits

**Single-process assumptions:**
- Current capacity: Scheduler singleton (`SourceScheduler.get_instance()`), advisory locks, and rate limiter all assume one backend process; pool is `pool_size=10, max_overflow=20` (`backend/app/db/session.py`).
- Limit: Multiple uvicorn workers double-run connectors (advisory locks mitigate but waste cycles) and each worker keeps its own GGUF model (~2+ GB RAM) and rate buckets.
- Scaling path: Redis-backed rate limiting; extract scheduler to a dedicated worker process; share model server (Ollama sidecar already supported).

**Vector search scale:**
- Current capacity: pgvector with 384-dim MiniLM embeddings; bronze table prunable via `RAW_SIGNAL_RETENTION_DAYS`.
- Limit: Exact scan fine at thousands of rows; needs IVFFlat/HNSW index if corpus reaches hundreds of thousands.
- Scaling path: Add pgvector index migration when signal counts grow.

## Dependencies at Risk

**`llama-cpp-python`:**
- Risk: Primary GGUF execution path requires it (`backend/app/providers/gemma.py` line 90) but it is absent from `backend/requirements.txt` — an undeclared soft dependency with silent fall-through to Ollama.
- Impact: Fresh installs get Ollama-only behavior with no error; GPU builds of llama-cpp are notoriously platform-sensitive.
- Migration plan: Document as optional extra (`requirements-llama.txt`) or detect and surface in `/health/models` telemetry.

**Unpinned Python dependencies:**
- Risk: `backend/requirements.txt` uses bare `>=` floors with no lockfile — builds are non-reproducible; `langgraph>=0.2.0` and `fastapi>=0.110.0` move fast.
- Impact: CI and local environments drift apart over time.
- Migration plan: Pin with hashes (`pip-compile`) or adopt `uv`/`poetry` lockfile.

**Bleeding-edge frontend stack:**
- Risk: Next.js 16.3.0 + React 19 + Tailwind v4 + ESLint 10 — repo's own agent rules warn APIs may differ from training data (`frontend/AGENTS.md`).
- Impact: Upgrades require reading bundled docs; some libs (`framer-motion@13`, `recharts@3`) release breaking changes frequently.
- Migration plan: Pin exact versions (currently done for `next`/`typescript` only); test upgrades on branches.

## Missing Critical Features

**Retention pruning never invoked:**
- Problem: `prune_expired_bronze(retention_days)` exists (`backend/app/services/ingestion.py` line 229, added 2026-08-23) but nothing calls it — no scheduler hook, no endpoint, no script. `RAW_SIGNAL_RETENTION_DAYS=30` is dead configuration.
- Blocks: Bronze table grows unbounded in long-running deployments; compliance intent of the retention setting unrealized.

**No frontend test infrastructure:**
- Problem: No jest/vitest/playwright/cypress anywhere; zero unit, component, or E2E tests for 20+ components and the API client.
- Blocks: All UI verification is manual browser walkthroughs (see debug docs); regressions like the recent KPI-animation churn cycle (8 consecutive `fix(ui)` commits) are caught only by eye.

## Test Coverage Gaps

**Auth & rate-limit dependencies:**
- What's not tested: `require_mutation_auth` and `mutation_rate_limit` have zero dedicated tests — grep finds no references in `tests/`.
- Files: `backend/app/api/deps.py`
- Risk: Security-critical gating could regress silently (e.g., header alias change, bucket math off-by-one).
- Priority: High.

**Scheduler resilience paths:**
- What's not tested: Advisory-lock contention (`SKIPPED_LOCKED`), exponential backoff transitions, post-ingestion pipeline trigger, and the silent DB-update failure at `scheduler.py:203`.
- Files: `backend/app/services/scheduler.py`, `tests/test_connector_health.py`
- Risk: Scheduling/starvation bugs appear only in multi-day runs.
- Priority: Medium-High.

**Frontend (entire):**
- What's not tested: All workspaces, `useLiveData` polling/abort semantics, `lib/mappers.ts` mapping rules ("never invent relevance" invariant), error-state rendering.
- Files: `frontend/lib/hooks.ts`, `frontend/lib/mappers.ts`, `frontend/lib/api.ts`, `frontend/components/**`
- Risk: Contract mapping bugs ship to users; polling leaks/regressions undetectable.
- Priority: High (introduce vitest + React Testing Library; playwright for smoke route).

**Coverage enforcement:**
- What's not tested: `pytest-cov` installed but no `--cov` gate or threshold in `pytest.ini` or `.github/workflows/ci.yml`; CI green ≠ meaningful coverage.
- Files: `pytest.ini`, `.github/workflows/ci.yml`
- Priority: Medium (add `--cov=backend/app --cov-fail-under=` floor).

---

*Concerns audit: 2026-08-24*
