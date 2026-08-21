# Debug Session: UI Canonical Consistency & Empty-State Alignment

**Status:** Resolved  
**Date:** 2026-08-21  
**Target:** Frontend workspaces + globals.css + sources health API  

## Symptoms
1. "No signals detected yet" alert in Overview (`DashboardPage`) was left-aligned, misplaced, and uncentered.
2. Workspaces (`/sources`, `/signals`, `/confluence`, `/red-team`, `/missing-signals`, `/developments`, `/intelligence`, `/functions`, `/calibrate`, `/observability`, `/settings`) looked scattered with inconsistent font sizes (`text-xl font-bold` vs `.section-title h1`), custom dashed empty states, non-canonical padding/margins, and hardcoded colors.
3. Sources & Connectors showed "No sources configured" in a dashed empty box when the database was unseeded.

## Root Cause Analysis
1. `frontend/app/globals.css` had a secondary `.empty-state` declaration with `align-items: flex-start` overriding the primary centered `.empty-state`.
2. Workspace components (`SignalList.tsx`, `SourcesOperationsWorkspace.tsx`, `ContradictionWorkspace.tsx`, `MissingSignalsWorkspace.tsx`, `DevelopmentsWorkspace.tsx`, `AthenaWorkspace.tsx`, `FunctionsWorkspace.tsx`, `CalibrationWorkspace.tsx`, `ActivityStreamWorkspace.tsx`, `SettingsWorkspace.tsx`, `EvidenceDrawer.tsx`, `DataModeBadge.tsx`, `ErrorState.tsx`) implemented disparate headers and hardcoded Tailwind color palettes, bypassing `<SectionTitle>`, `<Card>`/`.panel`, `<Badge>`, `.filter-bar`, and canonical CSS variables defined in `08-UI-SPEC.md`.
3. Backend `/api/v1/sources/health` and `/api/v1/sources` returned an empty list when DB `sources` table had 0 rows instead of surfacing canonical source providers with fallback status.

## Resolution Executed
1. **Fixed `globals.css`**: Removed the overriding `align-items: flex-start` from `.empty-state`, establishing the canonical centered empty state with unified typography and icon alignment.
2. **Standardized All Workspace Components**:
   - Refactored all workspace components to use `<SectionTitle eyebrow="..." title="..." detail="..." />`, matching the exact font size, font spacing, and panel styling of the Overview tab.
   - Refactored all components to use `<Card>` (`.panel`), `<Badge tone="...">`, `.filter-bar button` / `.filter-active`, and CSS variables (`var(--foreground)`, `var(--muted-foreground)`, `var(--surface)`, `var(--border)`, `var(--signal)`, `var(--primary)`, `var(--success)`, `var(--danger)`).
   - Replaced custom dashed boxes with canonical `<Card className="empty-state">`.
   - Refactored `EvidenceDrawer`, `DataModeBadge`, and `ErrorState` to eliminate hardcoded Tailwind colors.
3. **Enhanced Backend Sources Endpoints**:
   - `backend/app/api/v1/endpoints/observability.py` and `backend/app/api/v1/endpoints/registry.py` now ensure all 5 canonical providers (PubMed, ClinicalTrials.gov, OpenFDA, EMA, NewsAPI) always surface with truthful status.
4. **Verification Gates Passed**:
   - `node scripts/check-banned-classes.mjs`: Clean! Scanned 18 files, 0 violations found.
   - `npm --prefix frontend run lint`: 0 errors, 0 warnings.
   - `npm --prefix frontend run build`: Compiled successfully, type checking passed, static pages generated.
   - `pytest tests/ -v`: 114 passed, 1 skipped, 0 failures.
