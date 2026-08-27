---
phase: 11-productionization
plan: 11-02
subsystem: rbac-fsm-escalation
tags: [rbac, fsm, state-machine, escalation, audit-log, immutability, postgresql-trigger]
requires:
  - phase: 11-productionization
    plan: 11-01
    provides: User and Session models, Auth service, and get_current_user / get_optional_user dependencies
provides:
  - Migration 014 (AuditLog user_id, correlation_id, and PostgreSQL DB-level trigger trg_block_audit_log_update_delete)
  - SQLAlchemy ORM before_update and before_delete immutable event listeners on AuditLog
  - Server-side FSM state machine validation (validate_state_transition) with terminal ACTIONED lock (409 Conflict)
  - RBAC role scoping on GET /signals and role isolation on GET /signals/queue/{function_id}
  - Transition guard on ACTIONED status restricted to SAFETY, MARKET_ACCESS, LEADERSHIP, ADMIN (403 Forbidden)
  - Bidirectional Escalation & Resolution lifecycle engine with immutable audit telemetry
  - 100% passing test suites in tests/test_rbac.py and tests/test_review_state_machine.py
affects: [backend, database, migrations, rbac, signals, fsm, security]
key-files:
  created:
    - backend/alembic/versions/014_auditlog_user_correlation.py
    - tests/test_rbac.py
    - tests/test_review_state_machine.py
  modified:
    - backend/app/models/__init__.py
    - backend/app/schemas/__init__.py
    - backend/app/api/v1/endpoints/signals.py
    - tests/conftest.py
---

# Plan 11-02 Summary: Server-Side RBAC, FSM & Escalation Lifecycle Engine

## Executed Work
1. **Migration 014 (`backend/alembic/versions/014_auditlog_user_correlation.py`)**:
   - Added `user_id` (UUID foreign key to `users.user_id`) and `correlation_id` (VARCHAR(36)) to `audit_log` with B-tree indexes.
   - Installed PostgreSQL DB-level trigger `trg_block_audit_log_update_delete` executing `block_audit_log_mutation()` to reject any raw SQL `UPDATE` or `DELETE` statements on `audit_log`.

2. **AuditLog Immutability Enforcement (`backend/app/models/__init__.py`)**:
   - Updated `AuditLog` ORM model with `user_id` and `correlation_id`.
   - Attached SQLAlchemy `before_update` and `before_delete` event hooks raising `PermissionError` on any ORM modification.

3. **FSM State Machine Engine (`backend/app/api/v1/endpoints/signals.py`)**:
   - Implemented `VALID_TRANSITIONS` graph:
     - `UNREVIEWED` → `IN_REVIEW`, `DISMISSED`
     - `IN_REVIEW` → `REVIEWED`, `ACTION_REQUIRED`, `DISMISSED`
     - `REVIEWED` → `ACTION_REQUIRED`, `ACTIONED`
     - `ACTION_REQUIRED` → `ACTIONED`, `IN_REVIEW`
     - `DISMISSED` → `IN_REVIEW`
     - `ACTIONED` → `set()` (strictly terminal)
   - Implemented `validate_state_transition` asserting:
     - Terminal state lock on `ACTIONED` returns `409 Conflict`.
     - Escalation is only valid targeting `REVIEWED` or `ACTION_REQUIRED` (`409 Conflict` otherwise).
     - Target status `ACTIONED` restricted to `SAFETY`, `MARKET_ACCESS`, `LEADERSHIP`, and `ADMIN` (`403 Forbidden` otherwise).
     - Non-terminal override supported for `LEADERSHIP` and `ADMIN` with `is_override=True`.

4. **RBAC Scoping & Queue Isolation**:
   - `GET /signals`: Automatically scopes queries to `Signal.relevant_function == current_user.role` for non-leadership users. Only `LEADERSHIP` and `ADMIN` can pass `all_functions=true` (non-leadership returns `403 Forbidden`).
   - `GET /signals/queue/{function_id}`: Restricts access to user's matching role or `LEADERSHIP`/`ADMIN` (`403 Forbidden` otherwise). Returns unreviewed and in-review signals for that function.
   - `POST /signals/{signal_id}/review`: Validates FSM transition, updates `reviewed_by = user.display_name`, handles `escalate: true` (setting `is_escalated = true` and logging `SIGNAL_ESCALATED`), handles `resolve_escalation: true` (clearing `is_escalated` and logging `ESCALATION_RESOLVED`), and records immutable `SIGNAL_REVIEWED` audit log with `user_id` and `correlation_id`.

5. **Automated Verification**:
   - 8 tests in `tests/test_rbac.py` passed.
   - 8 tests in `tests/test_review_state_machine.py` passed.
   - Combined 16 tests in Wave 1 and Wave 2 pass with 100% success.
