# MetaRadar — Implementation Roadmap

## Milestones Overview

### Milestone v5.1 — Full Platform Architecture & Intelligence Experience (SHIPPED 2026-08-19)

- **Status:** COMPLETED & VERIFIED (Phases 00–06, 16 plans, 100% test pass rate)
- **Archive:** [v5.1-ROADMAP.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/milestones/v5.1-ROADMAP.md) | [v5.1-REQUIREMENTS.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/milestones/v5.1-REQUIREMENTS.md) | [v5.1-MILESTONE-AUDIT.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/v5.1-MILESTONE-AUDIT.md)

### Phase 00: Baseline Stabilization & Quality Governance
- **Goal:** Set up Next.js 16 + FastAPI core foundation, async Alembic migrations, PII/PHI scrubber, and Red-Team registry.
- **Status:** Completed & Verified

### Phase 01: Ingestion Connectors & Data Pipeline
- **Goal:** Production connectors for PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS + Bronze storage & deduplication.
- **Status:** Completed & Verified

### Phase 02: LangGraph 10-Node Intelligence Engine
- **Goal:** 10-node stateful workflow engine with MetaRadarState, PipelineRunner, and unit tests.
- **Status:** Completed & Verified

### Phase 03: Vector Search & LLM Provider Execution
- **Goal:** FastEmbed 384-dim embeddings + pgvector HNSW search + Ollama Gemma 3 4B + Grok privacy gate.
- **Status:** Completed & Verified

### Phase 04: Frontend API Integration & Real-Time Workspace
- **Goal:** Next.js App Router live REST client, portfolio momentum, and confluence radar workspaces.
- **Status:** Completed & Verified

### Phase 05: Calibration & End-to-End Verification
- **Goal:** Stakeholder calibration loop, haemophilia demo story, and Definition of Done audit.
- **Status:** Completed & Verified

### Phase 06: Full Doc-to-UI Mapping, Feature Synchronization & Automated Launchers
- **Goal:** 100% feature parity matrix, 8 dedicated intelligence pages, zero-config `setup.py` and `start.py`.
- **Status:** Completed & Verified

---

### Milestone v5.1 Extension — Trustworthy Intelligence & Platform Hardening (SHIPPED 2026-08-21)

> **Reference Document:** [docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md)  
> **Status:** COMPLETED & VERIFIED (Phases 07–08, 4 plans, 100% test pass rate)  
> **Core Objective:** Eliminate fabricated/placeholder telemetry, enforce end-to-end data provenance, upgrade structured observability, modularize frontend architecture, and harden test invariants.

### Phase 07: Trustworthy Intelligence Reconciliation & Platform Hardening
- **Goal:** Systematic audit removing hardcoded scores, mock data, and synthetic telemetry; transparent priority scoring; structured logging.
- **Status:** Completed & Verified

### Phase 08: Provenance Traceability + Canonical Overview/Lifecycle Design System Hardening
- **Goal:** Guarantee end-to-end source provenance, preserve source identifiers (PMID, NCT ID, FDA ID, EMA URL), truthful connector health telemetry, and canonical design system tokens across all workspaces.
- **Requirements:** REQ-P8-01 … REQ-P8-19
- **Status:** Completed & Verified
- **Plans:**
  - [x] 08-01-PLAN.md — Provenance end-to-end: migration 005, connector raw_payload keys, EvidenceDrawer TRACE
  - [x] 08-02-PLAN.md — Source honesty & observability: CONFIGURATION_ERROR reporting, real connector telemetry
  - [x] 08-03-PLAN.md — Canonical design system: banned-class grep gate, token sweep of 9 workspaces

---

### Milestone v5.2 — Real Signal Workflow, Discovery Connectors & Demo Operator (COMPLETED & VERIFIED)

> **Branch:** `feature/phase-09-signal-workflow-rss-connectors`  
> **Status:** Phase 09 — COMPLETED & VERIFIED  
> **Core Objective:** Wire review workflow to real API persistence, fix NewsAPI article-URL provenance, add Fierce Pharma + ET Pharma discovery connectors, implement Demo Operator for hackathon workflow demonstration, improve escalation logic.

### Phase 09: Real Signal Workflow, NewsAPI Provenance Fix & Pharma RSS Discovery Connectors
- **Goal:** Direct NewsAPI article URL pass-through, persistent review state machine (`POST /signals/{id}/review`) with `AuditLog`, Demo Operator persona selector, Fierce Pharma + ET Pharma RSS connectors, compound leadership escalation logic.
- **Requirements:** REQ-P9-01 … REQ-P9-18
- **Status:** Completed & Verified
- **Plans:**
  - [x] 09-01-PLAN.md — NewsAPI URL fix + Review API wiring + test_signal_routing_workflow.py
  - [x] 09-02-PLAN.md — Demo Operator selector + Audit History panel in Signal Detail + Routing Queue actions
  - [x] 09-03-PLAN.md — FiercePharmaRSSConnector + ETPharmaRSSConnector + BioPharma Dive configured_no_feed + Escalation logic

### Phase 10: Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement
- **Goal:** Make the 6-question signal journey undeniable, integrate active BioPharma Dive RSS connector, add adaptive NewsAPI quota governor, surface Evidence Convergence & "Why This Signal?" explainers, expose Red-Team self-challenging counter-factuals, and run brutal end-to-end scenario verifications.
- **Requirements:** REQ-P10-01 … REQ-P10-15
- **Status:** Completed & Verified
- **Plans:**
  - [x] 10-01-PLAN.md — BioPharma Dive RSS connector + adaptive NewsAPI quota governor & health UI
  - [x] 10-02-PLAN.md — Evidence convergence tree + "Why this signal?" explainer + Red-Team counter-factuals + source hierarchy tags
  - [x] 10-03-PLAN.md — Daily executive briefing dashboard + brutal 5-scenario E2E verification

---

---

### Milestone v5.3 — MetaRadar Productionization (COMPLETED & VERIFIED)

> **Branch:** `feature/phase-11-productionization`  
> **Status:** Phase 11 — COMPLETED & VERIFIED  
> **Core Objective:** Turn MetaRadar v5.2 into a functional, end-to-end, role-aware, reviewable, auditable, and secure decision-intelligence application. Complete vertical slice: Login → Role-Queue → Signal → Evidence → Review → Approve/Contest → Audit → Action → Leadership Visibility.

### Phase 11: MetaRadar Productionization
- **Goal:** Real authentication (User/Session/bcrypt), server-side RBAC, review state machine permission matrix, role-filtered signal queues, provenance completeness, operational FunctionsWorkspace, honest CalibrationWorkspace, Leadership cross-functional view, security hardening (CSRF, rate limiting, security headers, auth audit events), 30+ new tests, E2E vertical slice.
- **Priority:** P0 (auth/RBAC/provenance) → P1 (operational UI) → P2 (security hardening)
- **Requirements:** REQ-P11-01 … REQ-P11-48
- **Status:** Completed & Verified
- **Context:** [11-CONTEXT.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/11-productionization/11-CONTEXT.md)
- **Plans:**
  - [x] 11-01-PLAN.md — Identity & Auth Foundation (User/Session models, bcrypt, /auth/* endpoints)
  - [x] 11-02-PLAN.md — Server-Side RBAC & Review Enforcement (role filtering, permission matrix, queue endpoint)
  - [x] 11-03-PLAN.md — Provenance Completeness & Pharma Source Validation (NewsAPI URL, SOURCE_UNAVAILABLE)
  - [x] 11-04-PLAN.md — Operational Intelligence UI (FunctionsWorkspace, CalibrationWorkspace, Leadership view)
  - [x] 11-05-PLAN.md — Frontend Auth Integration & Demo Persona (real auth, ReviewQueue, signal lifecycle)
  - [x] 11-06-PLAN.md — Security Hardening (security headers, CSRF, rate limiting, auth audit events)
  - [x] 11-07-PLAN.md — Test Suite Expansion & E2E Vertical Slice (32 new tests, vertical slice script)

---

## Future Backlog / Next Milestone

Future milestone initiatives (v6.0+) can be planned and tracked here using `/gsd-new-milestone`.

