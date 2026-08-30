# Coding Conventions

**Analysis Date:** 2026-08-30

## Naming Patterns

### Files & Folders

| Layer | Pattern | Examples |
|-------|---------|----------|
| Python source files | `snake_case.py` | `auth.py`, `signals.py`, `logging.py`, `middleware.py`, `config.py`, `redact.py` |
| Python package directories | `snake_case` | `app/core/`, `app/schemas/`, `app/api/v1/endpoints/`, `app/services/`, `app/models/`, `app/providers/` |
| Test files | `test_*.py` | `test_auth.py`, `test_signals_endpoints.py`, `test_ingestion.py` |
| TypeScript source files | `snake_case.ts` or `kebab-case.tsx` | `api.ts`, `mappers.ts`, `errors.ts`, `hooks.ts`, `utils.ts` |
| React components | `PascalCase.tsx` | `MetaRadar.tsx`, `SignalCard.tsx`, `SpecularButton.tsx`, `AnimatedCounter.tsx` |
| Component subdirectories | `kebab-case` | `components/ui/`, `components/common/`, `components/signals/`, `components/theme/` |
| Schema files | `snake_case.py` | `auth.py`, `intelligence.py`, `registry.py` |
| Endpoint files | `snake_case.py` | `auth.py`, `signals.py`, `health.py`, `pipeline.py`, `feedback.py` |
| Config files | `snake_case` or standard names | `pytest.ini`, `eslint.config.mjs`, `setup.py` |

### Functions & Methods (Python Backend)

- **Standard functions:** `snake_case` — e.g., `validate_state_transition`, `_serialize_signal`, `configure_structlog`, `redact_text`
- **Private/helper functions:** Leading underscore — e.g., `_scrub_secrets`, `_set_auth_cookies`, `_clear_auth_cookies`
- **Async functions:** `async def` prefix — e.g., `async def login`, `async def get_signal_detail`
- **Class methods:** `snake_case` — e.g., `filter`, `scrub`, `classify_payload`, `validate`
- **Route handler functions:** `async def` matching the endpoint — e.g., `list_signals`, `submit_signal_review`, `get_overview`
- **State machine/validation functions:** `snake_case` — e.g., `validate_state_transition`
- **Database helpers:** `snake_case` — e.g., `_compile_params` in `FakeSession`

### Variables & Constants (Python Backend)

- **Module-level constants:** `UPPER_SNAKE_CASE` — e.g., `MAX_EVIDENCE_DISTANCE = 0.35`, `KNOWN_STATES`, `VALID_TRANSITIONS`, `ACTIONED_ALLOWED_ROLES`, `ATHENA_GREETINGS`
- **Database model fields:** `snake_case` — e.g., `signal_id`, `source_name`, `review_status`
- **Pydantic model fields:** `snake_case` — e.g., `novelty`, `clinical`, `regulatory`, `recency`, `total`
- **Type variables:** `snake_case` with type hints — e.g., `text: str`, `items: List[SignalSchema]`
- **Mutable default arguments:** `Field(default_factory=...)` — never mutable literals

### Types & Interfaces (TypeScript Frontend)

- **Interfaces:** `PascalCase` — e.g., `Signal`, `HealthResponse`, `ModelMetadata`, `ScoreBreakdown`, `AuditLogItem`, `SignalReviewPayload`
- **Type aliases:** `PascalCase` — e.g., `DataMode`, `ConfidenceType`, `HealthStatus`
- **Enum-like string unions:** `PascalCase` values — e.g., `"CRITICAL" | "HIGH" | "MEDIUM" | "LOW"` for priority
- **Exported types:** Always `export`ed from `frontend/types/api.ts`
- **Function types:** Arrow functions with explicit return types — e.g., `export async function fetchOverview(signal?: AbortSignal): Promise<DashboardOverview>`
- **API function names:** `camelCase` with `fetch`/`get`/`submit` prefix — e.g., `fetchOverview`, `getSignals`, `submitSignalFeedback`, `askAthena`, `streamAthena`

## Code Style

### Backend (Python)

- **Imports:** `from __future__ import annotations` in all source files
- **Import order:** stdlib → third-party → local app (grouped, alphabetically within groups)
- **Type hints:** Required on all function signatures, including return types and parameter types
- **String formatting:** f-strings throughout — e.g., `f"[ATHENA] Query received: '{trimmed[:80]}'"`
- **Docstrings:** Triple-quoted `"""` docstrings on modules, classes, and public functions
- **Error handling:** `try/except` blocks with specific exception types; bare `except Exception:` only where appropriate with logging
- **Async patterns:** `async/await` throughout; `AsyncSession` from SQLAlchemy; `AsyncGenerator` for streaming SSE
- **Pydantic v2:** `BaseModel` with `ConfigDict(from_attributes=True)` for models that accept ORM attributes; `field_validator` for custom validation; `Field(default_factory=...)` for mutable defaults
- **Logging:** `logging.getLogger(__name__)` for module-level loggers; `structlog` for structured JSON logging in `core/logging.py`; `logger.info()`, `logger.warning()`, `logger.debug()`, `logger.error()` patterns
- **HTTP exceptions:** `fastapi.HTTPException(status_code=status.HTTP_4xx_XXX, detail="...")` throughout endpoints
- **UUID usage:** `from uuid import UUID` and `uuid.uuid4()` for primary keys
- **Database queries:** SQLAlchemy 2.0 style `select(...)` with `await db.execute(query)`; `result.scalars().all()` for results
- **Constants location:** Module-level constants at top of file, before class/function definitions
- **No trailing semicolons**; one import per line (multi-import from same module on single line with parens)

### Frontend (TypeScript/React)

- **TypeScript version:** 5.7.3, strict mode
- **React:** 19 with Next.js 16.3.0; `'use client'` directive for client components
- **Tailwind CSS v4:** Custom CSS variables (`--muted-foreground`, `--border`, `--surface`, etc.); `twMerge(clsx(...))` via `cn()` utility
- **Class variants:** `cva` (class-variance-authority) for component variants like `buttonVariants`
- **Icon library:** `lucide-react` for all icons — e.g., `import { Activity, AlertTriangle, Bell } from 'lucide-react'`
- **Animation:** `framer-motion` (`AnimatePresence`, `motion`) for transitions
- **Data fetching:** Native `fetch` API wrapped in `apiFetch<T>()` with `AbortSignal` support; `credentials: 'include'` for cookies
- **Error handling:** `ApiError` class extends `Error` with `status`, `statusText`, `message`, `isRetryable`, `requestId`, `endpoint`; `formatError()` for display formatting
- **State management:** React `useState`, `useEffect`, `useCallback`, `useRef`; custom `useLiveData<T>()` hook for polling with visibility awareness and AbortController dedup
- **Mapper pattern:** `mapSignal()` in `lib/mappers.ts` transforms raw API responses into typed `Signal` objects; `RawSignalPayload` interface for raw data
- **No hardcoded colors:** `check-banned-classes.mjs` enforces no `bg-slate-*`, `text-slate-*`, `border-slate-*`, or hex-color Tailwind classes in components
- **CSS class naming:** `camelCase` React props; `kebab-case` CSS class names (Tailwind utility classes)
- **Component patterns:** Function components with explicit type annotations; `export function` for named exports; props destructured with types

## Import Organization

### Python Backend

```python
# 1. Future imports (always first)
from __future__ import annotations

# 2. Standard library
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

# 3. Third-party
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator

# 4. Local app imports (absolute paths from project root)
from app.core.config import settings
from app.db.session import get_db
from app.models import Signal, AuditLog
from app.schemas import SignalSchema, SignalListResponse
```

- **Path alias:** `app.` prefix resolved via `sys.path.insert(0, str(base_dir / "backend"))` in `conftest.py` and `tests/`
- **Barrel files:** `backend/app/schemas/__init__.py` re-exports all schemas so endpoints do `from app.schemas import SignalSchema` instead of deep imports
- **Lazy imports:** Used sparingly inside functions to avoid circular imports — e.g., `from app.services.auth_service import get_session_user` inside a function body

### TypeScript/React Frontend

```typescript
// 1. Type-only imports
import type { Signal, HealthResponse, ... } from '@/types/api'

// 2. Regular imports (aliased via @/)
import { ApiError, mapSignal } from '@/lib/api'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
```

- **Path alias:** `@/` maps to `frontend/` (configured by Next.js)
- **Type imports:** `import type { ... }` for type-only imports
- **Named re-exports:** `lib/api.ts` re-exports aliases like `export const getOverview = fetchOverview`
- **Default exports:** Rarely used; prefer named exports (`export function`, `export async function`)

## Error Handling

### Backend Strategy

- **HTTP errors:** `fastapi.HTTPException` with appropriate status codes:
  - `401_UNAUTHORIZED` — missing/invalid credentials
  - `403_FORBIDDEN` — RBAC denial, origin mismatch, CSRF failure, rate limit
  - `404_NOT_FOUND` — resource not found
  - `409_CONFLICT` — invalid state transition, terminal state modification
  - `422_UNPROCESSABLE_ENTITY` — empty prompt, validation failure
  - `429_TOO_MANY_REQUESTS` — rate limit exceeded
- **Validation:** Pydantic `field_validator` for schema-level validation; `Field(..., ge=1, le=5)` for numeric bounds; custom validators like `validate_stakeholder_function`
- **Runtime errors:** `pytest.raises(PermissionError)` for expected exceptions; `try/except Exception` with `logger.debug` for non-critical audit failures
- **State machine:** `validate_state_transition()` function centralizes all FSM validation with specific `HTTPException` messages per failure mode
- **Audit log immutability:** SQLAlchemy `@event.listens_for(AuditLog, "before_update")` and `before_delete` raise `PermissionError`; PostgreSQL triggers also block raw SQL updates/deletes

### Frontend Strategy

- **`ApiError` class:** Custom error class with `status`, `statusText`, `message`, `isRetryable`, `requestId`, `endpoint` fields
- **`formatError()` function:** Maps `ApiError` to display-friendly `FormattedError` with titles like "Resource Not Found" (404), "Rate Limit Exceeded" (429), "Authentication Error" (401/403), "Server Error" (500+), "Network Disconnected" (0)
- **Network errors:** `AbortError` re-thrown as-is; all other errors wrapped in `ApiError(0, 'NetworkError', ...)`
- **Graceful degradation:** `.catch(() => ({...defaultValue}))` patterns in `apiFetch` callers to provide fallback data when endpoints fail
- **Console logging:** `console.error('Failed to clear cache:', err)` for user-action failures; no `alert()` usage

## Logging

### Framework

- **Structured JSON logging:** `structlog` configured via `backend/app/core/logging.py`
- **Standard library:** `logging` module used for module-level loggers via `logging.getLogger(__name__)`
- **Default logger name:** `"metaradar"` (main), `"metaradar.http"` (middleware), `"metaradar.main"` (app startup)

### Patterns

- **Configuration:** `configure_structlog(json_logs=True)` sets up processors: `merge_contextvars → add_log_level → TimeStamper → StackInfoRenderer → _scrub_secrets → JSONRenderer`
- **Secret scrubbing:** `_scrub_secrets` processor redacts keys matching `SENSITIVE_KEYS` (`password`, `token`, `api_key`, `secret`, `authorization`, etc.) to `[REDACTED_SECRET]`; email keys to `[REDACTED_PII]`; all string values passed through `redact_text()`
- **Correlation IDs:** `CorrelationIdMiddleware` binds `request_id` and `correlation_id` to structlog contextvars via `structlog.contextvars.bind_contextvars()` for async-safe trace logging
- **Request telemetry:** `logger.info("http_request_completed", status_code=..., duration_ms=...)` emitted on every request completion
- **Module-level loggers:** `logger = logging.getLogger(__name__)` pattern in each module; used with `logger.info()`, `logger.warning()`, `logger.error()`, `logger.debug()`
- **String formatting:** `%s` style in logging calls — e.g., `logger.debug("Failed to record failed login audit: %s", e)` (not f-strings in logging)
- **Structured events:** `logger.info("service_startup", message="...", version=...)` — event name as first positional arg, context as kwargs

## Security & Privacy Invariants

- **PII/PHI Scrubbing:** `PIIPHIScrubber` (in `app/services/pii.py`) scrubs emails, phones, SSNs, MRNs, and DOBs from text before ingestion; replaces with `[EMAIL_REDACTED]`, `[PHONE_REDACTED]`, `[SSN_REDACTED]`, `[MRN_REDACTED]`, `[PATIENT_DOB_REDACTED]`
- **Secret redaction:** `app/core/redact.py` provides `redact_value()`, `redact_mapping()`, `redact_text()` for scrubbing API keys, passwords, tokens from log messages and query params
- **Audit log immutability:** `AuditLog` model has SQLAlchemy event listeners that raise `PermissionError` on UPDATE and DELETE; PostgreSQL triggers enforce this at the database level
- **Session security:** `SESSION_COOKIE_NAME = "metaradar_session"` with `httponly=True`, `samesite="lax"`; `CSRF_COOKIE_NAME = "metaradar_csrf"` with `httponly=False` (accessible to JS for `X-CSRF-Token` header)
- **CSRF validation:** Session-bound HMAC-SHA256 CSRF tokens via `generate_session_bound_csrf()` and `verify_session_bound_csrf()` in `app/core/security.py`
- **Origin validation:** `require_preauth_origin` dependency enforces exact scheme+host+port matching against `CORS_ORIGINS` on all pre-auth endpoints; blocks spoofed origins like `http://localhost:3000.evil.com`
- **Rate limiting:** `auth_rate_limit` dependency on auth endpoints (configurable via `AUTH_RATE_LIMIT_PER_MINUTE`); `mutation_rate_limit` on mutation endpoints
- **Password hashing:** `bcrypt` with `gensalt()` for password hashing; `hashlib.sha256` for session token hashing; `hmac.compare_digest` for constant-time comparison
- **Session tokens:** Timestamp-signed via `itsdangerous.TimestampSigner`; absolute timeout (8h) and idle timeout (1h) enforced
- **Privacy gate:** `GrokProvider.validate_privacy_gate()` blocks external API calls for `CONFIDENTIAL` and `UNKNOWN` data classifications; only `PUBLIC` and `SYNTHETIC` pass through
- **Banned CSS classes:** `scripts/check-banned-classes.mjs` enforces no hardcoded `bg-slate-*`, `text-slate-*`, `border-slate-*`, `dark:bg-*`, or arbitrary hex-color Tailwind classes in `frontend/components/`
- **`from_attributes=True`:** Pydantic models use `ConfigDict(from_attributes=True)` to accept ORM objects safely
