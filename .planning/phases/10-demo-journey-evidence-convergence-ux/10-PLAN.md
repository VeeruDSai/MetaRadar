# Phase 10 — Master Plan: Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement

**Phase:** Phase 10  
**Status:** Planned  
**Goal:** Perfect the 6-question signal journey, add active BioPharma Dive RSS connector (8th connector), implement adaptive NewsAPI quota governor, surface Evidence Convergence & "Why This Signal?" explainers, expose Red-Team self-challenging counter-factuals, and run brutal end-to-end scenario verifications.  
**Requirements:** REQ-P10-01 … REQ-P10-15  

---

## Waves Overview

```
Phase 10: Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement
├── Wave 1: 10-01-PLAN.md — BioPharma Dive RSS Connector & Adaptive NewsAPI Quota Governor
├── Wave 2: 10-02-PLAN.md — Evidence Convergence Tree, Explainer & Counter-Factuals
└── Wave 3: 10-03-PLAN.md — Executive Briefing Dashboard & Brutal 5-Scenario E2E Verification
```

---

## Wave Breakdown

### [Wave 1: 10-01-PLAN.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/10-demo-journey-evidence-convergence-ux/10-01-PLAN.md)
- **Objective:** Connect verified BioPharma Dive RSS feed (`https://www.biopharmadive.com/feeds/news/`), upgrade domain config from `configured_no_feed` to active source, and implement adaptive NewsAPI quota governor (30m/90m/pause) with UI quota badge.
- **Key Files:** `backend/app/connectors/biopharma_dive.py`, `backend/app/connectors/__init__.py`, `config/haemophilia.yaml`, `backend/app/services/scheduler.py`, `tests/test_connector_health.py`.

### [Wave 2: 10-02-PLAN.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/10-demo-journey-evidence-convergence-ux/10-02-PLAN.md)
- **Objective:** Build `EvidenceConvergenceWidget`, `PriorityScoreExplainer`, and `RedTeamCounterFactuals` components; integrate source hierarchy tags (`EVIDENCE PRIMARY`, `VALIDATION`, `DISCOVERY`) across `SignalCard` and `SignalDetailWorkspace`.
- **Key Files:** `frontend/components/signals/EvidenceConvergenceWidget.tsx`, `frontend/components/signals/PriorityScoreExplainer.tsx`, `frontend/components/signals/RedTeamCounterFactuals.tsx`, `frontend/components/signals/SignalCard.tsx`, `frontend/components/signals/SignalDetailWorkspace.tsx`.

### [Wave 3: 10-03-PLAN.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/.planning/phases/10-demo-journey-evidence-convergence-ux/10-03-PLAN.md)
- **Objective:** Refine main dashboard into a daily executive briefing view, build automated 5-scenario E2E test harness (`scripts/test_demo_scenarios_e2e.py`), and execute complete test matrix.
- **Key Files:** `frontend/app/page.tsx`, `scripts/test_demo_scenarios_e2e.py`, `tests/test_signal_routing_workflow.py`.

---

## Verification Gates

1. `pytest tests/ -v -m "not live"` (All 140+ tests pass)
2. `node scripts/check-banned-classes.mjs` (0 Tailwind token violations)
3. `npm --prefix frontend run build` (Next.js 16 production build clean)
4. `python scripts/export_openapi.py` (Contracts synchronized)
5. `python scripts/test_demo_scenarios_e2e.py` (Scenarios A through E pass)
