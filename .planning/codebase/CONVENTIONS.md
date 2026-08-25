# Coding Conventions

**Analysis Date:** 2026-08-25

## Naming Standards

**Files & Directories:**
- Python modules: `snake_case.py` matching service or domain area (`backend/app/services/calibration.py`, `backend/app/workflows/nodes/synthesize.py`)
- React components: `PascalCase.tsx` corresponding to the primary exported component (`frontend/components/signals/SignalDetailWorkspace.tsx`, `frontend/components/common/ProvenanceLink.tsx`)
- TypeScript library modules: `camelCase.ts` (`frontend/lib/api.ts`, `frontend/lib/mappers.ts`, `frontend/lib/utils.ts`)
- Component-scoped CSS: `kebab-case.css` or `PascalCase.css` (`frontend/components/effects/star-portal/styles.css`)
- Test suites: `test_<area>.py` located in the root `tests/` directory (`tests/test_provenance.py`, `tests/test_signals_endpoints.py`)

**Functions & Methods:**
- Python: `snake_case` for all sync and async functions (`compute_brier_score()`, `resolve_canonical_url()`, `node_synthesize()`). Private helpers prefixed with `_` (`_serialize_signal()`).
- TypeScript: `camelCase` for utilities, custom hooks (`useLiveData`, `useSignalDetail`), and API fetchers (`fetchOverview`, `fetchSignals`).

**Types & Interfaces:**
- Python: `PascalCase` for classes, Pydantic schemas, and dataclasses (`SignalSchema`, `ScoreBreakdown`, `MetaRadarState`). Enums inherit `(str, Enum)` with UPPERCASE keys.
- TypeScript: `PascalCase` for types and interfaces (`Signal`, `ConfluenceCluster`, `CalibrationOverview`). Props interfaces follow `<ComponentName>Props`.

## Code Style & Best Practices

**Backend (Python 3.11):**
- Strict type annotations on all function signatures using standard `typing` constructs (`Optional[T]`, `List[T]`, `Dict[str, Any]`, `Union[A, B]`).
- Stateless domain services instantiated as singletons or classmethods (`priority_scorer`, `calibration_service`, `embedding_service`).
- Honest telemetry: Missing data must produce explicit null/omission indicators rather than fabricated defaults.
- Structured logging: Standardized on `structlog.get_logger(...)` with request correlation IDs injected via middleware.
- Error handling: Explicit HTTP exceptions with standard RFC 7807 error detail payloads.

**Frontend (Next.js 16 / TypeScript 5.7):**
- Strict compiler mode (`strict: true`) with zero tolerance for `@ts-ignore` or `ignoreBuildErrors`.
- Client boundary discipline: Explicit `'use client'` directive on all interactive client components.
- Design tokens & CSS Variables: Zero hardcoded hex colors (`#...`) or Tailwind `slate-*` classes allowed in `frontend/components/`. All styling must use CSS custom properties (`var(--surface)`, `var(--primary)`, `var(--text-muted)`) and `color-mix()` for alpha blending. Enforced by `node scripts/check-banned-classes.mjs`.
- Contract fidelity: Frontend models in `frontend/types/api.ts` must stay strictly synchronized with the backend OpenAPI specification.

## Import Ordering

**Python:**
1. Standard library (`os`, `sys`, `typing`, `datetime`)
2. Third-party packages (`fastapi`, `sqlalchemy`, `pydantic`, `structlog`, `httpx`)
3. Internal application packages (`app.core.*`, `app.services.*`, `app.models.*`)

**TypeScript:**
1. React and Next.js built-ins (`react`, `next/navigation`, `next/link`)
2. External UI libraries (`lucide-react`, `framer-motion`, `@base-ui/react`)
3. Internal utilities and types (`@/lib/api`, `@/lib/utils`, `@/types/api`)
4. Internal components (`@/components/common/Badge`, `@/components/ui/card`)
