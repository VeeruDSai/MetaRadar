# Phase 11 — Context & Decisions (Revision 11.2)

## Phase Overview

**Phase Title:** MetaRadar Productionization — Real Identity, RBAC, Complete Operational Decision Workflows & Security Hardening  
**Phase Number:** 11 (Revision 11.2 — Execution-Ready Master Specification)  
**Depends On:** Phase 10 (Undeniable Demo Journey, Evidence Convergence, BioPharma Dive — COMPLETED & VERIFIED)  
**Target Branch:** `feature/phase-11-productionization`  
**Date:** 2026-08-27  
**Priority Classification:**
- **P0** — Core Decision Loop, State Guard Invariants, E2E Cross-Functional Verification, Provenance Truthfulness
- **P1** — Operational Workflows, DB-Level Audit Immutability, Session-Bound CSRF, Pre-Auth Exact-Origin Validation, Per-Function Calibration
- **P2** — Idle Session Timeouts, Baseline Hardened CSP Directives, Rate Limiting

---

## Strategic Objective

> "A user can log in, receive a role, see role-specific intelligence, inspect original evidence and verified provenance, review a signal, make an authorized decision, have that decision audited in an append-only database log, trigger a downstream cross-functional escalation, and have Leadership inspect and resolve that escalation to an authorized terminal state."

---

## The Complete Vertical Slice Workflow (Revision 11.2 Acceptance Topology)

The automated end-to-end acceptance harness (`scripts/test_e2e_vertical_slice.py`) executes an authentic cross-functional topology across all 6 stakeholder functions:

```
1. MEDICAL AFFAIRS:
   Login → Queue → Inspect Evidence & Provenance → IN_REVIEW → REVIEWED (Clinical readout verified) → Audit Trail Verified → Logout

2. REGULATORY AFFAIRS:
   Login → Queue → Inspect Evidence → IN_REVIEW → ACTION_REQUIRED (PDUFA filing tracking required) → Audit Trail Verified → Logout

3. SAFETY (Escalation Trigger):
   Login → Queue → Inspect Evidence → IN_REVIEW → ACTION_REQUIRED + escalate=true (Adverse event alert) → Verify is_escalated=true & SIGNAL_ESCALATED in AuditLog → Logout

4. LEADERSHIP (Escalation Resolution):
   Login → GET /leadership/summary → Assert Safety signal is present in pending_escalations → POST /signals/{id}/review (resolve_escalation=true, status=ACTIONED, resulting_action="Clinical hold approved") → Assert is_escalated=false, status=ACTIONED, and ESCALATION_RESOLVED in AuditLog → Logout

5. MARKET ACCESS:
   Login → Queue → Inspect Evidence → IN_REVIEW → ACTIONED (Reimbursement dossier complete) → Verify terminal status → Audit Trail Verified → Logout

6. COMMUNICATIONS:
   Login → Queue → Inspect Evidence → IN_REVIEW → DISMISSED (No media statement required) → Audit Trail Verified → Logout

7. LEADERSHIP (Direct Strategic Decision):
   Login → Inspect distinct unreviewed critical signal → IN_REVIEW → ACTIONED (Direct portfolio guidance) → Logout
```

---

## Revision 11.2 Architectural Decisions

### D-11-01: Session Lifecycle (Absolute + Idle Timeout)
- **Absolute Lifetime:** `SESSION_LIFETIME_SECONDS = 28800` (8 hours).
- **Idle Timeout:** `SESSION_IDLE_TIMEOUT_SECONDS = 3600` (1 hour).
- **Session Table Schema:** `sessions` table tracks `session_id`, `user_id`, `token_hash = sha256(token)`, `created_at`, `last_activity_at`, `expires_at`, `is_revoked`.
- **Validation:** Requests past `expires_at` OR with inactivity delta exceeding `idle_timeout` return 401. Active requests update `last_activity_at = now()`.

### D-11-02: Non-Deterministic Demo Credentials & Controlled Seeding
- When `DEMO_MODE=true`:
  - If `DEMO_USER_PASSWORD` is provided via env, use it.
  - If `DEMO_USER_PASSWORD` is unset, generate a cryptographically strong 16-character random token at startup via `secrets.token_urlsafe(12)`, print it once to stdout, and never write it to log files.
  - No static default passwords exist in code.
- When `DEMO_MODE=false`: Demo user auto-seeding is completely disabled; users must be provisioned through standard administrative procedures.

### D-11-03: Zero Frontend Password Leaks (`/auth/demo-login`)
- `POST /api/v1/auth/demo-login` accepts `{"role": "..."}` and is active **strictly when `DEMO_MODE=true`**.
- Frontend `DemoOperatorSelector` switches personas via this endpoint without passwords or credentials ever touching browser bundles or `NEXT_PUBLIC_*` variables.
- In production (`DEMO_MODE=false`), `POST /auth/demo-login` returns 404/403.

### D-11-04: Mandatory Authentication on All Protected APIs
- All protected endpoints (`/signals`, `/signals/queue/*`, `/signals/{id}/review`, `/function-stats/*`, `/leadership/*`) strictly enforce `current_user = Depends(get_current_user)` (401 on missing/invalid session).
- Anonymous bypass is disallowed in all standard, demo, and production configurations.

### D-11-05: State Machine, Terminal Enforcement & Escalation Contract
- **Terminal Enforcement:** `ACTIONED` is **strictly terminal for all roles** (including Leadership and Admin). Modifying an `ACTIONED` signal returns **409 CONFLICT**.
- **Standard Transitions:**
  - `UNREVIEWED` → `IN_REVIEW`, `DISMISSED`
  - `IN_REVIEW` → `REVIEWED`, `ACTION_REQUIRED`, `DISMISSED`
  - `REVIEWED` → `ACTION_REQUIRED`, `ACTIONED`
  - `ACTION_REQUIRED` → `ACTIONED`, `IN_REVIEW`
  - `DISMISSED` → `IN_REVIEW` (reopen)
  - `ACTIONED` → None (terminal)
- **Role Permissions:**
  - Marking `ACTIONED` is restricted to `SAFETY`, `MARKET_ACCESS`, `LEADERSHIP`, `ADMIN`.
  - `LEADERSHIP / ADMIN` Override: Can transition any *non-terminal* state directly to `IN_REVIEW`, `REVIEWED`, or `ACTION_REQUIRED`.
- **Escalation Invariants:**
  - Escalation (`escalate: true`) is **only permitted when transitioning to `REVIEWED` or `ACTION_REQUIRED`** (attempting to escalate with other statuses returns **409 CONFLICT**).
  - Escalation sets `Signal.is_escalated = true`, `Signal.routing_reason = escalation_reason`, and writes `SIGNAL_ESCALATED` to `AuditLog`.
  - Leadership resolution (`resolve_escalation: true`) sets `Signal.is_escalated = false`, applies the requested target status (`ACTIONED` or `DISMISSED`), and writes `ESCALATION_RESOLVED` to `AuditLog`.

### D-11-06: Database-Level Audit Immutability (PostgreSQL Trigger)
- In addition to SQLAlchemy ORM event listeners (`before_update`, `before_delete`), Migration 014 creates a PostgreSQL trigger on `audit_log`:
  ```sql
  CREATE OR REPLACE FUNCTION block_audit_log_mutation()
  RETURNS TRIGGER AS $$
  BEGIN
      RAISE EXCEPTION 'AuditLog records are append-only and cannot be updated or deleted';
  END;
  $$ LANGUAGE plpgsql;

  CREATE TRIGGER trg_block_audit_log_update_delete
  BEFORE UPDATE OR DELETE ON audit_log
  FOR EACH ROW EXECUTE FUNCTION block_audit_log_mutation();
  ```
- Guaranteed append-only immutability at both ORM and database engine levels.

### D-11-07: Pre-Auth Exact-Origin Validation & Session-Bound HMAC CSRF
- **Pre-Auth Endpoints (`/auth/login`, `/auth/demo-login`):**
  - Reject requests when both `Origin` and `Referer` headers are missing (403).
  - Extract exact `scheme://host[:port]` and validate against `settings.cors_origins_list` using exact matching (no prefix or `startswith` comparisons).
- **Authenticated Mutating Endpoints:**
  - Validate session-bound HMAC CSRF token: `csrf_token = hmac_sha256(SECRET_KEY, f"{session_id}:{nonce}") + ":" + nonce`.
- **Bootstrap:** `GET /api/v1/auth/csrf` provides explicit token initialization.
- **Client Integration:** `frontend/lib/api.ts` implements a centralized `apiFetch` wrapper that automatically reads `metaradar_csrf` and attaches `X-CSRF-Token` to all mutating requests.

### D-11-08: Correlation ID Propagation on All Audit Events
- Every audit record created during signal review, escalation, or resolution captures `correlation_id = request.state.correlation_id` directly from FastAPI middleware context.

### D-11-09: Complete 8-Connector Provenance & Evidence Inspection
- Provenance taxonomy:
  - `SOURCE_VERIFIED`: Canonical document ID / URL extracted directly from trusted primary/authoritative registries (PubMed, ClinicalTrials.gov, EMA EPAR, FDA Drugs@FDA, BioPharma Dive, Fierce Pharma, ET Pharma).
  - `URL_PRESENT`: Syntactically valid URL present from connector.
  - `SOURCE_UNAVAILABLE`: Missing or upstream generic aggregator URL (e.g. generic `newsapi.org` root).
- E2E acceptance tests explicitly verify `GET /signals/{id}` evidence blocks, interpretation text, and canonical provenance.

### D-11-10: Per-Function Calibration Status
- Structured per-function status (minimum 20 samples required):
  - `MEDICAL_AFFAIRS`: `calibrated` (25 samples, Brier: 0.12, ECE: 0.04)
  - `REGULATORY`: `calibrated` (22 samples, Brier: 0.14, ECE: 0.05)
  - `SAFETY`: `calibrated` (24 samples, Brier: 0.09, ECE: 0.03)
  - `MARKET_ACCESS`: `insufficient_data` (4 samples)
  - `COMMUNICATIONS`: `insufficient_data` (2 samples)
  - `LEADERSHIP`: `not_applicable`

### D-11-11: Hardened Baseline CSP & Rate Limiting
- CSP header includes:
  `default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self';`
- Documented as baseline hardened CSP; rate limiting documented as single-instance demo defense with Redis recommendations for multi-worker deployments.
