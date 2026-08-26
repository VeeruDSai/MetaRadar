# Phase 10 — Context & Decisions

## Phase Overview

**Phase Title:** Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement  
**Phase Number:** 10  
**Depends On:** Phase 09 (Real Signal Workflow, NewsAPI Provenance Fix & Pharma RSS Discovery Connectors — COMPLETED & VERIFIED)  
**Target Branch:** `feature/phase-10-demo-journey-evidence-convergence-ux`  
**Date:** 2026-08-27  

---

## Strategic Shift: From Architecture Expansion to Undeniable Demonstration

The MetaRadar platform has completed its fundamental architecture:
- 7 Active Connectors (PubMed, ClinicalTrials.gov, FDA, EMA, NewsAPI, Fierce Pharma, ET Pharma) + Bronze storage
- 11-Node LangGraph competitive intelligence pipeline
- Transparent priority scoring & 2-tier source authority model
- Persistent review state machine (`POST /signals/{id}/review`) with immutable `AuditLog` history
- Demo Operator non-auth role switcher (`sessionStorage`)
- 139 passing Pytest suites, 0 ESLint warnings, 0 type errors, 0 banned Tailwind classes

The focus of Phase 10 is **making the existing architecture undeniable, reliable, and demo-ready** by perfecting the **6-Question Signal Journey** on the **Signal Card + Signal Detail Workspace**, turning internal intelligence machinery into visible UI assets, connecting the verified BioPharma Dive RSS feed, and governing NewsAPI daily quota.

---

## The Six Core Intelligence Questions

Every signal must visibly answer:
1. **What changed?** (Verbatim primary excerpt & direct record link)
2. **Why does it matter?** (Strategic competitive impact on portfolio)
3. **Who should care?** (Destination queue & relevance score)
4. **Why should I trust it?** (Evidence hierarchy & multi-source convergence)
5. **What should I do?** (Clear actionable operational directive)
6. **What happened after I acted?** (Persistent review status & immutable audit history)

---

## Key Decisions

### D-10-01: BioPharma Dive RSS Connector
- **Source ID:** `biopharmadive`
- **RSS Feed URL:** `https://www.biopharmadive.com/feeds/news/` (verified HTTP 200)
- **Tier:** 3 (Discovery)
- **Implementation:** Create `backend/app/connectors/biopharma_dive.py` using `xml.etree.ElementTree` parsing and domain keyword filters, mirroring `FiercePharmaRSSConnector`.
- **Registration:** Upgrade from `configured_no_feed` to active source in `config/haemophilia.yaml`, `backend/app/connectors/__init__.py`, `backend/app/services/scheduler.py`, and `backend/app/api/v1/endpoints/ingestion.py`.

### D-10-02: Adaptive NewsAPI Quota Governor
- Prevent 100 req/day exhaustion in `backend/app/services/scheduler.py`:
  - `quota_remaining > 40`: Standard 30m interval
  - `15 <= quota_remaining <= 40`: Throttled 90m interval
  - `quota_remaining < 15`: Automated pause with `HEALTHY (QUOTA_PRESERVED)` status
- Expose remaining quota in `GET /api/v1/health/sources` and render `Quota: {remaining} / 100` badge in UI.

### D-10-03: Evidence Convergence Visualization
- Build `EvidenceConvergenceWidget` displaying how independent sources (e.g. `3 Authoritative + 1 Discovery`) converge into corroborated intelligence.
- Integrate into `frontend/components/signals/SignalDetailWorkspace.tsx` and `frontend/components/signals/SignalCard.tsx`.

### D-10-04: "Why This Signal?" Transparent Explainer
- Replace opaque raw score numbers with additive clinical factors:
  - `+30 pts` Clinical-Stage Readout (Phase III)
  - `+25 pts` Key Competitor Asset
  - `+20 pts` Multi-Source Corroboration
  - `+15 pts` Authoritative Provenance Tier

### D-10-05: "What Could Invalidate This?" Self-Challenging AI
- Surface Red-Team 19-rule counter-factuals in `SignalDetailWorkspace.tsx`:
  - 1. Unconfirmed clinical endpoints
  - 2. Protocol amendment altering target cohort
  - 3. Regulatory delay past PDUFA target
  - 4. Unexpected adverse event or immunogenicity signals

### D-10-06: Explicit Source Hierarchy Tags
- Tag all sources visibly:
  - `EVIDENCE PRIMARY` (ClinicalTrials.gov, PubMed)
  - `VALIDATION` (FDA, EMA)
  - `DISCOVERY` (Fierce Pharma, ET Pharma, BioPharma Dive, NewsAPI)

### D-10-07: Daily Executive Briefing Dashboard
- Refine `frontend/app/page.tsx` hero metrics into a concise executive daily briefing:
  - Total New Signals, High Priority Count, Pending Review Count, Leadership Escalations, Authoritative Validations.

### D-10-08: Brutal 5-Scenario Verification Matrix
- Execute Scenarios A through E:
  - **Scenario A:** Full Signal Journey (Ingestion → Scoring → Routing → Review → Audit)
  - **Scenario B:** Evidence Convergence (Discovery → Authoritative Validation)
  - **Scenario C:** Idle Sync (No-New-Data handling without status degradation)
  - **Scenario D:** Graceful Outage Resilience (Single connector failure isolation)
  - **Scenario E:** Zero Generic URLs (100% direct record/article links)
