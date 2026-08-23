# Codebase Concerns

**Analysis Date:** 2026-08-23

## Tech Debt

**Frontend monolith component:**
- Issue: `frontend/components/metaradar.tsx` is a single 2,079-line client component (~40 lucide icon imports) containing the app shell, navigation, filtering, polling orchestration, and inline page components (LifecyclePage, GenericPage).
- Files: `frontend/components/metaradar.tsx`
- Impact: Merge-conflict hotspot; whole-tree re-renders; workspace logic untestable/unreuseable.
- Fix approach: Extract shell/nav into `frontend/components/shell/`; per-section workspaces already exist (`frontend/components/confluence/ConfluenceWorkspace.tsx`, etc.) — move remaining inline pages out.

**Dual migration systems:**
- Issue: Proper Alembic chain (`backend/alembic/versions/001_initial_v51_schema.py` ... `011_widen_signals_fingerprint.py`) coexists with a raw-SQL script that hand-creates columns AND force-stamps `alembic_version` to `'004_phase7_truthfulness'`.
- Files: `scripts/apply_phase7_migrations.py`, `backend/alembic/versions/*`
- Impact: Running the script on a DB migrated past 004 silently rewrites alembic_version backwards; two sources of truth for DDL.
- Fix approach: Delete the script or reduce it to "run `alembic upgrade head`"; never hand-write `alembic_version` rows.

**Schema churn around signal identity columns:**
- Issue: Migrations 006 (`widen signals external_id`), 010 (`non_unique_signal_identifiers`), 011 (`widen signals fingerprint`) show the identity/dedup contract broke repeatedly.
- Files: `backend/alembic/versions/006_widen_signals_external_id.py`, `backend/alembic/versions/010_non_unique_signal_identifiers.py`, `backend/alembic/versions/011_widen_signals_fingerprint.py`
- Impact: High-risk area for future fingerprint/upsert changes.
- Fix approach: Lock identity contract behind tests (`tests/test_contract_drift.py`) before touching dedup code.

**Inconsistent logging frameworks (scrubbing bypassed):**
- Issue: structlog is configured with a secret-scrubbing processor (`_scrub_secrets`) in `backend/app/core/logging.py`, but most modules use stdlib `logging.getLogger(...)` which bypasses structlog processors entirely — including scrubbing.
- Files: stdlib logging in `backend/app/services/scheduler.py`, `backend/app/connectors/base.py`, `backend/app/workflows/runner.py`, `backend/app/providers/grok.py`, `backend/app/services/embeddings.py`, `backend/app/services/calibration.py`, all `backend/app/workflows/nodes/*.py`; structlog only in `backend/app/main.py`, `backend/app/core/middleware.py`, `backend/app/api/v1/endpoints/ingestion.py`.
- Impact: Secret scrubbing does not apply to most backend logs; two log formats in output.
- Fix approach: Replace `logging.getLogger(__name__)` with `from app.core.logging import get_logger` everywhere.

**Duplicated canonical-URL fallback + fabricated provenance URLs:**
- Issue: The "construct URL if missing" block is copy-pasted in two places; FDA/EMA fallbacks return generic landing pages (`https://open.fda.gov/drug/event/`, `https://www.ema.europa.eu/en/medicines`) yet rows are then marked `provenance_status="available"`.
- Files: `backend/app/workflows/runner.py` (lines ~233–245), `backend/app/api/v1/endpoints/signals.py` (`_serialize_signal`, lines ~66–78)
- Impact: Provenance honesty violation (D-22/D-23): a generic URL presented as record evidence; drift between the copies.
- Fix approach: Extract one shared helper (e.g., `app/services/provenance_urls.py`); build record-specific deep links or mark provenance as `landing_page_only`.

**Dead optional spaCy path:**
- Issue: `nlp_extract.py` tries to load spaCy models at import time, but `spacy` is not in `backend/requirements.txt` — branch can never run in a standard install.
- Files: `backend/app/workflows/nodes/nlp_extract.py` (lines 11–23), `backend/requirements.txt`
- Fix approach: Remove the branch or declare spacy as pinned extras.

**Script-style test file collects nothing:**
- Issue: `tests/test_foundation.py` defines `run_tests()` with prints/asserts but zero pytest-collectable `test_*` functions — its assertions never run under pytest (`pytest.ini` testpaths includes it).
- Files: `tests/test_foundation.py`
- Impact: False sense of coverage.
- Fix approach: Convert checks into real pytest functions or delete.

**Loose dependency pins (backend):**
- Issue: Every entry in `backend/requirements.txt` uses `>=`, no upper bounds, no lockfile.
- Files: `backend/requirements.txt`
- Impact: Non-reproducible CI installs/Docker builds; fastembed/langgraph/pydantic bumps break unpredictably.
- Fix approach: Pin exact versions or add lockfile (pip-tools/uv).

**Import-time default captures settings snapshot:**
- Issue: `def __init__(self, api_key: str = settings.XAI_API_KEY or "")` evaluates once at module import; later settings changes are invisible.
- Files: `backend/app/providers/grok.py` (line 43)
- Impact: Test flakiness; stale-key behavior if settings mutated after import.
- Fix approach: Read `settings.XAI_API_KEY` inside `__init__` body.

**Overload-style backward-compat shims in frontend API layer:**
- Issue: Nearly every export in `frontend/lib/api.ts` accepts unions like `filters?: SignalFilterParams | AbortSignal` plus trailing optional `signal?`, with runtime `instanceof` disambiguation repeated per function.
- Files: `frontend/lib/api.ts` (lines 41–120+)
- Impact: Type ambiguity; duplicated boilerplate; easy-to-misuse call sites.
- Fix approach: Migrate call sites (`frontend/components/**`) to explicit signatures and drop the shims.

**Silent exception swallowing (violates project's own ENGINEERING_STANDARDS):**
- Issue: Multiple bare `except Exception: pass` blocks discard failures with no log.
- Files: `backend/app/services/scheduler.py` (lines 195–204 scheduler DB state update), `backend/app/workflows/runner.py` (lines 137–138 PipelineRun failure-record commit), `backend/app/services/ingestion.py` (lines 175–178, 193–197 rollback paths), `backend/app/api/v1/endpoints/signals.py` (lines 48–59 malformed score/metadata downgraded)
- Impact: Failures leave no trace; contradicts AGENTS.md rule 5 spirit.
- Fix approach: Log at warning minimum; surface via `ScheduledJobState.last_error`.

## Known Bugs

**GrokProvider.generate_summary can never succeed:**
- Symptoms: With `XAI_API_KEY` configured, `generate_summary()` always raises `PermissionError` because it passes hardcoded `classification=DataClassification.UNKNOWN` and the privacy gate only permits PUBLIC/SYNTHETIC. Without a key it raises `GrokUnavailableError`. No input path leads to success.
- Files: `backend/app/providers/grok.py` (lines 117–128 vs gate at lines 56–70)
- Trigger: Any call reaching `generate_summary`.
- Workaround: Use `generate_intelligence` with an explicit classification instead.
- Fix approach: Accept a `classification` parameter or delete the method.

## Security Considerations

**API keys leak into error messages → database → API responses:**
- Risk: On HTTP >= 400, `ConnectorFetchError` embeds the FULL query param dict (`f"HTTP {response.status_code} from {url} (params={params})"`). PubMed passes `params["api_key"] = settings.NCBI_API_KEY` (`pubmed.py:79,105`) and OpenFDA passes `api_key` as param (`fda.py:107`). Error strings flow into `SourceHealthLog.last_error` / `sources.last_error` (`ingestion.py:117,136,188`) and are exposed via `/api/v1/health/connectors` (`health.py` returns `last_error`) and observability endpoints.
- Files: `backend/app/connectors/base.py` (lines 138–141), `backend/app/connectors/pubmed.py`, `backend/app/connectors/fda.py`, `backend/app/services/ingestion.py`, `backend/app/api/v1/endpoints/health.py`
- Current mitigation: `_scrub_secrets` in `backend/app/core/logging.py` redacts secret-named keys — but only for structlog loggers (these modules use stdlib) and never touches DB-stored values.
- Recommendations: Redact params before formatting errors; move keys to headers where supported; purge/redact existing `last_error` rows.

**Zero authentication on entire API surface:**
- Risk: Every endpoint — including mutations (`POST /api/v1/ingestion/*`, `POST /api/v1/pipeline/*`, cache clear, feedback/recalibrate) — relies solely on `Depends(get_db)`; no auth dependency anywhere.
- Files: all of `backend/app/api/v1/endpoints/*.py`; CORS config in `backend/app/main.py` (lines 66–73)
- Current mitigation: CORS defaults to `http://localhost:3000` (`backend/app/core/config.py`) — blocks browser cross-origin misuse only; direct network access unrestricted.
- Recommendations: Add API-key/JWT dependency for mutation routes before any non-loopback deployment.

**Hardcoded infrastructure credentials & exposed services:**
- Risk: Postgres password `metaradar_pass` hardcoded in `docker-compose.yml` (lines 7–9, 41, 72) AND as default `DATABASE_URL` in `backend/app/core/config.py` (line 19). Redis has no auth; Postgres/Redis/backend ports bind 0.0.0.0.
- Files: `docker-compose.yml`, `backend/app/core/config.py`
- Current mitigation: Dev-oriented stack; `.env` gitignored (verified via `git check-ignore`).
- Recommendations: Credentials only via `.env`; bind published ports to `127.0.0.1:`; enable Redis `requirepass`.

**Regex-only PII/PHI scrubbing:**
- Risk: `PIIPHIScrubber` detects only email/phone/SSN/MRN/DOB (`pii.py` PATTERNS dict). Person names, addresses, free-text narratives pass through into local LLM prompts and persisted content.
- Files: `backend/app/services/pii.py` (lines 5–11)
- Current mitigation: External transmission gated — UNKNOWN classification blocked at Grok privacy gate (`grok.py:88-91`); unsanitized text reaches only LOCAL Gemma and DB.
- Recommendations: Document pattern-list limitation as accepted risk for local-only processing; consider NER-based scrubbing before enabling hosted providers on raw text.

**CORS allows any method/header with credentials:**
- Risk: `allow_credentials=True, allow_methods=["*"], allow_headers=["*"]` broader than needed even for localhost origin.
- Files: `backend/app/main.py` (lines 67–73)
- Recommendations: Restrict to GET/POST once auth lands.

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
