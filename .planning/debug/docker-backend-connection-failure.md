# Debug Session: Workspace Connection Failure & Docker Launcher Startup

**Slug:** `docker-backend-connection-failure`
**Status:** `RESOLVED`
**Trigger:** `python start.py` resulted in Docker daemon pipe failure, degraded mode banner, and "Workspace Connection Failure" in UI.

## Symptoms
- **Expected:** `python start.py` starts PostgreSQL, Redis, FastAPI backend (8000), and Next.js frontend (3000) cleanly with live data.
- **Actual:**
  - Docker compose emitted pipe error: `open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`.
  - Backend started while PostgreSQL/Redis were not ready.
  - When Next.js queried `/api/v1/overview` and `/api/v1/signals`, FastAPI returned HTTP 500 (`ConnectionRefusedError` connecting to PostgreSQL on port 5432).
  - Frontend caught HTTP 500 and showed "Workspace Connection Failure: Could not connect to backend service at http://localhost:8000/api/v1".
  - Frontend banner showed Redis cache degraded mode (`Error 22 connecting to localhost:6379`).

## Root Cause Analysis
1. **Docker Daemon Startup Race Condition in `start.py`**:
   `start.py` invoked `docker compose up -d postgres redis` without checking Docker daemon readiness or waiting for Postgres (port 5432) and Redis (port 6379) to accept TCP connections before launching FastAPI and Next.js.
2. **Missing Alembic Schema Migrations**:
   Models `Contradiction` (`contradictions`), `CalibrationHistory` (`calibration_history`), `ScoringWeights` (`scoring_weights`), `LifecycleEvent.source_id`, and `Signal.model_metadata` existed in `app.models` but were missing from Alembic migrations, causing relation/column errors upon DB access and seeding.
3. **`backend/app/db/seed.py` Deficiencies**:
   - Imported non-existent `async_session_factory` instead of `AsyncSessionLocal`.
   - Missing `await session.flush()` after `Source` and `Company` insertions before inserting foreign-key dependent `Asset` objects.
   - Unhandled non-ASCII Unicode emojis in stdout caused `UnicodeEncodeError` on Windows (cp1252 terminal).

## Key Changes
1. **`backend/app/db/session.py`**:
   - Added `async_session_factory = AsyncSessionLocal` backward-compatible export.
2. **`backend/alembic/versions/003_contradictions_scoring.py`**:
   - Created migration adding `contradictions`, `calibration_history`, `scoring_weights`, `lifecycle_events.source_id`, and `signals.model_metadata`.
   - Successfully migrated schema with `alembic upgrade head`.
3. **`backend/app/db/seed.py`**:
   - Configured `sys.stdout.reconfigure(encoding='utf-8')` for Windows environments.
   - Fixed foreign key flush sequence and seeded reference and landscape data.
4. **`start.py`**:
   - Added `wait_for_backing_service` with TCP socket polling to guarantee PostgreSQL (port 5432) and Redis (port 6379) are online and accepting traffic before backend and frontend launch.

## Verification
- `pytest`: 80 passed, 1 skipped in 31.50s.
- `npx tsc --noEmit` in `frontend/`: 0 errors.
- `python -m alembic upgrade head`: Applied cleanly.
- `python -m app.db.seed`: [SUCCESS] Database seeding complete.
- Socket checks on `127.0.0.1:5432` and `127.0.0.1:6379`: Connected successfully.
