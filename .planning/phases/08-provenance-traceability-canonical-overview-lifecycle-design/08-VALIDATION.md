---
phase: 08
slug: provenance-traceability-canonical-overview-lifecycle-design
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-20
validated: 2026-08-21
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (backend), ESLint 10 + Next.js 16 build + check-banned-classes (frontend) |
| **Config file** | `backend/pyproject.toml` / `frontend/eslint.config.mjs` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Frontend gates** | `npm --prefix frontend run check:banned-classes` + `npm --prefix frontend run lint` + `npm --prefix frontend run build` |
| **Estimated runtime** | ~45 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v` + `npm --prefix frontend run lint` + `npm --prefix frontend run build`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 180 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 1 | REQ-P8-02 | — | Provenance survives serialize→API→mapper | integration | `pytest tests/test_provenance.py` | ✅ Yes | ✅ green |
| 08-01-02 | 01 | 1 | REQ-P8-01/03 | — | No fabricated canonical_url | unit | `pytest tests/test_provenance.py` | ✅ Yes | ✅ green |
| 08-01-03 | 01 | 1 | REQ-P8-05 | — | Synthetic never labeled live | unit | `pytest tests/test_provenance.py` | ✅ Yes | ✅ green |
| 08-01-04 | 01 | 1 | REQ-P8-14 | — | Single authoritative priority score | integration | `pytest tests/test_truthfulness_and_invariants.py` | ✅ Yes | ✅ green |
| 08-02-01 | 02 | 2 | REQ-P8-06/07 | — | Connector telemetry honest; config errors explicit | integration | `pytest tests/test_connector_health.py tests/test_config_errors.py` | ✅ Yes | ✅ green |
| 08-02-02 | 02 | 2 | REQ-P8-17 | — | Ingestion logs debuggable, no secrets | unit | `pytest tests/test_observability.py` | ✅ Yes | ✅ green |
| 08-02-03 | 02 | 2 | REQ-P8-15/16 | — | Confluence semantics truthful + evidence traceable | integration | `pytest tests/test_confluence_semantics.py` | ✅ Yes | ✅ green |
| 08-03-01 | 03 | 3 | REQ-P8-08/09/10 | — | Canonical typography applied everywhere | lint | `npm --prefix frontend run lint` | ✅ Yes | ✅ green |
| 08-03-02 | 03 | 3 | REQ-P8-11/12 | — | Theme single-system, no hardcoded colors | gate + build | `node scripts/check-banned-classes.mjs && npm --prefix frontend run build` | ✅ Yes | ✅ green |
| 08-03-03 | 03 | 3 | REQ-P8-13 | — | Drawers use design tokens | gate + build | `node scripts/check-banned-classes.mjs && npm --prefix frontend run build` | ✅ Yes | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/test_provenance.py` — verified tests for REQ-P8-01…05, 14
- [x] `tests/test_connector_health.py` — verified tests for REQ-P8-06/07
- [x] `tests/test_config_errors.py` — verified tests for missing/placeholder credentials
- [x] `tests/test_observability.py` — verified tests for REQ-P8-17
- [x] `tests/test_confluence_semantics.py` — verified tests for REQ-P8-15/16
- [x] `scripts/check-banned-classes.mjs` — verified CI gate script for REQ-P8-08…13

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions | Status |
|----------|-------------|------------|-------------------|:------:|
| Theme persistence across client navigation / refresh / direct URLs | REQ-P8-11 | Browser-only behavior | Switch dark→light, navigate all workspaces, refresh, reopen signal drawer, return — repeat in dark mode | ✅ Verified |
| "Open Original Source" opens exact PMID / NCT study | REQ-P8-03/04 | External link navigation | Click Open Original Source on a LIVE signal; confirm PubMed/NCT record | ✅ Verified |
| Credential status on Settings page | REQ-P8-07 | Env-dependent | Open /settings with NEWSAPI_KEY absent; confirm `CONFIGURATION_ERROR: NEWSAPI_KEY missing` | ✅ Verified |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify and test files exist
- [x] Sampling continuity: zero gaps across all waves
- [x] Wave 0 covers all requirements
- [x] No watch-mode flags
- [x] Feedback latency < 45s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-21