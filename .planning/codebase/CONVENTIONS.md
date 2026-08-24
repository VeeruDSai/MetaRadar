# Coding Conventions

**Analysis Date:** 2026-08-24

This is a dual-stack codebase: Python/FastAPI backend (`backend/`) and TypeScript/Next.js frontend (`frontend/`). Conventions differ per stack; both are documented here. Prescribed rules live in `docs/rules/ENGINEERING_STANDARDS.md` and `AGENTS.md`.

## Naming Patterns

**Files (Python backend):**
- `snake_case.py` module names: `scoring.py`, `pii.py`, `domain_config.py`
- Domain folders by role: `backend/app/api/v1/endpoints/`, `backend/app/services/`, `backend/app/providers/`, `backend/app/connectors/`, `backend/app/core/`, `backend/app/db/`, `backend/app/models/`, `backend/app/schemas/`

**Files (TypeScript frontend):**
- Components: `PascalCase.tsx`: `SignalCard.tsx`, `EvidenceDrawer.tsx`, `ThemeProvider.tsx`
- Lib modules: `camelCase.ts`: `api.ts`, `hooks.ts`, `mappers.ts`, `errors.ts`
- Route files use Next.js App Router lowercase convention: `frontend/app/page.tsx`, `frontend/app/[section]/page.tsx`
- Test files: `test_<module>.py` in root-level `tests/`

**Classes:**
- `PascalCase`: `PriorityScoringService`, `PubMedConnector`, `GemmaProvider`, `PIIPHIScrubber`, `ApiError` (`frontend/lib/errors.ts`)
- Custom exceptions end in `Error`: `OllamaUnavailableError`, `ConnectorFetchError` (`backend/app/connectors/base.py`)
- SQLAlchemy models are singular nouns: `Signal`, `Asset`, `Confluence`, `Development` (`backend/app/models/__init__.py`)
- Pydantic response schemas end in `Schema` or `Response`: `SignalSchema`, `SignalListResponse`, `OverviewResponse` (`backend/app/schemas/__init__.py`)

**Functions/Methods:**
- `snake_case` verbs: `scrub()`, `score_text()`, `run_profile()`, `generate_fingerprint()`
- Private/internal helpers prefixed `_`: `_serialize_signal()` (`backend/app/api/v1/endpoints/signals.py`), `_scrub_secrets()` (`backend/app/core/logging.py`), `_ensure_client()` (`backend/app/providers/gemma.py`)
- Async endpoints/functions use bare `async def` — no `async_` name prefix
- Frontend fetchers use verb prefixes: `fetchOverview()`, `fetchSignals()`, `submitSignalFeedback()`; legacy aliases exported as `getOverview = fetchOverview` for backward compatibility (`frontend/lib/api.ts:39`)

**Variables:**
- `snake_case` in Python, `camelCase` in TypeScript
- Module-level constants in `UPPER_SNAKE_CASE`: `SCORING_VERSION`, `CLINICAL_KEYWORDS`, `MAX_EVIDENCE_DISTANCE` (`backend/app/services/scoring.py`, `backend/app/api/v1/endpoints/signals.py:39`), `API_BASE` (`frontend/lib/api.ts:149`)

**Types (frontend):**
- Interfaces/types in `types/api.ts`, PascalCase: `Signal`, `DashboardOverview`, `ModelMetadata`
- Props interfaces named `{Component}Props`: `SignalCardProps` (`frontend/components/signals/SignalCard.tsx:26`)
- Generic hook state interfaces: `LiveDataState<T>` (`frontend/lib/hooks.ts:5`)

## Code Style

**Python:**
- No formatter config detected (no black/ruff/isort config files). Match existing style: 4-space indent, double quotes mostly, trailing commas omitted inconsistently — mirror surrounding code.
- Type hints on all public functions using `typing.Optional`, `Dict`, `List`, `Any` (legacy typing style, not PEP 604 unions): see `backend/app/services/scoring.py:146-151`
- Dataclasses for internal value objects: `@dataclass class ScoreInput` (`backend/app/services/scoring.py:37-43`)

**TypeScript:**
- `"strict": true` in `frontend/tsconfig.json` — never weaken it; never use `ignoreBuildErrors` or `@ts-ignore` (banned by `AGENTS.md`)
- Single quotes, no semicolons, 2-space indent (match existing files; no Prettier config present)
- Pragmatic `any` appears at API boundary parsing (e.g., `fetchOverview` uses `apiFetch<any>`) — prefer typing new code at the mapper boundary instead of spreading `any`

**Linting:**
- Frontend: ESLint 10 flat config in `frontend/eslint.config.mjs` extending `@next/eslint-plugin-next` recommended + `core-web-vitals`. Run via `pnpm lint`.
- Backend: no linter configured; correctness is enforced by pytest suite + type hints.
- **Banned Tailwind classes gate:** `pnpm run check:banned-classes` executes `scripts/check-banned-classes.mjs`, which fails the build if any `.tsx` under `frontend/components/` uses `slate-*` palette classes or arbitrary hex values like `bg-[#fff]` (exception: `metaradar.tsx`). Use design-token classes instead.

## Import Organization

**Python:**
1. Stdlib (`import json`, `from datetime import ...`)
2. Third-party (`fastapi`, `sqlalchemy`, `httpx`, `structlog`, `pydantic`)
3. First-party app imports (`from app.core.config import settings`, `from app.services.scoring import priority_scorer`)
- Example canonical ordering: `backend/app/api/v1/endpoints/signals.py:1-32`
- Deferred/lazy imports inside functions are used deliberately to avoid startup cost or circulars: `from llama_cpp import Llama` inside `_generate_with_local_gguf` (`backend/app/providers/gemma.py:90`), scheduler import inside lifespan (`backend/app/main.py:44`)

**TypeScript:**
1. `'use client'` directive first line (required for client components)
2. React/Next framework imports (`import { useState } from 'react'`, `import Link from 'next/link'`)
3. Icon imports from `lucide-react` / animation from `framer-motion`
4. Type-only imports using `import type {...}` form: `import type { Signal } from '@/types/api'` (`frontend/components/signals/SignalCard.tsx:6`)
5. Local components via `@/` alias; sibling modules via relative paths (`import { DataModeBadge } from '../common/DataModeBadge'`)

**Path Aliases:**
- `@/*` → repo-relative to `frontend/` root (`frontend/tsconfig.json` paths). Use `@/components/...`, `@/lib/...`, `@/types/api`.
- Backend uses absolute `app.*` imports; `pythonpath = backend .` in `pytest.ini` makes this resolvable.

## Error Handling

**Backend patterns:**
- HTTP errors via `HTTPException` with explicit status constants and descriptive detail: `raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Signal with ID '{signal_id}' not found.")` (`backend/app/api/v1/endpoints/signals.py:232-235`)
- **Never-crash contract (D-12):** providers raise typed errors (`OllamaUnavailableError`) so `ProviderFactory` falls through Gemma → Grok → DegradedProvider (BART factual mode) instead of crashing (`backend/app/providers/gemma.py:7-8`). Follow this chain pattern for any new provider/capability.
- Honest degradation over silent success: when scoring inputs are missing, return `None` and surface `scoring_status="not_computed"` rather than fabricating a score (`backend/app/services/scoring.py:102-107`, `backend/app/api/v1/endpoints/signals.py:44-54`). Never fabricate telemetry (AGENTS.md rule 4).
- Broad `try/except Exception` is acceptable ONLY when it converts failure into labeled degraded state or honest empty results (e.g., vector retrieval fallback to lexical search in `query_athena`, `backend/app/api/v1/endpoints/signals.py:379-448`). Do not use it to hide bugs.
- Config validation is pure-function based: `configuration_error_for(source_id)` returns human-readable `CONFIGURATION_ERROR:` strings checked by connectors (`backend/app/core/config.py:109-120`).

**Frontend patterns:**
- All network calls go through `apiFetch<T>()` which normalizes failures into a typed `ApiError` carrying `status`, `isRetryable` (status >= 500 or 429), `requestId` from `x-request-id` header, and `endpoint` (`frontend/lib/api.ts:151-202`)
- Never throw raw strings; always `Error` subclasses. Non-API errors are wrapped: `throw new ApiError(0, 'NetworkError', ...)` 
- UI display formatting centralized in `formatError()` mapping status codes → user titles (`frontend/lib/errors.ts:24-56`)
- Abort-aware: respect `AbortError` re-throws so cancelled polls don't surface as errors (`frontend/lib/hooks.ts:64-67`)
- Non-critical reads degrade with `.catch(() => fallback)` returning explicitly empty/labeled data — e.g., connector count returns `0` "never a hardcoded fabricated count" (`frontend/lib/api.ts:356-363`)

## Logging

**Framework:**
- Backend primary: **structlog** JSON logging configured once in `backend/app/core/logging.py`; obtain via `get_logger(name)` or `structlog.get_logger("metaradar.<module>")` (`backend/app/main.py:26`)
- Backend secondary: stdlib `logging.getLogger(__name__)` inside connectors/providers (`backend/app/connectors/pubmed.py:18`, `backend/app/providers/gemma.py:24`) — acceptable for module-scoped logs

**Patterns:**
- Log structured key-value events, not prose strings: `logger.info("service_startup", message="...")`, `logger.info("domain_config_loaded", disease_area=..., version=...)` (`backend/app/main.py:32-39`)
- Every log event passes through `_scrub_secrets` processor which redacts sensitive keys to `[REDACTED_SECRET]`, emails to `[REDACTED_PII]`, and runs `redact_text` on string values (`backend/app/core/logging.py:10-19`). Never log raw PII/PHI/secrets — scrubbing happens before persistence or external provider calls via `PIIPHIScrubber.scrub()` (`backend/app/services/pii.py`)
- Correlation: `CorrelationIdMiddleware` attaches request IDs surfaced as `x-request-id` (`backend/app/core/middleware.py`); tests assert its presence even on validation failures (`tests/test_failure_injection.py:58`)
- Frontend has no logger library; errors propagate to `formatError`/UI states instead of console noise

## Comments

**When to Comment:**
- Explain *why* and encode invariants/contracts: "Zero-fabrication gate: If no evidence is found, return honest failure notice" (`backend/app/api/v1/endpoints/signals.py:450`), "Single source of truth — the query filter and the docstring contract must never drift apart again" (`signals.py:37-38`)
- Number multi-step endpoint bodies as executable outlines: `# 1. PII / PHI scrubbing & content classification (CR-03)` … `# 5. Structured safe prompt execution via ProviderFactory` (`signals.py:346-463`)
- Reference requirement IDs where applicable: `(REQ-P1-1)`, `(REQ-P1-14)` (`backend/app/connectors/pubmed.py:22-26`)
- Section dividers with dashes organize large modules: `# --------------------------------------------------------------------------- #` (`pubmed.py:41`), `// 1. Dashboard Overview & Signals` (`frontend/lib/api.ts:204-206`)

**Docstrings:**
- Triple-quoted docstrings on every public Python class and method, stating purpose + contract: `PriorityScoringService` docstring includes the formula and None-return semantics (`backend/app/services/scoring.py:68-75`)
- Class docstrings cite requirement IDs and behavior contracts (`pubmed.py:22-27`)
- JSDoc block comments on non-obvious frontend logic: `useLiveData` hook documents polling/visibility/abort semantics (`frontend/lib/hooks.ts:14-20`)

## Function Design

**Size:** Endpoint handlers may be long but MUST decompose into numbered steps with helpers extracted for reuse (`_serialize_signal`). Prefer small pure helpers: `getSourceAuthority`, `getSignalFunction`, `getSuggestedAction` are exported pure functions above the component (`frontend/components/signals/SignalCard.tsx:34-119`)

**Parameters:**
- FastAPI endpoints declare filters via `Query(None, description=...)` with validation constraints: `limit: int = Query(20, ge=1, le=200)` (`backend/app/api/v1/endpoints/signals.py:140-147`)
- Frontend fetchers accept optional trailing `signal?: AbortSignal` parameter — always thread it through to `apiFetch` (`frontend/lib/api.ts`)

**Return Values:**
- Return typed Pydantic schemas via `response_model=` on every route
- Return `Optional[...]`/`null` honestly when computation isn't possible — never sentinel fake numbers
- Services return dataclasses/dicts with version stamps: `ScoreBreakdown.version` enables auditability (`backend/app/services/scoring.py:45-64`)

## Module Design

**Exports (Python):**
- Singleton service instances at module bottom consumed directly by importers: `priority_scorer = PriorityScoringService()` (`backend/app/services/scoring.py:163`), `provider_factory`, `embedding_service`, `confluence_engine`. New stateless services should follow this singleton-module pattern.
- Utility classes expose `@staticmethod`/`@classmethod` APIs: `PIIPHIScrubber.scrub()`, `PriorityScoringService.extract_keywords_count()`
- Barrel re-exports in package `__init__.py`: `backend/app/schemas/__init__.py`, `backend/app/models/__init__.py` — add new schemas/models there

**Exports (TypeScript):**
- Named exports only (no default exports except implicit Next.js page/layout defaults)
- One concern per lib module: transport (`api.ts`), error types (`errors.ts`), shape mapping (`mappers.ts`), hooks (`hooks.ts`)
- `metaradar.tsx` acts as shared component hub exporting `Badge` etc.; do NOT add banned classes there or in any component (gate enforces)

**Contract sync workflow (critical):**
- The frontend API contract is hand-maintained: edit the template inside `scripts/export_openapi.py`, run `python scripts/export_openapi.py`, commit `frontend/types/api.ts` + `contracts/openapi.json` together. CI (`​.github/workflows/ci.yml:35-40`) fails if `frontend/types/api.ts` is edited directly. Enforced again by `tests/test_contract_drift.py`.

---

*Convention analysis: 2026-08-24*
