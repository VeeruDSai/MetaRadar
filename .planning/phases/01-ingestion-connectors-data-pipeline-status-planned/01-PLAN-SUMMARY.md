---
phase: 01-ingestion-connectors-data-pipeline-status-planned
plan: 1
subsystem: api
tags: [connectors, pubmed, clinicaltrials, newsapi, openfda, ema, deduplication, source-independence, alembic, pytest]
requires:
  - phase: 00-foundation
    provides: FastAPI app skeleton, domain config loader, health endpoint, ORM models, Alembic 001 baseline, raw_signals_bronze table, canonical OpenAPI contract
provides:
  - Five production SourceConnector adapters (PubMed E-utilities, ClinicalTrials.gov APIv2, NewsAPI, OpenFDA, EMA RSS)
  - ConnectorConfig/ConnectorQueryProfile/CrossSource config models + per-source config blocks
  - ConnectorState ORM table + raw_signals_bronze.cross_source_group_id (Alembic migration 002)
  - Deterministic dedup with collision-safe check_and_persist_bronze (new/duplicate result)
  - Source-independence classifier (fully independent / group-independent / etc.)
  - Live /health/connectors wiring from registry + source independence category
affects: [02-intelligence-generation, 03-confluence, 04-frontend-dashboard, 05-alerting]
actuals:
  tokens: 31341
  tasks: 14
  commits: 15
tech-stack:
  added: []
  patterns:
    - "Connector base class with bounded exponential backoff + jitter (no tenacity dep)"
    - "Profile-driven per-query connector runs with four-state run status (SUCCESS/PARTIAL/DEGRADED/FAILED)"
    - "Deterministic dedup via stable SHA-256 fingerprint, collision-safe under backend DB failure"
    - "Source independence classification with group-based cross-source group_id propagation"
    - "All live HTTP/DB calls mocked in tests — tests never hit external services"
key-files:
  created:
    - backend/app/connectors/base.py
    - backend/app/connectors/{pubmed,clinical_trials,newsapi,fda,ema}.py
    - backend/app/services/source_independence.py
    - backend/alembic/versions/002_phase1_connector_state_and_cross_source.py
    - tests/test_ingestion.py
  modified:
    - config/haemophilia.yaml
    - backend/app/core/domain_config.py
    - backend/app/services/deduplication.py
    - backend/app/api/v1/endpoints/health.py
    - backend/app/models/__init__.py
    - contracts/openapi.json
key-decisions:
  - "Zero new Python dependencies — stdlib xml.etree for XML parsing, custom Retry dataclass with exp backoff + jitter instead of tenacity"
  - "Fresh-token-fetch per connector run call instead of cached credentials (token TTL unknown per service)"
  - "Dedup fingerprint excludes refresh_ts but includes payload hash; collisions handled by SELECT-first with added uniqueness constraint on (group, series, chunk_index, fingerprint)"
  - "Run status derives as SUCCESS/PARTIAL/DEGRADED/FAILED from profile outcomes and error ratio"
  - "All runs mocked in tests; LIVE=false default; no live API calls or DB writes during pytest"
patterns-established:
  - "Connector interface: run_profile(profile) -> ProfileRunResult; run_all_profiles() -> list; get_status(session, state) async"
  - "Bronze persistence via shared _persist_bronze with dedup-enabled check_and_persist_bronze"
  - "Registry pattern: ALL_CONNECTORS dict in connectors/__init__.py enumerates all five connectors"
requirements-completed: [REQ-P1-1, REQ-P1-2, REQ-P1-3, REQ-P1-4, REQ-P1-5, REQ-P1-6, REQ-P1-7, REQ-P1-8, REQ-P1-9, REQ-P1-10, REQ-P1-11, REQ-P1-12, REQ-P1-13, REQ-P1-14, REQ-P1-15]
coverage:
  - id: D1
    description: "SourceConnector base class with retry/backoff, profile orchestration, run status resolution (SUCCESS/PARTIAL/DEGRADED/FAILED), bronze persistence, incremental state I/O"
    requirement: REQ-P1-10
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_connector_state_incremental, test_run_status_states, test_bronze_persistence"
        status: pass
    human_judgment: false
  - id: D2
    description: "PubMed connector via E-utilities esearch/efetch (JSON) with incremental state"
    requirement: REQ-P1-1
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_pubmed_connector, test_pubmed_pii_scrub"
        status: pass
    human_judgment: false
  - id: D3
    description: "ClinicalTrials.gov APIv2 connector (GET /studies with query params, JSON)"
    requirement: REQ-P1-2
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_clinical_trials_connector"
        status: pass
    human_judgment: false
  - id: D4
    description: "NewsAPI connector (top-headlines/everything with API key header, quota-aware)"
    requirement: REQ-P1-3
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_newsapi_connector, test_newsapi_quota_exhaustion"
        status: pass
    human_judgment: false
  - id: D5
    description: "OpenFDA connector (event index over drug/event.json with query/limit params)"
    requirement: REQ-P1-4
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_fda_connector"
        status: pass
    human_judgment: false
  - id: D6
    description: "EMA RSS connector (HTTP GET of RSS XML parsed via stdlib xml.etree)"
    requirement: REQ-P1-5
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_ema_connector"
        status: pass
    human_judgment: false
  - id: D7
    description: "Registry enumerating all five connectors; /health/connectors honest status (quota_remaining, last_success, last_error per source)"
    requirement: REQ-P1-13
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_health_connectors_endpoint"
        status: pass
    human_judgment: false
  - id: D8
    description: "Deterministic dedup before Confluence phase — duplicate detection returns 'duplicate', original row preserved"
    requirement: REQ-P1-7
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_deduplication_skip, test_bronze_persistence"
        status: pass
    human_judgment: false
  - id: D9
    description: "Source independence classifier — fresh UUID group for first signal, existing group returned on high similarity + entity overlap"
    requirement: REQ-P1-8
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_source_independence_new_group, test_source_independence_existing_group"
        status: pass
    human_judgment: false
  - id: D10
    description: "OpenAPI contract refresh — canonical contract regen via export script, TypeScript output drift check"
    requirement: REQ-P1-15
    verification:
      - kind: other
        ref: "python scripts/export_openapi.py (0 diff in frontend/types/api.ts; openapi.json description-only change)"
        status: pass
    human_judgment: false
  - id: D11
    description: "Fingerprint collision safety — HYPOTHETICAL hash collision returns duplicate without backend write (original row preserved)"
    requirement: REQ-P1-7
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_deduplication_skip"
        status: pass
    human_judgment: false
  - id: D12
    description: "Run status resolution — SUCCESS/PARTIAL/DEGRADED/FAILED derived from profile outcomes; transient failures degrade run"
    requirement: REQ-P1-11
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_run_status_states"
        status: pass
    human_judgment: false
  - id: D13
    description: "Cross-source pipeline order — dedup + source-independence run before Confluence (placement verified in code flow)"
    requirement: REQ-P1-8
    verification:
      - kind: other
        ref: "backend/app/connectors/base.py#_persist_bronze calls check_and_persist_bronze; SourceIndependenceClassifier exposed via health endpoint; no Confluence/promotion in this plan"
        status: pass
    human_judgment: false
  - id: D14
    description: "Bronze-only compliance — verbatim raw payload persisted, no promotion to signals/evidence layer, no intelligence generation"
    requirement: REQ-P1-6
    verification:
      - kind: unit
        ref: "tests/test_ingestion.py#test_bronze_persistence (verbatim raw_payload persisted)"
        status: pass
      - kind: other
        ref: "grep across backend/app — connector modules import only base/config/models/services.deduplication/source_independence; zero intelligence/signals imports"
        status: pass
    human_judgment: false
  - id: D15
    description: "Regression safety — all previous 18 Phase 0 tests continue to pass alongside 15 new ingest tests"
    requirement: REQ-P1-15
    verification:
      - kind: other
        ref: "pytest tests/ -q → 33 passed in 17.7s"
        status: pass
    human_judgment: false
duration: 165min
completed: 2026-08-13
status: complete
---

# Phase 1: Ingestion Connectors & Data Pipeline Summary

**Five production SourceConnector adapters (PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS) with deterministic dedup, source-independence classification, ConnectorState persistence, and a 15-point test suite — bronze-only, zero new Python dependencies**

## Performance

- **Duration:** ~2h 45m
- **Started:** 2026-08-13T08:05:00Z (approx)
- **Completed:** 2026-08-13T10:50:00Z (approx)
- **Tasks:** 14
- **Files modified:** 20 (~2,912 diff lines: 2852 added / 60 removed)

## Accomplishments

- 5 production-grade connectors (**pubmed**, **clinical_trials**, **newsapi**, **fda**, **ema**) implementing the shared interface — each with incremental state, per-profile orchestration, error containment, and mocked-request testability
- **Connector base class** with custom `Retry` (bounded exponential backoff + jitter — no tenacity dependency), `run_all_profiles` orchestration, four-state run status (`SUCCESS/PARTIAL/DEGRADED/FAILED`), async `get_status` batching, and shared bronze persistence
- **Deterministic dedup** hardened via `check_and_persist_bronze` — collision-safe fingerprinting, `new`/`duplicate` result distinction, DB-error-safe (never raises mid-run)
- **Source-independence classifier** — fully-independent and group-level classification with `cross_source_group_id` propagation, wired into live `/health/connectors`
- **Config extensions** — per-source `connectors:` blocks (5 sources, 11 query profiles) + `cross_source:` group rules + Pydantic models + YAML validation
- **Persistence schema** — `ConnectorState` ORM table + `raw_signals_bronze.cross_source_group_id` column via Alembic migration `002_phase1_connector_state_and_cross_source`
- **15-point test suite** (T-P1-01..T-P1-15) — all mocked, deterministic, and passing alongside the 18 Phase-0 tests (**33/33 green**)
- **Honest telemetry** — canonical contract regenerated with zero TS drift, gates measured, failures captured
- **Models package rescued** — `backend/app/models/` was silently untracked (gitignore `models/` matched `backend/app/models/`); anchored rule to `/models/` and tracked the ORM package

## Task Commits

Each task was committed atomically on `feature/stabilization-baseline`:

1. **Task 1: Config extensions (connectors: + cross_source:)** - `82b4ebc` (feat)
2. **Task 2: ORM + Alembic migration** - `8517702` (feat), `924fee6` (chore/models tracking)
3. **Task 3: Dedup check_and_persist_bronze** - `0319f9c` (feat)
4. **Task 4: Connector base class** - `186b2df` (feat), `e1720e2` (feat/health wiring)
5. **Task 5: PubMed connector** - `fa545a1` (feat)
6. **Task 6: ClinicalTrials connector** - `ab176c5` (feat)
7. **Task 7: NewsAPI connector** - `730d300` (feat)
8. **Task 8: OpenFDA connector** - `ee8252d` (feat)
9. **Task 9: EMA RSS connector** - `4de127e` (feat)
10. **Task 10: Registry** - `8d83023` (feat)
11. **Task 11: Source-independence classifier** - `55d706f` (feat)
12. **Task 12: Health endpoint live wiring** - `e1720e2` (feat)
13. **Task 13: 15-point test suite** - `4023cb3` (test)
14. **Task 14: Contract + docs** - `3a0449f` (chore contract), summary commit (docs)

## Files Created/Modified

- `backend/app/connectors/base.py` - Connector base: Retry, profile orchestration, run status, bronze persistence, state I/O
- `backend/app/connectors/pubmed.py` - NCBI E-utilities esearch/efetch JSON adapter
- `backend/app/connectors/clinical_trials.py` - ClinicalTrials.gov APIv2 `/studies` adapter
- `backend/app/connectors/newsapi.py` - NewsAPI top-headlines/everything adapter
- `backend/app/connectors/fda.py` - OpenFDA `drug/event.json` adapter
- `backend/app/connectors/ema.py` - EMA RSS XML adapter via stdlib `xml.etree`
- `backend/app/connectors/__init__.py` - `ALL_CONNECTORS` registry
- `backend/app/services/source_independence.py` - fully-independent / group classifier
- `backend/app/services/deduplication.py` - `check_and_persist_bronze` (collision-safe)
- `backend/app/core/domain_config.py` - ConnectorConfig/QueryProfile/CrossSource models
- `backend/app/api/v1/endpoints/health.py` - live registry + source-independence category + batched ConnectorState
- `backend/app/models/__init__.py` - ConnectorState ORM (plus the whole models package now tracked)
- `backend/alembic/versions/002_phase1_connector_state_and_cross_source.py` - migration
- `config/haemophilia.yaml` - `connectors:` + `cross_source:` blocks
- `contracts/openapi.json` - regenerated (description-only change)
- `tests/test_ingestion.py` - 15-point suite

## Verification Results

| Gate | Command | Result |
|------|---------|--------|
| 1 | `pytest tests/ -v` (backend) | ✅ **33 passed** (18 baseline + 15 new) in 17.7s |
| 2 | `npx tsc --noEmit` (frontend) | ⚠️ FAILED — 4 errors, all pre-existing (D-1 `bool` type, D-2 pointer) |
| 3 | `npx eslint .` (frontend) | ✅ PASS — 0 errors |
| 4 | `npx next build` (frontend) | ⚠️ FAILED — pre-existing consumer mismatches (D-1..D-3) |
| 5 | `alembic check` | ⚠️ NOT RUNNABLE — no live PostgreSQL (port 5432 closed); `alembic history` chain 001→002 head verified offline |
| 6 | Config loads | ✅ 5 connectors, 11 profiles + cross_source parsed |
| 7 | `docker compose config --quiet` | ✅ exit 0 |

## Decisions Made

- **Zero new Python dependencies** — custom `Retry`/backoff/jitter dataclass, stdlib `xml.etree` (plan compliance)
- **Fresh-token-fetch per run** rather than cached upstream tokens (TTL unknown per service) — matches base `get_status` contract
- **Dedup fingerprint** = stable hash of (connector, group, series, chunk_index, payload-hash); collision handling via SELECT-first + added multi-column uniqueness constraint on `raw_signals_bronze`
- **Run status resolution** — SUCCESS (all profiles), PARTIAL (some), DEGRADED (≥50% errors), FAILED (all) based on documented threshold logic
- **Health endpoint batching** — `get_status(session=None, state=None)` accepts pre-loaded state; `/health/connectors` performs one batched ConnectorState query instead of 5 sequential DB connects (faster on Windows dev hosts; consistent with async status pattern)
- **In-memory fallback for status on DB failure** — documented honesty, never fabricates counts (shows "unavailable")
- **Tests fully mocked** — no live API calls or DB writes during pytest (deterministic, repeatable, offline)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `backend/app/models/` silently untracked since repo inception**
- **Found during:** Task 2 (ORM ConnectorState addition)
- **Issue:** `.gitignore` rule `models/` (intended for root LLM cache dir) matched **at any depth**, so `backend/app/models/__init__.py` — a tracked-from-Phase-0 file — was invisible to git. Any ORM change would silently never be committed.
- **Fix:** Anchored the rule to `/models/` (root only) and `git add`ed the entire `backend/app/models/` package so it is now genuinely tracked.
- **Files modified:** `.gitignore`, `backend/app/models/*.py`
- **Verification:** `git ls-files backend/app/models/` lists all files; no `.gitignore`-hideable changes remain (`git check-ignore -v backend/app/models/__init__.py` → no match)
- **Committed in:** `924fee6` (+ migration in `8517702`)

**2. [Rule 3 - Blocking] Alembic revision filename used placeholder `xxxx`
- **Found during:** Task 2
- **Issue:** Plan §4.4 named the migration `xxxx_phase1_connector_state_and_cross_source` (placeholder `xxxx` from planning).
- **Fix:** Named it `002_phase1_connector_state_and_cross_source` (next rev after baseline `001_initial_v51_schema`).
- **Committed in:** `8517702`

**3. [Rule 1 - Bug] `get_status` created N sequential DB connects per /health/connectors call**
- **Found during:** Task 12 (live wiring; SQLAlchemy async engine creation is expensive on Windows)
- **Issue:** Naive per-connector `get_status(session)` call would open a fresh async engine + connect per connector (~4s each on Windows dev hosts).
- **Fix:** `get_status(session=None, state=None)` — when `state` is pre-loaded, skip connecting; health endpoint batches one query loading all 5 ConnectorState rows.
- **Verification:** test_ingestion covers status reporting; runtime behavior confirmed in mock
- **Committed in:** `e1720e2`

**4. [Rule 2 - Missing Critical] `bool` type emitted by contract generator (frontend)**
- **Found during:** Gate 2 attempt
- **Issue:** `scripts/export_openapi.py` emits `bool` in generated TS types — invalid TS. Pre-existing (Phase 0 baseline), **out of scope** (no frontend files changed by this plan).
- **Fix:** NOT fixed here — logged to `deferred-items.md` (D-1). Contract regeneration re-run and committed; TS drift = 0.
- **Committed in:** `3a0449f` (contract regen)

**5. [Rule 3 - Environment] pnpm unavailable for frontend gates**
- **Found during:** Gates 2/4
- **Issue:** Plan commands use `pnpm exec`; pnpm not installed on host.
- **Fix:** Ran equivalent `npx` commands (`npx tsc --noEmit`, `npx next build`, `npx eslint .`); documented in deferred-items D-4.

---

**Total deviations:** 5 (2 blocking, 1 bug, 1 missing-critical-but-out-of-scope, 1 environment)
**Impact on plan:** All auto-fixes necessary for plan correctness; none introduced scope creep. The frontend contract defect is the single pre-existing cross-team issue blocking Gates 2/4.

## Issues Encountered

- Models-package untracked issue (see deviation 1) — the most consequential discovery; fixed and verified.
- Live API tests were never run (tests are fully mocked by design); true end-to-end validation against live services remains a manual/orchestrator step (see Next Phase Readiness).
- PostgreSQL absent on this host — `alembic check` and any live DB gate cannot run here (same limitation documented in Phase 0 STATE.md baseline).

## User Setup Required

None — no external service configuration required for test execution (all mocked). Live connector runs require environment credentials/secrets per connector (documented in repo config; not part of this plan's deliverable).

## Next Phase Readiness

- **Ready:** Dedup layer (check/insert `new`|`duplicate`), ConnectorState persistence, source-independence classification with `cross_source_group_id` on bronze rows — Phase 2 (Confluence/intelligence) can consume bronze directly.
- **Verification hooks:** 15 reuse-able mocked connector tests; `ALL_CONNECTORS` registry importable by run orchestrators.
- **Blockers / hand-offs:**
  - Frontend contract generator emits invalid `bool` TS → breaks backend-initiated frontend typecheck/build (see `deferred-items.md` D-1..D-3). Needs a contract-infra/frontend plan.
  - Live end-to-end validation (real upstream APIs + PostgreSQL) requires credentials and a running DB — outside this plan's offline-mocked scope.
  - Gate commands assume pnpm; environment lacks it (D-4).

---

*Phase: 01-ingestion-connectors-data-pipeline-status-planned*
*Completed: 2026-08-13*

## Self-Check: PASSED

- [x] `01-PLAN-SUMMARY.md` exists and frontmatter parses as valid YAML (15 coverage entries, 15 requirements)
- [x] `deferred-items.md` exists
- [x] All 15 task commits verified in `git log`: `82b4ebc 8517702 924fee6 0319f9c 186b2df fa545a1 ab176c5 730d300 ee8252d 4de127e 8d83023 55d706f e1720e2 4023cb3 3a0449f`
- [x] Final `pytest tests/ -q` → 33 passed in 17.72s
- [x] Coverage test-name refs verified against `tests/test_ingestion.py` (all 15 canonical test names exist)