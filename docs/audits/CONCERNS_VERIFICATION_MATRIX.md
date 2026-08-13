# Concerns Verification Matrix (Strict Audited Baseline)
> Date: 2026-08-13
> Governance Standard: Strict Executable Evidence Classification (PASS, PARTIAL, FAIL, BLOCKED, NOT EXECUTED)

| ID | Concern Description | Claimed Fix / Status | Required Evidence | Verification Command | Result | Remaining Risk / Notes |
|---|---|---|---|---|---|---|
| **C1** | Core pipeline stubs | Synthetic endpoints + domain config loaded | Pydantic response, domain config loaded | `pytest tests/test_config.py` | PASS | Connector adapters to be wired to live external APIs in Phase 1 |
| **C2** | Simulated LLM provider chain | Degraded BART fallback + mock posture | Provider capability & degraded fallback tests | `pytest tests/test_provider_matrix.py` | PASS | Local GPU weight loading environment dependent |
| **C3** | Dockerfiles missing | Authored backend/Dockerfile & frontend/Dockerfile | Dockerfiles present & `docker compose config` zero warnings | `docker compose config` | CONFIGURED (Runtime: NOT EXECUTED) | Docker Desktop daemon not running on host machine |
| **C4** | Incomplete Alembic scaffold | Added alembic.ini, env.py, script.py.mako | Async Alembic environment scaffolded | `python -m alembic check` | BLOCKED | Local PostgreSQL daemon not running on port 5432 |
| **C5** | Health status fabricated | Real DB/Redis check & honest freshness | Honest health endpoints response | `pytest tests/test_api_endpoints.py` | PASS | None |
| **H1** | PII/PHI detection missing | Created PIIPHIScrubber & explicit classification | Scrubbing regex & classification unit test | `pytest tests/test_privacy_boundary.py` | PASS | Heuristic coverage to be expanded for custom formatting |
| **H2** | Fallback chain dead code | Verified Degraded BART fallback path (Cases A-F) | Execution metadata reasoning=False | `pytest tests/test_provider_matrix.py` | PASS | None |
| **H3** | Red-Team service mock | Implemented 19-rule registry (Rules A–S) with priority gating | Priority gating & candidate capping unit tests | `pytest tests/test_redteam_behavior.py` | PASS | Full NLI transformer execution CPU bound |
| **H4** | DB schema incomplete | Added model_metadata & missing ORM models | ORM schema instantiation & timezone datetimes | `pytest tests/test_config.py` | PASS | Database runtime migration execution BLOCKED until DB running |
| **H5** | API surface health only | Registered /signals, /overview, /athena endpoints | FastAPI router execution tests | `pytest tests/test_api_endpoints.py` | PASS | None |
| **H7** | Frontend mock-driven | Reconciled lib/api.ts with fallback seam | Next.js build compilation | `npx next build` | BUILD VERIFIED (Browser: PARTIAL) | API integration to be expanded when live signals endpoints connect |
| **H8** | Fixed Postgres/Redis creds | Environment-variable driven settings | Config default check | `pytest tests/test_config.py` | PASS | Dev credentials should be changed in production .env |
| **H9** | OpenAPI export drift | Automated TS export & contract drift test | Unified contract at `frontend/types/api.ts` with 0 diff | `pytest tests/test_contract_drift.py` | PASS | None |
| **H-FE1**| Duplicate frontend trees | Consolidated active tree under frontend/app | Next.js Turbopack build pass | `npx next build` | PASS | Legacy frontend/src/app code preserved until contract migration |
| **H-FE2**| Unverified frontend build | ESLint 10 flat config, strict TS, CI job | 0 TS errors, 0 lint errors, build exit code 0 | `npx tsc --noEmit && npx eslint . && npx next build` | PASS | None |
| **H-FE3**| Uncommitted frontend code | Committed all active frontend files | Clean git working tree on feature branch | `git status` | PASS | None |

---

### Verification Summary Classification
- **Total Concerns Evaluated**: 16
- **PASS (Executable Code Verified)**: 12
- **CONFIGURED (Runtime NOT EXECUTED - Docker daemon unavailable)**: 2 (C3, Docker stack)
- **BLOCKED (Runtime execution blocked - Postgres daemon unavailable)**: 2 (C4, Database migration runtime)
- **FAIL**: 0
