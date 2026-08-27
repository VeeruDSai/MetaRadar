# Phase 11 — Master Plan: MetaRadar Productionization (Revision 11.2)

**Phase:** Phase 11  
**Status:** Planned (Revision 11.2 — Execution-Ready)  
**Goal:** Deliver a complete, functional, role-enforced decision-intelligence platform with authenticated RBAC, an explicit review/escalation state machine, database-level append-only auditing, session-bound CSRF, verified pharma provenance, operational function workspaces, per-function calibration, and cross-functional E2E verification.  
**Requirements:** REQ-P11-01 … REQ-P11-48  
**Context & Decisions:** [11-CONTEXT.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/11-productionization/11-CONTEXT.md)

---

## 7-Wave Execution Map & Gates

```
Phase 11: MetaRadar Productionization (Rev 11.2)
├── Wave 1 [P0]: 11-01-PLAN.md — Identity, Dual-Timeout Sessions & Auth Endpoints
│                                  Gate: pytest tests/test_auth.py -v
├── Wave 2 [P0]: 11-02-PLAN.md — Server-Side RBAC, FSM & Escalation Lifecycle Engine
│                                  Gate: pytest tests/test_rbac.py tests/test_review_state_machine.py -v
├── Wave 3 [P0]: 11-03-PLAN.md — Full 8-Connector Pharma Provenance & Reachability
│                                  Gate: pytest tests/test_provenance_completeness.py tests/test_connector_health.py -v
├── Wave 4 [P1]: 11-04-PLAN.md — Operational Functions Workspace, Per-Function Calibration & Leadership
│                                  Gate: pytest tests/test_intelligence_nodes.py tests/test_calibration_service.py -v
├── Wave 5 [P1]: 11-05-PLAN.md — Frontend Auth Integration (apiFetch + CSRF + Demo Login)
│                                  Gate: cd frontend && npx tsc --noEmit && npm run build
├── Wave 6 [P2]: 11-06-PLAN.md — Security Hardening & DB-Level Audit Immutability
│                                  Gate: pytest tests/test_security.py -v
└── Wave 7:      11-07-PLAN.md — Complete 6-Function Vertical Slice E2E Verification
                                   Gate: python scripts/test_e2e_vertical_slice.py + pytest -v (0 failures)
```

---

## Final Verification Checklist

```bash
# 1. Database Migrations (013 + 014 with DB trigger)
alembic upgrade head

# 2. Automated Test Suites (All feature areas must pass with 0 failures)
cd backend && pytest -v

# 3. Dedicated Security Suite (Headers, Session-Bound CSRF, Rate Limiting, Trigger Immutability)
pytest tests/test_security.py -v

# 4. Cross-Functional 6-Function E2E Decision Verification
python scripts/test_e2e_vertical_slice.py

# 5. OpenAPI Contract & TypeScript Synchronicity
python scripts/export_openapi.py

# 6. Strict TypeScript Compilation
cd frontend && npx tsc --noEmit

# 7. Production Next.js 16 Build
npm --prefix frontend run build

# 8. Design System Token Governance Gate
node scripts/check-banned-classes.mjs
```

---

## Requirements Traceability (Revision 11.2)

| Req ID | Description | Wave | Priority |
|---|---|---|---|
| REQ-P11-01 | `users` table with role, display_name, bcrypt hash | 1 | P0 |
| REQ-P11-02 | `sessions` table storing `token_hash = sha256(token)` + `last_activity_at` | 1 | P0 |
| REQ-P11-03 | Dual session timeout: 8h absolute, 1h idle | 1 | P0 |
| REQ-P11-04 | `POST /auth/login` sets signed HttpOnly `metaradar_session` cookie | 1 | P0 |
| REQ-P11-05 | `POST /auth/demo-login` role selector active only when `DEMO_MODE=true` | 1 | P0 |
| REQ-P11-06 | `POST /auth/logout` invalidates session in DB and clears cookie | 1 | P0 |
| REQ-P11-07 | `GET /auth/me` returns current user identity from session | 1 | P0 |
| REQ-P11-08 | Mandatory `get_current_user` dependency (no silent unauthenticated bypass) | 1 | P0 |
| REQ-P11-09 | Non-deterministic demo credentials (random token if unset, never static) | 1 | P0 |
| REQ-P11-10 | `GET /signals` strictly filters by `relevant_function = user.role` | 2 | P0 |
| REQ-P11-11 | `?all_functions=true` restricted to `LEADERSHIP` and `ADMIN` (403 for others) | 2 | P0 |
| REQ-P11-12 | State transition guard returning 409 on invalid transition | 2 | P0 |
| REQ-P11-13 | Permission matrix returning 403 on unauthorized role action | 2 | P0 |
| REQ-P11-14 | `ACTIONED` status is strictly terminal for all roles (409 on re-mutation) | 2 | P0 |
| REQ-P11-15 | Leadership override for non-terminal transitions | 2 | P0 |
| REQ-P11-16 | Escalation guard: `escalate: true` only valid on `REVIEWED` or `ACTION_REQUIRED` | 2 | P0 |
| REQ-P11-17 | Leadership escalation resolution: `resolve_escalation: true` sets `is_escalated=false` | 2 | P0 |
| REQ-P11-18 | `reviewed_by` and `AuditLog.user_id` injected from authenticated session | 2 | P0 |
| REQ-P11-19 | `AuditLog.correlation_id` populated from `request.state.correlation_id` | 2 | P0 |
| REQ-P11-20 | `GET /signals/queue/{function_id}` role-restricted queue endpoint | 2 | P0 |
| REQ-P11-21 | NewsAPI connector passes verbatim article `url` to `canonical_url` | 3 | P0 |
| REQ-P11-22 | Explicit `SOURCE_UNAVAILABLE` provenance status on missing/meta URLs | 3 | P0 |
| REQ-P11-23 | Provenance resolver preserves valid source URLs without override | 3 | P0 |
| REQ-P11-24 | Verified provenance auditing across all 8 connectors (incl. EMA & FDA) | 3 | P0 |
| REQ-P11-25 | UI renders "View Original Source" or "Source Unavailable" badge | 3 | P0 |
| REQ-P11-26 | FunctionsWorkspace: Pending Queue panel with real DB counts | 4 | P1 |
| REQ-P11-27 | FunctionsWorkspace: In Review panel with reviewer name | 4 | P1 |
| REQ-P11-28 | FunctionsWorkspace: Recent Decisions panel (last 10) | 4 | P1 |
| REQ-P11-29 | FunctionsWorkspace: Escalations panel with reasons | 4 | P1 |
| REQ-P11-30 | FunctionsWorkspace: Dual metrics (Time to first review, Time to decision) | 4 | P1 |
| REQ-P11-31 | CalibrationWorkspace: Per-function state (3 calibrated, 2 insufficient, 1 N/A) | 4 | P1 |
| REQ-P11-32 | Leadership cross-functional summary view and resolution endpoint | 4 | P1 |
| REQ-P11-33 | Pending review count badge in navigation bar | 4 | P1 |
| REQ-P11-34 | Centralized `apiFetch` in `frontend/lib/api.ts` with CSRF & cookies | 5 | P1 |
| REQ-P11-35 | DemoOperatorSelector calls `/auth/demo-login` (zero frontend password leaks) | 5 | P1 |
| REQ-P11-36 | `ReviewQueue` frontend component | 5 | P1 |
| REQ-P11-37 | SignalCard status chip and inline audit trail | 5 | P1 |
| REQ-P11-38 | Baseline hardened CSP header (nosniff, DENY, form-action 'self', etc.) | 6 | P2 |
| REQ-P11-39 | Session-bound HMAC CSRF token validation on all mutating endpoints | 6 | P2 |
| REQ-P11-40 | `GET /auth/csrf` explicit CSRF token bootstrap endpoint | 6 | P2 |
| REQ-P11-41 | Rate limiting on `/auth/login` and `/auth/demo-login` (5/min per IP) | 6 | P2 |
| REQ-P11-42 | PostgreSQL DB trigger on `audit_log` blocking UPDATE and DELETE | 6 | P1 |
| REQ-P11-43 | Auth events written to AuditLog (`LOGIN_SUCCESS`, `LOGIN_FAILED`, `LOGOUT`) | 6 | P2 |
| REQ-P11-44 | `.env.example` updated with all production security variables | 6 | P2 |
| REQ-P11-45 | `tests/test_auth.py` verifying authentication, session hashing, idle timeout | 7 | P0 |
| REQ-P11-46 | `tests/test_rbac.py` verifying role filtering & queue isolation | 7 | P0 |
| REQ-P11-47 | `tests/test_review_state_machine.py` verifying FSM guards & escalation engine | 7 | P0 |
| REQ-P11-48 | `scripts/test_e2e_vertical_slice.py` full cross-functional workflow verified | 7 | P0 |
