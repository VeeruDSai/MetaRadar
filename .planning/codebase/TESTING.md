# Testing

**Analysis Date:** 2026-08-13

> **Status:** Testing infrastructure is minimal. There is exactly **one test file** — `tests/test_foundation.py` (70 lines) — and one CI workflow (`.github/workflows/ci.yml`) that runs it. The declared testing strategy (Master Plan §10, `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md`, SDD §testing) describes a pytest + pytest-asyncio + pytest-cov suite in `backend/tests/` with ≥60% critical-path coverage and a set of acceptance evaluations (EV-1…EV-20). **None of that suite exists yet.** This document describes what actually runs, what it covers, and the gap.

## Test Framework & Setup

**Runner:**
- **None formal.** Tests are a plain Python script — no pytest collection, no `conftest.py`, no `pytest.ini`/`pyproject.toml`/`setup.cfg`, no `Makefile`.
- pytest 9.0.3 is installed in the local dev environment but is **absent from `backend/requirements.txt`** — the CI job installs only `requirements.txt`, so pytest cannot run in CI even if a suite were added.
- No coverage tooling: no `pytest-cov`, no `.coverage`, no `coverage.py` in dependencies.

**Structure of the existing test** (`tests/test_foundation.py`):
- Plain functions + module-level `assert`, executed via `asyncio.run(run_tests())` under `if __name__ == "__main__":`.
- Bootstraps imports with `sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))` (`test_foundation.py:7-9`) — because the test lives at the repo root while the package is `backend/app`.
- Output is print-based progress markers (`[PASS] ...`) ending with `=== ALL FOUNDATION VERIFICATION TESTS PASSED ===`. Exit code is non-zero only if an assert throws.

**Run Command (the only way to run tests today):**
```bash
python tests/test_foundation.py
```
Verified passing on 2026-08-13 (local env):

```
1. Testing DomainConfig loader...          [PASS]
2. Testing Deduplication & Chunking...     [PASS]
3. Testing Provider Execution & Capability Matrix... [PASS] x2
=== ALL FOUNDATION VERIFICATION TESTS PASSED ===
```

## What is covered (per layer/component)

### Foundation verification script (`tests/test_foundation.py`)

| # | Component | What is asserted | Status |
|---|---|---|---|
| 1 | `app.core.domain_config.get_domain_config` | loads `config/haemophilia.yaml`; `domain_config_version == "v5.1.0"`; ≥7 assets; `confluence.minimum_independent_signals == 3`; `emerging_threshold == 2` | ✅ passing |
| 2 | `app.services.deduplication.generate_fingerprint` | pmid input yields deterministic `"pmid:12345678"` fingerprint | ✅ passing |
| 2 | `app.services.deduplication.chunk_text_for_embedding` | 2000-char input chunks to ≤ `max_tokens * 4` (256-token budget) | ✅ passing |
| 3 | `app.providers.factory.provider_factory.execute_task` | REASON capability routes to `local_gemma`; returns `model_metadata` with `reasoning_available=True` | ✅ passing |
| 3 | `app.providers.degraded.DegradedProvider.generate_intelligence` | `mode == "degraded_factual"`; `reasoning_available=False`; `actions_available=False` | ✅ passing |

**Layer breakdown of actual coverage:**
- **Config/domain layer:** domain config loader only. `core/config.py` settings object is untested.
- **Services layer:** only the two pure functions in `deduplication.py`. `upsert_signal` (DB upsert) and `RedTeamNLIService` (`services/redteam.py`) are **untested**.
- **Providers layer:** the fallback *chain's happy path* (Gemma) and last-resort (degraded BART). The **Grok leg, the privacy gate (`grok.validate_privacy_gate`), and the mid-chain fallback behavior (Gemma fails → Grok → BART) are untested** — failure injection doesn't exist.
- **DB/session layer:** `get_db`, `try_advisory_lock`, `release_advisory_lock`, engine creation — untested (would need a live PostgreSQL).
- **Models layer:** no test asserts that ORM models (`models/__init__.py`) match the Alembic migration (`alembic/versions/001_initial_v51_schema.py`), nor that the migration applies.
- **API layer:** the three `/api/v1/health/*` endpoints (`api/v1/endpoints/health.py`) are **untested** — no TestClient, no pytest.
- **Connectors layer:** `connectors/base.py` has no concrete connectors yet, so none tested.
- **Frontend:** **zero test tooling** — no vitest/jest, no `test` script in `frontend/package.json`, no component/unit tests. The only frontend "check" is the OpenAPI contract-sync job in CI.

## Fixtures & Mocking strategy

- **Input data:** the only fixture is the real `config/haemophilia.yaml` loaded through `get_domain_config()` (`test_foundation.py:22-28`). No fixture factories, no `conftest.py`, no synthetic-signal fixtures (the prescribed 500-signal synthetic corpus in `data/synthetic/` does not exist yet).
- **Mocking:** none used. No `unittest.mock`, no pytest-mock. The providers are *simulated implementations* (Gemma returns canned `what_changed/why_it_matters` strings; DegradedProvider truncates text) rather than real inference — so the test verifies plumbing and capability metadata, not model behavior. This is implicit mocking without explicit mocks.
- **No live external calls** are made by the test (no network, no redis, no postgres needed to pass).
- **Declared-but-absent mocking targets** (from Master Plan/SRS, to be added later): mock `httpx` responses for connector tests; mock stakeholder feedback for calibration; failure-injection for the provider fallback chain (EV-19) and privacy gate (EV-20).

## Running tests (commands)

```bash
python tests/test_foundation.py              # The only test entry today — runs the foundation script

# Declared/planned (from docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md) — not yet operational:
# pytest tests/ -v --cov=services
# pytest tests/ -v --cov=services --cov-report=html
```

No `Makefile`, no `npm test`, no `scripts/test*` exist. Frontend has no test script (`frontend/package.json` defines only `dev`, `build`, `start`, `lint`).

## CI integration

**File:** `.github/workflows/ci.yml` — name `MetaRadar v5.1 CI`.

- **Triggers:** push / pull_request to `main` and `develop`.
- **Steps:**
  1. `actions/checkout@v4`
  2. `actions/setup-python@v5` with **Python 3.11**
  3. `pip install -r backend/requirements.txt`
  4. `python tests/test_foundation.py` — runs the foundation script
  5. `python scripts/export_openapi.py && git diff --exit-code frontend/src/types/api.ts` — contract-sync guard: fails the build if regenerated TS differs from the committed file.
- **No CI for the frontend** — no `npm ci`, no `next build`, no `npm run lint`, no frontend tests.
- **Quirks:**
  - The contract check compares regenerated output against the committed file, but `scripts/export_openapi.py:30-135` generates the TS from a **hardcoded template string** (not from `app.openapi()`), so the check can pass even if backend schemas drift from the TS contract unless someone also updates the hardcoded block. The JSON export (`contracts/openapi.json`) *is* derived from `app.openapi()`.
  - Because the implementation files are currently untracked in git, `git diff --exit-code` on a *new* file exits 0 — the sync guard silently no-ops until the first commit.
  - CI's `requirements.txt` has no `pytest`, so the ci.yml cannot be extended to run a pytest suite without a requirements update.

## Coverage status

- **Measured coverage: none.** No coverage tool is installed or run anywhere (local or CI).
- **Structural coverage (lines exercised by `tests/test_foundation.py`):** `core/domain_config.py` (loader path), `services/deduplication.py` (2 pure functions), `providers/base.py` (enums+base), `providers/factory.py` (happy path), `providers/degraded.py`, `providers/gemma.py` (simulated path), `config/haemophilia.yaml`. All other modules (`models/*` 259 lines, `schemas/*` 146 lines, `api/*`, `db/session.py`, `providers/grok.py`, `services/redteam.py`, `connectors/base.py`, `main.py`) are exercised only by import, if at all.
- **Declared targets (still unmet — to be demonstrated):** >80% total coverage overall; ≥60% unit+integration on critical pipeline components (ingestion, entity extraction, confluence, calibration, lifecycle, red-team, missing-signal, watch/routing); the five hackathon EV metrics (≥85% classification accuracy on the B.Pharm labelled set, 100% source-linked summaries, ≤5 min top-signal discovery, 0 confidential/patient data, ≥10-point calibration uplift).

## Gaps / Risks

1. **No pytest adoption (High):** the entire declared strategy presumes pytest + pytest-asyncio + pytest-cov; today there is exactly one script. Any new test must either adopt pytest (and add it to `requirements.txt` + CI) or follow the script pattern, which gives no fixtures, no parametrization, no async markers, no reporting, no coverage.
2. **API layer untested (High):** health endpoints exist and are the only public surface — no `TestClient` tests, no schema/response-model verification. A regression in `health.py` or `main.py` would not be caught.
3. **Provider fallback chain partially tested (Medium):** the privacy gate (`grok.py:25-39`), Grok leg, Gemma-failure fallthrough, and `PermissionError` path are untested. EV-19/EV-20 acceptance scenarios (10 failure-injection cases from the Master Plan) cannot pass as-is.
4. **DB/migration untested (High):** no test applies the Alembic migration against PostgreSQL+pgvector or verifies model/migration parity; `alembic.ini`/`env.py` missing means even manual verification is blocked.
5. **No contract-driven type verification (Medium):** the TS sync check compares against a hardcoded template in `export_openapi.py`, so it validates regenerated output is stable — not that TS types match the actual OpenAPI schema. `contracts/openapi.json` would drift unnoticed.
6. **Frontend testless and CI-absent (High):** no test framework, no frontend CI job, `next build` never exercised — and the skeleton lacks `tsconfig.json`/`next.config`, so any future build-based check would immediately fail.
7. **Tests use simulated providers (Medium risk of false confidence):** passing tests assert wiring of canned implementations. Real Gemma/embedding inference failure modes are untested and no degradation test validates actual model-load failures.
8. **No negative/edge-case tests:** dedup tests cover only the pmid branch; `nct:`/`reg:`/`hash:` branches and the 256-token boundary are untested. `chunk_text_for_embedding` short-circuits on empty input untested.
9. **CI/python-version drift (Low):** CI pins 3.11 while local artifacts indicate 3.13; `datetime.utcnow` deprecation warns on 3.12+.

---

*Testing analysis: 2026-08-13*