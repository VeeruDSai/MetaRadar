# Phase 10 — Research: Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement

**Phase:** Phase 10 — Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement  
**Date:** 2026-08-27  
**Status:** COMPLETE & PRESCRIPTIVE  
**Downstream Consumer:** `/gsd-plan-phase 10`  

---

## Executive Strategic Directive

The platform has graduated from the **"build the missing architecture"** phase to the **"make existing architecture undeniable, reliable, and demo-ready"** phase.

### Core Philosophy for Phase 10:
1. **Stop adding large horizontal features.** The architecture (7+ connectors, Bronze deduplication, 11-node LangGraph pipeline, priority scoring, authority tiers, persistent review state machine, immutable `AuditLog`, 139 tests) is complete.
2. **Make the Signal Journey undeniable.** Focus 80% of effort on the **Signal Card + Signal Detail Workspace** to visibly answer the 6 core intelligence questions:
   - *Q1: What changed?* (Verbatim primary excerpt & verified record link)
   - *Q2: Why does it matter?* (Strategic competitive impact on portfolio)
   - *Q3: Who should care?* (Destination queue & relevance score)
   - *Q4: Why should I trust it?* (Evidence hierarchy & multi-source convergence)
   - *Q5: What should I do?* (Clear actionable operational directive)
   - *Q6: What happened after I acted?* (Persistent review status & immutable audit history)
3. **Turn internal machinery into visible intelligence:**
   - **Evidence Convergence:** Visual multi-source alignment (e.g. 4 independent sources: 3 authoritative, 1 discovery) demonstrating confluence.
   - **"Why this signal?" Explainer:** Transparent priority breakdown (+ Clinical-stage, + Competitor asset, + Phase III evidence, + Multi-source).
   - **"What would change my mind?" Counter-factuals:** Expose Red-Team self-challenging logic (e.g. unconfirmed readout, amended registry filing).
4. **Connect BioPharma Dive via official RSS feed:** Verified active endpoint at `https://www.biopharmadive.com/feeds/news/`.
5. **Enforce NewsAPI Quota-Awareness:** Prevent 100 req/day exhaustion during judging demos by pausing or increasing polling intervals when remaining quota is low.

---

## Scope & Action Matrix

| Area / Recommendation | Action | Rationale |
|---|:---:|---|
| **NewsAPI Quota-Aware Polling** | **DO NOW** | Real demo risk: 15m polling consumes ~96 req/day against 100 limit. Add adaptive interval & clear remaining quota UI. |
| **BioPharma Dive RSS Connector** | **DO NOW** | Verified working RSS feed at `https://www.biopharmadive.com/feeds/news/`. Upgrades source from `configured_no_feed` to active 8th connector. |
| **Evidence Convergence UI** | **DO NOW** | Differentiator: Visually demonstrates how independent sources converge into high-confidence intelligence. |
| **"Why This Signal?" Breakdown** | **DO NOW** | Replaces opaque numerical score (e.g. 87) with transparent additive evidence factors. |
| **"What Could Invalidate This?"** | **DO NOW** | Surfaces Red-Team 19-rule engine as an active self-challenging intelligence layer. |
| **Source Hierarchy Clarification** | **DO NOW** | Visually distinguishes `EVIDENCE PRIMARY` (CT.gov, PubMed) vs `VALIDATION` (FDA, EMA) vs `DISCOVERY` (Fierce, ET, BioPharma Dive). |
| **Dashboard Daily Briefing View** | **DO NOW** | Compact hero summary ("Today: 12 signals, 4 high priority, 3 require review, 2 leadership alerts, 7 validated"). |
| **End-to-End Scenario Validation** | **DO NOW** | Execute brutal verification scenarios (Scenarios A through E) ensuring unbroken state flow and 0 generic URL links. |
| **Webhooks / Push Architecture** | **SKIP** | Too much infrastructure risk, zero added judging value over 15–60m polling scheduler. |
| **Redis Distributed Lock (Redlock)**| **SKIP** | PostgreSQL advisory locks are proven and reliable for single/dual instance deployment. |
| **OpenAPI AST Codegen (orval)** | **SKIP** | Static template + diff gate already enforces contract synchronization reliably. |
| **Full Auth / SSO System** | **SKIP** | Demo Operator role selector (`sessionStorage`) + backend persistent review state is completely defensible. |

---

## 1. Standard Stack & Library Strategy

### Backend
- **RSS Parsing:** Standard library `xml.etree.ElementTree` (mirrors `EMARSSConnector`, `FiercePharmaRSSConnector`, `ETPharmaRSSConnector`).
- **HTTP Client:** `httpx.AsyncClient` with custom `User-Agent: MetaRadar/5.1 (Biomedical Intelligence System)` and 10s timeout.
- **ORM & Database:** SQLAlchemy 2.0 Async (`backend/app/models/__init__.py`), existing `raw_signals_bronze`, `signals`, `sources`, `audit_log`.

### Frontend
- **Framework:** Next.js 16.3.0 (App Router), React 19, TypeScript 5.7.3.
- **Styling:** CSS variables in `globals.css` (`var(--surface)`, `var(--primary)`, `var(--border)`, `var(--success)`, `var(--warning)`, `var(--danger)`).
- **Icons:** `lucide-react` (`ShieldCheck`, `Layers`, `Network`, `History`, `Sparkles`, `AlertCircle`, `ArrowRight`, `Inbox`).
- **Components:** Base UI primitives, custom `Counter.tsx`, `Stepper.tsx`.

---

## 2. Architecture Patterns & Blueprint

### A. BioPharma Dive RSS Adapter (`BioPharmaDiveRSSConnector`)
- **Feed URL:** `https://www.biopharmadive.com/feeds/news/`
- **Tier:** 3 (Discovery)
- **Freshness Class:** `delayed`
- **Keyword Filters:** Matches haemophilia, hemophilia, gene therapy, clotting factor, Novo Nordisk, Roche, Hemlibra, emicizumab, fitusiran, Roctavian, valoctocogene.
- **Canonical URL:** Exact `<link>` extracted from `<item>`, validated against `_looks_like_http_url()` and landing page blocklist.

### B. Adaptive NewsAPI Quota Governor
- **Problem:** Fixed 15-minute polling consumes 96 requests/day against a 100/day developer cap.
- **Solution in `SourceScheduler`:**
  - If `quota_remaining > 40`: Standard 30m polling interval.
  - If `15 <= quota_remaining <= 40`: Throttle to 90m polling interval.
  - If `quota_remaining < 15`: Pause automated scheduler runs, report `connector_status: "HEALTHY (QUOTA_PRESERVED)"`, and resume on UTC date rollover.
  - Expose `quota_remaining` in `GET /api/v1/health/sources` and render `Quota: {remaining}/100` badge in the UI.

### C. Evidence Convergence & Source Hierarchy Component
Visualizes the transition from raw noise to multi-source validated intelligence:
```
┌────────────────────────────────────────────────────────────────────────┐
│ EVIDENCE CONVERGENCE • 4 INDEPENDENT SOURCES (HIGH CONFIDENCE)         │
├────────────────────────────────────────────────────────────────────────┤
│ [Tier 1 Authoritative]  ClinicalTrials.gov ──┐                         │
│ [Tier 1 Authoritative]  NCBI PubMed ─────────┤                         │
│ [Tier 1 Regulatory]     European Medicines ──┼──► CONVERGED INTELLIGENCE│
│ [Tier 3 Discovery]      Fierce Pharma ───────┘                         │
└────────────────────────────────────────────────────────────────────────┘
```

### D. "Why This Signal?" Transparent Scoring Breakdown
Replaces raw score integers with additive clinical reasoning factors:
- `+30 pts` **Clinical-Stage Readout** (Phase III primary endpoint reached)
- `+25 pts` **Key Competitor Asset** (Direct competitor to approved therapy)
- `+20 pts` **Multi-Source Corroboration** (Corroborated across 3 independent registries)
- `+15 pts` **Authoritative Tier 1 Provenance** (FDA / ClinicalTrials.gov)
- **Net Decision Priority:** `90 / 100` (CRITICAL)

### E. "What Could Invalidate This?" Self-Challenging Red-Team Counter-Factuals
Surfaces Red-Team logic directly on the Signal Detail page:
- *What would change our assessment?*
  1. Primary endpoint statistical significance not reproduced in full publication.
  2. Protocol amendment altering biomarker target population.
  3. Regulatory filing delay past PDUFA target window.
  4. Emergence of unexpected vector-related immunogenicity or hepatic enzyme elevation.

---

## 3. What NOT to Hand-Roll

1. **Do NOT hand-roll an authentication system.** Use the existing `DemoOperatorSelector` (`sessionStorage`).
2. **Do NOT hand-roll an HTML scraper for news sources.** Use only official XML RSS endpoints (`xml.etree.ElementTree`).
3. **Do NOT hand-roll a distributed locking system.** Use existing PostgreSQL `try_advisory_lock` in `session.py`.
4. **Do NOT hand-roll arbitrary CSS utility classes.** Use existing CSS custom properties from `globals.css`.

---

## 4. Common Pitfalls & Guardrails

| Pitfall | Consequence | Mitigation |
|---|---|---|
| **NewsAPI 429 Quota Exhaustion** | Live demo fails with rate limit errors | Implement quota-aware governor in `SourceScheduler` and persist `quota_remaining`. |
| **Generic URLs on Source Cards** | Violates Truthful Provenance Invariant | Validate that all 8 connectors emit direct record/article URLs and pass `test_provenance.py`. |
| **Over-crowded UI Views** | Judges overwhelmed by multiple tabs | Center the user experience on the **Signal Card + Signal Detail Workspace** with progressive disclosure. |
| **Stale Review State on Page Refresh** | Review appears temporary | Ensure `submitSignalReview()` persists to DB and re-fetches `fetchSignalAuditHistory()`. |

---

## 5. End-to-End Demo Verification Scenarios (The 5 Brutal Gates)

### Scenario A: Full Signal Journey (Ingestion → Review → Audit)
1. Ingest new signal into Bronze.
2. 11-Node pipeline classifies, embeds, scores, and routes signal to `Medical Affairs` (`review_status="UNREVIEWED"`).
3. Open Signal Detail page in frontend.
4. Verify Evidence URL links directly to source record.
5. Select `Demo Role: Medical Affairs Reviewer`.
6. Click `Acknowledge & Start Review` → Status updates to `IN_REVIEW`.
7. Click `Approve Signal` with rationale note → Status updates to `REVIEWED`.
8. Check Audit Trail panel → New immutable entry visible with timestamp and actor.

### Scenario B: Evidence Convergence (Discovery → Authoritative Validation)
1. Trade news connector (Fierce Pharma) reports clinical readout.
2. ClinicalTrials.gov connector records updated study results.
3. System detects confluence across sources and updates Evidence Convergence widget to show `3 Authoritative + 1 Discovery`.

### Scenario C: Clean Idle Sync (No-New-Data)
1. Scheduler triggers connector fetch.
2. External API reports 0 new records.
3. Source health updates `last_success` and status remains `HEALTHY (NO_NEW_DATA)`.

### Scenario D: Graceful Outage Resilience
1. Inject network error for single connector.
2. Source logs `DEGRADED`, records error in `source_health_logs`.
3. Scheduler continues running remaining 7 connectors without crashing.

### Scenario E: Zero Generic Landing Pages
1. Test all source buttons across all displayed signals.
2. 0 instances of `newsapi.org/register`, `fda.gov`, or `ema.europa.eu` homepages.

---

## Plan Formulation for Phase 10

Phase 10 should be structured into **3 focused execution waves**:

- **Wave 10-01 (Connectors & Governance):**
  - Integrate `BioPharmaDiveRSSConnector` (8th connector).
  - Implement adaptive NewsAPI quota-aware polling governor.
  - Register BioPharma Dive in `haemophilia.yaml`, `backend/app/connectors/__init__.py`, and scheduler.

- **Wave 10-02 (Intelligence Explanations & Convergence UI):**
  - Build `EvidenceConvergenceWidget` (visual multi-source confluence tree).
  - Build `PriorityScoreExplainer` ("Why this signal?" additive score factors).
  - Build `RedTeamCounterFactuals` ("What could invalidate this assessment?").
  - Enhance `SignalCard` and `SignalDetailWorkspace` with explicit Source Hierarchy tags (`EVIDENCE PRIMARY`, `VALIDATION`, `DISCOVERY`).

- **Wave 10-03 (Executive Dashboard Briefing & E2E Verification):**
  - Refine Radar Dashboard overview with daily executive intelligence metrics.
  - Run all 5 brutal validation scenarios (Scenarios A through E).
  - Execute full test suite (all 139+ pytest suites, Next.js build, banned-classes check).

---

*Research complete: 2026-08-27*
