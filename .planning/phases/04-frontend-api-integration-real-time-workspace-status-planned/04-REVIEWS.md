---
phase: 04
reviewers:
  - codex
reviewed_at: 2026-08-18T02:14:00Z
plans_reviewed:
  - 04-01-PLAN.md
  - 04-02-PLAN.md
  - 04-03-PLAN.md
---

# Cross-AI Plan Review — Phase 04: Frontend API Integration & Real-Time Workspace

## Codex Review

### Summary
The wave ordering (Wave 1: Backend & Client/Mapper/Hook; Wave 2: UI Workspace) is sound and strongly reflects the project's decisions on visibility-aware polling, anti-corruption mappers, and honest empty states. However, the plans need explicit Pydantic response models for `/overview`, concurrency/abort guards in the polling hook, robust error/retry handling in the Ask Athena UI, and precise search accessibility and empty-state taxonomy to achieve high-grade execution.

### Strengths
- **Clean Architecture & Separation of Concerns**: Clear demarcation between backend transport models, anti-corruption client mappers (`lib/api.ts`), custom React hooks (`lib/hooks.ts`), and UI presentation components (`metaradar.tsx`).
- **Strict Adherence to Decisions**: Eliminates backend synthetic try/except dictionary fallbacks (D-08), implements 30s polling with Page Visibility API (D-01, D-02, D-03), and removes hardcoded synthetic/demo labels across sidebar and footer (D-10).
- **Graceful Degradation Support**: Non-blocking amber warning banners for degraded health (D-12) and honest empty states when the database contains 0 signals (D-09).
- **Comprehensive Quality Gates**: Mandates strict TypeScript (`tsc --noEmit`), ESLint clean checks, Next.js build compilation, and pytest contract drift gates.

### Concerns & Findings

#### High Severity
1. **Backend Contract & Schema Explicitness (Plan 04-01)**:
   - Persisted `Signal` models in `backend/app/models/__init__.py` do not directly supply every UI field (`sources`, `stakeholders`, `score`, `confidence`).
   - *Correction*: Define explicit versioned Pydantic response schemas for `/overview` (`OverviewResponse`, `ConfluenceSummary`, `LifecycleSummary`, `TrendPoint`) and `/signals` (`SignalListResponse`). Ensure mapper functions explicitly define defaults/placeholders for unpopulated fields rather than inventing numbers.
2. **Polling Concurrency & Abort Safety (Plan 04-02)**:
   - Polling loops without `AbortController` or in-flight tracking can lead to out-of-order resolution, request overlap on slow networks, and state updates after unmount.
   - *Correction*: Integrate `AbortController` and cleanup guards into `useLiveData`, and ensure safe SSR execution in Next.js (checking `typeof document !== 'undefined'`).
3. **Ask Athena UI Completion (Plan 04-03)**:
   - `REQ-P4-3` must have a dedicated, robust UI task covering prompt input validation, loading animation, promise rejection/error recovery, and honest rendering of answer, confidence, and evidence count.
4. **Search Capability Labeling**:
   - `backend/app/services/vector_query.py` executes pgvector embedding + cosine similarity search. UI search modal should accurately describe its capability (Semantic Vector Search) without overstating lexical hybrid mechanisms until BM25 is added.

#### Medium Severity
1. **Health Polling Cadence**:
   - `/health/models` checks Ollama model status on every request. It should not be polled at high 30s frequency across multiple components; decouple health status polling to 60s or server-side cache.
2. **Comprehensive Empty State Matrix**:
   - Explicitly distinguish between: (a) Initial Loading, (b) DB Empty (0 signals overall -> Call to Action to run pipeline), (c) Filter Empty (0 signals matching current severity filter), and (d) Backend Offline / 503 (Error banner with manual retry).
3. **Complete Elimination of Hardcoded Demo Values**:
   - Enumerate all static UI values in `metaradar.tsx` (e.g. hardcoded KPI values `38`, `78`, `4.6d`, `94%`, hardcoded dates, synthetic banners) to ensure complete replacement with live backend data.

---

## Consensus & Actionable Plan Refinements

| Plan | Target Improvement | Impact |
|:---|:---|:---|
| **04-01** | Add explicit Pydantic response models (`OverviewResponse`, `SignalItemResponse`) and set-based aggregation queries. | Prevents schema drift and guarantees API contract stability. |
| **04-02** | Add `AbortController`, in-flight concurrency guards, typed `ApiError`, and SSR safety checks to `useLiveData`. | Prevents memory leaks, race conditions, and Next.js hydration issues. |
| **04-03** | Add dedicated Ask Athena UI task with error recovery; add accessible ⌘K search dialog with keyboard trap/Escape; map full empty-state taxonomy. | Fulfills `REQ-P4-3` and guarantees honest, production-grade user experience. |
