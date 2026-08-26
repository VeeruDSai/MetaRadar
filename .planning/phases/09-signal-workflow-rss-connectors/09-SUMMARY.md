---
phase: 09-signal-workflow-rss-connectors
plan: 09
subsystem: workflow-and-connectors
tags: [newsapi, provenance, review-workflow, audit-log, demo-operator, fierce-pharma, et-pharma, biopharmadive, escalation]
requires:
  - phase: 08-provenance-traceability-canonical-overview-lifecycle-design
    provides: Full provenance traceability, truthful connector health, canonical design tokens
provides:
  - Direct NewsAPI article URL provenance and landing page blocking
  - Persistent review workflow state machine (POST /signals/{id}/review)
  - Chronological audit history panel in SignalDetailWorkspace (GET /signals/{id}/audit-history)
  - Demo Operator persona selector (6 roles) stored in sessionStorage
  - Fierce Pharma and ET Pharma RSS discovery connectors
  - BioPharma Dive configured_no_feed registration in domain config
  - Improved leadership escalation logic (compound rule)
affects: [frontend, backend, connectors, routing, audit-log]
tech-stack:
  added: []
  patterns:
    - "NewsAPI article URL pass-through in resolve_canonical_provenance()"
    - "Persistent review state machine with synchronous AuditLog insertions"
    - "DemoOperator persona selector in Next.js 16 with hydration safety"
    - "Stdlib xml.etree RSS XML parsing with domain keyword filtering"
key-files:
  created:
    - backend/app/connectors/fierce_pharma.py
    - backend/app/connectors/et_pharma.py
    - frontend/components/common/DemoOperatorSelector.tsx
    - tests/test_signal_routing_workflow.py
    - .planning/phases/09-signal-workflow-rss-connectors/09-UI-REVIEW.md
  modified:
    - backend/app/services/provenance_urls.py
    - backend/app/services/routing.py
    - backend/app/connectors/__init__.py
    - backend/app/api/v1/endpoints/signals.py
    - backend/app/api/v1/endpoints/ingestion.py
    - backend/app/services/scheduler.py
    - config/haemophilia.yaml
    - frontend/components/signals/SignalDetailWorkspace.tsx
    - frontend/components/signals/SignalCard.tsx
    - frontend/components/metaradar.tsx
    - frontend/lib/api.ts
    - frontend/types/api.ts
---

# Phase 09 Summary: Real Signal Workflow, NewsAPI Provenance Fix & Pharma RSS Discovery Connectors

## Overview
Phase 09 delivered four major operational and workflow enhancements for the MetaRadar competitive intelligence platform:

1. **NewsAPI Article URL Provenance**: Fixed `resolve_canonical_provenance()` to pass through verified `article.url` values, removed hardcoded `https://newsapi.org` fallback in `SignalDetailWorkspace.tsx`, and added `newsapi.org/register` to landing page blocklists.
2. **Persistent Review Workflow & Audit Trail**: Wired all review buttons ("Acknowledge & Start Review", "Approve Signal", "Reject / Contest", "Request Additional Evidence", "Execute & Record Action", "Dismiss") to `POST /api/v1/signals/{id}/review`, persisting `review_status`, `reviewed_by`, `review_decision`, and `resulting_action` in PostgreSQL while creating immutable `AuditLog` rows.
3. **Demo Operator Persona System**: Added a 6-role non-auth persona switcher (`DemoOperatorSelector.tsx`) in the top navigation bar backed by `sessionStorage`, allowing seamless role-specific workflow demonstrations without requiring complex authentication.
4. **Pharma Discovery Connectors & Escalation Logic**: Added `FiercePharmaRSSConnector` and `ETPharmaRSSConnector` using stdlib XML parsing and domain keyword filtering, registered `biopharmadive` with `configured_no_feed` status in `haemophilia.yaml`, and updated leadership escalation logic to use compound domain and inflection event rules.

## Verification
- `pytest tests/ -v -m "not live"`: 139 passed, 0 failed.
- `node scripts/check-banned-classes.mjs`: 28 files scanned, 0 violations.
- `npm --prefix frontend run build`: Next.js 16 (Turbopack) production build passed with 0 TypeScript errors.
- `python scripts/export_openapi.py`: Contracts synchronized.
