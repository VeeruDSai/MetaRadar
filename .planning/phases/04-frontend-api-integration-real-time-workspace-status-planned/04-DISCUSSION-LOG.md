# Phase 4: Frontend API Integration & Real-Time Workspace - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 4-Frontend API Integration & Real-Time Workspace
**Areas discussed:** Live data refresh mechanism, Contract mapping strategy, Empty/degraded backend handling

---

## Live Data Refresh

| Option | Description | Selected |
|--------|-------------|----------|
| Polling on an interval | React Query/SWR or setInterval refetch every 15-30s. Simplest, works with existing REST endpoints, no backend infra changes. | ✓ |
| Server-Sent Events (SSE) | Streaming from FastAPI to push new signals. Near-instant, but adds new backend endpoint + reconnect logic for the RTX 3050 demo box. | |
| On-demand + visibility refetch | Refetch on mount, visibility change, manual refresh. No true "live" updates while sitting on a page. | |

**User's choice:** Polling on an interval

| Option | Description | Selected |
|--------|-------------|----------|
| 30s overview + signals, Athena manual | Overview refetches every 30s; signals 30s; Athena stays request/response. | ✓ |
| 15s everywhere | More aggressive, fresher demo feel. Higher load on demo box + Postgres. | |
| 30s overview, signals on-demand | Overview 30s; signals only on mount + manual refresh. | |

**User's choice:** 30s overview + signals, Athena manual

| Option | Description | Selected |
|--------|-------------|----------|
| Pause when tab hidden | Use document.visibilityState to pause polling in background, resume on focus. | ✓ |
| Always poll | Keep polling regardless of tab state. Simpler but wasteful. | |

**User's choice:** Pause when tab hidden

| Option | Description | Selected |
|--------|-------------|----------|
| Custom hook, no new deps | usePolling/useLiveData wrapping setInterval + fetch + visibility pausing. Fits minimal hand-rolled repo patterns. | ✓ |
| Add TanStack Query | Polling + caching + background refetch. Heavier dependency addition. | |

**User's choice:** Custom hook, no new deps

---

## Contract Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Frontend mapper in lib/api.ts | mapSignal/mapOverview transforms backend shapes into UI types. Canonical contract stays backend-true, zero backend changes, components unchanged. | ✓ |
| Backend enriches to UI shape | Backend /signals + /overview return the full UI shape. Contract gains UI-only fields; export script + drift tests updated. | |
| Hybrid | Frontend maps simple renames, backend adds server-derived values. More surface area. | |

**User's choice:** Frontend mapper in lib/api.ts

| Option | Description | Selected |
|--------|-------------|----------|
| Map what exists, leave rest empty | severity from priority, summary from content, detectedAt from published_at. UI-only fields with no backend source stay empty/undefined, rendered as neutral placeholders. Honest. | ✓ |
| Deterministic fallback values | Fill UI-only fields with priority-ranked placeholders. Richer UI but risks presenting placeholder numbers as real intelligence. | |

**User's choice:** Map what exists, leave rest empty

| Option | Description | Selected |
|--------|-------------|----------|
| Extend backend /overview to full shape | Return confluence, lifecycle, trends computed from real DB. Contract/OpenAPI updated via export script. Honest source for radar + momentum chart. | ✓ |
| Frontend derives from /signals | Confluence score and momentum derived from the /signals payload. Zero backend change but approximations. | |
| Hybrid | Backend extends confluence + lifecycle; frontend derives trends as 7-day signal-volume bucketing. | |

**User's choice:** Extend backend /overview to full shape

| Option | Description | Selected |
|--------|-------------|----------|
| Wire to real data, drop un-sourceable KPIs | Wire KPIs to what /overview + /health return. Drop "Time to decision" / "Source coverage" if no backend source. Honest empty rather than invented numbers. | ✓ |
| Keep demo KPI values labeled | Keep all four KPI cards with demo values, clearly labeled. Preserves the look but contradicts honest-telemetry. | |

**User's choice:** Wire to real data, drop un-sourceable KPIs

---

## Empty/Degraded Backend

| Option | Description | Selected |
|--------|-------------|----------|
| Honest empty/error states, drop synthetic fallback | Remove backend hardcoded fallback; return honest empty lists / 503. Frontend renders real empty states + error banner. Aligns with AGENTS.md + /health/ready degraded model. | ✓ |
| Labeled demo-mode toggle | Keep mock-data layer as env-flagged demo mode with banner; backend keeps fallback. Safe for demos without a running stack, but keeps fabricated data in the product path. | |

**User's choice:** Honest empty/error states, drop synthetic fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Distinguish empty vs unavailable | Empty DB → friendly empty state ("No signals yet — run the pipeline"). Backend down / 5xx → error banner with retry. | ✓ |
| Single generic state | One "data unavailable" state with retry. Simpler, less informative. | |

**User's choice:** Distinguish empty vs unavailable

| Option | Description | Selected |
|--------|-------------|----------|
| Wire health footer to real endpoints | Drive footer from /health/ready + /health/models; remove "Demo environment · Synthetic data" and "Synthetic signal environment" labels. | ✓ |
| Leave footer labels for now | Only swap data feeds; UI keeps claiming synthetic data. | |

**User's choice:** Wire health footer to real endpoints

| Option | Description | Selected |
|--------|-------------|----------|
| Manual retry + poll-cycle retry | "Retry" button plus automatic retry on next 30s poll cycle. No backoff complexity. | ✓ |
| Exponential backoff retry | Backoff retries with max before banner. More robust but more logic than the demo needs. | |

**User's choice:** Manual retry + poll-cycle retry

| Option | Description | Selected |
|--------|-------------|----------|
| Non-blocking warning banner | Show warning banner when /health/ready is degraded but app still renders data. Matches backend fail-degrade design. | ✓ |
| Treat degraded as error | Treat degraded like down. Simpler but overstates severity. | |

**User's choice:** Non-blocking warning banner

---

## the agent's Discretion

- **Search (⌘K) wiring:** presented but not selected for discussion. Phase 3's `search.py` docstring says the Phase 4 frontend consumes `POST /api/v1/search`. Researcher confirms the contract; planner may wire ⌘K search or leave as placeholder — keep small.
- **AthenaResponse mapping:** real `/athena` returns `evidence_count` not `sources`; planner picks the minimal honest adaptation.
- **Unused client helpers:** `getSignals` / `getTrends` / `getHealth` / `getSources` in `lib/api.ts` — consolidate or drop as appropriate.

## Deferred Ideas

- **Ask Athena grounded in search retrievals** — possible later-phase enhancement; REQ-P4-3 scopes Athena to `/athena` only.