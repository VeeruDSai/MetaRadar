---
doc_type: codebase-map
focus: quality
analysis_date: 2026-08-22
---

# Code Conventions

**Analysis Date:** 2026-08-22

Governing standards live in `docs/rules/ENGINEERING_STANDARDS.md` and `AGENTS.md` (mandatory for all agents): no `@ts-ignore`, no `ignoreBuildErrors`, no fabricated telemetry, no silent exception swallowing, zero secrets.

## Python (Backend)

### Style & Typing
- Type hints on function signatures throughout; `typing` generics (`Optional`, `List`, `Dict`, `Literal`, `Annotated`) — modern builtin generics not yet adopted.
- Module-level `logger = logging.getLogger(__name__)` in every module; structlog JSON logging configured centrally in `backend/app/core/logging.py`.
- Docstrings cite decision IDs (`D-01`, `D-11`, `D-23`, `D-26`) linking behavior to `.planning/` decisions.
- Pydantic v2 models for I/O boundaries (`RawSignalPayload`, `ConnectorStatus`); SQLAlchemy declarative models in a single `backend/app/models/__init__.py`.

### Error Handling Pattern
- **Fail loud, degrade gracefully**: custom exceptions (`ConnectorFetchError`); retries with exponential backoff inside connectors; per-profile isolation so one connector failure doesn't abort the run (`89e2ca8` "isolate connector rollback on error").
- Provider chain catches exceptions and falls through with `logger.warning` + fallback reason recorded in `model_metadata` (`backend/app/providers/factory.py:33-46`). Degraded mode is always explicitly labeled — never silent.
- DB session: commit-on-success / rollback-on-error / close-always in `get_db()` (`backend/app/db/session.py:31`).
- Configuration problems return explicit `CONFIGURATION_ERROR: …` strings with remediation instructions (`configuration_error_for()`, `backend/app/core/config.py:61`).

### Honesty/Truthfulness Invariants
- Every AI output carries `model_metadata` (provider/model/fallback reason/`reasoning_available`).
- Synthetic data always flagged (`is_synthetic`, `data_mode="synthetic"`); provenance columns mandatory on signals.
- UTC everywhere via shared `utc_now()` helper.

## TypeScript/React (Frontend)

### Style & Typing
- `"strict": true`; no ESM `any` leakage tolerated by review; ESLint 10 flat config (`frontend/eslint.config.mjs`) with next/core-web-vitals rules; zero-warning policy enforced by CI gates. Legacy `frontend/src/` is lint-ignored.
- Path alias `@/*` → frontend root (`@/types/api`, `@/lib/...`).
- Typed API client: every endpoint has a typed wrapper in `frontend/lib/api.ts` returning generated types from `frontend/types/api.ts` — components never call raw `fetch`.
- DTO→view transformation isolated in `frontend/lib/mappers.ts`; error normalization in `ApiError` (`frontend/lib/errors.ts`).
- Components: PascalCase files, one component per file, domain-folder organization (`components/<domain>/`), shadcn/ui primitives under `components/ui/`.

### Styling Rules (hard gate)
- `scripts/check-banned-classes.mjs` bans Tailwind `slate-*` palette classes and arbitrary hex values (`bg-[#...]`) in all `.tsx` except the root shell `metaradar.tsx`. Canonical theme tokens only (`components/theme/`).
- `cn()` utility (`clsx` + `tailwind-merge`) for class composition; CVA for variants.

## Cross-Cutting

- **Contract-first**: backend schema change → `python scripts/export_openapi.py` → committed regenerated `frontend/types/api.ts`. Drift fails CI (`tests/test_contract_drift.py`).
- **Commits**: conventional-commit scopes referencing areas, e.g. `fix(provenance,scoring,brand): ...`, `chore(brand): ...` (see git log). Feature branches only (`feature/*`, `fix/*`), never direct-to-main.
- **No comments unless essential**; docstrings reserved for contracts/invariants.
- **Config**: all tunables through `Settings` env vars or `config/haemophilia.yaml` — no magic numbers scattered in nodes; versioned pins (`scoring_config_version`, `prompt_version`, `embedding_model_version`).

---

*Mapped as part of full-repo codebase analysis: 2026-08-22*
