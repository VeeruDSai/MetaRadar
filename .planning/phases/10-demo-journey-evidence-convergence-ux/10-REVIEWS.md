---
phase: 10
reviewers: [gemini, codex, claude]
reviewed_at: 2026-08-27T01:03:00Z
plans_reviewed:
  - 10-01-PLAN.md
  - 10-02-PLAN.md
  - 10-03-PLAN.md
---

# Cross-AI Plan Review — Phase 10: Undeniable Demo Journey, Evidence Convergence, BioPharma Dive & UX Refinement

## Consensus Summary

All three reviewer evaluations agree that **Phase 10 is appropriately scoped, tightly bounded, and directly targets the highest-value demonstration goals** without introducing architectural risk or unneeded dependencies. The shift from "expanding features" to "making existing capabilities undeniable" is strongly endorsed.

### Agreed Strengths
- **BioPharma Dive via Stdlib XML:** Reusing `xml.etree.ElementTree` with domain keyword filtering mirrors proven `EMARSSConnector` and `FiercePharmaRSSConnector` patterns without adding third-party packages.
- **NewsAPI Adaptive Quota Governor:** Protecting the 100 req/day cap via dynamic interval adjustment (30m → 90m → pause at <15) directly eliminates a major live demonstration vulnerability.
- **Progressive Intelligence Disclosure:** `EvidenceConvergenceWidget`, `PriorityScoreExplainer`, and `RedTeamCounterFactuals` convert opaque numbers and internal LangGraph states into understandable, interactive UI assets.
- **Brutal E2E Verification Suite:** Automated script `scripts/test_demo_scenarios_e2e.py` covering Scenarios A through E guarantees end-to-end reliability.

### Agreed Concerns & Mitigations
1. **Single-Source Evidence Rendering (Medium):** When a signal has only 1 source, `EvidenceConvergenceWidget` must display a clean single-source provenance summary rather than an awkward empty tree.
   - *Mitigation:* Include a single-source "Direct Evidence Anchor" view when `sources.length === 1`.
2. **Backward-Compatible Score Factors (Medium):** Legacy or synthetic signals without explicit `priority_factors` arrays could cause `PriorityScoreExplainer` to fail.
   - *Mitigation:* Implement defensive score factor synthesis falling back to standard 4-factor weights (`Clinical Impact`, `Competitor Asset`, `Source Authority`, `Recency`).
3. **RSS Date Parsing Edge Cases (Low):** BioPharma Dive RSS dates can vary in timezone representation.
   - *Mitigation:* Use `email.utils.parsedate_to_datetime` for standard RFC 2822 / 822 compliance.

---

## Gemini Review (Architecture & Integration)

### Summary
The plan cleanly executes the necessary connector and scheduler adjustments. Upgrading BioPharma Dive from `configured_no_feed` to an active 8th connector closes a known catalog gap with zero external scraping dependencies.

### Strengths
- Clear file-by-file changes across `backend/app/connectors/biopharma_dive.py`, `backend/app/services/scheduler.py`, and `config/haemophilia.yaml`.
- Adaptive throttling logic in `SourceScheduler` handles developer quota limits without database schema migrations.
- Explicit health telemetry in `GET /api/v1/health/sources` exposes `quota_remaining`.

### Concerns
- `haemophilia.yaml` updates must maintain strict YAML validation in `backend/app/core/domain_config.py:112`.
- Connector error logs during quota pause should clearly state `HEALTHY (QUOTA_PRESERVED)` to avoid false positive error alarms in the UI.

### Risk Assessment
- **Risk Level:** `LOW` — Architecture is stable, changes are additive and isolated.

---

## Codex Review (Frontend Architecture & Interactions)

### Summary
The UI plan effectively concentrates on the **Signal Card + Signal Detail Workspace** as the primary product surface. Transforming raw scores into additive clinical factors and multi-source confluence into an evidence tree will impress evaluators.

### Strengths
- 100% token adherence with CSS variables from `globals.css` and verified zero banned Tailwind classes.
- Explicit visual taxonomy: `EVIDENCE PRIMARY` (CT.gov, PubMed) vs `VALIDATION` (FDA, EMA) vs `DISCOVERY` (Fierce, ET, BioPharma Dive, NewsAPI).
- Responsive grid breakdown ensures readability on all screen resolutions.

### Concerns
- `EvidenceConvergenceWidget.tsx` must be responsive and collapse gracefully on mobile viewports.
- Tooltips or information badges on `RedTeamCounterFactuals` should clearly clarify that these are AI-generated stress-test questions, not active contradictions.

### Risk Assessment
- **Risk Level:** `LOW` — Highly modular components with isolated render boundaries.

---

## Claude Review (Verification & Scenario Testing)

### Summary
Plan 10-03's 5-scenario testing harness (`scripts/test_demo_scenarios_e2e.py`) is the ideal verification gate for a hackathon-ready release. It verifies the complete signal lifecycle from ingestion to immutable audit log persistence.

### Strengths
- Execution of Scenarios A through E validates all critical user and system journeys.
- Zero-generic-URL gate (`test_provenance.py` / Scenario E) guarantees that no dead or redirect landing pages appear in the evidence links.
- Maintains strict CI invariants: TypeScript type checking, Pytest 100% pass rate, contract sync gate.

### Concerns
- Ensure that the automated scenario test script is self-contained, resets test database state cleanly, and does not interfere with existing unit test suites.

### Risk Assessment
- **Risk Level:** `LOW` — Comprehensive test harness prevents regressions.

---

## Final Review Verdict

**Recommendation:** **APPROVED — Proceed to Execution (`/gsd-execute-phase 10`)**.
