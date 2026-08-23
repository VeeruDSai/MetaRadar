# Coding Conventions

**Analysis Date:** 2026-08-23

## Naming Patterns

**Files:**
- Backend Python: `snake_case.py` matching domain concept - e.g. `backend/app/services/source_independence.py`, `backend/app/connectors/clinical_trials.py`
- Backend API endpoints: one file per domain under `backend/app/api/v1/endpoints/` - `feedback.py`, `signals.py`, `health.py`, etc.
- Frontend components: `PascalCase.tsx` - e.g. `frontend/components/signals/SignalCard.tsx`; workspace screens use `<Domain>Workspace.tsx` suffix (`AthenaWorkspace.tsx`, `ConfluenceWorkspace.tsx`)
- Frontend lib helpers: lowercase names - `frontend/lib/api.ts`, `frontend/lib/errors.ts`, `frontend/lib/mappers.ts`
- Tests: `test_<domain>.py` at repo-root `tests/` directory (never co-located)

**Functions:**
- Python: `snake_case` verbs - `submit_feedback()`, `detect_confluence_in_signals()`, `generate_fingerprint()`; async functions are plain `async def`
- FastAPI endpoint handlers: `snake_case` verb_noun - see `backend/app/api/v1/endpoints/feedback.py` (`submit_feedback`, `get_feedback_summary`, `trigger_recalibration`)
- TypeScript: `camelCase` for functions; hooks prefixed `useXxx` (`frontend/lib/hooks.ts` -> `useLiveData`)
- Test functions: `test_<behavior>` describing the scenario - `test_calibration_service_weight_clamping_and_empty_feedback`

**Variables:**
- Python: `snake_case`; module-level constants `UPPER_SNAKE_CASE` - e.g. `CONFLUENCE_VERSION`, `SIGNAL_TYPE_WEIGHTS` in `backend/app/services/confluence.py`
- TypeScript: `camelCase`; UPPER_SNAKE acceptable for script gates

**Types:**
- Pydantic schemas: `PascalCase` classes suffixed by role - `FeedbackSubmissionRequest`, `FeedbackSubmissionResponse`, `CalibrationWeightsResponse` (`backend/app/schemas/intelligence.py`)
- Enums: `PascalCase` class + `UPPER_SNAKE` members - `DataMode.LIVE = "live"` (`backend/app/schemas/intelligence.py`)
- SQLAlchemy models: `PascalCase` class with snake_case plural `__tablename__` - `PipelineRun` -> `"pipeline_runs"` (`backend/app/models/__init__.py`)
- TS interfaces: `PascalCase`; props interface always exported as `<Component>Props` - `SignalCardProps` in `frontend/components/signals/SignalCard.tsx`
- Connector class attributes act as constants: `source_id`, `source_type`, `freshness_class`, `BATCH_SIZE` (`backend/app/connectors/pubmed.py`)

## Code Style

**Formatting:**
- No automated formatter config committed (no Black/Prettier/Biome configs). Match surrounding style manually.
- Python: 4-space indent, double quotes
- TypeScript/TSX: 2-space indent, **single quotes, no semicolons** (consistent across `frontend/lib/*.ts` and components)
- Trailing commas in multi-line TS structures

**Linting:**
- Frontend: ESLint flat config `frontend/eslint.config.mjs` using `@next/eslint-plugin-next` recommended + core-web-vitals rules. Ignores `.next/`, `node_modules/`, `out/`, `build/`, `src/`. Run via `pnpm lint`.
- Type safety gate: `pnpm exec tsc --noEmit` with `"strict": true` in `frontend/tsconfig.json`. NEVER bypass with `@ts-ignore` or `ignoreBuildErrors` (mandated by `AGENTS.md` and `docs/rules/ENGINEERING_STANDARDS.md`).
- Custom Tailwind gate: `scripts/check-banned-classes.mjs` (run via `pnpm run check:banned-classes`) fails if any component uses banned utility classes:
  - `bg-slate-*`, `text-slate-*`, `border-slate-*` plus dark: variants
  - Arbitrary hex colors `bg-[#...]`, `text-[#...]`, `border-[#...]` plus dark: variants
  - Use CSS variables instead: `text-[var(--muted-foreground)]`, `border-[var(--border)]`, `style={{ color: 'var(--success)' }}` (see `frontend/components/signals/SignalCard.tsx`)
  - Exception: `metaradar.tsx` design-system file is exempt from the scan
- Backend: no ruff/flake8/mypy/black config committed. Correctness enforced via pytest suite and CI contract-sync check. Keep imports clean anyway; test files use `# noqa: E402` where the sys.path bootstrap forces late imports (`tests/test_ingestion.py`).

**Type Hints:**
- All public Python functions carry full type hints using `typing` names (`Optional`, `List`, `Dict`, `Any`) - e.g. `detect_confluence_in_signals(self, signals: List[Dict[str, Any]], ...) -> Optional[ConfluenceResult]`
- Pydantic v2 idioms throughout: `model_config = SettingsConfigDict(...)`, `Field(default_factory=dict)`, `(str, Enum)` base for string enums
- Return-type annotations on FastAPI handlers are mandatory in practice (`-> FeedbackSubmissionResponse`)

## Import Organization

**Order (Python):**
1. stdlib (`import logging`, `from datetime import datetime, timezone`)
2. third-party (`from pydantic import BaseModel`, `from fastapi import APIRouter, Depends`)
3. local app imports (`from app.core.config import settings`, `from app.services.calibration import ...`)

**Order (TypeScript):**
1. `'use client'` directive on first line (interactive components only)
2. React / framework imports
3. type-only imports (`import type { Signal } from '@/types/api'`)
4. local lib/component imports
5. icon/utility packages (`lucide-react`)

**Path Aliases:**
- Frontend: `@/*` maps to frontend root (`@/types/api`, `@/components/metaradar`) per `frontend/tsconfig.json`
- Relative imports within sibling component folders (`../common/DataModeBadge`)
- Every test file bootstraps `sys.path.insert(0, str(base_dir / "backend"))` at top; pytest also sets `pythonpath = backend .` via `pytest.ini`

## Error Handling

**Patterns:**
- FastAPI endpoints wrap service calls in `try/except Exception`, log with `logger.error(f"...: {e}", exc_info=True)`, then raise `HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="<user-safe message>")`. Internal error strings never leak to clients - see `backend/app/api/v1/endpoints/feedback.py`
- Re-raise known HTTP exceptions first: `except HTTPException: raise` before the broad catch
- Validation errors return explicit `HTTP_400_BAD_REQUEST` with an enumerated allowed-values message (same file, `trigger_recalibration`)
- Pure configuration validation: `configuration_error_for(source_id)` in `backend/app/core/config.py` returns a human-readable `CONFIGURATION_ERROR: ...` string or `None`; side-effect-free so trivially unit-testable. Follow this pattern for new config checks
- Graceful degradation over crashes: provider chain Local Gemma -> Grok fallback -> `DegradedProvider` ("degraded_factual" mode) in `backend/app/providers/degraded.py`; connectors raise typed `ConnectorFetchError` from `backend/app/connectors/base.py`, translated into run-status records rather than unhandled crashes
- Connectors use `_fetch_with_retry` (base class) with backoff instead of ad-hoc retry loops
- Honest telemetry rule: synthetic/degraded/mock data MUST be labeled (`is_synthetic`, `data_mode`, `mode: "degraded_factual"`) - never silently substituted (`docs/rules/ENGINEERING_STANDARDS.md`)
- Frontend: typed `ApiError extends Error` carrying `status`, `isRetryable`, `requestId`, `endpoint` (`frontend/lib/errors.ts`); normalize anything throwable through `formatError(error)` before display; abort-aware fetches skip state updates when `controller.signal.aborted` (`frontend/lib/hooks.ts`)

## Logging

**Framework:** stdlib `logging` with `logger = logging.getLogger(__name__)` at module top is the dominant pattern in services/connectors/endpoints. Structured JSON logging is centralized in `backend/app/core/logging.py` (structlog + secret scrubbing via `SENSITIVE_KEYS` mapping to `[REDACTED_SECRET]` / `[REDACTED_PII]`), configured on import.

**Patterns:**
- Log errors with context and `exc_info=True`; include entity IDs (profile_id, source_id) in messages
- Never log raw secrets or PII - the structlog processor is a backstop, not permission
- Frontend has no logger; errors surface through state (`error: Error | null` in `LiveDataState`) rendered by `ErrorState` components

## Comments

**When to Comment:**
- Explain *why* behind non-obvious logic - e.g. the note in `backend/app/services/confluence.py` explaining the `or` chain prevents explicit None values becoming phantom sources
- Requirement/decision traceability IDs in docstrings: `REQ-P1-x` phase requirements (`backend/app/connectors/pubmed.py`), `D-01..D-08` decision references (`backend/app/api/v1/endpoints/feedback.py`)
- Section banner comments segment large files (see `tests/test_ingestion.py`):
```python
# --------------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------------- #
```
- Docstrings on every class and non-trivial function; triple-quoted module docstrings summarize scope and constraints at top of test files

## Function Design

**Size:** Services keep methods focused (roughly under 60 lines); complex algorithms decompose into private helpers prefixed `_` (e.g. `PubMedConnector._window_start`, `FakeSession._compile_params`)

**Parameters:** Keyword-friendly signatures with sensible defaults (`min_sources: int = 3, window_hours: int = 48`); FastAPI query params declared via `Query(..., description=...)`

**Return Values:** Always annotated; services return Pydantic response models; engines return typed models or `Optional[Model]` for "no result"; tuples used sparingly with documented order (`tuple[float, Dict[str, float]]` meaning `(total, breakdown)`)

## Module Design

**Exports:**
- Backend: one primary service/engine class per module plus module-level singleton where shared (`confluence_engine = ConfluenceEngine()` in `backend/app/services/confluence.py`)
- Aggregation via package `__init__.py` re-exports (`backend/app/models/__init__.py`, `backend/app/schemas/__init__.py`) - import models/schemas from the package, not deep paths
- Connectors subclass `SourceConnector` from `backend/app/connectors/base.py` and declare `source_id` / `source_type` / `freshness_class` class attributes
- LangGraph pipeline nodes are thin modules registered in `build_graph()` in `backend/app/workflows/graph.py` in canonical order (ingest, validate, embed, nlp_extract, ontology_enrich, confluence, lifecycle, redteam, missing_signal, synthesize, calibrate)

**Barrel Files:**
- `metaradar.tsx` acts as the frontend design-system barrel (`Card`, `Badge` primitives); prefer importing primitives from `@/components/metaradar`
- API client functions live in `frontend/lib/api.ts` with backward-compat aliases exported explicitly (`export const getOverview = fetchOverview`)

## Contract Synchronization (Critical Convention)

The frontend API contract is hand-maintained but machine-enforced:

1. Canonical template lives inside `scripts/export_openapi.py` (header comment documents this in `frontend/types/api.ts`)
2. Running `python scripts/export_openapi.py` re-emits `frontend/types/api.ts` verbatim from the template and dumps `contracts/openapi.json`
3. CI (`.github/workflows/ci.yml`) runs the script then `git diff --exit-code frontend/types/api.ts` - direct edits to `frontend/types/api.ts` fail the build
4. To change the contract: edit the template inside `scripts/export_openapi.py`, run it, commit both files together
5. `tests/test_contract_drift.py` additionally asserts required OpenAPI paths and required TS interface exports exist

## Component Conventions (Frontend)

- Mark interactive components `'use client'` on line 1 (`frontend/components/signals/SignalCard.tsx`)
- Named function exports, not default exports: `export function SignalCard({ signal, onSelect }: SignalCardProps)`
- Props destructured inline; optional callbacks invoked with `?.` (`onSelect?.(signal)`)
- Styling exclusively through Tailwind classes using CSS-variable tokens; never raw palette/hex classes (enforced by banned-class gate)
- Data fetching through `useLiveData<T>(fetcher, intervalMs, deps)` hook from `frontend/lib/hooks.ts` (visibility-aware polling, AbortController, in-flight dedupe) - do not roll ad-hoc useEffect polling

---

*Convention analysis: 2026-08-23*
