# Coding Conventions

**Analysis Date:** 2026-08-27

## Naming Patterns

**Files:**
- Frontend Components: `PascalCase.tsx` (`SignalDetailWorkspace.tsx`, `DemoOperatorSelector.tsx`)
- Frontend Utilities & Hooks: `camelCase.ts` (`api.ts`, `errors.ts`, `mappers.ts`, `hooks.ts`)
- Backend Modules: `snake_case.py` (`provenance_urls.py`, `fierce_pharma.py`, `redteam.py`)
- Test Files: `test_<feature>.py` (`test_provenance.py`, `test_connector_health.py`)

**Functions:**
- Python: `snake_case()` (`resolve_canonical_provenance()`, `calculate_authority_tier()`, `fetch_records()`)
- TypeScript / React: `camelCase()` (`fetchSignals()`, `mapSignal()`, `useSignals()`, `handleStatusChange()`)

**Variables:**
- Python: `snake_case` (`signal_id`, `review_status`, `raw_payload`, `records_fetched`)
- TypeScript: `camelCase` (`selectedSignal`, `isSubmitting`, `activeRole`, `errorMessage`)
- Constants & Enums: `UPPER_SNAKE_CASE` (`DEFAULT_RETENTION_DAYS`, `VALID_REVIEW_STATUSES`, `PII_PATTERNS`)

**Types:**
- TypeScript Interfaces / Types: `PascalCase` (`Signal`, `ConfluenceAlertItem`, `SignalReviewPayload`, `HealthStatus`)
- Pydantic Models & SQLAlchemy Classes: `PascalCase` (`SignalCreate`, `SignalReviewUpdate`, `PipelineRun`, `RawSignalBronze`)

## Code Style

**Formatting:**
- Frontend: Prettier / ESLint with 2 spaces indentation, single quotes for TypeScript strings, and semicolons omitted where standard.
- Backend: PEP 8 standard, 4 spaces indentation, type hints on all public function signatures.

**Linting:**
- Frontend: ESLint 10 with `@next/eslint-plugin-next` and custom rules. Zero warnings permitted in CI.
- CSS Token Enforcement: `scripts/check-banned-classes.mjs` prevents hardcoded hex colors and default `slate-*` Tailwind classes.
- Type Safety: `tsc --noEmit` and `ignoreBuildErrors: false` in `next.config.mjs`.

## Import Organization

**Order (TypeScript / Frontend):**
1. React & framework core imports (`import React, { useState, useEffect } from 'react'`)
2. Third-party packages (`framer-motion`, `lucide-react`, `recharts`, `@base-ui/react`)
3. Internal library utilities & mappers (`import { getSignals } from '@/lib/api'`, `import { cn } from '@/lib/utils'`)
4. Type definitions (`import type { Signal, HealthStatus } from '@/types/api'`)
5. Sibling / child UI components (`import { SignalCard } from './SignalCard'`)

**Order (Python / Backend):**
1. Standard library modules (`import uuid`, `from datetime import datetime, timezone`, `from typing import Optional, List`)
2. Third-party libraries (`from fastapi import FastAPI, Depends`, `import structlog`, `from sqlalchemy import select`)
3. Local application modules (`from app.core.config import settings`, `from app.models import Signal`, `from app.services.routing import route_signal`)

**Path Aliases:**
- Frontend: `@/*` maps to `frontend/*` (e.g. `@/components/common/DataModeBadge`, `@/lib/api`, `@/types/api`).
- Backend: `app.*` maps to `backend/app/*` (e.g. `from app.core.config import settings`).

## Error Handling

**Patterns:**
- **Frontend:** API errors are wrapped in strongly-typed `ApiError` instances (`frontend/lib/errors.ts`) preserving HTTP status codes and backend detail payloads. Error boundaries and `ErrorState` components render user-friendly messages with correlation IDs.
- **Backend:** Route handlers catch domain exceptions and re-raise structured `HTTPException(status_code=..., detail=...)`.
- **Database Transactions:** Always wrap modifying queries in `try...except` blocks with explicit `await session.rollback()` on failure.
- **SQLAlchemy 2.0 Invariant:** `session.add()` is synchronous on `AsyncSession`; never await `session.add()`.

## Logging

**Framework:** `structlog` (`backend/app/core/logging.py`) with JSON output and correlation tracing.

**Patterns:**
- Use key-value structured logging: `logger.info("signal_routed", signal_id=str(signal.signal_id), destination=dest, score=score)`.
- Automatic PII/PHI scrubbing: `backend/app/core/redact.py` automatically scrubs patient names, MRNs, and email patterns before output.
- Request correlation: Every log event includes `correlation_id` propagated via `asgi-correlation-id`.

## Comments

**When to Comment:**
- Document non-obvious business rules, regulatory logic, or mathematical weighting algorithms.
- Explain decisions matching formal project decisions (e.g. `// Ref: Decision D-09-01`).
- Avoid redundant comments that simply restate function names.

**Docstrings / TSDoc:**
- All Python service methods, connectors, and endpoints require concise docstrings with parameter and return type notes.
- Exported TypeScript API helper functions in `frontend/lib/api.ts` include TSDoc parameter descriptions.

## Function Design

**Size:** Keep functions modular (<50 lines where practical). Extract complex branching or mathematical scoring into dedicated helper services.

**Parameters:** Prefer explicit keyword arguments or Pydantic DTO schemas in Python. Use typed parameter objects for TypeScript functions with >2 arguments.

**Return Values:** Always declare explicit return type annotations (`Promise<Signal[]>`, `-> Tuple[str, float]`). Avoid untyped dictionary or `any` returns.

## Module Design

**Exports:**
- Use named exports for components and utility functions in TypeScript.
- Group public package exports in `__init__.py` for Python packages (`backend/app/connectors/__init__.py`, `backend/app/models/__init__.py`).

**Barrel Files:**
- Use focused barrel files for clean module boundaries without creating circular import hazards.

---

*Convention analysis: 2026-08-27*
