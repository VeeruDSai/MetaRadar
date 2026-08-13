# Testing

**Analysis Date:** 2026-08-13

> **Status:** Backend testing is unchanged since the previous map — exactly **one test file**, `tests/test_foundation.py` (70 lines), plus one CI workflow (`.github/workflows/ci.yml`) that runs it; verified **passing** locally on 2026-08-13. The frontend has grown from a skeleton into a **full mock-driven Next.js app with zero test tooling**: no vitest/jest, no `test` script, no component tests, no frontend CI job, and the declared `lint` script is non-functional as committed. The declared strategy (Master Plan §10, SDD, `docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md`) — pytest + pytest-asyncio + pytest-cov ≥60% coverage, EV-1…EV-20 evaluations — remains unimplemented.

## Test Framework & Setup

**Runner:**
- **Backend: none formal.** Tests are a plain Python script — no pytest collection, no `conftest.py`, no `pytest.ini`/`pyproject.toml`/`setup.cfg`, no `Makefile`. pytest 9.0.3 is installed in the local env but is **absent from `backend/requirements.txt`**, so CI cannot run pytest even if a suite were added.
- **Frontend: none.** No vitest/jest/playwright, no `test` script in `frontend/package.json` (only `dev`, `build`, `start`, `lint`), no test files, no testing deps in `devDependencies`.
- No coverage tooling anywhere: no `pytest-cov`, no `.coverage`, no coverage config.

**Structure of the existing test** (`tests/test_foundation.py`):
- Plain functions + module-level `assert`, executed via `asyncio.run(run_tests())` under `if __name__ == "__main__":`.
- Bootstraps imports with `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))` (`test_foundation.py:7-9`) — the test lives at repo root while the package is `backend/app`.
- Print-based progress (`[PASS] ...`) ending with `=== ALL FOUNDATION VERIFICATION TESTS PASSED ===`; non-zero exit only if an assert throws.

## What is covered (per layer/component)

### Foundation verification script (`tests/test_foundation.py`)

| # | Component | What is asserted | Status |
|---|---|---|---|
| 1 | `app.core.domain_config.get_domain_config` | loads real `config/haemophilia.yaml`; `domain_config_version == "v5.1.0"`; ≥7 assets; `minimum_independent_signals == 3`; `emerging_threshold == 2` | ✅ passing |
| 2 | `app.services.deduplication.generate_fingerprint` | pmid input yields deterministic `"pmid:12345678"` | ✅ passing |
| 2 | `app.services.deduplication.chunk_text_for_embedding` | 2000-char input fits ≤ `max_tokens * 4` (256-token budget) | ✅ passing |
| 3 | `app.providers.factory.provider_factory.execute_task` | REASON capability routes to `local_gemma`; `model_metadata.provider == "local_gemma"`, `reasoning_available=True` | ✅ passing |
| 3 | `app.providers.degraded.DegradedProvider.generate_intelligence` | `mode == "degraded_factual"`; `reasoning_available=False`; `actions_available=False` | ✅ passing |

**Layer breakdown of actual coverage:**
- **Config/domain layer:** domain-config loader only. `core/config.py` settings object untested.
- **Services layer:** only the two pure functions in `deduplication.py`. `upsert_signal` (DB upsert) and `RedTeamNLIService` (`services/redteam.py`) are **untested**.
- **Providers layer:** fallback chain happy path (Gemma) and last resort (degraded BART). **Grok leg, privacy gate (`grok.validate_privacy_gate`), mid-chain fallback (Gemma fails → Grok → BART), and the `PermissionError` path are untested** — no failure injection exists.
- **DB/session layer:** `get_db`, `try_advisory_lock`, `release_advisory_lock`, engine creation — untested (would need live PostgreSQL).
- **Models layer:** no test asserts ORM models (`models/__init__.py`) match the Alembic migration (`backend/alembic/versions/001_initial_v51_schema.py`) or that the migration applies.
- **API layer:** all `/api/v1/health/*` endpoints (`backend/app/api/v1/endpoints/health.py`) and `main.py` are **untested** — no FastAPI TestClient anywhere.
- **Connectors layer:** `connectors/base.py` has no concrete connectors; none tested.
- **Frontend:** **zero tests** — no vitest/jest, no component/render tests, no E2E. The only frontend "check" is the OpenAPI contract-sync step in CI (below).

## Fixtures & Mocking strategy

- **Input data:** the only fixture is the real `config/haemophilia.yaml` loaded through `get_domain_config()` (`test_foundation.py:22-28`). No fixture factories, no `conftest.py`, no synthetic-signal corpus fixtures (the declared 500-signal `data/synthetic/` set does not exist).
- **Mocking:** none used (`unittest.mock`, pytest-mock absent). The providers are *simulated implementations* — `GemmaProvider.generate_intelligence` returns canned strings (`providers/gemma.py:53-58`), `DegradedProvider` truncates text — so tests verify plumbing and capability metadata, not model behavior. This is implicit mocking without explicit mocks, and it gives **false confidence**: the same canned code paths pass regardless of real inference availability.
- **No live external calls** (no network, redis, or postgres) are needed for the test to pass.
- **Frontend mock layer:** `frontend/lib/mock-data.ts` ships 4 signals, 4 sources, confluence/lifecycle/trends/health fixtures; `frontend/lib/api.ts` wraps them in a `delay()` promise. This is demo data, not test fixtures — nothing asserts over it.

## Running tests (commands)

```bash
python tests/test_foundation.py              # The only test entry today — verified PASSING 2026-08-13

# Declared/planned (from docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md, SDD) — not operational:
# pytest tests/ -v --cov=services
# pytest tests/ -v --cov=services --cov-report=html
```

No `Makefile`, no `npm test`, no `scripts/test*`. The frontend has no test script; the declared `lint` script cannot run as committed (see below).

## Frontend testing status

- **Framework:** none installed — `frontend/package.json` `devDependencies` contain only `eslint`, `eslint-config-next`, `typescript`, `tailwindcss`, `postcss`, `@types/*`. No vitest/jest/testing-library, no `test` script.
- **What would need testing (and isn't):**
  - `components/metaradar.tsx` (16 KB, ~60 lines of dense JSX) — the entire UI: `Shell` nav/theme toggle, `DashboardPage` KPI/bento grid, `SignalsPage` filtering + drawer, `IntelligencePage` prompt/answer flow. All client-side logic (filtering with `useMemo`, async `getOverview().then(setData)`, drawer open/close, theme class toggling) is untested.
  - `lib/api.ts` / `lib/mock-data.ts` — data-shape contract between types and components.
  - `app/[section]/page.tsx` — route dispatch and the `pages` map fallback.
- **Runnable state:** `node_modules` is **not installed** in the workspace, so even `pnpm dev`/`build`/`lint` cannot run without `pnpm install` (lockfile `frontend/pnpm-lock.yaml` is committed, so install is deterministic).
- **`next build` type-safety:** `frontend/next.config.mjs` sets `typescript.ignoreBuildErrors: true` — even a successful build would **not** type-check the app. The strict `tsconfig.json` only bites when `npx tsc --noEmit` is run manually (never in CI).

## Lint / Typecheck status

- **Frontend lint — broken as committed:** `frontend/package.json` declares `"lint": "eslint ."` with `eslint ^10.8.1` + `eslint-config-next ^16.3.0`, but **no `eslint.config.mjs` (or `.eslintrc*`) exists anywhere**. ESLint 10 is flat-config-only; `eslint .` errors out with "could not find config". The `lint` script is dead until a config is added.
- **Frontend typecheck — not run anywhere:** `npx tsc --noEmit` is the only way to enforce `strict: true`; not scripted, not in CI, and bypassed at build time by `ignoreBuildErrors: true`. Spot check: the codebase has a duplicated type tree (`types/api.ts` vs `src/types/api.ts`) with divergent field conventions; only the stale `src/` tree is guarded by CI.
- **Backend:** no linter or formatter configured (no ruff/black/flake8/pyproject); no type checker (mypy/pyright) configured; CI runs neither.

## CI integration

**File:** `.github/workflows/ci.yml` — `MetaRadar v5.1 CI`.

- **Triggers:** push / pull_request to `main` and `develop`.
- **Steps:**
  1. `actions/checkout@v4`
  2. `actions/setup-python@v5` — **Python 3.11** (local env is 3.13)
  3. `pip install -r backend/requirements.txt` (no pytest)
  4. `python tests/test_foundation.py` — the foundation script
  5. `python scripts/export_openapi.py && git diff --exit-code frontend/src/types/api.ts` — contract-sync guard
- **No frontend CI whatsoever:** no `pnpm install`, no `next build`, no `eslint`, no `tsc --noEmit`, no frontend tests. The frontend could be pushed in a broken, uncompilable state and CI would stay green.
- **Quirks:**
  - The contract check compares regenerated output against the committed file, but `scripts/export_openapi.py:30-135` emits a **hardcoded TS template string** (not derived from `app.openapi()`), so it proves determinism, not schema truth — `contracts/openapi.json` (which *is* derived) can drift from the TS types unnoticed.
  - The guarded file (`frontend/src/types/api.ts`) is **not imported by the running app** (which uses hand-written `frontend/types/api.ts`), so the gate protects a contract nobody consumes.
  - No `frontend/src/types/api.ts` sync check failure is possible today in a *new* tree state; the file exists and is committed as part of the next commit, after which the guard is live.
  - `backend-gpu`/`frontend` docker-compose services reference Dockerfiles that **do not exist** — no container-level CI/build verification exists for them.

## Coverage status

- **Measured coverage: none.** No coverage tool installed or run (local or CI).
- **Structural coverage (lines exercised by `tests/test_foundation.py`):** `core/domain_config.py` (loader path), `services/deduplication.py` (2 pure functions), `providers/base.py` (enums+base), `providers/factory.py` (happy path), `providers/gemma.py` + `providers/degraded.py` (simulated paths), `config/haemophilia.yaml`. All other backend modules (`models/*` 259 lines, `schemas/*` 146 lines, `api/*`, `db/session.py`, `providers/grok.py`, `services/redteam.py`, `connectors/base.py`, `main.py`) are exercised only by import, if at all.
- **Frontend coverage: 0%** (no runner exists).
- **Declared targets (unmet):** >80% total; ≥60% on critical pipeline components; EV-1…EV-20 acceptance metrics (≥85% classification accuracy, 100% source-linked summaries, ≤5 min top-signal discovery, 0 confidential/patient data leaks, ≥10-point calibration uplift).

## Gaps / Risks

1. **No pytest adoption (High):** the declared strategy presumes pytest + pytest-asyncio + pytest-cov; today there is one script. pytest isn't even in `backend/requirements.txt`, so CI can't run it without a requirements change.
2. **API layer untested (High):** health endpoints are the only public surface — no TestClient, no response-model verification. A regression in `health.py`/`main.py` is invisible.
3. **Frontend entirely untested + CI-absent (High):** no test framework, no frontend CI job, `next build` never exercised, and type errors are explicitly suppressed via `ignoreBuildErrors: true`. The most user-visible artifact of the product has zero automated verification.
4. **`lint` script broken (High):** `eslint .` cannot run without an `eslint.config.mjs`; combined with no prettier, the two divergent formatting dialects (v0 single-quote style in `app/` vs double-quote/semicolon in `src/`) will persist unchecked.
5. **Contract sync guards the wrong artifact (Medium):** TS template is hardcoded in `scripts/export_openapi.py` and the generated file is unused by the app; real API-integration bugs (snake_case ↔ camelCase drift between `backend/app/schemas/__init__.py` and `frontend/types/api.ts`) are undetectable until the mock layer is replaced.
6. **Provider fallback chain partially tested (Medium):** privacy gate, Grok leg, Gemma-failure fallthrough, and `PermissionError` are untested — Master Plan EV-19/EV-20 failure-injection scenarios cannot pass as-is.
7. **DB/migration untested (High):** no test applies the Alembic migration against PostgreSQL+pgvector or verifies model/migration parity; missing `alembic.ini`/`env.py` blocks even manual verification.
8. **Simulated providers give false confidence (Medium):** tests assert wiring of canned implementations; real Gemma/embedding load failures are never exercised.
9. **No negative/edge-case tests (Medium):** dedup covers only the pmid branch; `nct:`/`reg:`/`hash:` branches and the 256-token boundary are untested; empty-input chunking untested; frontend empty/error states (`Loading`, drawer, no-answer) untested.
10. **Env drift (Low):** CI pins Python 3.11 while local is 3.13; `datetime.utcnow` deprecation warns on 3.12+; frontend uses Next 16 while docs/CI narrative says Next 15.

---

*Testing analysis: 2026-08-13*
