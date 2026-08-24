# Coding Conventions

**Analysis Date:** 2026-08-24

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` matching the primary symbol (`backend/app/services/scoring.py` -> `PriorityScoringService`)
- Frontend components: `PascalCase.tsx` named after the exported component (`frontend/components/common/ErrorState.tsx` -> `ErrorState`)
- Frontend lib/helpers: `camelCase.ts` (`frontend/lib/api.ts`, `frontend/lib/hooks.ts`, `frontend/lib/mappers.ts`)
- Frontend CSS assets: `kebab-case.css` (`frontend/components/effects/star-portal/styles.css`) or `PascalCase.css` for component-scoped styles (`frontend/components/ui/Counter.css`)
- Tests: `test_<area>.py` in central `tests/` directory (see TESTING.md)

**Functions:**
- Python: `snake_case`; async functions also `snake_case` (`node_ingest()` in `backend/app/workflows/nodes/ingest.py:39`, `resolve_signal_routing()` in `backend/app/services/routing.py`)
- Private/internal helpers prefixed with `_` (`_serialize_signal()` at `backend/app/api/v1/endpoints/signals.py:54`, `_load_synthetic_fallback()` at `backend/app/workflows/nodes/ingest.py:15`)
- TypeScript: `camelCase`; `fetch*` prefix for raw API calls, `get*` for compatibility wrappers (`fetchOverview` / `getOverview` in `frontend/lib/api.ts:208` and `:39`)
- React hooks: `useXxx` (`useLiveData` in `frontend/lib/hooks.ts:21`)

**Variables:**
- Python module-level constants: `UPPER_SNAKE_CASE` (`SCORING_VERSION`, `CLINICAL_KEYWORDS` at `backend/app/services/scoring.py:7-9`; `MAX_EVIDENCE_DISTANCE` at `backend/app/api/v1/endpoints/signals.py:51`)
- Settings fields: `UPPER_SNAKE_CASE` env-var names on the pydantic-settings class (`backend/app/core/config.py:16-104`)
- TypeScript: `camelCase` locals; `UPPER_SNAKE_CASE` constants (`API_BASE` at `frontend/lib/api.ts:149`)

**Types/Classes:**
- Python classes `PascalCase`; enums use `class X(str, Enum)` with UPPERCASE members (`DataMode.LIVE` at `backend/app/schemas/intelligence.py:8-12`)
- Pure value objects as dataclasses: `ScoreInput`, `ScoreBreakdown` (`backend/app/services/scoring.py:37-46`)
- Pydantic response schemas end in `Schema` or describe payload (`SignalSchema`, `OverviewResponse` in `backend/app/schemas/intelligence.py`)
- TypeScript interfaces `PascalCase`; props interfaces are `<Component>Props` (`ErrorStateProps` at `frontend/components/common/ErrorState.tsx:7`)

## Code Style

**Backend (Python):**
- No enforced formatter/linter config (no ruff/black/flake8 config present). Match surrounding style: 4-space indent, double-quoted strings, trailing commas in multiline literals.
- Full type hints on signatures using `typing` generics (`Optional[...]`, `List[...]`, `Dict[str, Any]`) - see `backend/app/services/scoring.py:81-101`
- Docstrings on every public class and method, including business rationale ("Returns None if any mandatory input is missing (allows honest 'not_computed' display)" - `backend/app/services/scoring.py:68-75`)
- Stateless domain services exposed as module-level singletons imported by endpoints: `priority_scorer`, `confluence_engine`, `embedding_service` (imported at `backend/app/api/v1/endpoints/signals.py:40-42`). Use this pattern for new services.
- Classmethod-based utility methods when no instance state is needed (`PriorityScoringService.extract_keywords_count` - `backend/app/services/scoring.py:80-89`)
- Workflow pipeline steps are pure-ish node functions taking typed state: `async def node_ingest(state: MetaRadarState, session) -> Dict[str, Any]` (`backend/app/workflows/nodes/ingest.py:39`); each returns a partial-state dict including `node_statuses`

**Frontend (TypeScript):**
- `strict: true` (`frontend/tsconfig.json:7`); never disable with `@ts-ignore` or `ignoreBuildErrors` (explicitly forbidden by root `AGENTS.md` rule 5)
- Single quotes, no semicolons, 2-space indent (no Prettier/Biome config exists - match existing files)
- `'use client'` directive as first line of every client component/hook (`frontend/components/common/ErrorState.tsx:1`, `frontend/lib/hooks.ts:1`)
- Named function declarations plus explicit Props interface per component (`export function ErrorState({...}: ErrorStateProps)`)
- Inline JSDoc blocks above non-obvious helpers (`/** Helper to categorize source authority tier */` - `frontend/components/signals/SignalCard.tsx:33`)

**Linting:**
- ESLint flat config `frontend/eslint.config.mjs`: `@next/eslint-plugin-next` recommended + core-web-vitals rules only
- Custom gate `scripts/check-banned-classes.mjs`: forbids Tailwind `slate-*` utilities and arbitrary hex classes (`bg-[#...]`) in `frontend/components/**/*.tsx`; run via `pnpm run check:banned-classes`. Use CSS variables (`var(--danger)`, `var(--surface)`) with `color-mix()` instead (example: `frontend/components/common/ErrorState.tsx:44-47`)
- CI runs `pnpm exec tsc --noEmit`, `pnpm run check:banned-classes`, `pnpm lint`, `pnpm build` (`.github/workflows/ci.yml:52-59`)

## Import Organization

**Backend order (observed consistently):**
1. Python stdlib (`import os`, `from datetime import datetime, timezone`)
2. Third-party (`fastapi`, `sqlalchemy`, `structlog`, `pydantic`)
3. App imports absolute from `app.` package root (`from app.services.scoring import priority_scorer`)
- Reference example: `backend/app/api/v1/endpoints/signals.py:1-44`

**Frontend order:**
1. `'use client'` directive
2. React / Next.js imports
3. Type-only imports from `@/types/api`
4. Internal components via `@/components/...` alias
5. Relative sibling imports (`../common/DataModeBadge`)
6. Icon library (`lucide-react`) last
- Reference example: `frontend/components/signals/SignalCard.tsx:1-24`

**Path Aliases:**
- `@/*` maps to the frontend root (`frontend/tsconfig.json:21-23`); shadcn aliases configured in `frontend/components.json`

## Error Handling

**Honest telemetry is the governing rule** (`docs/rules/ENGINEERING_STANDARDS.md` section 1.2): never fabricate values; degrade visibly and label synthetic/mock data.

**Backend patterns (use these):**
- Return `None` plus a status string when inputs are missing instead of inventing defaults: scoring returns `None`, endpoint sets `scoring_status = "not_computed"` (`backend/app/services/scoring.py:102-107`, `backend/app/api/v1/endpoints/signals.py:56-66`)
- Defensive dict-to-schema parsing in `try/except Exception` that downgrades to `None` + status flag rather than crashing (`_serialize_signal` at `backend/app/api/v1/endpoints/signals.py:59-73`)
- Graceful provider degradation chain: local Gemma -> Grok fallback -> `DegradedProvider` "degraded_factual" mode; every response carries a `model_metadata` block exposing `mode`, `fallback_used`, `reasoning_available` (`backend/app/providers/degraded.py`, consumed in `tests/test_foundation.py:93-101`)
- Synthetic data must be tagged at ingestion: `is_synthetic=True`, `data_mode="test_fixture"`, `provenance_status="fixture"` (`backend/app/workflows/nodes/ingest.py:27-32`)
- Configuration problems are reported as human-readable `CONFIGURATION_ERROR:` strings via the pure evaluator `configuration_error_for()` (`backend/app/core/config.py:109-120`) - do not raise on missing optional keys
- Endpoint-level failures raise FastAPI `HTTPException`; validation errors return 422 with correlation headers intact (asserted in `tests/test_failure_injection.py:45-58`)
- Log-and-continue for non-fatal fallbacks with `logger.warning(...)` including context (`backend/app/workflows/nodes/ingest.py:35`)
- Never swallow errors silently: root `AGENTS.md` rule 5 forbids silent `try...except` used to hide failures

**Frontend patterns (use these):**
- All API calls funnel through `apiFetch<T>()` which throws typed `ApiError` carrying `status`, `statusText`, `isRetryable`, `requestId`, `endpoint` (`frontend/lib/api.ts:151-202`)
- `ApiError` class defined in `frontend/lib/errors.ts:1-13`; map any thrown value to display form with `formatError()` (`frontend/lib/errors.ts:24-56`)
- Network/abort errors are re-thrown, not swallowed; AbortError propagates (`frontend/lib/api.ts:186-201`)
- Components render dedicated state components on failure: `ErrorState` (`frontend/components/common/ErrorState.tsx`) and `EmptyState` (`frontend/components/common/EmptyState.tsx`) - never render fabricated data
- Data fetching uses `useLiveData<T>` hook with AbortController + visibility-aware polling; error surfaced as `error: Error | null` in state (`frontend/lib/hooks.ts:21-77`)

## Logging

**Framework:** structlog with JSON renderer, configured once in `backend/app/core/logging.py:22-46`

**Patterns:**
- One logger per module: `logger = structlog.get_logger("metaradar.<module>")` (`backend/app/main.py:26`, `backend/app/core/middleware.py:6`)
- Event-name-first structured calls: `logger.info("http_request_completed", status_code=..., duration_ms=...)` - keyword context, not f-strings (`backend/app/core/middleware.py:60-64`)
- Correlation IDs: `CorrelationIdMiddleware` reads/generates `X-Request-ID` / `X-Correlation-ID`, binds them to structlog contextvars, echoes them on responses; tests assert their presence (`backend/app/core/middleware.py:19-54`, asserted in `tests/test_failure_injection.py:57-58`)
- Secret/PII scrubbing happens inside logging processors `_scrub_secrets` + `SecretScrubFilter` (`backend/app/core/logging.py:10-19`, filters added at `:44-46`); redaction primitives live in `backend/app/core/redact.py`
- Some workflow nodes still use stdlib `logging.getLogger(__name__)` (`backend/app/workflows/nodes/ingest.py:12`) - prefer structlog for new code

## Comments

**When to Comment:**
- Explain WHY and guard against regressions: single-source-of-trust warnings ("Single source of truth - the query filter and the docstring contract must never drift apart again." - `backend/app/api/v1/endpoints/signals.py:48-51`)
- Contract-sync instructions belong in the generated file header (`frontend/types/api.ts:1-5`)

**JSDoc/TSDoc:**
- Python: triple-quoted docstrings on classes/methods; module docstrings for multi-concept modules (`backend/app/services/authority.py:1-8`)
- TypeScript: `/** */` blocks above exported helpers/hooks; inline `//` for clarifying non-obvious behavior (`frontend/lib/api.ts:165`, `frontend/lib/hooks.ts:14-20`)

## Function Design

**Size:** No hard rule; endpoints may be long but delegate to service-layer helpers. Follow the endpoint -> service split seen in `backend/app/api/v1/endpoints/signals.py` + `backend/app/services/*`

**Parameters:**
- Prefer typed input dataclasses over long positional lists (`ScoreInput` fed to `PriorityScoringService.score()` - `backend/app/services/scoring.py:102`)
- Optional params default to `None` and are checked explicitly
- Frontend hooks take a fetcher callback + interval + deps (`useLiveData(fetcher, intervalMs, deps)` - `frontend/lib/hooks.ts:21-25`); fetchers accept an optional `AbortSignal`

**Return Values:**
- Services return typed objects/dataclasses or `Optional[...]` when computation is impossible
- Workflow nodes return partial-state dicts merged by the runner (`backend/app/workflows/runner.py`)
- Async functions return `Promise<T>` with explicit generic on fetch helpers (`apiFetch<T>` - `frontend/lib/api.ts:151`)

## Module Design

**Exports:**
- Backend: one primary class/function per module plus module singleton; routers expose `router = APIRouter()` registered in `backend/app/main.py:76-85`
- Frontend: named exports only for functions/components; one class per lib file where applicable (`ApiError` in `frontend/lib/errors.ts`)

**Barrel Files:**
- Backend models/schemas use `__init__.py` re-export barrels (`backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`); workflow nodes likewise (`backend/app/workflows/nodes/__init__.py`)
- Frontend has no barrel files except shared UI kit `frontend/components/metaradar.tsx` (Card/Badge etc. imported from it - see `frontend/components/common/ErrorState.tsx:4`)

## Contract Synchronization (cross-cutting rule)

The frontend type contract is hand-maintained but CI-enforced:
1. Canonical template lives inside `scripts/export_openapi.py`
2. Running it regenerates `frontend/types/api.ts` verbatim and dumps `contracts/openapi.json`
3. `tests/test_contract_drift.py` asserts required paths/interfaces exist; CI runs the script then `git diff --exit-code frontend/types/api.ts` (`.github/workflows/ci.yml:35-40`)
- To change the API contract: edit the template in `scripts/export_openapi.py`, run it, commit both outputs together. Never edit `frontend/types/api.ts` directly.

---

*Convention analysis: 2026-08-24*
