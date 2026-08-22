# Phase 07: Trustworthy Intelligence Reconciliation & Platform Hardening Specification

> **Phase Reference:** Phase 07  
> **Source Specification:** [11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md)  
> **Execution Mode:** Single-Wave Continuous Execution (All 36 engineering dimensions in 1 wave)

---

## Purpose & Scope

This phase executes a holistic audit, data-truthfulness reconciliation, intelligence pipeline correction, observability upgrade, frontend modularization, and codebase-map update for MetaRadar v5.1. 

The goal is to transition MetaRadar from an early prototype with potential placeholder mockups into an enterprise-grade, rigorously verified competitive intelligence platform where **every number, status, excerpt, and metric is truthful, computed, and traceable to verified bronze sources**.

---

## Core Pillars of Phase 07

1. **Elimination of Fabricated Intelligence & Placeholders**
   - Zero hardcoded scores (priority, confluence, confidence, momentum).
   - Zero synthetic excerpts in Red-Team contradictions or Athena synthesis.
   - Clean removal of dead code and obsolete mock files.

2. **Synthetic Data Governance**
   - Strict typing with `is_synthetic: bool`, `data_mode: "live" | "recorded_demo" | "test_fixture"`, and `provenance_status`.
   - High-visibility UI labeling separating live production feeds from recorded demo scenarios.

3. **Deterministic Scoring & Confluence Engines**
   - Transparent, versioned Priority Scoring ($P \in [0, 100]$) with exact score breakdown (`Novelty`, `Clinical`, `Regulatory`, `Recency`).
   - Real multi-source convergence calculation across $\ge 3$ independent source types in 48-hour windows.
   - Categorized confidence semantics (`extraction`, `classification`, `heuristic`, `model`, `human`).

4. **Athena Retrieval Truth & Red-Team Integrity**
   - Strict pgvector cosine similarity retrieval with verbatim evidence citations.
   - Direct rejection when evidence is insufficient (`"No sufficiently relevant evidence found"`).
   - Real pairwise contradiction detection with verbatim claim citations and 19-rule taxonomy.

5. **Operational Observability & Correlation Tracing**
   - Real connector health monitoring (`HEALTHY`, `DEGRADED`, `STALE`, `RATE_LIMITED`, `AUTH_FAILED`, `ERROR`, `DISABLED`, `NEVER_CONNECTED`).
   - End-to-end correlation IDs (`X-Request-ID`, `X-Correlation-ID`, `pipeline_run_id`).
   - Structured JSON logging across all backend services, connectors, and workflow nodes.

6. **Frontend Architecture Refactor & Error Resilience**
   - Refactor monolithic `metaradar.tsx` into clean bounded contexts under `frontend/components/` and `frontend/lib/`.
   - Comprehensive error UX with reusable `ErrorState` components, retry buttons, and diagnostic correlation IDs.
   - Complete 8-state UI representation (`loading`, `success`, `empty`, `stale`, `degraded`, `unavailable`, `error`, `not_computed`).

7. **Database & Lifecycle Correctness**
   - Idempotent `CalibrationRun` lifecycle (unapplied feedback -> run -> applied -> history).
   - Pure GET endpoints with zero database mutations.
   - Timezone-aware UTC datetimes and robust asyncpg connection handling.

8. **Automated Verification & Codebase Map Synchronization**
   - Comprehensive backend and frontend invariant test suite.
   - Automated failure-injection tests (API rate limits, timeouts, DB/Redis disconnects, LLM outages).
   - Full regeneration and synchronization of all `.planning/codebase/` documentation.

---

## Detailed Guidelines & Decision Log

See [docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md) for full architectural guidelines, mathematical formulations, schema definitions, and testing standards.
