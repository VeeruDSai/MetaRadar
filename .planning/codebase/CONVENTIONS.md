---
doc_type: codebase-map
focus: quality
analysis_date: 2026-08-23
---

# Code Conventions

**Analysis Date:** 2026-08-23

Governing standards live in `docs/rules/ENGINEERING_STANDARDS.md` and `AGENTS.md` (mandatory for all agents): no `@ts-ignore`, no `ignoreBuildErrors`, no fabricated telemetry, no silent exception swallowing, zero secrets.

## Python (Backend)

### Style & Typing
- Strict type hints on function signatures; `typing` generics (`Optional`, `List`, `Dict`, `Literal`, `Annotated`, `Tuple`).
- Module-level `logger = logging.getLogger(__name__)` in every module; structlog JSON logging configured centrally in `backend/app/core/logging.py`.
- Docstrings cite design & decision IDs (`D-01`, `D-11`, `D-23`, `D-26`, `REQ-P1-*`).
- Pydantic v2 models for all request/response serialization; SQLAlchemy declarative models in `backend/app/models/__init__.py`.

### Truthfulness & Honesty Rules (Absolute Standard)
- **Truthful Source Health**: Never classify a successful request returning 0 new records as `DEGRADED`. A clean empty sync is `NO_NEW_DATA` or `HEALTHY`.
- **Timestamp Integrity**: `last_success` must be updated on all clean checks (`HEALTHY`, `NO_NEW_DATA`, `CONNECTED`).
- **Telemetry Precision**: Telemetry must truthfully record `records_fetched`, `records_new`, `records_updated`, `records_duplicate`, `duration_ms`, and `upstream_data_timestamp`.
- **Model Traceability**: Every AI output carries `model_metadata` (provider, model, fallback reason, `reasoning_available`).
- **Synthetic Flagging**: Synthetic data is always explicitly flagged (`is_synthetic=True`, `data_mode="synthetic"`).

### Concurrency & Locking
- Distributed concurrency protection: Background scheduled jobs must acquire a PostgreSQL advisory lock (`try_advisory_lock(session, lock_id)`) before execution and release it in a `finally` block.

## TypeScript/React (Frontend)

### Style & Typing
- Strict TypeScript (`"strict": true`); zero `@ts-ignore` or type-suppressing comments.
- ESLint 10 with `eslint-config-next` with 0 warnings / 0 errors policy.
- Path alias `@/*` maps to frontend root (`@/types/api`, `@/lib/...`).
- Typed API client: all API interactions go through `frontend/lib/api.ts` using types from `frontend/types/api.ts` — components never call raw `fetch`.
- DTO→view transformations isolated in `frontend/lib/mappers.ts`; errors normalized via `ApiError` in `frontend/lib/errors.ts`.

### Styling Rules (Hard Gate)
- `scripts/check-banned-classes.mjs` enforces design system hygiene: bans Tailwind `slate-*` classes and arbitrary hex values (`bg-[#...]`) across all domain components.
- `cn()` utility (`clsx` + `tailwind-merge`) for composition; CVA for component variants.

## Cross-Cutting Rules

- **Contract Synchronization**: Backend schema updates must immediately be exported via `python scripts/export_openapi.py` to regenerate `contracts/openapi.json` and canonical `frontend/types/api.ts`.
- **Git Branching & Commits**: Never push directly to `main`. Use descriptive feature branches (`feature/*`, `fix/*`, `gsd-reviewfix/*`). Conventional commits with clear scopes.
