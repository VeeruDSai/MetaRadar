---
doc_type: codebase-map
focus: concerns
analysis_date: 2026-08-22
---

# Concerns & Technical Debt

**Analysis Date:** 2026-08-22

## Documentation Drift (High — user-facing)

- `README.md` is badly stale vs reality: claims "Next.js 15" (actual: **Next.js 16.3.0**, `frontend/package.json:22`), "51/51 tests passing / Phase 2 completed" (actual: 114 passed/1 skipped, Phase 8 complete per `.planning/STATE.md`), and "repository currently contains planning documents only (no code yet)" (`README.md:726`). Any new stakeholder or agent reading README first gets a wrong mental model.
- README tech-stack table says Python 3.11 + APScheduler/httpx scheduler; requirements.txt has no APScheduler — scheduling lives in `start.py`/connector cursors. Reconcile.

## Dead / Legacy Code (Medium)

- `frontend/src/` — stale duplicate containing old `app/sources/page.tsx` and an outdated generated `types/api.ts`. It is lint-ignored and excluded from the canonical contract; risk of an agent/human editing the wrong file. Candidate for deletion.
- `frontend/app/[section]/` — empty directory scaffold; unused routing leftover.
- `tests/test_foundation.py` — script-style (`asyncio.run(run_tests())` with prints); pytest collects **zero** tests from it despite its name, so its coverage silently vanished from suite counts. Convert to real pytest functions or move to `scripts/`.

## Test Brittleness (Medium)

- Endpoint tests rely on ordered `mock_db.execute.side_effect` queues (`tests/test_api_endpoints.py:66`) — adding any query to an endpoint shifts the queue and breaks tests with confusing failures. Consider result-shape-based stubbing or a lightweight test DB.
- Mixed test styles across files (`@pytest.mark.asyncio` present even though `asyncio_mode=auto`).
- Frontend has no unit/integration tests at all; UI regressions only caught by TSC/lint/build.

## Dependency Hygiene (Low–Medium)

- `backend/requirements.txt` mixes runtime and test dependencies in one unpinned floor-range file (all `>=`). No lockfile → non-reproducible builds; Docker builds may drift between machines.
- Both `pnpm-lock.yaml` AND a tracked `frontend/package-lock.json` exist — npm lockfile can go stale and mislead contributors; pick one package manager artifact.

## Security Notes (acceptable for prototype, flag for production)

- No authentication/authorization anywhere in the API — every endpoint (including `POST /cache/clear`, pipeline triggers) is open. Fine for hackathon demo; blocker for anything beyond localhost.
- CORS uses `allow_credentials=True` with wildcard methods/headers (`backend/app/main.py:60-67`); origins are restricted but method/header wildcards are broader than needed.
- Dev credentials (`metaradar/metaradar_pass`) are hard-coded defaults in `docker-compose.yml` and `config.py` fallbacks — documented dev-only posture; ensure it never reaches a shared environment.
- `.env` correctly gitignored and untracked (verified). `.env.example` contains no secrets. Good.
- Grok privacy gate exists and is tested (`test_privacy_boundary.py`), but it is opt-in (`ENABLE_GROK_FALLBACK=false`) — keep default off.

## Fragile Areas (handle with care when refactoring)

- `backend/app/models/__init__.py` — all 20 tables in one 381-line module; migrations 001–006 must stay in sync with it manually.
- `MetaRadarState` channel reducers (`backend/app/workflows/state.py`) — the `replace_list` reducer exists specifically because naive `operator.add` duplicated signals; changing node return shapes risks reintroducing duplication bugs.
- Provider chain ordering assumptions in `backend/app/providers/factory.py` (capability support + privacy gate + fallback reason recording) — heavily covered by truthfulness tests; don't reorder casually.
- Contract sync chain: forgetting `python scripts/export_openapi.py` after schema edits fails CI via drift test — always regenerate before committing backend changes.

## Performance Watch Items

- Embedding backfill service (`embeddings_backfill.py`) and HNSW queries are untested under load; vector index build cost unknown on large signal volumes.
- `start.py` auto-applies Alembic migrations on boot — convenient locally, risky pattern if ever used beyond dev.

---

*Mapped as part of full-repo codebase analysis: 2026-08-22*
