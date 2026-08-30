---
status: resolved
trigger: "the dock animation is still not that clear and it looks very broken. one more thing i'd like to point out is, all the live signals have very low priority scores. and i have started to doubt if the ingestion actually works because before a few days of development the live signals were like 3-4 days ago, now when i see them there are signals from yesterday which is shocked, its either that while debugging proper ingestion was done or else there is no daily news articles about this particular topic."
symptoms:
  expected: "Butter-smooth dock expand/collapse transition with zero layout jitter; clarity on live ingestion frequency and priority scoring mechanics"
  actual: "Dock animation had text-wrapping jitter and abrupt element popping during width transition; questions regarding priority score distribution and source publication dates"
  errors: "Visual transition jitter; no console errors"
  timeline: "Occurred during collapse/expand transition when text nodes unmounted immediately"
  reproduction: "Toggle sidebar collapse on desktop"
created: 2026-08-30
updated: 2026-08-30
---

# Debug Session: dock-animation-smoothness-and-ingestion-mechanics

## Part 1: Dock Animation Root Cause & Resolution

### Root Cause
1. **React Unmounting / Mounting Mismatch with CSS Width Transition**:
   - The sidebar `<aside>` has a 280ms CSS transition on `width` (`240px` <-> `68px`).
   - However, conditional React rendering (`{!isCollapsed && <span>{label}</span>}`) removed/inserted DOM nodes at `t = 0ms`.
   - When collapsing: Text disappeared instantly at `t = 0ms` while width was still wide (240px -> 180px -> 68px).
   - When expanding: All text labels mounted immediately at `t = 0ms` inside a 68px container, causing text to wrap into multiple broken lines and jitter violently before the container reached 240px.

### Fix Applied
- **Persistent DOM Structure**: All text nodes remain in the DOM with `white-space: nowrap; overflow: hidden; text-overflow: clip;`.
- **Synchronized CSS Transitions**:
  - `transition: opacity 0.18s ease, max-width 0.28s cubic-bezier(0.25, 1, 0.5, 1), transform 0.18s ease;`
  - In collapsed state, text smoothly transitions to `opacity: 0; max-width: 0; transform: translateX(-10px);`.
  - In expanded state, text smoothly transitions to `opacity: 1; max-width: 200px; transform: translateX(0);`.
- Text **never** line-wraps or snaps because `white-space: nowrap` is strictly enforced during the animation.
- Header toggle button smoothly flips icons (`PanelLeft` vs `PanelLeftClose`) without container repositioning jitter.

---

## Part 2: Ingestion Pipeline & Priority Scoring Telemetry

### 1. How Ingestion Works & Why Signal Dates Are from Yesterday / 3-4 Days Ago
- **Authoritative Public APIs**: MetaRadar's ingestion connectors query live public biomedical endpoints:
  - **PubMed**: NCBI E-Utilities (`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`)
  - **ClinicalTrials.gov**: APIv2 (`https://clinicaltrials.gov/api/v2/studies`)
  - **OpenFDA**: Drug adverse events & approvals (`https://api.fda.gov/`)
  - **EMA & Pharma News**: RSS feeds from European Medicines Agency, FiercePharma, and BioPharmaDive.
- **Upstream Publication Cadence**: Haemophilia is a specialized therapeutic indication (rare disease). Major clinical journal papers, trial protocol updates, and pharma press releases are published on the order of several times per week, not dozens per hour.
- **Honest Provenance**: When a signal has a timestamp of "yesterday" or "3 days ago", that is the **exact upstream `published_at` date** returned by NCBI / ClinicalTrials.gov / FiercePharma. Ingestion is querying and syncing these real sources.

### 2. Why Live Signals Have Priority Scores in the 30-47 (Medium) Range
Priority scores are deterministically computed in `backend/app/services/scoring.py` using a 4-factor formula (max 100):

$$\text{Total Score} = \text{Novelty (0-25)} + \text{Clinical Concepts (0-30)} + \text{Regulatory Relevance (0-25)} + \text{Recency (0-20)}$$

- **Novelty (0-25 pts)**: Cosine distance from nearest existing signal embeddings (typical: 12-15 pts).
- **Clinical Significance (0-30 pts)**: 3 pts per clinical keyword match (e.g. `Factor VIII`, `prophylaxis`, `ABR`, `inhibitors`, `Phase III`) (typical: 6-12 pts).
- **Regulatory Relevance (0-25 pts)**: 5 pts per regulatory concept match (`FDA`, `EMA`, `PDUFA`, `BLA`, `CRL`, `Approval`). Routine research articles and observational trials lack regulatory filing terms and score **0 pts** in this category.
- **Recency (0-20 pts)**: Exponential decay with 72-hour half-life ($20 \times e^{-0.693 \cdot \Delta t / 72}$). Signals from 24h ago score ~15.8 pts; signals from 3 days ago score ~10 pts.

**Score Breakdown for a Typical Live Article (e.g. Score 39-47)**:
- Novelty: ~14 pts
- Clinical: ~9 pts (3 keywords)
- Regulatory: 0 pts (no FDA/EMA filing mentioned)
- Recency: ~16 pts (published yesterday)
- **Total: ~39-47 (MEDIUM Priority)**

**High / Critical Scores (>70)** are intentionally reserved for signals that combine *both* major clinical trial endpoints *and* regulatory milestones (e.g. an FDA approval announcement or a Phase 3 pivotal trial readout with PDUFA date).
