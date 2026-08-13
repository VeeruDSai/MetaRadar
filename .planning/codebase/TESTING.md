# Testing & Verification Strategy

**Analysis Date:** 2026-08-13 (Refreshed Post-Stabilization Baseline)

> **Current state:** Backend quality is enforced by an 18-point `pytest` test suite (`tests/`) covering configuration, FastAPI endpoints, provider matrix fallback (Cases A–F), PII scrubbing, privacy gate bypass prevention, Red-Team priority gating, candidate capping, caching, and OpenAPI contract drift. Frontend quality is enforced by `npx tsc --noEmit` (`typescript: { ignoreBuildErrors: false }`), ESLint 10 native flat config (`frontend/eslint.config.mjs`), and `npx next build`. All gates are automated in `.github/workflows/ci.yml`.

## Automated Quality Gates Summary

| Verification Layer | Executable Command | Executed Status | Verification Scope |
|---|---|---|---|
| **Backend Pytest Suite** | `pytest -v` | **`PASS`** (18/18 passed) | Domain config, FastAPI routes (`/health`, `/signals`, `/overview`, `/athena`), Cases A–F provider matrix, PII regex scrubbing & Grok gate bypass prevention, Red-Team 19-rule gating & caching, contract drift. |
| **Frontend Typecheck** | `pnpm exec tsc --noEmit` | **`PASS`** (0 errors) | Strict TypeScript compiler validation across `frontend/app/` and components. |
| **Frontend Linting** | `pnpm lint` (`eslint .`) | **`PASS`** (0 errors) | ESLint 10 flat config (`eslint.config.mjs`) checking code syntax & Next.js conventions. |
| **Frontend Production Build**| `pnpm build` (`next build`) | **`BUILD VERIFIED`** (0 errors) | Turbopack compilation & static route generation for `/dashboard`, `/signals`, `/intelligence`, etc. |
| **Contract Sync Drift** | `python scripts/export_openapi.py` | **`PASS`** (0 diff) | Zero-diff verification of generated canonical TypeScript contract at `frontend/types/api.ts`. |
| **Database Migration** | `alembic upgrade head` | **`BLOCKED`** | Async Alembic engine scaffolded; migration execution pending local PostgreSQL daemon on port 5432. |
| **Docker Stack Runtime** | `docker compose up -d` | **`NOT EXECUTED`** | `docker compose config` zero warnings; container runtime execution pending local Docker Desktop daemon. |

## Pytest Test Suite Structure

```
tests/
├── pytest.ini              # Pytest discovery & asyncio configuration
├── test_config.py          # Domain config & settings validation
├── test_api_endpoints.py   # FastAPI endpoints verification (/health/*, /signals, /overview, /athena)
├── test_provider_matrix.py # Cases A–F provider matrix fallback & capability tests
├── test_privacy_boundary.py# PIIPHIScrubber regex patterns & Grok privacy gate bypass prevention
├── test_redteam_behavior.py# RedTeamNLIService priority gating, candidate capping, & caching
└── test_contract_drift.py  # FastAPI OpenAPI to TypeScript contract drift validation
```

## Continuous Integration Workflow

Workflow File: `.github/workflows/ci.yml`

- **Least-Privilege Security**: Configured with `permissions: contents: read`.
- **Python Step**: Sets up Python 3.11, installs `backend/requirements.txt` (including `pytest`, `pytest-asyncio`, `pytest-cov`), and executes `pytest -v`.
- **Contract Drift Step**: Runs `python scripts/export_openapi.py` and checks `git diff --exit-code frontend/types/api.ts`.
- **Frontend Step**: Sets up Node 20 + pnpm 11, installs dependencies, and runs `pnpm exec tsc --noEmit`, `pnpm lint`, and `pnpm build`.
