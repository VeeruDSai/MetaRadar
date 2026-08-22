# Phase 07: Context & Decisions

> **Phase:** 07  
> **Topic:** Trustworthy Intelligence Reconciliation & Platform Hardening  
> **Reference Document:** [docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md)

---

## User Constraints & Directives

1. **Single-Wave Execution**:
   - The user explicitly requested that all code changes across all 36 dimensions must NOT stop after each sub-stage.
   - All tasks in Phase 07 are bundled into **1 large continuous phase / wave** and executed in one go.

2. **Zero Aesthetic Compromise & No Fake Redesign**:
   - This task is NOT a cosmetic visual redesign.
   - It is a combined codebase audit, architecture reconciliation, data-truthfulness correction, intelligence pipeline correction, observability upgrade, UX error-handling enhancement, frontend refactoring, test hardening, and codebase-map update.

3. **Truthfulness Over Convenience**:
   - Never fabricate intelligence or placeholders.
   - Distinguish live production streams from recorded demo fixtures.
   - Explicitly type confidence metrics and state breakdowns.
   - Display real connector statuses and failure diagnostics.

---

## Key Architecture & Implementation Decisions

- **D-07-01 (Continuous Single-Wave Plan)**: Consolidate all tasks into a single comprehensive plan `07-PLAN.md` with organized sub-tasks, executing sequentially without blocking checkpoints.
- **D-07-02 (Canonical Reference)**: All technical design decisions, schemas, error states, and invariant expectations reference `docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md`.
- **D-07-03 (Modular Frontend Architecture)**: Deconstruct monolithic `metaradar.tsx` into domain-bounded packages under `frontend/components/` and `frontend/lib/`.
- **D-07-04 (End-to-End Tracing)**: Enforce `X-Request-ID` and `pipeline_run_id` across FastAPI middleware, connectors, workflow state, and UI error views.
- **D-07-05 (Deterministic Scoring & Provenance)**: Add explicit scoring breakdowns and calculation versions to all signals, confluences, contradictions, and watches.
- **D-07-06 (Codebase Map Refresh)**: Synchronize `.planning/codebase/*.md` with the authoritative state of the codebase upon completion.
