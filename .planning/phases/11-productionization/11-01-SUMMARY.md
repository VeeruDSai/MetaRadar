---
phase: 11-productionization
plan: 11-01
subsystem: identity-and-auth
tags: [auth, identity, sessions, bcrypt, sha256, dual-timeout, rbac, csrf]
requires:
  - phase: 10-demo-journey-evidence-convergence-ux
    provides: Hardened demo journey and 8 active connectors
provides:
  - Migration 013 (users and sessions tables with UUID primary keys and indices)
  - SQLAlchemy User and Session models in app/models/auth.py
  - Cryptographic security utilities in app/core/security.py (bcrypt, token hashing, session signing, HMAC-SHA256 CSRF)
  - AuthService managing demo personas, password auth, session creation, and dual-timeout verification
  - Auth REST API endpoints (/auth/login, /auth/demo-login, /auth/logout, /auth/me, /auth/csrf)
  - Mandatory get_current_user and optional get_optional_user FastAPI dependencies
  - 100% passing test suite in tests/test_auth.py
affects: [backend, database, migrations, auth, security, api]
key-files:
  created:
    - backend/alembic/versions/013_auth_user_role_session.py
    - backend/app/models/auth.py
    - backend/app/core/security.py
    - backend/app/services/auth_service.py
    - backend/app/schemas/auth.py
    - backend/app/api/v1/endpoints/auth.py
    - tests/test_auth.py
    - tests/conftest.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/schemas/__init__.py
    - backend/app/core/config.py
    - backend/app/core/middleware.py
    - backend/app/api/deps.py
    - backend/app/main.py
---

# Plan 11-01 Summary: Identity, Dual-Timeout Sessions & Auth Endpoints

## Executed Work
1. **Migration 013 (`backend/alembic/versions/013_auth_user_role_session.py`)**:
   - Created `users` table with UUID primary key, indexed `email` and `role`, bcrypt `hashed_password`, and `is_active`.
   - Created `sessions` table with UUID primary key, indexed foreign key to `users`, indexed `token_hash = sha256(token)`, `last_activity_at`, `expires_at`, and `is_revoked`.
   - Executed and verified via `alembic upgrade head`.

2. **Domain Models & Schemas**:
   - Implemented `User` and `Session` SQLAlchemy models in `backend/app/models/auth.py` and exported them in `backend/app/models/__init__.py`.
   - Implemented Pydantic v2 `ConfigDict` schemas in `backend/app/schemas/auth.py` (`LoginRequest`, `DemoLoginRequest`, `UserMe`, `CsrfResponse`, `LogoutResponse`).

3. **Core Security (`backend/app/core/security.py`)**:
   - Bcrypt password hashing (`hash_password`, `verify_password`).
   - Deterministic SHA-256 token hashing (`hash_token`) for database lookup without storing plaintext tokens.
   - Timestamp-signed session cookie generation and verification (`sign_session_token`, `unsign_session_token`).
   - Session-bound HMAC-SHA256 CSRF token creation and verification (`generate_session_bound_csrf`, `verify_session_bound_csrf`).

4. **Auth Service & Startup Seeding (`backend/app/services/auth_service.py`)**:
   - `seed_demo_users_if_needed`: Seeds standard stakeholder personas (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`, `LEADERSHIP`, `ADMIN`) with non-deterministic runtime password fallback.
   - `get_session_user`: Enforces dual session timeout (8-hour absolute maximum lifetime and 1-hour idle inactivity timeout) and updates `last_activity_at` upon each authenticated request.
   - `invalidate_session`: Revokes active sessions in the database upon logout.

5. **FastAPI Endpoints & Dependencies**:
   - Added `POST /api/v1/auth/login`, `POST /api/v1/auth/demo-login`, `POST /api/v1/auth/logout`, `GET /api/v1/auth/me`, and `GET /api/v1/auth/csrf` in `backend/app/api/v1/endpoints/auth.py`.
   - Implemented `get_current_user`, `get_optional_user`, `require_preauth_origin`, and `auth_rate_limit` in `backend/app/api/deps.py`.
   - Added `SecurityHeadersMiddleware` and updated `CorrelationIdMiddleware` in `backend/app/core/middleware.py`.

6. **Automated Verification**:
   - All 8 tests in `tests/test_auth.py` pass cleanly with zero failures.
