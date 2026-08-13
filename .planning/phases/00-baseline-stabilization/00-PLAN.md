# Phase 0 Plan: Baseline Stabilization & Quality Governance

> **Phase Status:** COMPLETED & VERIFIED  
> **Target Branch:** `feature/stabilization-baseline`  
> **Commit SHA:** `01f8ca8`  
> **Specification References:** `docs/rules/ENGINEERING_STANDARDS.md`, `docs/rules/DEFINITION_OF_DONE.md`, `docs/rules/TESTING_STRATEGY.md`, `docs/10_ARCHITECTURE_HARDENING_REPORT.md`

---

## 1. Goal & Scope

Reconcile dual frontend tree, enforce strict type checking and flat ESLint 10 rules, build an 18-point `pytest` backend test suite, author multi-stage Dockerfiles, scaffold async Alembic migrations, unify the OpenAPI TypeScript contract at `frontend/types/api.ts`, and establish least-privilege GitHub Actions CI governance.

---

## 2. Requirements & Verification Matrix

| Requirement | Implementation File | Verification Command | Status |
|---|---|---|---|
| REQ-P0-1: Next.js 16 + React 19 + Tailwind 4 Stack | `frontend/package.json` | `pnpm exec tsc --noEmit` | **PASS** |
| REQ-P0-2: ESLint 10 Flat Config & Strict TS | `frontend/eslint.config.mjs` | `pnpm lint` (`npx eslint .`) | **PASS** |
| REQ-P0-3: Alembic Async Engine Scaffold | `backend/alembic/env.py` | Scaffold created (`alembic.ini`) | **CONFIGURED** (DB daemon dependent) |
| REQ-P0-4: Container Dockerfiles | `backend/Dockerfile`, `frontend/Dockerfile` | `docker compose config` | **PASS** (Zero warnings) |
| REQ-P0-5: PII Scrubber & Red-Team 19-Rule Registry | `backend/app/services/pii.py`, `redteam.py` | `pytest tests/test_privacy_boundary.py` | **PASS** |
| REQ-P0-6: Honest Health & Diagnostics | `backend/app/api/v1/endpoints/health.py` | `pytest tests/test_api_endpoints.py` | **PASS** |
| REQ-P0-7: Canonical OpenAPI Contract Unification | `scripts/export_openapi.py` -> `frontend/types/api.ts` | `pytest tests/test_contract_drift.py` | **PASS** |
| REQ-P0-8: 18-Point Pytest Test Suite | `tests/` directory | `pytest -v` | **PASS** (18/18 passed in 5.03s) |
| REQ-P0-9: Least-Privilege CI Security | `.github/workflows/ci.yml` | Workflow syntax validation | **PASS** |
| REQ-P0-10: Repository Operating Standards | `docs/rules/`, `AGENTS.md`, `GEMINI.md` | Workspace rule enforcement | **PASS** |

---

## 3. Plan Execution Summary

1. **Frontend Architecture Reconciliation**: Consolidated active App Router tree under `frontend/app/`. Pinned Node 20 in `.nvmrc` and `engines`. Added native ESLint 10 flat config (`frontend/eslint.config.mjs`). Set `typescript: { ignoreBuildErrors: false }` in `next.config.mjs`.
2. **Backend Services & DB Scaffolding**: Authored `backend/Dockerfile` and `frontend/Dockerfile`. Created async Alembic migration environment (`alembic.ini`, `env.py`, `script.py.mako`). Built `PIIPHIScrubber` for regex PII/PHI redaction. Enhanced `RedTeamNLIService` with 19-rule registry (`REDTEAM_RULES` A–S). Updated `HealthResponse`, `HealthReadyResponse`, `HealthConnectorsResponse` to use timezone-aware UTC datetimes.
3. **Contract Unification**: Updated `scripts/export_openapi.py` to write the canonical TypeScript contract directly to `frontend/types/api.ts` and set `frontend/src/types/api.ts` as a re-export pointer. Tested 2x export determinism with 0 diff.
4. **Backend Pytest Suite**: Authored 18-point `pytest` test suite (`test_config.py`, `test_api_endpoints.py`, `test_provider_matrix.py`, `test_privacy_boundary.py`, `test_redteam_behavior.py`, `test_contract_drift.py`). Verified 18/18 tests pass cleanly.
5. **CI Governance**: Added least-privilege `permissions: contents: read` to `.github/workflows/ci.yml` with automated pytest, contract drift, and frontend typecheck/lint/build jobs.
