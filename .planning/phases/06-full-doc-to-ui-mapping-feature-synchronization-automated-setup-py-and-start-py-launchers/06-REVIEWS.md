# Phase 6: Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers — Cross-AI Peer Review

**Date:** 2026-08-18
**Phase:** 06
**Status:** COMPLETE
**Reviewers:** Antigravity / Gemini / Claude Multi-Model Peer Review Matrix

---

## Executive Summary

Phase 6 delivers full doc-to-UI feature parity, OpenAPI contract synchronization, interactive Next.js 16 intelligence/registry views, and zero-config `setup.py` / `start.py` process automation. The 3-wave plan structure (`06-01-PLAN.md`, `06-02-PLAN.md`, `06-03-PLAN.md`) is well-partitioned and tightly grounded in existing database models (`backend/app/models/__init__.py`), existing UI design tokens (`frontend/app/globals.css`), and the hardening decisions in `docs/10_ARCHITECTURE_HARDENING_REPORT.md` (specifically decision A1: no Celery worker).

---

## Plan Reviews

### Plan 06-01: Backend Intelligence Reads, Signal Filters, Cache Flush API & Contract Export (Wave 1)

#### Strengths
- **Grounding in Existing Relational Schema:** Directly reuses existing PostgreSQL models (`Confluence`, `LifecycleEvent`, `Contradiction`, `WatchItem`, `Evidence`, `Development`, `Source`) without requiring destructive schema modifications or new database tables.
- **Contract-Drift Governance:** Integrates `scripts/export_openapi.py` to regenerate `contracts/openapi.json` and `frontend/types/api.ts` directly after adding the new routes, verified by `pytest tests/test_contract_drift.py`.
- **Safe Server-Side Filtering (D-06):** Implements dynamic SQLAlchemy parameterization (`where()` clauses) rather than raw string concatenation, preventing SQL injection (ASVS T-06-01).

#### Concerns & Edge Cases
- **[Severity: MEDIUM] Missing Async Join Handling:** In `backend/app/api/v1/endpoints/intelligence.py` and `registry.py`, querying `Confluence` or `Development` with foreign key relationships (`asset_id`, `company_id`, `development_id`) using `selectinload` or explicit joins is necessary to avoid `sqlalchemy.exc.MissingGreenlet` errors under asyncpg.
- **[Severity: LOW] Redis Connection Resilience:** If Redis is down or unreachable when calling `POST /api/v1/cache/clear`, the endpoint should degrade gracefully (e.g. log a warning and return `{ "status": "cache_unavailable", "keys_cleared": 0 }`) rather than throwing an unhandled 500 error.

#### Suggestions
- Ensure async queries in `intelligence.py` use `select(Confluence).options(selectinload(...))` or explicit `outerjoin` for title resolution.
- Add try/except block around Redis client execution in `cache.py` to support environments where Redis caching is optional or in memory fallback.

---

### Plan 06-02: Feature Parity Manifest, Parity Matrix Generator, Next.js Intelligence Pages & UI Synchronization (Wave 2)

#### Strengths
- **Single Source of Truth Manifest (D-10):** `docs/manifests/feature_parity_manifest.json` provides an auditable, programmatic basis for generating `docs/FEATURE_PARITY_MATRIX.md` and verifying it via `tests/test_parity_matrix.py`.
- **Honest Status Vocabulary (D-09):** Clear taxonomy (`WIRED`, `PARTIAL`, `NOT_WIRED`, `DEFERRED`) adheres strictly to `AGENTS.md` and prevents misleading mock claims.
- **Zero-Redesign UI Alignment (D-01, D-02, D-03):** Reuses the established `metaradar.tsx` component system, `globals.css` color tokens, and `@base-ui/react` modal primitives as locked in `06-UI-SPEC.md`.

#### Concerns & Edge Cases
- **[Severity: MEDIUM] Next.js Hydration Mismatch with LocalStorage:** The Dark Mode toggle in `SettingsPage` should ensure `localStorage.getItem('theme')` is read in an effect or pre-hydration script to prevent React hydration mismatch warnings between server render and client state.
- **[Severity: LOW] Framer Motion Height Transition on Mobile:** In `FilterBar`, ensure `framer-motion` height transitions use `auto` with `overflow-hidden` so filters don't clip on small viewport widths (≤560px).

#### Suggestions
- Add a tiny inline script or `useMounted` guard in `SettingsPage` to sync dark mode without hydration flickers.
- Use `AnimatePresence initial={false}` for `FilterBar` to prevent unwanted initial mount animations.

---

### Plan 06-03: Automated Zero-Config setup.py & Production-Grade start.py Process Launcher (Wave 3)

#### Strengths
- **Compose DBs + Host Processes (D-11, D-13):** Cleanly separates containerized stateful dependencies (PostgreSQL 16, Redis 7, Ollama) from host developer processes (`uvicorn`, `next dev`), enabling direct GPU acceleration and fast Next.js hot module replacement.
- **Strict Compliance with Hardening Decision A1 (D-13):** Does not attempt to launch Celery, respecting the single in-process APScheduler architecture.
- **Robust Telemetry & Graceful Teardown (D-14):** Log streaming to `logs/*.log` paired with live HTTP polling (`/health/ready`, `/health/models`, frontend `/`) and SIGTERM signal trapping.

#### Concerns & Edge Cases
- **[Severity: MEDIUM] Windows Process Tree Termination:** On Windows, `child_proc.terminate()` on a shell command (like `pnpm run dev` or `uvicorn`) may terminate the parent CMD/PowerShell process while leaving the underlying Node.js or Python child process running on port 3000/8000.
  - *Mitigation:* In `start.py`, on Windows use `subprocess.Popen(..., creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)` and terminate via `taskkill /F /T /PID <pid>` to clean up the entire process subtree.
- **[Severity: LOW] Database Readiness Poll in setup.py:** `docker compose up -d` returns before PostgreSQL is fully initialized. `setup.py` must poll `pg_isready` in a loop before running `alembic upgrade head`.

#### Suggestions
- Implement a helper `terminate_process_tree(pid)` in `start.py` that handles Windows `taskkill /F /T /PID` and POSIX `os.killpg(os.getpgid(pid), signal.SIGTERM)`.
- Include a 10-attempt loop with 2-second sleep checking `docker compose exec postgres pg_isready -U metaradar` in `setup.py`.

---

## Risk Assessment

| Risk Category | Level | Justification |
|---------------|-------|---------------|
| **Architecture & Stack** | **LOW** | 100% compliant with approved Next.js 16 + FastAPI + PostgreSQL + Ollama Gemma architecture; no Celery; no forbidden libraries. |
| **Contract & Type Safety** | **LOW** | Automated OpenAPI contract synchronization (`scripts/export_openapi.py`) and pytest contract drift gates prevent drift. |
| **Process Orchestration** | **LOW-MEDIUM** | Windows subprocess termination edge cases are well-understood and addressed via process-group signal trapping. |
| **Overall Execution Risk** | **LOW** | Plans are actionable, self-contained, and verified against real repository code. |

---

## Actionable Review Findings to Incorporate During Execution

1. **`06-01` Backend Read Queries:** Use async SQLAlchemy outer joins or `selectinload` when querying intelligence models to populate title and asset details safely without greenlet exceptions.
2. **`06-01` Cache Flush Safety:** Wrap Redis clear calls in `cache.py` with try/except so cache clear endpoint remains available in in-memory fallback modes.
3. **`06-02` Dark Mode Hydration:** Add client-side mount check in `SettingsPage` to avoid SSR hydration warnings for theme selection.
4. **`06-03` Process Subtree Teardown in `start.py`:** Use `taskkill /F /T /PID` on Windows to guarantee child Node.js and Uvicorn workers are completely terminated on Ctrl+C.
5. **`06-03` PostgreSQL Readiness Gate:** Add explicit retry loop checking `pg_isready` in `setup.py` before applying Alembic migrations.

---

*Review completed: 2026-08-18*
*Status: PASSED — Ready for execution*
