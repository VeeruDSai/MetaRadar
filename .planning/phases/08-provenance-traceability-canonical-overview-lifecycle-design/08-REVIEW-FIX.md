---
phase: 08-provenance-traceability-canonical-overview-lifecycle-design
reviewed_source: 08-REVIEW.md
status: all_fixed
iteration: 2
fix_scope: critical_warning
findings_in_scope: 30
fixed: 30
skipped: 0
branch: gsd-reviewfix/08-29652
base: 31010e8 (fix/docker-startup-schema-drift)
---

# Phase 08 Code Review Fix Report

Fixes applied on worktree branch `gsd-reviewfix/08-29652` (worktree `.claude/worktrees/rf-08-29652-1787306533`).
Iteration 1 was interrupted mid-run; iteration 2 resumed and completed the scope. Every finding was
re-verified against current code before fixing. Each fix is an atomic commit (`fix(08): ...`).

## Disposition Summary

| Severity | Findings | Fixed | Notes |
|----------|----------|-------|-------|
| Blocker  | 1 (BL-01)   | 1 | |
| Critical | 4 (CR-01..04) | 4 | CR-01 resolved by **revert** — finding was a false positive (see below) |
| Warning  | 25 (WR-01..25) | 25 | WR-01..15 in iteration 1; WR-16..25 in iteration 2 |
| **Total** | **30** | **30** | 0 skipped |

## False-Positive Correction: CR-01

REVIEW.md claimed both synthetic-fallback dataset paths were nonexistent ("fixture mode silently dead").
Executable verification disproved this: `<repo>/backend/app/data/synthetic_signals.json` exists (500 entries,
stable `external_id` on every row) and pre-fix `_load_synthetic_fallback(limit=5)` returned 5 items;
`test_node_ingest_synthetic_fallback` passed on the base commit. The iteration-1 fix repointed resolution to
root `data/synthetic_signals.json` (3 entries) and regressed that test (`assert 3 == 5`). The fix was reverted:

```
2fcd49e Revert "fix(08): CR-01 resolve synthetic fallback dataset from repo root data dir"
```

Fixture-mode resolution is restored to the legacy 500-entry dataset; CR-04's deterministic identity chain in
`runner.py` remains in force. Root `data/synthetic_signals.json` (3 curated fixtures, now with stable
`external_id`s from fd8f72c) remains the canonical E2E scenario dataset asserted by `tests/test_e2e_calibration_scenario.py`.

## Iteration 1 — Blocker + Critical + WR-01..15 (20 commits)

| Commit | Finding | Fix |
|--------|---------|-----|
| `54e4d6e` | BL-01 | Import `HTTPException` in `intelligence.py` so inspect 404 works instead of raising NameError |
| `4ab5b56` → **reverted by `2fcd49e`** | CR-01 | False positive — see correction section above |
| `4aa90f6` | CR-02 | Widen `signals.external_id` to String(255); truncate defensively in runner |
| `ef2fef8` | CR-03 | Exclude failed silver persists from bronze promotion (stops permanent silent data loss) |
| `fd8f72c` | CR-04 | Stable `external_id`s for fixture signals; deterministic runner fallback (`external_id` → `fingerprint` → UUID) |
| `4a7a028` | WR-01 | Reuse canonical `SIGNAL_TYPE_WEIGHTS` in both confluence handlers |
| `c3c8465` | WR-02 | Count distinct `source_id`s in confluence list, matching inspect endpoint |
| `a5ccaf1` | WR-03 | Extract shared `_derive_external_id` helper for list/inspect evidence rows |
| `d65727b` | WR-04 | Tz-aware epoch for state preload comparison; log preload failures |
| `f17b739` | WR-05 | Expose public `GemmaProvider.aclose`; stop touching private `_client` in health |
| `eb28546` | WR-06 | Derive ingestion run status from per-source connector results (no always-`success`) |
| `8e40ede` | WR-07 | Count unpromoted bronze rows via SQL `COUNT` instead of loading ORM rows |
| `d23f05c` | WR-08 | Import connector types for annotations; unify `records_rejected` semantics |
| `4d6d84e` | WR-09 | Log observability query failures loudly instead of swallowing at DEBUG |
| `0f96a25` | WR-10 | Escape LIKE wildcards in registry disease search |
| `27b2d77` | WR-11 | Align Athena evidence distance gate with documented 0.35 contract |
| `2067117` | WR-12 | Stop writing company display names into `company_id` FK; leave unresolved as None |
| `0c54832` | WR-13 | Remove dead `dev_id`; hoist `parse_date` out of per-group loop |
| `a0416a5` | WR-14 | Persist real `published_at` in connector payloads (silver no longer equates crawl time) |
| `a59a05a` | WR-15 | Fix confluence engine docstring; guard source chain against None |

## Iteration 2 — WR-16..25 (11 commits)

| Commit | Finding | Fix |
|--------|---------|-----|
| `0fc3e03` | WR-16 | Feedback error handling; render missing urgency control in EvidenceDrawer |
| `a2319fe` | WR-17 | Gate PII/PHI scrub claim on explicit `pii_scrubbed` flag (no unconditional HIPAA banner) |
| `ec877e5` | WR-18 | Correct signal source filter ids to registry values (`fda`, `ema`) |
| `17ae99e` | WR-19 | Debounce signal search 300ms; abort superseded requests (race clobbering) |
| `3e68df0` | WR-20 | Render 0% action approval rate faithfully instead of fabricated "100%" |
| `681dfcc` | WR-21 | Translate computed watch-state buckets into date-window SQL filters (status filter matches) |
| `92a8215` | WR-22 | Stop fabricating credibility, stakeholder impacts, random fallback ids in signal mapper |
| `6ad3e70` | WR-23 | Fetch real connector count in `fetchHealth`; stop defaulting similarity to 0.5 |
| `349e381` | WR-24 | Non-empty guard in synthetic fallback test (vacuous pass can no longer mask loader failure) |
| `5a5b95c` | WR-25 | Relabel hand-maintained TS contract honestly (no false OpenAPI-autogeneration claim) |
| `61947fd` | WR-17/22 | Keep `pii_scrubbed` + optional credibility in canonical TS contract template |

## Executable Verification (worktree @ `61947fd`, run verbatim)

```
$ python -m pytest tests/ -q
114 passed, 1 skipped, 1 warning in 53.28s

$ npm --prefix frontend run lint
> eslint .
(no errors)

$ npm --prefix frontend run build
▲ Next.js (Turbopack)
✓ Compiled successfully
○ / (Static) · ○ /_not-found (Static) · ƒ /[section] (Dynamic)

$ npm --prefix frontend run check:banned-classes
[BANNED-CLASS-GATE] Clean! Scanned 18 file(s), 0 violations found.
```

Baseline comparison: base `31010e8` also reported 114 passed / 1 skipped; the run at the interrupted
iteration-1 tip regressed to 113 passed / 1 failed (`test_node_ingest_synthetic_fallback`); final state is
green again with all 30 scoped findings addressed.
