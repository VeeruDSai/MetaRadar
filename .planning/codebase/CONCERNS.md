# Concerns & Technical Debt Audit

> Property of the developer. Strict status classification: PASS, PARTIAL, FAIL, BLOCKED, NOT EXECUTED, CONFIGURED.

## Active & Pending Runtime Concerns

### Blocked Runtime Execution
- **B1. Database Migration Runtime Execution (BLOCKED)**
  - Description: Async Alembic engine scaffolded (`alembic.ini`, `env.py`, `script.py.mako`), but runtime execution of `alembic upgrade head` and `alembic check` requires a running PostgreSQL daemon on port 5432.
  - Evidence: `alembic check` returns `ConnectionRefusedError [WinError 1225]` when PostgreSQL service is not active.
  - Recommended action: Launch local PostgreSQL 16 daemon on port 5432 to execute database runtime migration verification.

### Unexecuted Container Runtime
- **U1. Docker Stack Container Execution (NOT EXECUTED)**
  - Description: Container images authored (`backend/Dockerfile`, `frontend/Dockerfile`) and `docker compose config` validated with zero warnings. Runtime container startup (`docker compose up -d`) and health checks require an active Docker Desktop daemon.
  - Evidence: `docker ps` returns daemon connection failure on host machine.
  - Recommended action: Launch Docker Desktop daemon on host machine to execute full container stack runtime verification.

---

## Resolved Concerns Baseline (Stabilized & Verified)

- **Backend Pytest Test Suite (M2, resolved 2026-08-13):**
  - Authored an 18-point `pytest` backend test suite (`tests/`) covering configuration, FastAPI endpoints (`/health/*`, `/signals`, `/overview`, `/athena`), Cases A–F provider matrix, PII regex scrubbing & Grok gate bypass prevention, Red-Team 19-rule gating & caching, and contract drift. All 18 tests passed cleanly in 5.03s.
- **Canonical API Contract Location (H9, resolved 2026-08-13):**
  - Unified canonical contract export location at `frontend/types/api.ts` with legacy pointer at `frontend/src/types/api.ts`. Verified zero-diff deterministic generation.
- **Frontend Build & Quality Gates (H-FE2, resolved 2026-08-13):**
  - Enforced strict TypeScript build checking (`typescript: { ignoreBuildErrors: false }`). Verified 0 type errors via `npx tsc --noEmit`.
  - Added native ESLint 10 flat config (`frontend/eslint.config.mjs`). Verified 0 lint errors via `npx eslint .`.
  - Verified production build compilation via `npx next build`.
- **Least-Privilege CI Security (CI-CD, resolved 2026-08-13):**
  - Added `permissions: contents: read` to `.github/workflows/ci.yml` and added backend `pytest` suite execution step.