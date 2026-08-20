# Coding Conventions

**Analysis Date:** 2026-08-20

## Language Split

This repo has two distinct codebases with independent conventions:

- **Backend** — Python 3.11+ / FastAPI / async SQLAlchemy in `backend/app/`
- **Frontend** — TypeScript 5.7 / React 19 / Next.js 16 App Router in `frontend/`

Follow the convention set for the codebase you are editing. Do not port patterns across them.

## Backend (Python) Naming Patterns

**Files:**
- `snake_case.py` — e.g. `backend/app/services/calibration.py`, `backend/app/connectors/pubmed.py`

**Functions & methods:**
- `snake_case` — e.g. `submit_feedback()`, `run_profile()`, `_serialize_signal()`
- Private helpers prefixed with single underscore: `_resolve_run_status()`, `_parse_article()`, `_fail()` (`backend/app/connectors/base.py`, `backend/app/connectors/pubmed.py`)
- Async functions use `async def`; everything touching DB/HTTP is async

**Classes:**
- `PascalCase` — `StakeholderCalibrationService`, `PubMedConnector`, `GrokProvider`, `PipelineRunner`

**Variables:**
- `snake_case` — `mock_db`, `sug_congress`, `res_count`

**Module constants:**
- `UPPER_SNAKE_CASE` — `CANONICAL_FUNCTIONS`, `KEYWORDS_MAP` (`backend/app/services/calibration.py`), `XAI_API_URL`, `XAI_MODEL` (`backend/app/providers/grok.py`)
- Config settings are `UPPER_SNAKE_CASE` class attributes in `Settings` (`backend/app/core/config.py`)

**Pydantic schema classes:**
- Schema classes end in `Schema` — `SignalSchema`, `ScoreBreakdownSchema`, `RoleWeightSchema` (`backend/app/schemas/__init__.py`)
- Request/response models use `...Request` / `...Response` — `FeedbackSubmissionRequest`, `RecalibrateResponse`
- This naming distinguishes wire models from domain models

## Frontend (TypeScript) Naming Patterns

**Files:**
- `kebab-case.tsx` / `kebab-case.ts` — `components/metaradar.tsx`, `components/ui/button.tsx`, `lib/mock-data.ts`
- Next.js route files keep framework names: `app/page.tsx`, `app/[section]/page.tsx`

**Components:**
- `PascalCase`, named exports only — `Shell`, `Badge`, `Card`, `SectionTitle`, `DashboardPage` (`frontend/components/metaradar.tsx`)
- Components defined as `function Name(...)` (not arrow consts) and exported at bottom or inline

**Functions & variables:**
- `camelCase` — `getOverview`, `apiFetch`, `mapSignal`, `intervalMs`, `inFlightRef`

**Types & interfaces:**
- `PascalCase` — `DashboardOverview`, `Signal`, `LiveDataState<T>`
- Backend wire types are auto-generated into `frontend/types/api.ts` (header: "DO NOT EDIT DIRECTLY")
- Frontend UI-shape types (e.g. `Signal.severity`, `Signal.detectedAt`) are appended to the generated interfaces — see the "Frontend UI & Dashboard properties" comment block in `frontend/types/api.ts` (lines 62-72)

**Hooks:**
- `use` prefix — `useLiveData<T>` (`frontend/lib/hooks.ts`)

**Constants:**
- `UPPER_SNAKE_CASE` — `API_BASE` (`frontend/lib/api.ts`)

## Code Style

**Backend formatting:**
- 4-space indentation, double-quoted strings by default, ~100-char lines
- Standard library before third-party before app imports, alphabetized within groups:
  ```python
  import hashlib
  import logging
  from datetime import datetime, timezone

  from sqlalchemy import case, func, select

  from app.models import Signal, WatchItem
  from app.schemas import RecalibrateResponse
  ```
- No `black`/`ruff`/`flake8` config file detected; consistency is enforced by review
- Module-level `logger = logging.getLogger(__name__)` in every module that logs (`backend/app/services/calibration.py`, `backend/app/api/v1/endpoints/feedback.py`)

**Frontend formatting:**
- No semicolons, single quotes, trailing commas on multiline structures (prettier-default style, no `.prettierrc` present)
- `'use client'` directive as first line of client components (`frontend/components/metaradar.tsx`, `frontend/lib/hooks.ts`)
- `tsconfig.json` sets `"strict": true`, `target: ES6`, `moduleResolution: bundler`

**Linting (frontend):**
- `frontend/eslint.config.mjs` uses `@next/eslint-plugin-next` recommended + `core-web-vitals` rule sets
- `pnpm lint` runs `eslint .`
- **Note:** the config `ignores` list contains `'src/'` — files under `frontend/src/` (`src/app/sources/page.tsx`, `src/types/api.ts`) are excluded from linting
- No ESLint/ruff config detected for the backend

## Import Organization

**Backend (Python):**
1. Standard library (`os`, `logging`, `datetime`)
2. Third-party (`fastapi`, `sqlalchemy`, `pydantic`)
3. App modules (`from app.connectors.base import ...`, `from app.schemas import ...`)

**Frontend (TypeScript):**
1. React/Next imports
2. Third-party libraries (`framer-motion`, `lucide-react`, `recharts`)
3. `@/` alias imports (project root)
4. Type-only imports last, using `import type { ... }` — see `frontend/components/metaradar.tsx` lines 70-89 and `frontend/lib/api.ts` lines 1-29

**Path Aliases:**
- `@/*` maps to project root (`frontend/tsconfig.json` `paths`) — e.g. `@/lib/api`, `@/types/api`, `@/components/ui/button`
- Backend uses absolute `app.*` imports (no relative imports between modules)

## Error Handling

**Backend — domain exception classes:**
- Custom exceptions per bounded context, defined next to the module that raises them:
  - `GrokUnavailableError` (`backend/app/providers/grok.py`)
  - `OllamaUnavailableError` (`backend/app/providers/gemma.py`)
  - `ConnectorFetchError` (`backend/app/connectors/base.py`)
  - `EmbeddingError` (`backend/app/services/embeddings.py`)
  - `SearchError` (`backend/app/services/vector_query.py`)
- Exceptions carry docstrings explaining who catches them (e.g. `GrokUnavailableError` → `ProviderFactory` falls through to degraded mode)

**Backend — FastAPI endpoints:**
- Thin endpoints wrap service calls in `try/except` and translate to `HTTPException`:
  ```python
  try:
      service = StakeholderCalibrationService(db)
      return await service.submit_feedback(payload)
  except Exception as e:
      logger.error(f"Error submitting feedback: {e}", exc_info=True)
      raise HTTPException(
          status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
          detail="Failed to record stakeholder feedback.",
      )
  ```
  (`backend/app/api/v1/endpoints/feedback.py` lines 36-44)
- Validation/business errors re-raise HTTPException unchanged: `except HTTPException: raise` (`backend/app/api/v1/endpoints/feedback.py` lines 104-105)
- Client-error validation happens inside the endpoint before touching the service: `raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=...)` (`backend/app/api/v1/endpoints/feedback.py` lines 85-98)
- `400` for domain validation, `422` for Pydantic schema validation (automatic), `500` for unexpected failures

**Backend — graceful degradation (honesty telemetry):**
- Providers/connectors return status strings rather than raising: `RunStatus = Literal["SUCCESS", "PARTIAL", "DEGRADED", "FAILED"]` (`backend/app/connectors/base.py` line 49)
- Degraded fallback chain: Local Gemma → Grok → BART degraded factual mode; `mode` field in `model_metadata` reports truthfully (`backend/app/providers/degraded.py`)
- Privacy gate blocks non-PUBLIC/SYNTHETIC payloads from external transmission via `PermissionError` (`backend/app/providers/grok.py` `validate_privacy_gate`)

**Frontend:**
- Central `ApiError` class carrying `status`, `statusText`, `message`, `isRetryable` (`frontend/lib/api.ts` lines 33-43)
- `apiFetch<T>` wrapper normalizes network failures to `ApiError(0, 'NetworkError', ...)` and re-throws; AbortError is propagated untouched (`frontend/lib/api.ts` lines 45-86)
- `useLiveData` hook stores errors in state (`error: Error | null`) and ignores errors from aborted requests (`frontend/lib/hooks.ts` lines 64-67)

## Logging

**Backend framework:** stdlib `logging`, no loguru/structlog.

**Patterns:**
- Module-level `logger = logging.getLogger(__name__)`
- `logger.error(f"...", exc_info=True)` inside endpoint `except` blocks (always include `exc_info=True`)
- `logger.warning` for recoverable conditions (privacy gate blocks, quota exhaustion)
- `%`-style args for parameterized warnings: `logger.warning("Connector %s: failed to load domain config: %s", self.source_id, e)` (`backend/app/connectors/base.py` line 99)

**Frontend:** No logging framework; errors surface via React state and the `ApiError` class. No `console.log` in committed source detected.

## Comments

**Backend:**
- Module docstrings explain purpose and cite decision references: `"""GrokProvider — real xAI Grok API client (D-13, D-14, D-16)."""` (`backend/app/providers/grok.py`)
- Class/function docstrings on non-trivial units; decision IDs (`D-01`, `D-05`, `D-23`) link to the decision log — do not strip them
- Inline comments explain the *why* (e.g. "deterministic suggestion ID", "2.0 clamp")

**Frontend:**
- `/** JSDoc */` block comments on exported functions describing contract and behavior — `frontend/lib/api.ts` has one per fetcher
- Honesty labeling required for mock/fallback data: `frontend/lib/mock-data.ts` and the `mapSignal` docstring ("Does not invent numbers (D-05)")

## Function Design

**Backend:**
- **Endpoints are thin** — parse/validate input, instantiate service with injected session, delegate, translate exceptions (`backend/app/api/v1/endpoints/feedback.py`)
- **Services own business logic** — `StakeholderCalibrationService(db)` with `AsyncSession` constructor injection; pure logic extracted to `@staticmethod` (`HeuristicWatchParser.parse`)
- Type annotations on every function signature and return type — e.g. `def utc_now() -> datetime:`
- `Optional[UUID] = None` for optional params; keyword-only style for long signatures
- Module-level constants instead of magic values (`CANONICAL_FUNCTIONS`, `KEYWORDS_MAP`)

**Frontend:**
- **Pure mapper functions** convert backend shapes to UI shapes: `mapSignal`, `mapSearchResult` (`frontend/lib/api.ts`) — keep them pure and deterministic
- **Fetchers** are thin typed wrappers over `apiFetch<T>`, each taking optional `signal?: AbortSignal` for cancellation
- **Hooks** encapsulate side-effect complexity; `useLiveData` is the single polling pattern (don't write ad-hoc `setInterval` in pages)
- Small UI primitives (`Badge`, `Card`, `SectionTitle`) exported from `components/metaradar.tsx`; shadcn-style primitives with `cva` variants in `components/ui/`

## Module Design

**Backend:**
- One responsibility per module under `backend/app/`: `api/v1/endpoints/`, `services/`, `connectors/`, `providers/`, `schemas/`, `models/`, `workflows/nodes/`
- `backend/app/models/__init__.py` is the single barrel for all SQLAlchemy models (no split model files)
- `backend/app/schemas/__init__.py` re-exports from `schemas/intelligence.py` and `schemas/registry.py`
- Services never import endpoints; endpoints import services; both import schemas/models

**Frontend:**
- `lib/` = non-component logic (`api.ts`, `hooks.ts`, `utils.ts`, `mock-data.ts`)
- `components/` = UI; `components/ui/` = shadcn primitives
- `types/api.ts` = auto-generated wire types (regenerate with `python scripts/export_openapi.py`, never hand-edit)
- `app/` = Next.js routes; `app/[section]/page.tsx` is the single dynamic route dispatching to page components in `components/metaradar.tsx`
- Barrel re-exports at file bottom: `export { Button, buttonVariants }` (`frontend/components/ui/button.tsx`)

## Constraints

- **No fabricated telemetry**: mock data, fallbacks, and synthetic data must be explicitly labeled (AGENTS.md, `docs/rules/ENGINEERING_STANDARDS.md`)
- **No `@ts-ignore`, no `ignoreBuildErrors`, no silent exception swallowing** (AGENTS.md core rules)
- **Frontend `types/api.ts` is generated** — edit `scripts/export_openapi.py` or backend schemas, then regenerate; CI fails on drift (`.github/workflows/ci.yml` line 40)
- **All DB work is async** — never use sync SQLAlchemy sessions in `backend/app/`

---

*Convention analysis: 2026-08-20*
