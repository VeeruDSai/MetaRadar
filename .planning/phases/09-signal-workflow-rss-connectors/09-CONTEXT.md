# Phase 09 — Context & Decisions

## Phase Overview

**Phase Title:** Real Signal Workflow, NewsAPI Provenance Fix & Pharma RSS Discovery Connectors
**Phase Number:** 09
**Depends On:** Phase 08 (Provenance Traceability — COMPLETED & VERIFIED)
**Target Branch:** `feature/phase-09-signal-workflow-rss-connectors`
**Date:** 2026-08-26

---

## Problem Statement

The current MetaRadar system has four interconnected gaps that prevent a credible hackathon demonstration:

1. **NewsAPI source links are broken.** The frontend falls back to `https://newsapi.org` (the API portal) instead of the article's actual `article.url`. The NewsAPI connector stores `url: article.url` correctly in `raw_payload.article.url` and `raw_payload.url`, but `SignalDetailWorkspace.tsx:103` hardcodes `'https://newsapi.org'` as the last-resort URL — bypassing the real article link. The `resolve_canonical_provenance` service has no handler for `source_id == "newsapi"`, so it cannot construct the URL either.

2. **"Routing" is destination classification, not an organizational workflow.** `backend/app/services/routing.py` correctly classifies signals to stakeholder functions using content heuristics and config-driven thresholds. But from the UI perspective, clicking "Approve / Reject / Action" in `SignalDetailWorkspace.tsx:113–117` calls `handleUpdateReview(st)` which only mutates local React state — no API call is made. The `POST /signals/{id}/review` endpoint exists and properly persists state + writes an audit log, but the frontend buttons never call it. The result: review state resets on page reload.

3. **The review workflow has no concept of a reviewer actor.** There is no "Demo Operator" role concept, so the workflow cannot demonstrate "Regulatory queue → Demo Regulatory Operator → Acknowledge → Review → Approve/Reject → Action." The database already has `reviewed_by`, `review_decision`, `resulting_action` fields, but no UI allows assigning a demo actor identity.

4. **Three pharma-specific news sources are missing from the connector tier.** NewsAPI is the only news discovery source. Fierce Pharma (RSS), ET Pharma (RSS), and BioPharma Dive (web) would substantially improve signal quality for the hackathon domain. Fierce Pharma and ET Pharma publish official RSS feeds. BioPharma Dive requires compliant link-level discovery (no RSS; no scraping).

---

## Architecture Context (Relevant Existing Infrastructure)

### Backend — What Already Exists

| Component | Relevant To Phase 09 | Location |
| :--- | :--- | :--- |
| `POST /signals/{id}/review` | Persists review_status, reviewed_by, review_decision, resulting_action; writes AuditLog | `backend/app/api/v1/endpoints/signals.py:382` |
| `GET /signals/{id}/audit-history` | Returns chronological audit history | `backend/app/api/v1/endpoints/signals.py:463` |
| `Signal.review_status` | DB column: UNREVIEWED, IN_REVIEW, REVIEWED, ACTION_REQUIRED, ACTIONED, DISMISSED | `backend/app/models/__init__.py:280` |
| `Signal.reviewed_by`, `Signal.review_decision`, `Signal.resulting_action` | DB columns already present | `backend/app/models/__init__.py:281–285` |
| `AuditLog` | Immutable audit table with entity_id, action, performed_by, timestamp, details | `backend/app/models/__init__.py:421` |
| `resolve_canonical_provenance()` | Provenance URL resolver — currently has no newsapi handler | `backend/app/services/provenance_urls.py:92` |
| `EMARSSConnector` | RSS parsing pattern to reuse for Fierce Pharma & ET Pharma | `backend/app/connectors/ema.py` |
| `SourceConnector` base | Abstract connector with `_fetch_with_retry`, `_persist_bronze`, backoff | `backend/app/connectors/base.py` |
| `haemophilia.yaml` | Domain config — source_tiers, connectors config, routing matrix | `config/haemophilia.yaml` |
| `SignalRouting` table | Database table with baseline and calibrated routing — wire to workflow status | `backend/app/models/__init__.py:372` |
| `baseline_routing_matrix` | Config-driven routing from domain YAML (correct approach) | `config/haemophilia.yaml:154` |

### Frontend — What Already Exists But Is Broken

| Component | Issue | Location |
| :--- | :--- | :--- |
| `handleUpdateReview` | Only updates local React state, no API call | `SignalDetailWorkspace.tsx:113` |
| `evidenceUrl` fallback | Hardcodes `https://newsapi.org` for newsapi source | `SignalDetailWorkspace.tsx:103` |
| `reviewState` | Local useState, resets on refresh | `SignalDetailWorkspace.tsx:106` |
| Review buttons | Do not call `POST /signals/{id}/review` | `SignalDetailWorkspace.tsx:253–267` |

---

## Key Decisions

### D-09-01: NewsAPI URL Fix Strategy
Use `article.url` from the raw NewsAPI response as the canonical URL. The connector already stores `url` and `raw_payload.url` and `raw_payload.article.url` correctly. Fix requires:
- Remove `https://newsapi.org` fallback from `evidenceUrl` chain in `SignalDetailWorkspace.tsx:103`
- Add `newsapi` handler to `resolve_canonical_provenance()` that returns the stored `existing_url` directly (it is already a valid article URL)
- Add `newsapi.org/register` to the `LANDING_PAGE_URLS` block list so it is treated as a generic landing page

### D-09-02: Review Workflow API Integration
Wire all review buttons to `POST /signals/{id}/review`. Add:
- `submitSignalReview(signalId, payload)` function to `frontend/lib/api.ts`
- `useSignalReview` hook that calls the API, updates optimistic state, and handles errors
- Fetch audit history from `GET /signals/{id}/audit-history` and render it in the detail view
- Introduce a `DemoOperator` selector (not authentication — a clearly labeled "Demo Role" dropdown with 6 function options matching stakeholder functions) that sets `reviewer` in review API calls

### D-09-03: Demo Operator Pattern
Implement a session-level demo operator selector (stored in `localStorage` or `sessionStorage`, never a real auth token). UI label: **"Demo Role: [Regulatory Affairs]"**. The selected role is passed as `reviewer` in all `POST /signals/{id}/review` calls. This enables demonstrating "Regulatory queue → Demo Regulatory Operator → open signal → Acknowledge → Approve → Action" as a real state-persisting workflow.

### D-09-04: Routing vs. Classification Terminology
Rename user-facing UI labels:
- "Routed to" → "Organizational Destination" or keep "Routed to" but add "QUEUE" badge
- Add a visible "Review Queue" section to Signal Detail showing: queue membership, number of unreviewed signals in that function's queue, reviewer, and workflow status

### D-09-05: Fierce Pharma RSS Connector
- Source ID: `fierce_pharma`
- RSS URL: `https://www.fiercepharma.com/rss/xml` (official feed)
- Tier: 3 (Discovery)
- Pattern: Mirror `EMARSSConnector` — parse `<item>` elements, filter by haemophilia keywords
- Store article `<link>` as canonical URL (not newsapi-style external, but directly from RSS `<link>` element)

### D-09-06: ET Pharma RSS Connector
- Source ID: `et_pharma`
- RSS URL: `https://pharma.economictimes.indiatimes.com/rss/topstories` (primary) + `https://pharma.economictimes.indiatimes.com/rss/drug_approvals`
- Tier: 3 (Discovery)
- Pattern: Mirror `EMARSSConnector`, same approach as Fierce Pharma
- Keyword filter: haemophilia, hemophilia, gene therapy, FDA approval, EMA, Novo Nordisk, emicizumab, fitusiran

### D-09-07: BioPharma Dive — Link-Level Discovery Only
BioPharma Dive does not expose an RSS feed. Do not scrape or crawl.
- Approach: Add `biopharmadive` as a configured source in `haemophilia.yaml` with `freshness_class: manual` and `status: configured_no_feed`
- This makes it visible in the sources registry with an honest status rather than appearing absent
- Add a domain note in `haemophilia.yaml` that a compliant API/feed integration can be added when available

### D-09-08: Escalation Logic Improvement
Replace `score >= 80.0` blanket escalation with compound rule:
- `CRITICAL` priority **AND** (`REGULATORY` or `COMMERCIAL_PATENT` domain) → Leadership escalation
- `HIGH` priority **AND** major event keyword (`approved`, `crl`, `trial halted`, `black box`) → Leadership escalation
- Remove "high score alone = Leadership" pattern that produces false escalations

### D-09-09: No Alembic Migration Required for Review Workflow
All review columns (`review_status`, `reviewed_by`, `review_decision`, `resulting_action`, `routing_timestamp`) already exist in the Signal table. The AuditLog table is also already present. Phase 09 requires zero new migrations.

---

## Requirements Coverage

| Req ID | Description |
| :--- | :--- |
| REQ-P9-01 | NewsAPI signal detail page shows `article.url` in "Open source article" link — never `newsapi.org/register` or `newsapi.org` |
| REQ-P9-02 | `resolve_canonical_provenance()` passes through valid `https://` URLs for `newsapi` source without alteration |
| REQ-P9-03 | `POST /signals/{id}/review` is called on all review button actions (Acknowledge, Start Review, Approve, Reject, Request Evidence, Action, Dismiss) |
| REQ-P9-04 | Review state persists across page reloads (fetched from backend, not local state) |
| REQ-P9-05 | Audit history is displayed in Signal Detail page (chronological list of state transitions with reviewer, timestamp, decision) |
| REQ-P9-06 | Demo Operator selector provides 6 named function roles; selected role appears as `reviewer` in review API payload |
| REQ-P9-07 | Fierce Pharma RSS connector fetches articles, filters by domain keywords, persists to bronze, stores article URL as canonical URL |
| REQ-P9-08 | ET Pharma RSS connector fetches from pharma-specific feeds, filters by domain keywords, persists to bronze |
| REQ-P9-09 | BioPharma Dive is registered in `haemophilia.yaml` with `status: configured_no_feed`; appears in Sources Registry with honest status |
| REQ-P9-10 | `haemophilia.yaml` updated with `fierce_pharma`, `et_pharma`, `biopharmadive` under `tier_3_discovery` |
| REQ-P9-11 | Leadership escalation logic uses compound rule (not score threshold alone) |
| REQ-P9-12 | `test_signal_routing_workflow.py` added; covers full state machine: UNREVIEWED → IN_REVIEW → REVIEWED → ACTIONED |
| REQ-P9-13 | All existing 114 pytest tests continue to pass with 0 failures |
| REQ-P9-14 | `pnpm exec tsc --noEmit` passes with 0 errors |
| REQ-P9-15 | `node scripts/check-banned-classes.mjs` passes with 0 violations |
| REQ-P9-16 | `pnpm lint` passes with 0 warnings |
| REQ-P9-17 | `pnpm build` passes with 0 TypeScript errors and clean Turbopack build |
| REQ-P9-18 | OpenAPI contract synchronized after any backend schema additions |
