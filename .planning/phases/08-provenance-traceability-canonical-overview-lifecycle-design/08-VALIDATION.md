---
phase: 08
slug: provenance-traceability-canonical-overview-lifecycle-design
# status lifecycle: draft (seeded by plan-phase) → validated (set by validate-phase §6)
# audit-milestone §5.5 distinguishes NOT-VALIDATED (draft) from PARTIAL (validated + nyquist_compliant: false) (#2117)
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-08-20
---

# Phase 08 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x (backend), ESLint 10 + Next.js 16 build (frontend) |
| **Config file** | `backend/pyproject.toml` / `frontend/eslint.config.mjs` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Frontend gates** | `npm --prefix frontend run lint` + `npm --prefix frontend run build` |
| **Estimated runtime** | ~180 seconds |

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
| 08-01-01 | 01 | 1 | REQ-P8-02 | — | Provenance survives serialize→API→mapper | integration | `pytest tests/test_provenance.py` | ❌ W0 | ⬜ pending |
| 08-01-02 | 01 | 1 | REQ-P8-01/03 | — | No fabricated canonical_url | unit | `pytest tests/test_provenance.py` | ❌ W0 | ⬜ pending |
| 08-01-03 | 01 | 1 | REQ-P8-05 | — | Synthetic never labeled live | unit | `pytest tests/test_provenance.py` | ❌ W0 | ⬜ pending |
| 08-01-04 | 01 | 1 | REQ-P8-14 | — | Single authoritative priority score | integration | `pytest tests/test_priority_consistency.py` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 2 | REQ-P8-06/07 | — | Connector telemetry honest; config errors explicit | integration | `pytest tests/test_connector_health.py` | ❌ W0 | ⬜ pending |
| 08-02-02 | 02 | 2 | REQ-P8-17 | — | Ingestion logs debuggable, no secrets | unit | `pytest tests/test_observability.py` | ❌ W0 | ⬜ pending |
| 08-02-03 | 02 | 2 | REQ-P8-15/16 | — | Confluence semantics truthful + evidence traceable | integration | `pytest tests/test_confluence_semantics.py` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 3 | REQ-P8-08/09/10 | — | Canonical typography applied everywhere | lint | `npm --prefix frontend run lint` | ❌ W0 | ⬜ pending |
| 08-03-02 | 03 | 3 | REQ-P8-11/12 | — | Theme single-system, no hardcoded colors | lint + build | `npm --prefix frontend run build` | ❌ W0 | ⬜ pending |
| 08-03-03 | 03 | 3 | REQ-P8-13 | — | Drawers use design tokens | lint + build | `npm --prefix frontend run build` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_provenance.py` — stubs for REQ-P8-01…05, 14
- [ ] `tests/test_connector_health.py` — stubs for REQ-P8-06/07
- [ ] `tests/test_observability.py` — stubs for REQ-P8-17
- [ ] `tests/test_confluence_semantics.py` — stubs for REQ-P8-15/16

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Theme persistence across client navigation / refresh / direct URLs | REQ-P8-11 | Browser-only behavior | Switch dark→light, navigate all workspaces, refresh, reopen signal drawer, return — repeat in dark mode |
| "Open Original Source" opens exact PMID / NCT study | REQ-P8-03/04 | External link navigation | Click Open Original Source on a LIVE signal; confirm PubMed/NCT record |
| Credential status on Settings page | REQ-P8-07 | Env-dependent | Open /settings with NEWSAPI_KEY absent; confirm `CONFIGURATION_ERROR: NEWSAPI_KEY missing` |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 180s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** {pending / approved 2026-08-20}