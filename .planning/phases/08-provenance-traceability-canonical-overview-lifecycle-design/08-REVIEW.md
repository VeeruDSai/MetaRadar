---
phase: 08-provenance-traceability-canonical-overview-lifecycle-design
reviewed: 2026-08-21T00:00:00Z
depth: standard
files_reviewed: 47
files_reviewed_list:
  - backend/alembic/versions/005_provenance_traceability.py
  - backend/app/api/v1/endpoints/health.py
  - backend/app/api/v1/endpoints/ingestion.py
  - backend/app/api/v1/endpoints/intelligence.py
  - backend/app/api/v1/endpoints/observability.py
  - backend/app/api/v1/endpoints/registry.py
  - backend/app/api/v1/endpoints/signals.py
  - backend/app/connectors/base.py
  - backend/app/connectors/clinical_trials.py
  - backend/app/connectors/ema.py
  - backend/app/connectors/fda.py
  - backend/app/connectors/newsapi.py
  - backend/app/connectors/pubmed.py
  - backend/app/core/config.py
  - backend/app/models/__init__.py
  - backend/app/schemas/__init__.py
  - backend/app/schemas/registry.py
  - backend/app/services/confluence.py
  - backend/app/services/ingestion.py
  - backend/app/workflows/nodes/confluence.py
  - backend/app/workflows/nodes/ingest.py
  - backend/app/workflows/runner.py
  - frontend/lib/api.ts
  - frontend/lib/mappers.ts
  - frontend/types/api.ts
  - frontend/components/common/DataModeBadge.tsx
  - frontend/components/common/EmptyState.tsx
  - frontend/components/common/ErrorState.tsx
  - frontend/components/common/EvidenceDrawer.tsx
  - frontend/components/signals/SignalCard.tsx
  - frontend/components/signals/SignalList.tsx
  - frontend/components/confluence/ConfluenceWorkspace.tsx
  - frontend/components/contradictions/ContradictionWorkspace.tsx
  - frontend/components/developments/DevelopmentsWorkspace.tsx
  - frontend/components/functions/FunctionsWorkspace.tsx
  - frontend/components/athena/AthenaWorkspace.tsx
  - frontend/components/missing-signals/MissingSignalsWorkspace.tsx
  - frontend/components/activity/ActivityStreamWorkspace.tsx
  - frontend/components/settings/SettingsWorkspace.tsx
  - frontend/components/sources/SourcesOperationsWorkspace.tsx
  - frontend/components/calibration/CalibrationWorkspace.tsx
  - tests/test_config_errors.py
  - tests/test_confluence_semantics.py
  - tests/test_connector_health.py
  - tests/test_ingestion.py
  - tests/test_observability.py
  - tests/test_provenance.py
  - tests/test_signals_endpoints.py
  - tests/test_truthfulness_and_invariants.py
  - scripts/check-banned-classes.mjs
  - scripts/export_openapi.py
  - .github/workflows/ci.yml
  - contracts/openapi.json
  - frontend/package.json
  - data/synthetic_signals.json
findings:
  critical: 5
  warning: 25
  info: 7
  total: 37
status: issues_found
---

# Phase 08: Code Review Report

**Reviewed:** 2026-08-21T00:00:00Z
**Depth:** standard
**Files Reviewed:** 47 (+ supporting cross-checks: models, migrations, fixtures, glob verification)
**Status:** issues_found

## Summary

Phase 08 adds provenance traceability columns (migration 005), canonical `/overview`, confluence lifecycle/inspect endpoints, connector configuration-error surfacing, and frontend truthfulness UI. The core serialization round-trip (`_serialize_signal`), connector health mapping, PII scrubbing, and most test suites are solid. However, the phase ships with **one guaranteed-crash bug** (`HTTPException` used but never imported in `intelligence.py`), **a broken synthetic-fallback file path that silently disables the entire fixture mode**, **a schema-length mismatch that permanently drops NewsAPI signals while still marking their bronze rows promoted (silent data loss)**, and **multiple fabricated-telemetry violations of AGENTS.md rule #4** on the frontend (hardcoded `sourceCount: 5`, `credibility: 90`, magic-multiplier stakeholder values, unconditional HIPAA-compliance banner, `0% → "100%"` rendering bug). Several filters are wired to value spaces that can never match backend data (source filter IDs, missing-signal status casing).

Cross-checks performed: verified `backend/data/` does not exist (glob); traced fingerprint assignment chain (`validate.py` → `nlp_extract.py` → `ontology.py` → confluence node — consistent keys); confirmed column widths (`RawSignalBronze.external_id` String(255) vs `signals.external_id` String(100)) via models and migrations 001/005.

## Critical Issues

### BL-01: `HTTPException` raised but never imported — inspect endpoint crashes with NameError instead of returning 404

**File:** `backend/app/api/v1/endpoints/intelligence.py:215` (import at line 5)
**Issue:** Line 5 imports only `APIRouter, Depends, Query` from fastapi, but line 215 raises `HTTPException(status_code=404, ...)` when a confluence id is not found. Every miss on `GET /api/v1/confluence/{confluence_id}/inspect` raises `NameError: name 'HTTPException' is not defined` → unhandled 500. This violates the OpenAPI contract (openapi.json documents the 404 response) and breaks the frontend `ConfluenceWorkspace` fallback path that specifically handles 404.
**Fix:**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
```

### CR-01: Synthetic-fallback dataset path resolution is wrong — fixture mode silently disabled

**File:** `backend/app/workflows/nodes/ingest.py:17-20`
**Issue:** `_load_synthetic_fallback` resolves `Path(__file__).resolve().parents[3] / "data" / "synthetic_signals.json"`. For `backend/app/workflows/nodes/ingest.py`, `parents[3]` is `backend/`, yielding `backend/data/synthetic_signals.json` — **verified nonexistent** (glob shows no `backend/data/`). The fallback branch resolves `parents[4]/backend/app/data/synthetic_signals.json` = `<root>/backend/app/data/synthetic_signals.json` — **also nonexistent**. The actual fixture lives at repo root `data/synthetic_signals.json`. Because the function swallows the miss and returns `[]` (line 36), demo/fixture mode silently produces zero signals with no error surfaced — exactly the kind of dishonest degradation AGENTS.md forbids.
**Fix:**
```python
data_path = Path(__file__).resolve().parents[4] / "data" / "synthetic_signals.json"
if not data_path.exists():
    logger.error(f"Synthetic fallback dataset missing at {data_path}")
```
(Remove the bogus second candidate or point it at the real location.)

### CR-02: `external_id` length mismatch silently drops NewsAPI signals on every run

**File:** `backend/app/workflows/runner.py:225-279`; schema: `backend/alembic/versions/005_provenance_traceability.py:20`, `backend/app/models/__init__.py:163,211`
**Issue:** Bronze stores `external_id` as `String(255)` (models line 163) and the NewsAPI connector writes the **full article URL** into it. Runner copies it verbatim into `signals.external_id` which migration 005 defines as `String(100)` (line 20). Real NewsAPI URLs routinely exceed 100 chars → asyncpg `StringDataRightTruncationError` on the `pg_insert` at runner.py:225-277, caught by the broad `except` at 278-279 which logs a warning and continues. Result: every long-URL news signal is dropped from silver on **every** pipeline run, while the run reports success.
**Fix:** Widen the column and truncate defensively:
```python
# new migration
op.alter_column('signals', 'external_id', existing_type=sa.String(100), type_=sa.String(255))
```
```python
ext_id = sig.get("external_id") or str(sig_uuid)
if len(ext_id) > 255:
    ext_id = ext_id[:255]
```

### CR-03: Bronze rows marked promoted even when silver persistence failed — permanent silent data loss

**File:** `backend/app/workflows/runner.py:301-314` (interacts with 278-279)
**Issue:** Step 4 marks **all** ids from `final_state["raw_signals"]` as promoted (`pipeline_run_id=run_uuid`) regardless of whether their silver insert succeeded. Signals whose persist raised (e.g., all CR-02 victims) are caught-and-logged at 278, then their bronze rows are stamped promoted at 309-314 — so `node_ingest`'s queue filter (`pipeline_run_id.is_(None)`, ingest.py:62) will never select them again. Combined with CR-02 this is an unrecoverable, invisible data-loss loop.
**Fix:** Track failed signal ids during step 2 and exclude them from the promotion update:
```python
failed_ids = set()
...
except Exception as e:
    logger.warning(f"Could not persist signal {sig.get('title')}: {e}")
    if sig.get("id"):
        failed_ids.add(str(sig["id"]))
...
bronze_ids = [uuid.UUID(str(s["id"])) for s in final_state.get("raw_signals", [])
              if s.get("id") and len(str(s["id"])) == 36 and str(s["id"]) not in failed_ids]
```

### CR-04: Synthetic fixture signals get random UUIDs as `external_id`/`pmid` and unstable fingerprints — duplicates accumulate

**File:** `backend/app/workflows/runner.py:167-172,168`; fixture: `data/synthetic_signals.json`
**Issue:** Fixture items carry no `external_id` key, so line 167 falls back to `str(sig_uuid)` — a fresh random UUID per run. Consequences: (a) for the pubmed fixture item, `pmid` (line 170) is persisted as a random UUID — fabricated identifier data; (b) the derived fingerprint `sig:{source}:{ext_id}` (line 168) changes every run, so the `on_conflict_do_update(index_elements=["fingerprint"])` upsert never matches and duplicate rows accumulate on each pipeline run. Latent today only because CR-01 prevents fixtures from loading at all; becomes live the moment CR-01 is fixed.
**Fix:** Add stable `external_id` (and ideally `fingerprint`) fields to every item in `data/synthetic_signals.json`, and make the default deterministic:
```python
ext_id = sig.get("external_id") or sig.get("fingerprint") or str(sig_uuid)
```

## Warnings

### WR-01: Inline confluence points diverge from canonical `SIGNAL_TYPE_WEIGHTS`

**File:** `backend/app/api/v1/endpoints/intelligence.py:131-140, 251-260`
**Issue:** Both handlers hardcode their own type→points maps instead of importing `SIGNAL_TYPE_WEIGHTS`: CONGRESS gets 25 (canonical 15) and ACCESS gets 25 (canonical 15). List view and inspect view therefore agree with each other but disagree with the engine and with any future weight change — three sources of truth.
**Fix:** Import and reuse `SIGNAL_TYPE_WEIGHTS` (with `.get(t, DEFAULT_POINTS)`) in both places; delete the inline dicts.

### WR-02: `independent_sources_count` means different things in list vs inspect

**File:** `backend/app/api/v1/endpoints/intelligence.py:166` vs `:289`
**Issue:** The list endpoint computes `independent_count = len(set(signal_types))` (counts signal *types*), while the inspect endpoint correctly counts `len(distinct_source_ids)` (distinct *sources*). Same confluence reports different independence counts depending on which endpoint you ask; the field name says "sources".
**Fix:** Compute distinct `source_id`s in the list handler exactly as the inspect handler does.

### WR-03: Inconsistent `external_id` fallback between list and inspect evidence rows

**File:** `backend/app/api/v1/endpoints/intelligence.py:118` vs `:262`
**Issue:** List fallback chain ends with the full fingerprint `s[4]` (e.g., `sig:pubmed:38123456:…`, 64+ chars); inspect truncates `s[4][:12]`. The same underlying signal renders different `external_id` values in the two views, breaking traceability joins against bronze.
**Fix:** Extract one shared helper `_derive_external_id(row)` used by both handlers (prefer pmid/nct/regulatory, then `fingerprint[:12]`, then str(id)).

### WR-04: Naive-vs-aware datetime comparison can abort health state preload silently

**File:** `backend/app/api/v1/endpoints/health.py:106-109`
**Issue:** `(row.updated_at or datetime.min)` compares tz-aware `updated_at` against naive `datetime.min` → `TypeError: can't subtract offset-naive and offset-aware datetimes` whenever one row has `updated_at IS NULL` and another doesn't. The surrounding `except Exception: pass` (108-109) then silently aborts the **entire** preload loop, degrading freshness classification for all connectors with no telemetry.
**Fix:**
```python
_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)
latest = max((r.updated_at or _EPOCH for r in rows), default=_EPOCH)
```
and log the exception instead of passing.

### WR-05: Health endpoint reaches into provider private attribute

**File:** `backend/app/api/v1/endpoints/health.py:74`
**Issue:** `provider._client` accesses a private attribute of the LLM provider; any refactor of the provider internals breaks health checks at runtime rather than at import time.
**Fix:** Expose a public `provider.is_available()` / `provider.client_ok` property and use that.

### WR-06: Ingestion run status is always `"success"` — dishonest telemetry

**File:** `backend/app/api/v1/endpoints/ingestion.py:85`
**Issue:** `"status": "success" if ingest_telemetry["total_fetched"] >= 0 else "partial"` — `total_fetched` is a count and can never be negative, so the else-branch is dead and the API always reports success even when connectors failed/degraded. Violates AGENTS.md #4 (no fabricated behavior).
**Fix:** Derive status from per-source results, e.g. `"success" if all(r["status"] == "HEALTHY" ...) else "partial"`.

### WR-07: Unpromoted-bronze count materializes all ORM rows

**File:** `backend/app/api/v1/endpoints/ingestion.py:110-112`
**Issue:** Loads every unpromoted `RawSignalBronze` row into memory just to take `len(rows)`; unbounded growth makes this endpoint progressively heavier and can OOM at scale.
**Fix:** `await session.execute(select(func.count()).select_from(RawSignalBronze).where(RawSignalBronze.pipeline_run_id.is_(None)))`.

### WR-08: Service-layer annotation references unimported names; `records_rejected` semantics inconsistent

**File:** `backend/app/services/ingestion.py:37,52,102`
**Issue:** Local annotations `results_by_source: Dict[str, List[SourceConnector]]` and `List[ProfileRunResult]` reference names never imported (not evaluated at runtime, but breaks mypy/pyright and misleads readers). Line 102 sets `records_rejected=conn_dups` while `base.py:_persist_health_log` sets `records_rejected=result.errors` — two different definitions of "rejected" feeding the same metric.
**Fix:** Import the names (or annotate with correct types); pick one definition of `records_rejected` (duplicates vs errors) and document it.

### WR-09: Observability endpoints swallow DB errors behind debug logs

**File:** `backend/app/api/v1/endpoints/observability.py:59-60, 89-90`
**Issue:** Broad `except Exception` blocks log at DEBUG and return empty/partial payloads; an outage of `activity_logs` looks identical to "no activity". For an observability feature, hiding its own failure mode is self-defeating.
**Fix:** Log at `logger.warning`/`error` with `exc_info=True`, and include a top-level `"degraded": true` flag in the response.

### WR-10: Registry search does not escape LIKE wildcards

**File:** `backend/app/api/v1/endpoints/registry.py:35`
**Issue:** User input is passed to `ilike(f"%{query}%")` unescaped. Parameterized (no SQL injection), but `%`/`_` in input act as wildcards — a search for `100%` matches everything, and crafted patterns enable cheap table scans.
**Fix:** Escape before use: `query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")` and pass `.escape("\\")` context to `ilike`.

### WR-11: Similarity threshold contradicts its own comment

**File:** `backend/app/api/v1/endpoints/signals.py:329`
**Issue:** Code filters `distance < 0.40` directly above a comment stating candidates require distance < 0.35 (similarity ≥ 0.65). One of them is wrong; whichever way, the Athena evidence gate differs from its documented contract.
**Fix:** Align constant and comment (extract `MAX_EVIDENCE_DISTANCE = 0.35` and reuse).

### WR-12: Workflow sets `company_id` to a company *name*

**File:** `backend/app/workflows/nodes/confluence.py:89`
**Issue:** New developments get `company_id` set from the extracted company **name** (and literally `"Unknown"` when absent). `companies.company_id` is a String PK keyed by normalized ids, not display names — inserts will either violate the FK or silently create junk company rows keyed by arbitrary display strings.
**Fix:** Resolve names→ids via the companies table (or domain config alias map) before assignment; leave `company_id=None` when unresolved.

### WR-13: Confluence node error path clobbers state; dead variable; function redefined in loop

**File:** `backend/app/workflows/nodes/confluence.py:52, 60, 175`
**Issue:** (a) The outer `except` returns `developments: []` — under LangGraph-style state merge this can wipe developments accumulated by upstream nodes instead of preserving them. (b) `dev_id` assigned at line 52 and never used. (c) `parse_date` is redefined inside the per-development loop — wasted redefinition and confusing shadowing.
**Fix:** On error return `{}` or preserve `state.get("developments", [])`; delete `dev_id`; hoist `parse_date` above the loop.

### WR-14: `published_at` silently equals retrieval time — provenance timestamps are misleading

**File:** `backend/app/workflows/nodes/ingest.py:78` interacting with all five connectors
**Issue:** Connectors store publication dates under keys like `pub_date`/`action_date`/`publishedAt` in `raw_payload`, but none store a `published_at` key, so ingest always falls back to `row.retrieved_at`. Every silver signal's `published_at` (displayed in the UI and feeding recency scoring/trends) is really its crawl time — fabricated provenance that overstates freshness.
**Fix:** Normalize in each connector: write `raw_payload["published_at"] = <parsed date>.isoformat()` (or `None` when genuinely unknown) and let ingest distinguish "unknown" from "now".

### WR-15: Confluence engine docstring contradicts implementation; `str(None)` edge case

**File:** `backend/app/services/confluence.py:117` and docstring
**Issue:** Docstring says detection requires N independent signal *types*; the code gates on distinct `source_id`s (correct per tests, but the docstring misleads maintainers). Also `str(source_id)` where `source_id` may be `None` yields the literal string `"None"`, which would count as one "distinct source".
**Fix:** Fix the docstring; guard `source_id` before stringifying and skip None-source signals.

### WR-16: Feedback submission has no error handling; urgency rating control missing

**File:** `frontend/components/common/EvidenceDrawer.tsx` (handleFeedback try/finally; urgency state declared ~line 29, submit body)
**Issue:** (a) `try { await submitFeedback(...) } finally { ... }` with no `catch` — API failures become unhandled promise rejections; the user gets no feedback and the drawer gives no indication anything failed. (b) An `urgency` state exists and is submitted as `urgency_rating`, but no urgency input is ever rendered — every submission sends the default `4`, polluting calibration data with fabricated ratings.
**Fix:** Add `catch` with visible error state (reuse `ErrorState`); render a urgency 1–5 selector bound to the existing state, or stop submitting `urgency_rating` until the control exists.

### WR-17: Unconditional "HIPAA Safe Harbor compliant" claim regardless of actual scrubbing

**File:** `frontend/components/common/EvidenceDrawer.tsx:230`
**Issue:** The drawer always renders "PII/PHI scrubber evaluated … HIPAA Safe Harbor compliant" — there is no per-signal scrub status field driving it. This is fabricated compliance telemetry (AGENTS.md #4/#7 territory) and dangerous in a health-data product.
**Fix:** Render the claim only when the payload carries an explicit scrub result (e.g., `pii_scrubbed === true` from raw_payload/evidence metadata); otherwise show "scrub status unknown".

### WR-18: Signal list source filter options reference nonexistent source ids

**File:** `frontend/components/signals/SignalList.tsx:95-96`
**Issue:** Filter dropdown offers `openfda` and `ema_rss`; backend registry/source ids are `fda` and `ema`. Selecting either option queries `?source=openfda|ema_rss` and always returns zero results.
**Fix:** Use `fda` and `ema` (ideally import the options from the sources registry response instead of hardcoding).

### WR-19: Search fires per keystroke with no debounce or abort — race conditions

**File:** `frontend/components/signals/SignalList.tsx` (search useEffect/handler)
**Issue:** Each keystroke triggers a fetch with no debounce and no `AbortSignal`; slow earlier responses can resolve after later ones and clobber newer results (out-of-order state overwrite).
**Fix:** Debounce ~300 ms and pass an `AbortController` signal, ignoring aborted responses:
```ts
const ctrl = new AbortController();
const res = await fetchSignals(q, { signal: ctrl.signal });
...
return () => ctrl.abort();
```

### WR-20: `0%` action approval rate renders as `100%`

**File:** `frontend/components/functions/FunctionsWorkspace.tsx:104`
**Issue:** `{role.action_approval_rate ? `${...}%` : '100%'}` — falsy `0` falls into the `'100%'` branch. A role with zero approval (the strongest possible negative calibration signal) displays as perfect approval. Fabricated telemetry.
**Fix:** `{role.action_approval_rate != null ? \`${role.action_approval_rate}%\` : '—'}`.

### WR-21: Missing-signals status filter can never match

**File:** `frontend/components/missing-signals/MissingSignalsWorkspace.tsx` (status filter construction) vs `backend/app/api/v1/endpoints/intelligence.py` (watch-items filter)
**Issue:** Frontend derives computed statuses (`OVERDUE`/`DUE`/`WITHIN_WINDOW`, uppercase) and sends them as `status`, but the backend filters `WatchItem.status == status` against **stored** lowercase lifecycle values (`watching`/`satisfied`/`suppressed`). Every filtered query returns empty.
**Fix:** Either map computed buckets to server-side overdue/due-date query params, or have the backend accept the computed bucket and translate it into date-window comparisons.

### WR-22: Mapper fabricates credibility, stakeholder values, and unstable IDs

**File:** `frontend/lib/mappers.ts:93, 121, 127-132`
**Issue:** (a) `SIG-${Math.random()}` fallback id produces different ids on every render/re-map — unstable React keys and broken row identity. (b) Hardcoded `credibility: 90` for every source. (c) Stakeholder impacts derived via magic multipliers `*3.3`/`*4.0` — numbers presented as data but invented. All violate AGENTS.md #4.
**Fix:** Use the signal's real id/fingerprint as fallback key; omit `credibility` until backend supplies it; render stakeholders only from real data (or clearly label as illustrative).

### WR-23: Health/search mappers hardcode fabricated metrics

**File:** `frontend/lib/api.ts:308, 128`
**Issue:** `fetchHealth` returns `sourceCount: 5` unconditionally (should come from `/health/connectors` length or `/overview`); `mapSearchResult` defaults `similarity_score` to `0.5` when absent — invented relevance shown to users.
**Fix:** Fetch real count (or drop the field); render similarity as "—" when the backend omits it.

### WR-24: Vacuous synthetic-fallback test masks CR-01

**File:** `tests/test_provenance.py:125-131`
**Issue:** `test_synthetic_fallback_tagging` iterates `items` and asserts per-item properties — but because of CR-01 the loader returns `[]`, the loop body never executes, and the test passes while the feature is completely broken. No `assert items` guard exists.
**Fix:** Add `assert len(items) > 0, "synthetic fallback returned no items — check dataset path"` at the top of the test.

### WR-25: "Contract sync" gate validates nothing — TS types are a static template

**File:** `scripts/export_openapi.py:30-597` (vs lines 15, 599-602); `.github/workflows/ci.yml:35-40`
**Issue:** `export_openapi.py` calls `app.openapi()` but only dumps it to JSON; the "auto-generated" `frontend/types/api.ts` is a hand-maintained string literal embedded in the script. The CI job regenerates the file and `git diff --exit-code`s it — which can only ever pass, because the file is regenerated from the same static template. Drift between the real FastAPI schema and the TS contract is undetectable, while the header claims "Auto-generated from FastAPI OpenAPI Schema". This is a false-assurance gate contrary to TESTING_STRATEGY's contract-sync intent.
**Fix:** Generate TS types from the schema (datamodel-code-generator/openapi-typescript) or add a validation step comparing schema response models against the template's interfaces; at minimum change the header to honestly say "hand-maintained".

## Info

### IN-01: CI disables lockfile enforcement

**File:** `.github/workflows/ci.yml:55`
**Issue:** `pnpm install --frozen-lockfile=false` allows dependency drift in CI builds; reproducibility and supply-chain guarantees are weakened.
**Fix:** Use `pnpm install --frozen-lockfile` (and commit the lockfile).

### IN-02: Contract check ignores the legacy stub the exporter also writes

**File:** `.github/workflows/ci.yml:40` vs `scripts/export_openapi.py:604-610`
**Issue:** The exporter writes `frontend/src/types/api.ts` too, but CI only diffs `frontend/types/api.ts`.
**Fix:** Diff both files (or stop writing the legacy stub).

### IN-03: Unused imports across reviewed modules

**File:** `backend/app/api/v1/endpoints/intelligence.py:1` (`uuid`), `:4` area (`func`); `health.py:2` (`status`); `endpoints/ingestion.py:1,3` (`logging`, `Query`, `status`, unused module-level `logger`); `observability.py:1` (`time`), unused `uuid4`, `AuditLog`
**Issue:** Dead imports accumulate noise and trip lint configs.
**Fix:** Remove them (or wire up the intended usage, e.g., the ingestion `logger`).

### IN-04: Duplicated `utc_now()` helper

**File:** multiple backend modules (services, workflows nodes, endpoints)
**Issue:** Identical `def utc_now(): return datetime.now(timezone.utc)` reimplemented per module.
**Fix:** Move to `app/core/timeutil.py` and import.

### IN-05: Pipeline trigger label is inaccurate for API-triggered runs

**File:** `backend/app/workflows/runner.py:58`
**Issue:** `trigger="scheduled" if not raw_signals else "manual"` labels API-initiated runs (which pass no `raw_signals`) as "scheduled".
**Fix:** Accept an explicit `trigger` argument from the caller (API passes `"manual"`).

### IN-06: Overview endpoint issues one query per development

**File:** `backend/app/api/v1/endpoints/signals.py` (overview lifecycle section)
**Issue:** N+1 signal-count query per development (capped at 10 today). Correctness unaffected; flagged for awareness only (perf out of scope v1).
**Fix:** Single grouped count query `GROUP BY development_id` when convenient.

### IN-07: Calibration workspace uses `alert()` and swallows error details

**File:** `frontend/components/calibration/CalibrationWorkspace.tsx:66-68`
**Issue:** `alert()` for success/error is inconsistent with the `ErrorState`/toast patterns used elsewhere; the catch discards the server's error message.
**Fix:** Route through shared error/success UI and surface `err.message`.

---

_Reviewed: 2026-08-21T00:00:00Z_
_Reviewer: the agent (gsd-code-reviewer)_
_Depth: standard_
