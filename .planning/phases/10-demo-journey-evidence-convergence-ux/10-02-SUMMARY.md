---
phase: 10-demo-journey-evidence-convergence-ux
plan: 10-02
subsystem: frontend-signals
tags: [evidence-convergence, priority-explainer, red-team-falsification, source-hierarchy, ui]
requires:
  - plan: 10-01
    provides: BioPharma Dive connector, adaptive quota governor
provides:
  - EvidenceConvergenceWidget displaying multi-source alignment tree (Authoritative vs Discovery)
  - PriorityScoreExplainer with additive scoring factor breakdown (+pts)
  - RedTeamCounterFactuals displaying active self-challenging conditions
  - Explicit Source Hierarchy tags across SignalCard and SignalDetailWorkspace
  - Clean Next.js 16 build with 0 banned Tailwind classes
affects: [frontend, signals]
key-files:
  created:
    - frontend/components/signals/EvidenceConvergenceWidget.tsx
    - frontend/components/signals/PriorityScoreExplainer.tsx
    - frontend/components/signals/RedTeamCounterFactuals.tsx
  modified:
    - frontend/components/signals/SignalCard.tsx
    - frontend/components/signals/SignalDetailWorkspace.tsx
---

# Plan 10-02 Summary: Evidence Convergence Tree, Explainer & Counter-Factuals

## Executed Work
1. **Evidence Convergence Tree Component (`EvidenceConvergenceWidget.tsx`)**:
   - Built visual multi-source alignment tree categorizing sources into Tier 1 Authoritative (ClinicalTrials.gov, PubMed), Tier 1 Regulatory (FDA, EMA), and Tier 3 Discovery (Fierce Pharma, ET Pharma, BioPharma Dive, NewsAPI).
   - Features robust single-source fallback rendering and multi-source corroboration status.
2. **Priority Scoring Factor Breakdown (`PriorityScoreExplainer.tsx`)**:
   - Replaced opaque priority numbers with transparent additive clinical factors: `+30 Phase III / Late-Stage Readout`, `+25 Key Competitor Asset`, `+20 Multi-Source Corroboration`, `+15 Tier 1 Authoritative Provenance`.
3. **Self-Challenging AI Red-Team Falsification (`RedTeamCounterFactuals.tsx`)**:
   - Built "What Would Change Our Assessment?" panel surfacing 3 stress-test criteria: Independent Clinical Replication, Registry Protocol Revision, and Regulatory PDUFA Delay.
4. **Source Hierarchy Tags & Confluence Badge**:
   - Updated `SignalCard.tsx` with explicit visual badges: `EVIDENCE PRIMARY`, `VALIDATION`, and `DISCOVERY`, along with `{N}x Convergence` pills.
5. **Layout Integration & Gate Verification**:
   - Integrated all 3 components into `SignalDetailWorkspace.tsx`.
   - `node scripts/check-banned-classes.mjs`: Clean across 31 files.
   - `npm --prefix frontend run build`: Clean Next.js 16 Turbopack production build.
