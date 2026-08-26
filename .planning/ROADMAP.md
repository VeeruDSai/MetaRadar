# MetaRadar — Implementation Roadmap

## Milestones Overview

### [Milestone v5.1 — Full Platform Architecture & Intelligence Experience](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/milestones/v5.1-ROADMAP.md) (SHIPPED 2026-08-19)

- **Status:** COMPLETED & VERIFIED (Phases 00–06, 16 plans, 100% test pass rate)
- **Archive:** [v5.1-ROADMAP.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/milestones/v5.1-ROADMAP.md) | [v5.1-REQUIREMENTS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/milestones/v5.1-REQUIREMENTS.md) | [v5.1-MILESTONE-AUDIT.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/v5.1-MILESTONE-AUDIT.md)

---

### Milestone v5.1 Extension — Trustworthy Intelligence & Platform Hardening (COMPLETED & VERIFIED)

> **Reference Document:** [docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md)  
> **Status:** COMPLETED & VERIFIED (Phases 07–08, 4 plans, 100% test pass rate)  
> **Core Objective:** Eliminate fabricated/placeholder telemetry, enforce end-to-end data provenance, upgrade structured observability, modularize the frontend architecture, and harden test invariants across all 36 audit dimensions.

```
Phase 07: Trustworthy Intelligence Reconciliation & Platform Hardening (COMPLETED)
   │ └── Governed by: docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md
   │ └── Plan: .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-PLAN.md
   │ └── Summary: .planning/phases/07-trustworthy-intelligence-reconciliation-and-platform-hardening/07-SUMMARY.md
```

#### Phase 07 Scope & Deliverables

- **Codebase Audit & Discrepancy Reconciliation**: Systematic audit of all 12 platform areas removing hardcoded scores, fake "LIVE" badges, and mock evidence strings.
- **Synthetic Data Governance**: Strict `DataMode` metadata (`live`, `recorded_demo`, `test_fixture`) and high-visibility UI badges.
- **Scoring & Confluence Engines**: Transparent Priority Scoring formula with score breakdowns and dynamic multi-source confluence clustering (48h window).
- **Retrieval & Excerpt Truth**: Verified pgvector cosine similarity retrieval for Athena and real verbatim source excerpts for Red-Team contradictions.
- **Operational Observability**: JSON structured logging, `X-Request-ID` / `pipeline_run_id` correlation propagation, and connector health tracking.
- **Modular Frontend Architecture**: Refactored `frontend/components/` by bounded context, reusable `EvidenceDrawer` and `ErrorState` components.
- **Hardened Invariants & Failure Injection**: Automated tests for truthfulness invariants and simulated external service outages.
- **Codebase Map Synchronization**: Complete regeneration and reconciliation of `.planning/codebase/*.md`.

### Phase 08: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening

**Goal:** Guarantee end-to-end source provenance for every displayed signal (provider → raw response → normalized record → database → Signal → serializer → frontend → EvidenceDrawer → source link), preserve source-specific identifiers (PMID, NCT ID, FDA ID, EMA item URL, NewsAPI article URL), make synthetic/test-fixture records impossible to confuse with live data, report missing credentials explicitly without fabricating values, make connector health reflect actual ingestion (not just HTTP 200), and canonicalize the Overview/Lifecycles typography + semantic design tokens + persistent light/dark theme across every workspace and drawer — with the prior 4-factor priority score consistent end-to-end and truthful Confluence source-count semantics.
**Requirements**: REQ-P8-01 … REQ-P8-19 (see .planning/REQUIREMENTS.md)
**Depends on:** Phase 7
**Plans:** 3 plans

Plans:

- [x] 08-01-PLAN.md — Provenance end-to-end: migration 005, connector raw_payload keys, honest serializer/mapper, EvidenceDrawer SOURCE PROVENANCE/VERBATIM EVIDENCE/TRACE, TEST FIXTURE/SYNTHETIC badges
- [x] 08-02-PLAN.md — Source honesty & observability: CONFIGURATION_ERROR reporting, real connector telemetry, per-attempt ingestion logs, truthful confluence source_id semantics + per-evidence traceability
- [x] 08-03-PLAN.md — Canonical design system: banned-class grep gate, token sweep of 9 workspaces, typography/font/theme gates, UI-SPEC §10 manual matrix

---

## Future Backlog / Next Milestone

Future milestone initiatives (v5.3 / v6.0) can be planned and tracked here using `/gsd-new-milestone`.

---

### Milestone v5.2 — Real Signal Workflow, Discovery Connectors & Demo Operator (IN PROGRESS)

> **Branch:** `feature/phase-09-signal-workflow-rss-connectors`
> **Status:** Phase 09 — PLANNING COMPLETE, EXECUTION IN PROGRESS
> **Core Objective:** Wire the review workflow to real API persistence, fix NewsAPI article-URL provenance, add Fierce Pharma + ET Pharma discovery connectors, implement Demo Operator for hackathon workflow demonstration, improve escalation logic.

```
Phase 09: Real Signal Workflow, NewsAPI Provenance Fix & Pharma RSS Discovery Connectors (IN PROGRESS)
   │ └── Context: .planning/phases/09-signal-workflow-rss-connectors/09-CONTEXT.md (D-09-01…09)
   │ └── Plan: .planning/phases/09-signal-workflow-rss-connectors/09-PLAN.md
```

#### Phase 09 Scope & Plans

- [ ] 09-01-PLAN.md — NewsAPI URL fix (remove newsapi.org fallback, add provenance handler) + Review API wiring (POST /review called on all buttons) + test_signal_routing_workflow.py
- [ ] 09-02-PLAN.md — Demo Operator selector (top nav, sessionStorage, 6 function roles) + Audit History panel in Signal Detail + Routing Queue display with live action buttons
- [ ] 09-03-PLAN.md — FiercePharmaRSSConnector + ETPharmaRSSConnector (mirror EMARSSConnector pattern) + BioPharma Dive configured_no_feed registration + Escalation logic compound rule fix

**Requirements:** REQ-P9-01 … REQ-P9-18 (18 requirements — see [09-CONTEXT.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/09-signal-workflow-rss-connectors/09-CONTEXT.md))
