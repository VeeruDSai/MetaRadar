# Phase 4: Frontend API Integration & Real-Time Workspace — Technical Research

> **Target Phase:** Phase 4 (Frontend API Integration & Real-Time Workspace)  
> **Status:** Research Complete & Prescriptive  
> **Specification Authority:** `docs/rules/*`, `docs/4_UI_DESIGN_DOCUMENT.md`, `docs/METARADAR_MASTER_PLAN_v5.0.md` §3, `docs/10_ARCHITECTURE_HARDENING_REPORT.md` §6, and `04-CONTEXT.md`.

---

## Executive Summary

Phase 4 bridges the Next.js 16 App Router interface to the live FastAPI backend (`/api/v1`). It replaces the static mock fixture seam (`frontend/lib/mock-data.ts`) with a live typed REST client, an anti-corruption mapping layer (`frontend/lib/api.ts`), and a client-side polling hook with Page Visibility pausing (30s cadence).

The primary architectural mandate is **Honest Telemetry**: eliminate all synthetic fallbacks from the backend endpoints and UI fixtures, render honest empty states when the database contains no signals, surface degraded status banners when optional sidecars are down, and wire real hybrid vector search (`POST /api/v1/search`) to the topbar ⌘K search bar.

---

## Standard Stack

| Layer | Technology | Role & Version |
| :--- | :--- | :--- |
| **Framework** | Next.js 16.3.0 (App Router) | Client & Server Component tree |
| **UI Runtime** | React 19.0.0 | Hooks, State, Effects, Suspense |
| **Styling** | Vanilla CSS (`globals.css`) + Tailwind CSS 4 | Design tokens, layouts, bento grids, glassmorphism |
| **Visualizations** | Recharts 3.x | Area charts for signal velocity & trends |
| **Animations** | Framer Motion 13.x | Drawer transitions, backdrop fading, modal animations |
| **Icons** | Lucide React | Clean semantic iconography |
| **Data Fetching** | Native `fetch` with custom `useLiveData` hook | Zero extra dependencies; wraps `setInterval` + `document.visibilityState` |
| **Contract** | Canonical TypeScript (`frontend/types/api.ts`) | Auto-generated via `python scripts/export_openapi.py` |

---

## Architecture Patterns

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Next.js 16 App Router UI                         │
│                                                                             │
│  ┌────────────────────────┐  ┌─────────────────────────┐  ┌──────────────┐  │
│  │ DashboardPage          │  │ SignalsPage             │  │ Intelligence │  │
│  │ (KPIs, Radar, Trends)  │  │ (Filters, Drawer, List) │  │ (Ask Athena) │  │
│  └───────────┬────────────┘  └────────────┬────────────┘  └───────┬──────┘  │
│              │                            │                       │         │
│              └──────────────────────┐     │     ┌─────────────────┘         │
│                                     ▼     ▼     ▼                           │
│                          ┌────────────────────────────────┐                 │
│                          │      useLiveData / usePolling  │                 │
│                          │ (30s timer, tab visibility)    │                 │
│                          └──────────────┬─────────────────┘                 │
│                                         │                                   │
│                                         ▼                                   │
│                          ┌────────────────────────────────┐                 │
│                          │     frontend/lib/api.ts        │                 │
│                          │  (Mapper / Anti-Corruption)    │                 │
│                          └──────────────┬─────────────────┘                 │
└─────────────────────────────────────────┼───────────────────────────────────┘
                                          │ HTTP REST
                                          ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                             FastAPI 0.115 Backend                           │
│                                                                             │
│  GET /api/v1/overview       ──► DB Aggregations (Confluence, Stage counts)  │
│  GET /api/v1/signals        ──► SQLAlchemy Signals query (ordered by date)  │
│  POST /api/v1/athena        ──► ProviderFactory reasoning synthesis         │
│  POST /api/v1/search        ──► VectorQueryService pgvector hybrid search   │
│  GET /api/v1/health/ready   ──► DB & Redis readiness telemetry              │
│  GET /api/v1/health/models  ──► Active LLM provider metadata & status      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Pattern 1: Anti-Corruption Mapper Layer
The backend models (`backend/app/models/__init__.py`) and OpenAPI schemas represent raw relational records (e.g. `signal_id`, `published_at`, `priority`, `content`). The frontend presentation components consume rich UI contracts (`id`, `detectedAt`, `severity`, `summary`, `stakeholders`).

**Prescriptive Strategy:**
In `frontend/lib/api.ts`, create explicit pure mapper functions:
- `mapSignal(raw: BackendSignal): Signal`
- `mapOverview(raw: BackendOverview): DashboardOverview`
- `mapAthenaResponse(raw: BackendAthenaResponse): AthenaResponse`
- `mapSearchResult(raw: SignalSearchResult): Signal`

This insulates frontend UI components from backend schema naming differences while maintaining strict type safety on both sides.

### Pattern 2: Visibility-Aware Polling Hook (`useLiveData`)
To satisfy **D-01**, **D-02**, and **D-03**:
- Wrap `setInterval` and `fetch` inside a reusable hook `useLiveData<T>(fetcher, intervalMs)`.
- Listen to the `visibilitychange` event on `document`. When `document.visibilityState === 'hidden'`, clear the active interval timer. When `document.visibilityState === 'visible'`, immediately trigger a refetch and restart the interval.
- Track loading, error, and last-updated timestamp states.

### Pattern 3: Honest Degraded & Empty State Handling
To satisfy **D-08**, **D-09**, **D-10**, and **D-12**:
- If `signals.length === 0`, render a dedicated empty state explaining that no signals have been ingested yet, with a helpful call-to-action to run the ingestion pipeline.
- If `/health/ready` reports `status: "degraded"` (e.g., Redis down, DB up), render a non-blocking amber warning banner at the top of the workspace.
- If the backend is unreachable (fetch fails / 503), render a clear error alert banner with a manual **Retry** button.
- Wire the health footer directly to `/health/ready` and `/health/models` (displaying actual database connection, latency, and active provider like Gemma/Grok/BART).

### Pattern 4: Hybrid Search Modal (⌘K Integration)
Wire the existing topbar "Search signals" button and `⌘K` keyboard shortcut to open a modal dialog that invokes `POST /api/v1/search`. Results display matching signals with cosine similarity scores and open the evidence drawer on click.

---

## Backend Endpoint Analysis & Parity Requirements

### 1. `GET /api/v1/signals`
- **Current Behavior:** Tries `select(Signal).limit(limit)`, falls back to a hardcoded synthetic signal on error.
- **Required Change (D-08):** Remove synthetic fallback try/except. Return real records from `signals` table ordered by `published_at DESC` or `created_at DESC`. Return `{"signals": [...], "total": N}`. If DB is empty, return `{"signals": [], "total": 0}`.

### 2. `GET /api/v1/overview`
- **Current Behavior:** Returns static numbers (`active_signals: 38`, `weekly_change: "+12.4%"`).
- **Required Change (D-06):** Extend the endpoint in `backend/app/api/v1/endpoints/signals.py` to query real database aggregations:
  - `active_signals`: `SELECT COUNT(*) FROM signals`
  - `confluences_detected`: `SELECT COUNT(*) FROM confluences`
  - `monitored_assets`: `SELECT COUNT(*) FROM assets`
  - `confluence`: compute score and drivers from recent `confluences` / `signals`
  - `lifecycle`: group developments by `current_stage`
  - `trends`: signal volume aggregated by time period (or daily/weekly buckets)
  - `health`: current readiness and latency
- **Drift Gate Alignment:** Update `scripts/export_openapi.py` and run `pytest -k contract` to ensure 0 contract drift.

### 3. `POST /api/v1/athena`
- **Current Behavior:** Accepts `AthenaQueryRequest(prompt=...)` and runs `provider_factory.execute_task`.
- **UI Adaptation:** Wire `askAthena(prompt)` to send `POST /api/v1/athena`. Adapt the response: render `answer`, `confidence`, and `evidence_count`.

### 4. `POST /api/v1/search`
- **Status:** Already implemented in Phase 3 (`backend/app/api/v1/endpoints/search.py`).
- **UI Adaptation:** Create `searchSignals(query, top_k)` in `frontend/lib/api.ts` calling `POST /api/v1/search`.

### 5. `GET /api/v1/health/ready` & `GET /api/v1/health/models`
- **Status:** Already implemented in `backend/app/api/v1/endpoints/health.py`.
- **UI Adaptation:** Create `getHealthReady()` and `getHealthModels()` in `frontend/lib/api.ts` to power the top degraded banner and footer status bar.

---

## Don't Hand-Roll

| Feature | Standard Library / Native Approach | DO NOT Hand-Roll |
| :--- | :--- | :--- |
| **Data Fetching** | Native `fetch` with standard HTTP response checking (`response.ok`, `response.json()`) | Do not add Axios or heavy client wrappers |
| **Query State** | Clean React custom hook (`useLiveData`) with `useEffect` + `useCallback` | Do not install TanStack Query, SWR, or Redux Toolkit for simple polling |
| **Real-time Protocol** | 30s Polling per Decision D-01 | Do not hand-roll custom WebSocket servers or complex SSE push infrastructure |
| **Contract Synchronization** | Run `python scripts/export_openapi.py` | Never hand-edit `frontend/types/api.ts` or bypass OpenAPI schemas |
| **Mock Telemetry** | Honest empty states & database counts | Never fabricate fake scores, fake charts, or hardcoded mock fallbacks |

---

## Common Pitfalls & Edge Cases

### 1. React Hydration Mismatch with Timestamps
* **Symptom:** Next.js throws hydration mismatch errors when rendering relative timestamps (e.g. "2 minutes ago") computed during SSR.
* **Remedy:** Ensure relative timestamp formatters execute only after mounting on the client (or format in client components using `useEffect` / state).

### 2. Interval Leaks and Multiple Timers
* **Symptom:** Fast navigation between tabs creates orphaned `setInterval` timers, causing duplicate network requests and CPU spikes.
* **Remedy:** In `useLiveData`, always return a cleanup function `() => clearInterval(timerId)` inside `useEffect`, and remove `visibilitychange` event listeners properly.

### 3. Backend Unavailability on Initial Page Load
* **Symptom:** Blank screen or unhandled promise rejection if FastAPI backend is starting up or temporarily offline.
* **Remedy:** Graceful error boundary / error state card with a "Backend service offline — Retry" button; keep UI shell interactive.

### 4. Zero Signals Ingested (Fresh DB State)
* **Symptom:** Radar chart crashes on division by zero or empty array index out of bounds (`signals[0]`).
* **Remedy:** Provide explicit guards: if `signals.length === 0`, display informative empty state cards ("No signals detected yet. Ingest data via pipeline or connectors.") with radar score default `0`.

---

## Code Examples & Reference Implementations

### 1. Visibility-Aware Polling Hook (`frontend/lib/hooks.ts` or `frontend/lib/useLiveData.ts`)

```typescript
'use client'

import { useState, useEffect, useCallback, useRef } from 'react'

export interface LiveDataState<T> {
  data: T | null
  loading: boolean
  error: Error | null
  lastUpdated: Date | null
  refetch: () => Promise<void>
}

export function useLiveData<T>(
  fetcher: () => Promise<T>,
  intervalMs = 30000
): LiveDataState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<Error | null>(null)
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const executeFetch = useCallback(async () => {
    try {
      const result = await fetcherRef.current()
      setData(result)
      setError(null)
      setLastUpdated(new Date())
    } catch (err) {
      setError(err instanceof Error ? err : new Error(String(err)))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let timer: NodeJS.Timeout | null = null

    const startPolling = () => {
      if (timer) clearInterval(timer)
      timer = setInterval(() => {
        if (document.visibilityState === 'visible') {
          executeFetch()
        }
      }, intervalMs)
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        executeFetch()
        startPolling()
      } else {
        if (timer) {
          clearInterval(timer)
          timer = null
        }
      }
    }

    // Initial fetch
    executeFetch()
    startPolling()

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      if (timer) clearInterval(timer)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [executeFetch, intervalMs])

  return { data, loading, error, lastUpdated, refetch: executeFetch }
}
```

### 2. Client Mapper Module (`frontend/lib/api.ts`)

```typescript
import type {
  DashboardOverview,
  Signal,
  SignalSource,
  AthenaResponse,
  HealthReadyResponse,
  HealthModelsResponse,
  SearchResponse,
} from '@/types/api'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1'

async function apiFetch<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })
  if (!res.ok) {
    throw new Error(`API error ${res.status}: ${res.statusText}`)
  }
  return res.json()
}

export function mapSignal(raw: any): Signal {
  const severityMap: Record<string, 'critical' | 'high' | 'medium' | 'low' | 'neutral'> = {
    CRITICAL: 'critical',
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low',
  }

  return {
    id: raw.signal_id || raw.id || 'SIG-UNKNOWN',
    title: raw.title || 'Untitled Signal',
    summary: raw.content || raw.summary || 'No summary available',
    severity: severityMap[raw.priority?.toUpperCase()] || 'neutral',
    status: raw.status || 'new',
    score: raw.score_breakdown?.total_score || raw.score || 0,
    confidence: raw.confidence || 85,
    detectedAt: raw.published_at ? new Date(raw.published_at).toLocaleDateString() : 'Recent',
    tags: raw.disease ? [raw.disease, raw.signal_type].filter(Boolean) : [],
    sources: raw.source_id ? [{ id: raw.source_id, name: raw.source_id, type: raw.signal_type || 'feed', credibility: 90 }] : [],
    stakeholders: raw.stakeholders || {},
    ...raw,
  }
}

export async function getOverview(): Promise<DashboardOverview> {
  const raw = await apiFetch<any>('/overview')
  const rawSignals = await apiFetch<{ signals: any[]; total: number }>('/signals?limit=20')

  return {
    active_signals: raw.active_signals ?? rawSignals.total ?? 0,
    monitored_assets: raw.monitored_assets ?? 0,
    confluences_detected: raw.confluences_detected ?? 0,
    contradictions_flagged: raw.contradictions_flagged ?? 0,
    signals: (rawSignals.signals || []).map(mapSignal),
    confluence: raw.confluence || {
      score: 0,
      label: 'No confluence calculated',
      drivers: [],
      updatedAt: 'Just now',
    },
    lifecycle: raw.lifecycle || [],
    trends: raw.trends || [],
    health: {
      api: raw.health?.api || 'healthy',
      lastSync: raw.last_sync || new Date().toLocaleTimeString(),
      latencyMs: raw.health?.latency_ms || 120,
      sourceCount: raw.health?.source_count || 5,
    },
  }
}

export async function askAthena(prompt: string): Promise<AthenaResponse> {
  const raw = await apiFetch<{ answer: string; confidence: number; evidence_count: number }>('/athena', {
    method: 'POST',
    body: JSON.stringify({ prompt }),
  })
  return {
    answer: raw.answer,
    confidence: raw.confidence,
    sources: [],
  }
}

export async function searchSignals(query: string, top_k = 10): Promise<SearchResponse> {
  return apiFetch<SearchResponse>('/search', {
    method: 'POST',
    body: JSON.stringify({ query, top_k }),
  })
}

export async function getHealthReady(): Promise<HealthReadyResponse> {
  return apiFetch<HealthReadyResponse>('/health/ready')
}

export async function getHealthModels(): Promise<HealthModelsResponse> {
  return apiFetch<HealthModelsResponse>('/health/models')
}
```

---

## Verification Strategy & Quality Gates

To complete Phase 4 with full Definition of Done compliance, the following gates must be executed and confirmed:

1. **TypeScript Type Safety:**
   ```bash
   npx tsc --noEmit
   ```
   Must exit with 0 errors across the entire `frontend/` codebase (`ignoreBuildErrors: false`).

2. **ESLint Clean:**
   ```bash
   npm run lint
   ```
   Must pass with 0 errors on ESLint 10 flat config.

3. **Next.js Production Build:**
   ```bash
   npm run build
   ```
   Must compile all routes (`/dashboard`, `/signals`, `/intelligence`, `/developments`, `/sources`, `/calibrate`, `/settings`) cleanly.

4. **OpenAPI Contract Drift Gate:**
   ```bash
   python scripts/export_openapi.py
   pytest tests/test_contract_drift.py -v
   ```
   Must pass with 0 schema drift between FastAPI backend and generated TypeScript contracts.

5. **Backend Pytest Suite:**
   ```bash
   pytest -v
   ```
   All 61+ unit and endpoint tests must pass.
