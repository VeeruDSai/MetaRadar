# Deferred Items — Phase 1 (Ingestion Connectors & Data Pipeline)

> Pre-existing defects discovered during Plan 1 execution that are **out of scope**
> for this backend plan. Zero frontend files were created or modified by this plan
> (`git status --short frontend/` clean throughout). These failures block Gates 2
> (typecheck) and 4 (build) and must be triaged by the orchestrator.

| # | Gate | Item | Evidence | Suggested fix |
|---|------|------|----------|---------------|
| D-1 | Gate 2 / Gate 4 | `frontend/types/api.ts` (lines 83-86, `HealthModelsResponse`) declares `result: bool` — `bool` is not a valid TypeScript type | `cd frontend && npx tsc --noEmit` → 4× `TS2304: Cannot find name 'bool'`; file committed unchanged in Phase 0 baseline (`git blame` → fix commit exist before Phase 1) | `scripts/export_openapi.py` emits bare `bool` for `boolean` schemas — fix generator or hand-fix the generated contract; then regenerate `frontend/types/api.ts` |
| D-2 | Gate 2 / Gate 4 | `frontend/src/types/api.ts` re-export pointer resolves to nonexistent `../../../types/api` (repo root, not `frontend/types`) | `TS2307: Cannot find module '../../../types/api'` | Fix re-export path to `../../types/api` or regenerate cleanly |
| D-3 | Gate 4 | `frontend/lib/api.ts` + `frontend/lib/mock-data.ts` reference types absent from the canonical contract (`HealthStatus`, `TrendPoint`, `DashboardOverview`, `SignalSource{id}`, `Signal.id`) — many consumer-mismatch type errors | `cd frontend && npx next build` → exit 1 (`"Failed to compile"` / type check failures) | Reconcile lib consumers with the canonical contract or restore the removed exports |
| D-4 | Gates 2/4 | Plan's Gate commands use `pnpm exec ...` but pnpm is not installed on this host | `Get-Command pnpm` → empty | Orchestrator: install pnpm or relax gates to `npx` equivalents (used here: `npx tsc --noEmit`, `npx next build`, `npx eslint .`) |

## How these were handled

- **Not fixed** — out of scope (Rule scope boundary: pre-existing failures in unchanged files).
- **Verified pre-existing**: `git status --short frontend/` shows no changes; all frontend files identical to Phase 0 baseline; failures reproduced from a clean checkout state with zero Phase-1 involvement.
- **Escalated**: Gates 2 and 4 cannot PASS until a frontend/contract-infra plan addresses D-1..D-3.

## Verification status of the affected gates

| Gate | Command | Result | Cause |
|------|---------|--------|-------|
| 2 | `npx tsc --noEmit` (frontend) | ⚠️ FAILED (4 errors) | D-1 + D-2 |
| 3 | `npx eslint .` (frontend) | ✅ PASS (0 errors) | — |
| 4 | `npx next build` (frontend) | ⚠️ FAILED | D-1..D-3 |
| 5 | `alembic check` | ⚠️ NOT RUNNABLE (no live PostgreSQL on this host — port 5432 closed; migration chain validated offline via `alembic history`) | environment |