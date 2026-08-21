# Phase 08 Plan 03 Summary: Canonical Design System Token Sweep & Banned-Class Grep Gate

**Phase:** Phase 08 — Provenance Traceability, Canonical Overview, Lifecycle & Design Tokens  
**Wave:** Wave 3 — Plan 08-03  
**Status:** COMPLETED & VERIFIED  
**Date:** 2026-08-21  

---

## 1. Objectives & Executive Summary

Wave 3 achieved 100% design system token purity and visual consistency across all workspaces, common components, and navigation surfaces in MetaRadar:
1. **CI-able Banned-Class Grep Gate Script (`scripts/check-banned-classes.mjs`):**
   - Zero-dependency Node script scanning all `.tsx` components under `frontend/components/` (excluding only the canonical reference `metaradar.tsx`).
   - Scans for hardcoded slate utilities (`bg-slate-*`, `text-slate-*`, `border-slate-*`), dark variants, and bracket hex values (`bg-[#...]`, etc.).
   - Integrated as `npm run check:banned-classes` in `frontend/package.json`.
2. **Canonical Design System Token Sweep Across All Workspaces:**
   - Swept all components to semantic CSS variables (`var(--foreground)`, `var(--card)`, `var(--border)`, `var(--surface-muted)`, `var(--surface-subtle)`).
   - Applied canonical SectionTitle hierarchy (`eyebrow` uppercase 11px, `h2` 20px font-bold, `muted-foreground` subtitle).
   - Standardized status badges, filter buttons, side-by-side cards, and data table containers.
3. **Settings Dynamic Credential Governance:**
   - Connected `SettingsWorkspace.tsx` to `fetchSourcesHealth()` to render real API-provided `configuration_error_message` for connectors with missing required keys (`NEWSAPI_KEY`), with official acquisition steps and links.
4. **Theme & Typography Invariant Enforcement:**
   - Single theme provider in `ThemeProvider.tsx` maintaining persistent theme state across navigation, refresh, and direct URLs.
   - Monospace font strictly limited to technical identifiers, run IDs, fingerprints, and timestamps.

---

## 2. Components Swept & Transformed

| Component | Path | Transformation Summary |
|-----------|------|------------------------|
| **Banned Class Gate** | `scripts/check-banned-classes.mjs` | Automated grep oracle scanning 18 files; exits 0 with 0 violations |
| **EmptyState** | `frontend/components/common/EmptyState.tsx` | Replaced slate borders/surfaces with `var(--border)` and `var(--surface-subtle)` |
| **ErrorState** | `frontend/components/common/ErrorState.tsx` | Replaced slate correlation box and diagnostics with semantic tokens |
| **CalibrationWorkspace** | `frontend/components/calibration/CalibrationWorkspace.tsx` | Swept 100+ slate classes; canonical SectionTitle; token-variable active weights and audit log |
| **SignalList** | `frontend/components/signals/SignalList.tsx` | Canonical SectionTitle (`Live Signals`); token filter bar and card grid |
| **SettingsWorkspace** | `frontend/components/settings/SettingsWorkspace.tsx` | Tokenized surface cards; dynamic `fetchSourcesHealth()` credential alert rendering |
| **ContradictionWorkspace** | `frontend/components/contradictions/ContradictionWorkspace.tsx` | Canonical SectionTitle (`Red-Team Contradiction Engine`); tokenized pairwise comparison boxes |
| **FunctionsWorkspace** | `frontend/components/functions/FunctionsWorkspace.tsx` | Canonical SectionTitle (`Stakeholder Functions Intelligence`); tokenized 6 canonical role metrics |
| **DevelopmentsWorkspace** | `frontend/components/developments/DevelopmentsWorkspace.tsx` | Canonical SectionTitle (`Competitive Developments Registry`); tokenized disease tracks |
| **MissingSignalsWorkspace** | `frontend/components/missing-signals/MissingSignalsWorkspace.tsx` | Canonical SectionTitle (`Missing Signal Watch Engine`); tokenized watch cards and status pills |
| **AthenaWorkspace** | `frontend/components/intelligence/AthenaWorkspace.tsx` | Canonical SectionTitle (`Athena Intelligence Synthesis`); tokenized query textarea and citations |
| **ActivityStreamWorkspace** | `frontend/components/observability/ActivityStreamWorkspace.tsx` | Canonical SectionTitle (`System Activity & Observability Stream`); tokenized log cards & diagnostics |
| **ConfluenceWorkspace** | `frontend/components/confluence/ConfluenceWorkspace.tsx` | Fixed remaining backdrop and badge tokens in backward trace inspector |

---

## 3. Executable Verification Results

```bash
# 1. Banned Class Grep Gate
$ npm --prefix frontend run check:banned-classes
> node ../scripts/check-banned-classes.mjs
[BANNED-CLASS-GATE] Clean! Scanned 18 file(s), 0 violations found.

# 2. Frontend ESLint
$ npm --prefix frontend run lint
> eslint .
✔ No ESLint warnings or errors.

# 3. Frontend Next.js Production Build
$ npm --prefix frontend run build
▲ Next.js 16.3.0 (Turbopack)
✓ Compiled successfully in 2.5s
✓ Finished TypeScript in 3.1s
✓ Generating static pages (3/3) in 828ms

# 4. Backend Pytest Test Suite
$ pytest tests/ -x -q
114 passed, 1 skipped, 1 warning in 44.01s
```

---

## 4. UI-SPEC Section 10 Verification Matrix

| Step | Requirement | Verified State |
|------|-------------|----------------|
| **1-2** | Dark/Light theme toggle | All workspaces render dual-theme semantic tokens without light/dark bleed |
| **3-4** | Theme persistence | LocalStorage key `metaradar_theme` persists across client navigations and page refresh |
| **5-7** | Evidence Drawer | Real provenance data (`canonical_url`, `provenance_status`, raw record ref); direct PubMed/ClinicalTrials links |
| **8** | Test Fixture Signal | `TEST FIXTURE` badge (danger tone) + `SOURCE URL UNAVAILABLE` |
| **9** | Confluence Backward Trace | Multi-source threshold (≥3 distinct providers); unbroken verbatim citation chain |
| **10-11** | Source Operations Telemetry | Real HTTP statuses (or `—` when unprobed), records fetched/accepted, and `CONFIGURATION_ERROR` badge |
| **12-14** | Workspace Filters & Settings | Canonical SectionTitle headers, filter active states, and dynamic API credential status |
| **15** | Light mode audit | Clean contrast across all 9 workspaces |

---

## 5. Artifacts & Code Sync

- `scripts/check-banned-classes.mjs`
- `frontend/package.json`
- `frontend/components/common/EmptyState.tsx`
- `frontend/components/common/ErrorState.tsx`
- `frontend/components/calibration/CalibrationWorkspace.tsx`
- `frontend/components/signals/SignalList.tsx`
- `frontend/components/settings/SettingsWorkspace.tsx`
- `frontend/components/contradictions/ContradictionWorkspace.tsx`
- `frontend/components/functions/FunctionsWorkspace.tsx`
- `frontend/components/developments/DevelopmentsWorkspace.tsx`
- `frontend/components/missing-signals/MissingSignalsWorkspace.tsx`
- `frontend/components/intelligence/AthenaWorkspace.tsx`
- `frontend/components/observability/ActivityStreamWorkspace.tsx`
- `frontend/components/confluence/ConfluenceWorkspace.tsx`
