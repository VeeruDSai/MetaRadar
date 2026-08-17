# Phase 4: Frontend API Integration & Real-Time Workspace - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Connect the Next.js App Router UI (`frontend/lib/api.ts`) to the real FastAPI backend `/api/v1` REST endpoints (`/signals`, `/overview`, `/athena`). Replace the mock-data layer with a live client, render real signals with severity filtering and evidence drawers, wire Ask Athena to `/athena`, and render portfolio momentum charts and confluence radar visualizations fed by real backend data. The workspace becomes "live" (30s polling) rather than a one-shot mount fetch.

</domain>

<decisions>
## Implementation Decisions

### Live Data Refresh
- **D-01:** Polling on a fixed interval drives "real-time" updates — no SSE/WebSocket infrastructure added. 30s cadence for the dashboard overview and the signals feed; Ask Athena stays request/response (no polling of an LLM synthesis call). — **Reversibility:** reversible — swaps to SSE/WS later without migrating persisted state.
- **D-02:** Polling pauses when the browser tab is hidden (`document.visibilityState`) and resumes on focus — saves the RTX 3050 demo box and Postgres from idle poll cycles.
- **D-03:** The polling layer is a custom hook (e.g., `usePolling`/`useLiveData`) wrapping `setInterval` + `fetch` + visibility pausing. No new dependencies (no TanStack Query) — fits the repo's minimal hand-rolled pattern.

### Contract Mapping
- **D-04:** A frontend mapper module in `frontend/lib/api.ts` (e.g., `mapSignal`, `mapOverview`) transforms backend response shapes into the UI types components already consume (`Signal`, `DashboardOverview`). The canonical OpenAPI contract (`frontend/types/api.ts`) stays backend-true; existing components (`SignalRow`, `Radar`, `TrendChart`) keep working unchanged. — **Reversibility:** reversible — mapping is local to the frontend client.
- **D-05:** The mapper maps what the backend actually returns (e.g., `priority` → `severity`, `content` → `summary`, `published_at` → `detectedAt`) and leaves UI-only fields with no backend source (`score`, `confidence`, `stakeholders`, `tags`, `sources`) empty/undefined, rendering neutral placeholders. No invented numbers — honest telemetry per AGENTS.md.
- **D-06:** The backend `/overview` endpoint is extended to return the full dashboard shape — `confluence` (score/label/drivers), `lifecycle`, and `trends` — computed from real DB data (signal counts per development stage, aggregated velocity). The mapper then only adapts names. Contract/OpenAPI updated through `scripts/export_openapi.py` to keep the drift gate green. — **Reversibility:** costly — changes the canonical OpenAPI contract and the `/overview` response; undoing requires reverting the backend endpoint, the exported contract, and the mapper.
- **D-07:** KPI cards wire to what `/overview` and `/health` actually return (`active_signals`, `weekly_change`, latency, source_count). KPIs with no backend source at all ("Time to decision 4.6d", "Source coverage 94%") are dropped or neutralized rather than rendered with demo values.

### Empty/Degraded Backend
- **D-08:** Honest empty/error states. The backend's hardcoded synthetic fallback (`signals.py` try/except → canned payload) is removed; endpoints return honest empty lists or 503 on DB failure. The frontend renders real empty states and error banners. No labeled demo-mode toggle in the product path.
- **D-09:** The UI distinguishes "DB empty — no signals yet" (friendly empty state per section, e.g., "No signals yet — run the pipeline") from "backend unreachable" (error banner with retry), driven by fetch failures and the existing `/health/ready` status.
- **D-10:** The sidebar "Synthetic signal environment" note and footer "Demo environment · Synthetic data" labels are removed; the footer health strip is wired to the real `/health/ready` and `/health/models` endpoints (api status, last sync, latency, provider/model info).
- **D-11:** Retry = manual "Retry" button on the error banner plus automatic retry on the next 30s poll cycle. No exponential backoff complexity — polling already provides the retry cadence.
- **D-12:** A `degraded` `/health/ready` status (e.g., Redis down, app still functional) renders a non-blocking warning banner — the workspace still renders data, matching the backend's fail-degrade design.

### the agent's Discretion
- **Search (⌘K) wiring:** The existing "Search signals" button in the topbar was presented as a gray area but the user did not select it for discussion. NOTE: Phase 3's `backend/app/api/v1/endpoints/search.py` docstring explicitly states the Phase 4 frontend consumes `POST /api/v1/search`. Researcher should confirm the `/search` contract; planner may wire the ⌘K search to `/search` or leave it as a placeholder — use judgment, keep it small, and do not let it grow past a lightweight search box → results list.
- **AthenaResponse mapping:** The real `/athena` returns `answer`, `confidence`, `evidence_count`; the UI `AthenaResponse` type expects `sources`. Planner decides the minimal honest adaptation (e.g., render evidence count, drop the mock sources list).
- **`getSignals` / `getTrends` / `getHealth` / `getSources`** in `lib/api.ts` are defined but unused today; the mapper refactor may consolidate or drop them as the researcher/planner sees fit.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Specifications (ROADMAP-mandated for Phase 4)
- `docs/4_UI_DESIGN_DOCUMENT.md` — §3 Page Specifications (dashboard `/dashboard`, signals, Ask Athena `/athena`), §4 Interactive Elements, §15 Four-Question Display Specifications
- `docs/METARADAR_MASTER_PLAN_v5.0.md` §3 — Four-Question Decision Interface (Q1–Q4 panels the UI must express)
- `docs/rules/ARCHITECTURE_RULES.md` — approved Next.js 16 + FastAPI + PostgreSQL 16 architecture (no silent architecture changes)

### Contract Governance
- `contracts/openapi.json` — OpenAPI 3.1 schema snapshot; the drift gate compares against it
- `frontend/types/api.ts` — canonical generated TS contract (backend + UI-domain fields); MUST be regenerated via `scripts/export_openapi.py`, not hand-edited
- `scripts/export_openapi.py` — OpenAPI JSON + TypeScript contract generator; `python scripts/export_openapi.py` must stay 0-drift

### Backend API Surface (Phase 4 wiring targets)
- `backend/app/api/v1/endpoints/signals.py` — `/signals`, `/overview`, `/athena` (endpoints to wire; `/overview` to be extended per D-06)
- `backend/app/api/v1/endpoints/search.py` — `POST /api/v1/search` hybrid vector search (Phase 3; docstring says Phase 4 frontend consumes it)
- `backend/app/api/v1/endpoints/health.py` — `/health/ready`, `/health/models` (footer health strip + degraded banner sources)
- `backend/app/api/v1/endpoints/pipeline.py` — `POST /pipeline/run`, `GET /pipeline/status/{id}` (run trigger, relevant to "No signals yet — run the pipeline" empty state)

### Frontend Files
- `frontend/lib/api.ts` — mock seam to be replaced with the real fetch client + mapper (D-04)
- `frontend/components/metaradar.tsx` — `Shell`, `DashboardPage`, `SignalsPage`, `IntelligencePage`, `SignalRow`, `SignalDrawer`, `Radar`, `TrendChart`, `KPI`, `GenericPage`
- `frontend/lib/mock-data.ts` — synthetic fixtures; to be removed or repurposed as test fixtures only

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SignalRow`, `SignalDrawer`, `Radar`, `TrendChart`, `KPI`, `Badge`, `Card` in `frontend/components/metaradar.tsx`: already render from the UI types — the mapper (D-04) keeps them working unchanged.
- `/health/ready` and `/health/models` endpoints: ready/degraded status + provider/model metadata for the footer and degraded banner (D-10, D-12).
- `/api/v1/search` from Phase 3: existing hybrid vector search endpoint for the ⌘K search (agent discretion).

### Established Patterns
- Canonical contract flow: any backend response shape change (D-06) MUST flow through `scripts/export_openapi.py` and `contracts/openapi.json` to keep the contract-drift pytest green.
- Strict quality gates: `tsc --noEmit` 0 errors (`ignoreBuildErrors: false`), ESLint flat config 0 errors, `next build` clean, `pytest -v` passing.
- Backend fail-degrade design (`/health/ready` → `ready`/`degraded`): the UI's degraded handling (D-12) mirrors this.
- Honest telemetry (AGENTS.md): no fabricated data in the product path — drives D-05, D-07, D-08, D-10.
- Hand-rolled minimal client (mock `api.ts` with `delay()` helper): no data-fetching library in the stack — D-03 stays consistent.

### Integration Points
- `frontend/lib/api.ts`: the single seam where mock `delay()` calls are swapped for real `fetch` + mapper (D-04, D-08).
- `DashboardPage` / `SignalsPage` / `IntelligencePage` `useEffect(() => getOverview(), [])`: the one-shot fetches to be replaced by the polling hook (D-01).
- Footer health strip + sidebar "Synthetic signal environment" note: to be wired to real health endpoints and de-labeled (D-10).
- Topbar "Search signals" ⌘K button: candidate consumer of `/api/v1/search` (agent discretion).

</code_context>

<specifics>
## Specific Ideas

No specific requirements beyond the decisions captured above — open to standard approaches for the polling hook, mapper module shape, and empty-state visuals (follow the existing `.planning/codebase/CONVENTIONS.md` and `docs/4_UI_DESIGN_DOCUMENT.md` §8 Error & Empty States).

</specifics>

<deferred>
## Deferred Ideas

- **Ask Athena grounding with search results** (Athena answering grounded in `POST /api/v1/search` retrievals) — presented during discussion but not selected; a possible enhancement for a later phase. Not required by REQ-P4-3, which scopes Athena to `/athena`.
- None — discussion otherwise stayed within phase scope.

</deferred>

---

*Phase: 4-Frontend API Integration & Real-Time Workspace*
*Context gathered: 2026-08-18*