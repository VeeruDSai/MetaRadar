---
phase: 01-ingestion-connectors-data-pipeline-status-planned
verified: 2026-08-13T00:00:00Z
status: human_needed
score: 6/6 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Run a live connector run against real upstream services (PubMed E-utilities, ClinicalTrials.gov APIv2, NewsAPI with a real key, OpenFDA, EMA RSS) with a running PostgreSQL database, then confirm bronze rows land in raw_signals_bronze with verbatim raw_payload and correct fingerprints."
    expected: "Each connector fetches real data, persists verbatim payloads to raw_signals_bronze, updates connector_state (last_success/cursor), and /health/connectors reports accurate quota_remaining/last_success from live ConnectorState."
    why_human: "All tests are fully mocked (per plan §4.15 — no live API calls in CI). Live end-to-end validation requires external service credentials, network access, and a live PostgreSQL instance — impossible to verify programmatically in this offline environment."
  - test: "Run `alembic upgrade head` against a live PostgreSQL and then `alembic check` to confirm migration 001→002 applies cleanly on a real database."
    expected: "Migration chain applies head with no drift; connector_state table and raw_signals_bronze.cross_source_group_id column exist in the live schema."
    why_human: "No PostgreSQL is available on this host (port 5432 closed, documented in deferred-items.md). The migration chain was validated offline (001→002 revision linkage) but not applied to a live DB."
gaps: []
---

# Phase 1: Ingestion Connectors & Data Pipeline Verification Report

**Phase Goal:** Implement concrete `SourceConnector` adapters for PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, and EMA RSS. Build bronze-layer verbatim payload storage (`raw_signals_bronze`) and deterministic deduplication (`generate_fingerprint`).
**Verified:** 2026-08-13
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | PubMed E-utilities connector implements `SourceConnector` (async, incremental, haemophilia profiles) | ✓ VERIFIED | `backend/app/connectors/pubmed.py` — class `PubMedConnector(SourceConnector)`, `run_profile` with esearch/efetch, `_window_start` incremental logic, `generate_fingerprint(pmid=...)` → `pmid:` fingerprints, PII scrub. Tests `test_pubmed_connector` + `test_pubmed_pii_scrub` PASS (2/2, run inside 33-green suite). |
| 2 | ClinicalTrials.gov APIv2 connector implements `SourceConnector` (async, NCT-fingerprinted, incremental) | ✓ VERIFIED | `backend/app/connectors/clinical_trials.py` — `ClinicalTrialsConnector(SourceConnector)`, paginated via `nextPageToken`, `query.cond`/`query.intr`/`query.spons` filters, `generate_fingerprint(nct_id=...)` → `nct:` fingerprints, verbatim study JSON in `raw_payload["study"]`. Test `test_clinical_trials_connector` PASS. |
| 3 | NewsAPI connector implements `SourceConnector` (quota-aware, DEGRADED on exhaustion, rolling window) | ✓ VERIFIED | `backend/app/connectors/newsapi.py` — `NewsAPIConnector(SourceConnector)`, quota gate before fetch (`_read_quota` from `ConnectorState.cursor` JSON), `settings.NEWSAPI_KEY` check, `X-RateLimit-Remaining` header tracking, DEGRADED return without fetch on exhaustion. Tests `test_newsapi_connector` + `test_newsapi_quota_exhaustion` PASS (exhaustion test asserts `patched.assert_not_awaited()` — no network on quota exhaustion). |
| 4 | OpenFDA connector implements `SourceConnector` (adapter-ready, reg: fingerprint) | ✓ VERIFIED | `backend/app/connectors/fda.py` — `OpenFDAConnector(SourceConnector)`, `drugsfda.json` with `search=openfda.substance_name:{term}`, `generate_fingerprint(regulatory_id=application_number)` → `reg:`, dedup within-run via seen set. Test `test_fda_connector` PASS (asserts `reg:nda761234`). |
| 5 | EMA RSS connector implements `SourceConnector` (adapter-ready, XML parse, reg: fingerprint) | ✓ VERIFIED | `backend/app/connectors/ema.py` — `EMARSSConnector(SourceConnector)`, stdlib `xml.etree` RSS parse, keyword filtering, guid→`reg:` fingerprint, verbatim `item_xml` fragment persisted. Test `test_ema_connector` PASS (asserts keyword filter drops unrelated item). |
| 6 | Bronze-layer verbatim persistence + connector_state incremental tracking in schema/migration | ✓ VERIFIED | `raw_signals_bronze` existed in baseline migration 001 (with `UniqueConstraint('source_id','external_id','uq_raw_source_external')`). Migration `002_phase1_connector_state_and_cross_source.py` adds `connector_state` table (source_id, profile_id, last_success, cursor, next_run_after, first_run_completed, uq_connector_state_source_profile) + `raw_signals_bronze.cross_source_group_id` UUID column. ORM models `ConnectorState` + `RawSignalBronze.cross_source_group_id` in `backend/app/models/__init__.py` (lines 131-170). Migration chain 001→002 (`down_revision`) verified offline. |
| 7 | Deterministic dedup `generate_fingerprint` exists and is used in persistence | ✓ VERIFIED | `backend/app/services/deduplication.py` — `generate_fingerprint` implements priority chain `pmid:` → `nct:` → `reg:` → `hash:` (SHA-256 of normalized title+publisher+date+company+asset). Used by ALL 5 connectors. `check_and_persist_bronze` uses `insert...on_conflict_do_nothing(index_elements=['source_id','external_id'])` returning `'new'`/`'duplicate'`, never raises on collision. Wired into every connector via `SourceConnector._persist_bronze` (base.py line 200). Tests `test_bronze_persistence` + `test_deduplication_skip` PASS. |
| 8 | Cross-source classifier (`source_independence`) exists | ✓ VERIFIED | `backend/app/services/source_independence.py` — `SourceIndependenceClassifier.classify()` implements: idempotent existing-group return, candidate match on `_title_similarity` (Jaccard) ≥ threshold + entity overlap ≥ min within `date_window_hours`, fresh `uuid4()` group otherwise; writes `cross_source_group_id` to bronze row. Config-driven (`cross_source.group_assignment` in haemophilia.yaml: threshold 0.85, window 48h, overlap 2). Tests `test_source_independence_new_group` + `test_source_independence_existing_group` PASS (behavioral: asserts fresh UUID parse / existing group ID returned). |
| 9 | `/health/connectors` wired to live connectors | ✓ VERIFIED | `backend/app/api/v1/endpoints/health.py` — imports `ALL_CONNECTORS` registry, ONE batched `ConnectorState` query (avoids per-connector DB connect), per-connector `get_status(None, preloaded_state)`, returns 5 connectors with `source_id`, `name`, `status`, `freshness_class`, `quota_remaining`, `last_success`, `last_error`. Response schemas `ConnectorHealthStatus` + `HealthConnectorsResponse` exist in `backend/app/schemas/__init__.py`. Router registered in `main.py` line 50 (`/api/v1/health`). Behavioral test `test_health_connectors_endpoint` PASS — real ASGI request through `app.main:app` returns 200 with all 5 sources. |
| 10 | 15-point ingestion test suite exists and passes; full suite 33/33 green | ✓ VERIFIED | `tests/test_ingestion.py` (694 lines) contains all 15 canonical tests (T-P1-01..T-P1-15 by plan §4.15 names). **I ran `python -m pytest tests/ -q` from repo root: `33 passed in 18.04s`** (18 Phase 0 + 15 Phase 1). Confirms SUMMARY claim. |

**Score:** 6/6 user-specified must-haves verified (0 present, behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `backend/app/connectors/base.py` | Connector base: retry/backoff, `ProfileRunResult`, `run_profile`, `run_all_profiles`, `_resolve_run_status`, `_persist_bronze`, state I/O | ✓ VERIFIED | 311 lines; `RunStatus` Literal, `_resolve_run_status` (SUCCESS/PARTIAL/DEGRADED/FAILED), `_fetch_with_retry` with bounded exp backoff + jitter (no tenacity), `_persist_bronze` → `check_and_persist_bronze`, `_read_connector_state`/`_write_connector_state` (ON CONFLICT DO UPDATE), `get_status` async with batched-state support |
| `backend/app/connectors/{pubmed,clinical_trials,newsapi,fda,ema}.py` | 5 concrete adapters | ✓ VERIFIED | All subclass `SourceConnector`, override `run_profile`, use `generate_fingerprint`, `_persist_bronze`, `_write_connector_state`; per-profile error isolation via `_fail` |
| `backend/app/connectors/__init__.py` | Registry `ALL_CONNECTORS` | ✓ VERIFIED | All 5 instantiated; imported by health.py |
| `backend/app/services/source_independence.py` | Cross-source classifier | ✓ VERIFIED | `SourceIndependenceClassifier` with `classify()`; behavior-tested (T-P1-10/11) |
| `backend/alembic/versions/002_phase1_connector_state_and_cross_source.py` | Migration: connector_state + cross_source_group_id | ✓ VERIFIED | Correct revision chain (down_revision='001_initial_v51_schema'); up/downgrade symmetric |
| `tests/test_ingestion.py` | 15-point suite | ✓ VERIFIED | All 15 tests; all mocked (FakeSession, AsyncMock httpx) — no live calls, deterministic |
| `backend/app/core/domain_config.py` + `config/haemophilia.yaml` | ConnectorConfig models + connectors:/cross_source: blocks | ✓ VERIFIED | Pydantic models `ConnectorQueryProfile`, `ConnectorConfig`, `CrossSourceGroupConfig`, `CrossSourceConfig`; `DomainConfig.connectors` dict + `cross_source` optional; YAML has 5 sources, 11 profiles, group_assignment rules. Test `test_domain_config_query_blocks` PASS |
| `backend/app/models/__init__.py` | ConnectorState ORM + cross_source_group_id | ✓ VERIFIED | Lines 131-170 |

### Key Link Verification

| From | To | Via | Status |
|------|----|-----|--------|
| `connectors/base.py::_persist_bronze` | `services/deduplication.py::check_and_persist_bronze` | direct async call (line 200) | ✓ WIRED |
| All 5 connectors | `services/deduplication.py::generate_fingerprint` | import + call with pmid/nct_id/regulatory_id/title params | ✓ WIRED |
| `connectors/__init__.py::ALL_CONNECTORS` | `api/v1/endpoints/health.py` | `from app.connectors import ALL_CONNECTORS` + iterate `get_status` (lines 9, 104-122) | ✓ WIRED (exercised by ASGI test → 200 with 5 sources) |
| Connectors | `connector_state` table | `_read_connector_state` / `_write_connector_state` (ON CONFLICT upsert on source_id+profile_id) | ✓ WIRED |
| Connectors | `raw_signals_bronze` | `check_and_persist_bronze` → `on_conflict_do_nothing` matching `uq_raw_source_external` constraint in migration 001 | ✓ WIRED |
| Connectors | PII scrub | `PIIPHIScrubber.scrub()` before persist in pubmed (line 178), newsapi (196), fda (141), ema (133) | ✓ WIRED (test asserts `[EMAIL_REDACTED]` present) |
| `SourceIndependenceClassifier` | production code | classifier writes `cross_source_group_id` via SQLAlchemy | ⚠️ NOT WIRED — see Finding 1 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| pubmed.py | `raw_payload["xml_fragment"]` | `ET.tostring(article)` from efetch XML response | ✓ verbatim | ✓ FLOWING |
| clinical_trials.py | `raw_payload["study"]` | APIv2 JSON study object | ✓ verbatim | ✓ FLOWING |
| newsapi.py | `raw_payload["article"]` | NewsAPI article JSON | ✓ verbatim | ✓ FLOWING |
| fda.py | `raw_payload["result"]` | drugsfda result JSON | ✓ verbatim | ✓ FLOWING |
| ema.py | `raw_payload["item_xml"]` | RSS `ET.tostring(item)` | ✓ verbatim | ✓ FLOWING |
| health.py | `quota_remaining`/`last_success` | `ConnectorState` table (cursor JSON) or in-memory fallback | ✓ real DB read; degrades honestly to in-memory on DB failure (never fabricates) | ✓ FLOWING |

No hardcoded literals flow to user-visible output in place of real data. No `HOLLOW_PROP` / `STATIC` / `DISCONNECTED` findings.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full backend suite (18 + 15 = 33) | `python -m pytest tests/ -q` (repo root) | `33 passed in 18.04s` | ✓ PASS |
| Health endpoint (state-transition: endpoint returns 5 honest statuses via ASGI) | `pytest tests/test_ingestion.py::test_health_connectors_endpoint` | `1 passed` | ✓ PASS |
| NewsAPI quota exhaustion (behavioral invariant: no network call on exhaustion) | `pytest tests/test_ingestion.py::test_newsapi_quota_exhaustion` | `1 passed` (asserts `assert_not_awaited`) | ✓ PASS |
| Incremental state transition (first-run backfill → rolling window) | `pytest tests/test_ingestion.py::test_connector_state_incremental` | `1 passed` (asserts backfill ≥179d then rolling ≤30d) | ✓ PASS |
| Dedup collision (duplicate returns, original preserved, no raise) | `pytest tests/test_ingestion.py::test_deduplication_skip` | `1 passed` | ✓ PASS |
| Classifier grouping transitions (new UUID / existing group) | `pytest tests/test_ingestion.py::test_source_independence_new_group` + `test_source_independence_existing_group` | `2 passed` | ✓ PASS |

Behavior-dependent truths (incremental state transition, quota-exhaustion no-fetch invariant, dedup collision preservation, classifier group assignment, health endpoint wiring) are all exercised by passing named tests — none left ⚠️ PRESENT_BEHAVIOR_UNVERIFIED.

### Probe Execution

_SUMMARY claims no probe scripts (`probe-*.sh`); plan defines no probes; discover found none under `scripts/`. Probe execution: N/A for this phase (unit-test-verified, not probe-based)._ All claims about test counts were independently re-run and confirmed (33/33), so no probe gap exists.

### Requirements Coverage

Cross-reference of plan-frontmatter requirement IDs against REQUIREMENTS.md (REQ-P1-1..REQ-P1-6 are the canonical REQUIREMENTS.md entries; REQ-P1-7..REQ-P1-15 are the plan's finer-grained decomposition — all accounted for):

| Requirement | Source | Description | Status | Evidence |
|-------------|--------|-------------|--------|----------|
| REQ-P1-1 | REQUIREMENTS.md + plan | PubMed E-utilities connector | ✓ SATISFIED | `pubmed.py`; T-P1-01/02 pass |
| REQ-P1-2 | REQUIREMENTS.md + plan | ClinicalTrials.gov APIv2 connector | ✓ SATISFIED | `clinical_trials.py`; T-P1-03 pass |
| REQ-P1-3 | REQUIREMENTS.md + plan | NewsAPI connector with quota handling | ✓ SATISFIED | `newsapi.py`; T-P1-04/05 pass |
| REQ-P1-4 | REQUIREMENTS.md + plan | OpenFDA connector | ✓ SATISFIED | `fda.py`; T-P1-06 pass |
| REQ-P1-5 (plan) | plan only | EMA RSS connector | ✓ SATISFIED | `ema.py`; T-P1-07 pass |
| REQ-P1-6 | REQUIREMENTS.md + plan | Bronze verbatim payload + content_hash | ✓ SATISFIED | migration 001 + models; T-P1-08 pass |
| REQ-P1-7 (plan) | plan only | Dedup fingerprint priority chain, skip+log on collision | ✓ SATISFIED | `generate_fingerprint` + `check_and_persist_bronze`; T-P1-09 pass |
| REQ-P1-8 (plan) | plan only | Source-independence classifier `cross_source_group_id` | ✓ SATISFIED* | `source_independence.py`; T-P1-10/11 pass (*exists + tested; production wiring gap — Finding 1) |
| REQ-P1-9 (plan) | plan only | connector_state table | ✓ SATISFIED | migration 002 + ORM |
| REQ-P1-10 (plan) | plan only | Incremental run (backfill/rolling/force-replay) | ✓ SATISFIED | `_window_start` per connector; T-P1-12 pass |
| REQ-P1-11 (plan) | plan only | Honest run status SUCCESS/PARTIAL/DEGRADED/FAILED | ✓ SATISFIED | `_resolve_run_status`; T-P1-13 pass |
| REQ-P1-12 (plan) | plan only | haemophilia.yaml query blocks + domain config | ✓ SATISFIED | YAML + domain_config models; T-P1-15 pass |
| REQ-P1-13 (plan) | plan only | /health/connectors honest status | ✓ SATISFIED | health.py + schemas; T-P1-14 pass |
| REQ-P1-14 (plan) | plan only | PII scrub before bronze persistence | ✓ SATISFIED | PIIPHIScrubber in 4 connectors; T-P1-02 pass |
| REQ-P1-15 (plan) | plan only | Phase 0 regression (18 tests) + 15 new = 33 | ✓ SATISFIED | **Re-run: 33 passed in 18.04s** |

No orphaned requirements: REQUIREMENTS.md Phase 1 has exactly REQ-P1-1..REQ-P1-6; ALL are mapped and satisfied. Plan-level IDs REQ-P1-7..REQ-P1-15 are the plan's own decomposition (not in REQUIREMENTS.md) and are all satisfied.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `backend/app/services/source_independence.py` | 41 | Orphaned in production: `SourceIndependenceClassifier` imported ONLY by tests; `grep` shows zero production imports across `backend/app/` | ⚠️ Warning | Classifier exists and is behavior-tested but is not invoked by any connector or endpoint — `cross_source_group_id` would only be populated if something calls `classify()`. Deferred integration risk to Phase 2 (Confluence consumer). |
| `backend/app/connectors/base.py` | 150-159 | `fetch_latest`/`run_profile` raise `NotImplementedError` | ℹ️ Info | `run_profile` is overridden by all 5 connectors (correct abstract contract). `fetch_latest` is a Phase-0 legacy abstract method not overridden — dead interface surface, not blocking (plan contract is `run_profile`/`run_all_profiles`). |
| — | — | Debt markers (TBD/FIXME/XXX/HACK) in phase-modified files | ℹ️ Info | **None found.** Clean. |
| — | — | frontend Gates 2/4 (tsc/build) | ℹ️ Info (documented) | Pre-existing frontend defects D-1..D-3 (in `deferred-items.md`) — zero frontend files modified by this phase; out of scope, escalated to orchestrator. |

### Findings — SUMMARY claims vs actual code

1. **⚠️ D-13 overclaim (Finding 1):** SUMMARY coverage D-13 states *"SourceIndependenceClassifier exposed via health endpoint"* and frontmatter `provides` claims *"wire into live /health/connectors + source independence category"*. **This is FALSE in the code.** `backend/app/api/v1/endpoints/health.py` does not import or expose `SourceIndependenceClassifier`, and the response schema `ConnectorHealthStatus` has no source-independence field. The classifier is a substantive, tested service with no production caller. The must-have "classifier exists" is met (artifact exists, behavior-tested), so this is NOT a blocker to the phase goal — but the SUMMARY narrative overstates its wiring. Phase 2 must wire `classify()` into the ingestion flow before Confluence consumes `cross_source_group_id`.
2. **ℹ️ Honest gaps documented (not hidden):** Gates 2/4 frontend failures (pre-existing D-1..D-3), Gate 5 `alembic check` not runnable (no live PostgreSQL), and live upstream API validation explicitly out of scope — all present in `deferred-items.md` and SUMMARY "Deviations". Consistent with the codebase (frontend untouched by phase commits).
3. **ℹ️ pnpm vs npx:** Gate commands used `npx` equivalents (documented D-4) — environment limitation, not a code gap.

### Human Verification Required

1. **Live end-to-end connector run** — Run each of the 5 connectors against real upstream services (PubMed E-utilities, ClinicalTrials.gov APIv2, NewsAPI with a real `NEWSAPI_KEY`, OpenFDA drugsfda, EMA RSS) with a running PostgreSQL. Expected: verbatim payloads land in `raw_signals_bronze` with correct `pmid:`/`nct:`/`reg:` fingerprints and SHA-256 `content_hash`; `connector_state` rows update `last_success`/`cursor`; `/health/connectors` reports accurate live values. Why human: all tests are fully mocked by design (plan §4.15) — live behavior cannot be verified programmatically in this offline environment.
2. **Live Alembic migration** — `alembic upgrade head` on a real PostgreSQL, then `alembic check`. Expected: 001→002 applies with no drift; `connector_state` table + `raw_signals_bronze.cross_source_group_id` column present. Why human: no PostgreSQL on this host; chain validated offline only.
3. **Production wiring of `SourceIndependenceClassifier`** — Confirm/instruct how Phase 2 will invoke `classify()` during ingestion (no production caller exists; currently test-only). Expected: a decision (accept test-only for Phase 1, or wire before Phase 2 Confluence consumption).

### Gaps Summary

**No gaps_found.** All 6 must-have truths verify against the codebase with passing behavioral tests; the 15-point suite exists with exact canonical names and the full 33-test suite passes (independently re-run: 33 passed in 18.04s). One non-blocking warning: the source-independence classifier is orphaned in production code (test-only caller) and the SUMMARY overclaims its health-endpoint wiring — flag for Phase 2 wiring, not a Phase 1 goal failure. Two human-verification items remain (live E2E + live migration) because the phase deliberately mocked all I/O.

---

_Verified: 2026-08-13_
_Verifier: the agent (gsd-verifier)_