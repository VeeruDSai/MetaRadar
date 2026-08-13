# Development Conventions & Standards

**Analysis Date:** 2026-08-13 (Refreshed Post-Stabilization Baseline)

> **Current state:** Frontend architecture reconciled with Next.js 16 + React 19 + Tailwind 4 + Base UI/shadcn, strict TypeScript checking (`typescript: { ignoreBuildErrors: false }`), ESLint 10 native flat config (`frontend/eslint.config.mjs`), and unified canonical contract at `frontend/types/api.ts`. Backend standardized with FastAPI 0.115, Pydantic v2, async SQLAlchemy 2.0, timezone-aware UTC datetimes, PII/PHI scrubber (`PIIPHIScrubber`), Red-Team 19-rule registry (`RedTeamNLIService`), and an 18-point `pytest` test suite (`tests/`). Infrastructure container images authored (`backend/Dockerfile`, `frontend/Dockerfile`) and CI workflows configured with least-privilege token access (`permissions: contents: read`).

## Language & Framework Standards

- **Backend**: Python 3.11+ (CI target Python 3.11). Framework: **FastAPI `>=0.110.0`** with **Pydantic v2 `>=2.6.0`**.
- **Persistence**: SQLAlchemy 2.0 async (`sqlalchemy.ext.asyncio`), asyncpg driver, pgvector for 384-dim embeddings (`backend/app/db/session.py`).
- **Frontend**: **Next.js `16.3.0` + React 19 + TypeScript 5.7.3**, package manager **pnpm 11** (`frontend/pnpm-lock.yaml`). TailwindCSS **4.3.3** CSS-first styling pipeline (`@tailwindcss/postcss` in `frontend/postcss.config.mjs`).
- **Component System**: Base UI (`@base-ui/react`) + shadcn/ui "base-nova" style (`frontend/components.json`), `class-variance-authority` for variants, `clsx` + `tailwind-merge` for utility merging.
- **Migration Engine**: Async Alembic engine (`backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`).
- **Test Infrastructure**: 18-point `pytest` backend suite under `tests/` (`test_config.py`, `test_api_endpoints.py`, `test_provider_matrix.py`, `test_privacy_boundary.py`, `test_redteam_behavior.py`, `test_contract_drift.py`).

## Naming Conventions

**Python:**
- Modules/files: `snake_case.py` (e.g. `deduplication.py`, `domain_config.py`, `pii.py`, `redteam.py`).
- Functions/methods: `snake_case` (e.g. `generate_fingerprint`, `chunk_text_for_embedding`, `upsert_signal`).
- Classes: `CamelCase` (e.g. `Settings`, `ProviderFactory`, `GemmaProvider`, `PIIPHIScrubber`, `RedTeamNLIService`).
- Pydantic schemas: Suffix `Schema` or explicit Response model (e.g. `SignalSchema`, `HealthReadyResponse`).
- Datetimes: Timezone-aware UTC datetimes using `datetime.now(timezone.utc)` or `utc_now()` helper.
- Enums: `CamelCase` members with lowercase/uppercase `str` values (e.g. `ProviderCapability.REASON`, `DataClassification.PUBLIC`).

**Frontend:**
- Files: App Router conventions (`page.tsx`, `layout.tsx`), `components/metaradar.tsx` for client workspace, `types/api.ts` for canonical contract.
- Components: `PascalCase` exported functions (`Shell`, `DashboardPage`, `SignalsPage`, `IntelligencePage`, `GenericPage`).
- TS Interfaces: `PascalCase` (e.g. `Signal`, `Development`, `ModelMetadata`, `HealthResponse`).
- Types: Generated contract interfaces in snake_case matching FastAPI OpenAPI schema.

## Error Handling & Reliability

- **Provider Fallback Chain**: Local Gemma -> Grok fallback (if `ENABLE_GROK_FALLBACK` enabled, `XAI_API_KEY` present, and `validate_privacy_gate` passes) -> Degraded BART mode (factual summary only, `reasoning_available = False`).
- **Privacy Boundary**: `PIIPHIScrubber` redacts raw & nested PII (email, phone, SSN, MRN, patient DOB) before external transmission. Grok external calls are strictly gated against `CONFIDENTIAL`, `PATIENT_IDENTIFIABLE`, or `UNKNOWN` payloads.
- **Red-Team Contradiction Evaluator**: `RedTeamNLIService` evaluates pairwise contradictions across 19 rules (Rules A–S) with priority gating (`HIGH`/`CRITICAL` only), candidate capping (max 3 claims), and in-memory caching.
- **Fail-Degrade Endpoint Design**: Readiness endpoint `/api/v1/health/ready` returns `"ready"` when DB and Redis are healthy, or `"degraded"` if auxiliary services fail.

## Contract Synchronization & Code Quality

- **Canonical Source of Truth**: FastAPI OpenAPI schema exported to `contracts/openapi.json` and generated directly into `frontend/types/api.ts` by `scripts/export_openapi.py`.
- **Legacy Re-export Pointer**: `frontend/src/types/api.ts` re-exports from `../../../types/api` to maintain reference compatibility without maintaining duplicate contract files.
- **Build Quality Gates**:
  - `npx tsc --noEmit` -> 0 errors (`typescript: { ignoreBuildErrors: false }`).
  - `npx eslint .` -> 0 errors (`frontend/eslint.config.mjs` flat config).
  - `npx next build` -> 0 build errors.
  - `pytest -v` -> 18/18 tests passed cleanly.
