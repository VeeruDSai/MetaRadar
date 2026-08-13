# Concerns
> Property of the developer to fix. Append-only.

## Active Concerns (grouped by severity, each with: description, evidence - file:line or path, impact, recommended action)

### High

**H7. Frontend mock-driven seam — API fallback ready for full connection.**
- Description: `frontend/lib/api.ts` currently provides synthetic mock fixtures while `NEXT_PUBLIC_API_BASE_URL` is set to `http://localhost:8000/api/v1`. The mock banner discloses synthetic data in demo mode.
- Evidence: `frontend/lib/api.ts`, `frontend/components/metaradar.tsx`
- Impact: The demo UI uses mock fixtures when offline or during initial frontend preview.
- Recommended action: Progressively replace mock fallback with live API calls as backend connector features expand.

### Medium

**M1. Scheduler & Async background pipeline.**
- Description: APScheduler job runner and background fetching pipeline scheduled execution.
- Recommended action: Connect background scheduler for 2-hour syndication polling when live connectors ship.

---

## Resolved Concerns (note what was fixed, when)

- **Frontend package reconciliation, linting, build quality & CI (resolved 2026-08-13):**
  - Reconciled `frontend/package.json` with name `metaradar-frontend`, version `5.1.0`, Next 16.3 + React 19 + Tailwind 4 stack, Node 20 engines, and `pnpm@11.21.0`.
  - Added native ESLint 10 flat config in `frontend/eslint.config.mjs`.
  - Removed `typescript.ignoreBuildErrors: true` from `frontend/next.config.mjs`.
  - Added `.nvmrc` with Node 20 runtime pinning.
  - Verified `pnpm exec tsc --noEmit` passes with 0 errors.
  - Verified `pnpm lint` (`eslint .`) passes with 0 errors.
  - Verified `pnpm build` (`next build`) passes with 0 build errors.
  - Added frontend typecheck, lint, and build job to `.github/workflows/ci.yml`.

- **Missing Dockerfiles & Docker Compose readiness (C3 & M11, resolved 2026-08-13):**
  - Created `backend/Dockerfile` (Python 3.11-slim, uvicorn, non-root user, curl healthcheck).
  - Created `frontend/Dockerfile` (Node 20-alpine multi-stage build).
  - Updated `docker-compose.yml` service dependencies and healthchecks.

- **Alembic Database Migration Scaffolding (C4, resolved 2026-08-13):**
  - Created `backend/alembic.ini`, `backend/alembic/env.py` (async engine support), and `backend/alembic/script.py.mako`.

- **Health Endpoint Honesty & Real Diagnostics (C5 & M7, resolved 2026-08-13):**
  - Updated `backend/app/api/v1/endpoints/health.py` to report real database & redis readiness, runtime provider status, and correct freshness classes (PubMed batch/delayed, ClinicalTrials.gov batch/delayed).

- **PII/PHI Detection, Redaction & Explicit Classification (H1, resolved 2026-08-13):**
  - Created `backend/app/services/pii.py` (`PIIPHIScrubber` for email, phone, SSN, MRN, DOB regex redaction and explicit classification).

- **Fallback Chain Unit Testing & Degraded Mode (H2, resolved 2026-08-13):**
  - Verified Degraded BART fallback execution and added test cases in `tests/test_foundation.py`.

- **Red-Team Contradiction Service & Rule Registry (H3, resolved 2026-08-13):**
  - Enhanced `backend/app/services/redteam.py` with `REDTEAM_RULES` registry covering 19 rules (Rules A–S) and contradiction evaluation.

- **Database Models & Schema Synchronization (H4 & M3, resolved 2026-08-13):**
  - Added `model_metadata` column to `Signal` ORM model.
  - Added `Contradiction`, `CalibrationHistory`, and `ScoringWeights` ORM models to `backend/app/models/__init__.py`.
  - Fixed naive datetimes by converting all defaults to timezone-aware `datetime.now(timezone.utc)`.

- **FastAPI Business API Surface Expansion (H5, resolved 2026-08-13):**
  - Created `backend/app/api/v1/endpoints/signals.py` for `/signals`, `/overview`, and `/athena` endpoints and registered router in `backend/app/main.py`.

- **OpenAPI Contract Generation & CI Synchronization (H9, resolved 2026-08-13):**
  - Updated `scripts/export_openapi.py` and exported `contracts/openapi.json` and `frontend/src/types/api.ts`.
  - Verified CI contract check step passes cleanly.

- **Frontend Tree Consolidation & Asset Cleanup (H-FE1, L-FE6, M-FE5, resolved 2026-08-13):**
  - Consolidated active frontend tree under `frontend/app/`, `frontend/components/`, `frontend/lib/`, `frontend/types/`.
  - Preserved `frontend/src/types/api.ts` for CI contract verification.
  - Removed v0 generator tags and `@vercel/analytics` from `app/layout.tsx`.
  - Removed unused public placeholder assets from `frontend/public/`.
  - Cleaned v0 sandbox entries from `frontend/.gitignore`.

- **All implementation code committed (C6 / H-FE3, resolved 2026-08-13):**
  - Backend foundation committed in `ddf4f97`; frontend reconciliation and codebase concerns committed in follow-up.