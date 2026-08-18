# MetaRadar: Feature Parity Matrix

**Version:** 5.1.0  
**Last Updated:** 2026-08-18  
**Generated From:** `docs/manifests/feature_parity_manifest.json`  
**Status Vocabulary:** `WIRED` (Implemented & Gated) · `PARTIAL` (Partially Wired) · `NOT_WIRED` (Planned/Unwired) · `DEFERRED` (Explicitly Deferred)

---

## Executive Parity Summary

| Metric | Count | Percentage |
|--------|-------|------------|
| **Total Specifications Audited** | **15** | **100.0%** |
| **Active In-Scope Features** | **13** | **86.7%** |
| **WIRED & Verified Features** | **13** | **86.7%** |
| **PARTIAL Implementations** | **0** | **0.0%** |
| **NOT_WIRED (Deferred Gaps)** | **0** | **0.0%** |
| **DEFERRED (Out of Scope)** | **2** | **13.3%** |
| **In-Scope Parity Coverage** | **13/13** | **100.0%** |

---

## Feature Parity Specification & Verification Matrix

| Doc Spec | Control / Feature | Component | Endpoint | Status | Notes |
|:---|:---|:---|:---|:---:|:---|
| `docs/4_UI_DESIGN_DOCUMENT.md §2.1` | Overview Dashboard (Four-Question Layout) | `DashboardPage` | `GET /api/v1/overview` | **WIRED** | Renders Q1-Q4 decision panels, KPI cards, trend chart, and confluence/lifecycle previews. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.1` | Signals Feed & Real-Time Stream | `SignalsPage` | `GET /api/v1/signals` | **WIRED** | Paginated signals list with priority badges, expandable drawer, and source metadata. |
| `docs/4_UI_DESIGN_DOCUMENT.md §4.2` | Apply Filter Control (Severity, Date, Entity, Type) | `FilterBar` | `GET /api/v1/signals` | **WIRED** | Inline expandable filter panel with server-side query parameter filtering. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.2` | Confluence Alerts View | `ConfluencePage` | `GET /api/v1/confluence` | **WIRED** | Displays multi-signal confluence stories, severity, and expandable evidence chains. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.3` | Lifecycle Timelines View | `LifecyclePage` | `GET /api/v1/lifecycles` | **WIRED** | State-machine timeline visualization across clinical/regulatory milestones. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.4` | Red-Team Contradictions View | `RedTeamPage` | `GET /api/v1/red-team` | **WIRED** | Surfaces pairwise claim contradictions with confidence scores and red-team notes. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.5` | Missing Signals View (Watch Rules) | `MissingSignalsPage` | `GET /api/v1/missing-signals` | **WIRED** | Overdue expected milestones with growing-confidence indicators and watch confirmation. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.6` | Ask Athena Synthesis Interface | `IntelligencePage` | `POST /api/v1/athena` | **WIRED** | Natural language Q&A with PII/PHI scrubbing and provider reasoning/degraded mode. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.7` | Developments Registry View | `DevelopmentsPage` | `GET /api/v1/developments` | **WIRED** | Development asset grouping, stage badges, and linked clinical signals. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.8` | Functions Routing Breakdown | `FunctionsPage` | `GET /api/v1/feedback/summary` | **WIRED** | Role-based relevance score routing bars and top function-targeted signals. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.9` | Sources Registry & Connector Health | `SourcesPage` | `GET /api/v1/sources` | **WIRED** | Registry of public sources with live connector statuses and freshness classes. |
| `docs/4_UI_DESIGN_DOCUMENT.md §4.4` | Settings & Cache Clear Confirmation Modal | `SettingsPage` | `POST /api/v1/cache/clear` | **WIRED** | Workspace controls (dark mode, polling interval) and Redis cache flush modal. |
| `docs/4_UI_DESIGN_DOCUMENT.md §1.1 #11` | Stakeholder Feedback Calibration Widget | `CalibrationWidget` | `POST /api/v1/feedback` | **WIRED** | Interactive 5-star HITL rating and batch recalibration. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.10` | Narrative Briefs Generation (/briefs) | `BriefsPage` | `POST /api/v1/briefs/generate` | `DEFERRED` | Requires net-new complex background narrative synthesis engine; deferred to Phase 7. |
| `docs/4_UI_DESIGN_DOCUMENT.md §3.11` | Weekly Intelligence Digest (/digest) | `DigestPage` | `GET /api/v1/digest/weekly` | `DEFERRED` | Requires periodic email/PDF compiler service; deferred to Phase 7. |

---

## Verification & Audit Governance

This matrix is validated by automated contract tests in `tests/test_parity_matrix.py`:
1. Every row marked `WIRED` has an active route in `contracts/openapi.json`.
2. Every component referenced is exported from `frontend/components/metaradar.tsx`.
3. Every test gate in `docs/rules/TESTING_STRATEGY.md` passes without warnings.
