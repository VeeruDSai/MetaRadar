# Plan 04-02 Summary: Live API Client, Mapper Module & Polling Hook

## Overview
Implemented the production-grade Next.js REST client in `frontend/lib/api.ts` to communicate with the FastAPI backend `/api/v1` routes (`/signals`, `/overview`, `/athena`, `/search`, `/health/ready`, `/health/models`). Implemented pure mapper functions (Decisions D-04, D-05) to bridge OpenAPI relational schemas to frontend UI contracts, and built the concurrency-safe, visibility-aware `useLiveData` hook (Decisions D-01, D-02, D-03) with `AbortController`, 30s polling, in-flight request deduplication, and automatic tab-visibility pausing.

## Key Changes
- `frontend/lib/hooks.ts`:
  - Created `useLiveData<T>` hook managing `loading`, `isRefreshing`, `error`, `lastUpdated`, and `refetch`.
  - Added in-flight request tracking (`inFlightRef`) to prevent request overlap.
  - Added `AbortController` cancellation on unmount and visibility change.
  - Added `document.visibilityState` event listener pausing intervals when the browser tab is hidden and immediately refreshing upon tab refocus.
  - Added Next.js SSR guards (`typeof window !== 'undefined'`).
- `frontend/lib/api.ts`:
  - Replaced static mock imports from `@/lib/mock-data` with typed `apiFetch` against `NEXT_PUBLIC_API_URL || http://localhost:8000/api/v1`.
  - Defined `ApiError` class with status, statusText, and `isRetryable`.
  - Implemented pure mappers `mapSignal`, `mapOverview`, `mapAthenaResponse`, `mapSearchResult` providing honest defaults without fabricating non-existent numbers (D-05).
  - Exported typed functions `getOverview`, `getSignals`, `askAthena` (with 500-char input clamping), `searchSignals`, `getHealthReady`, `getHealthModels`.

## Verification
- `node frontend/node_modules/typescript/bin/tsc --project frontend/tsconfig.json --noEmit`: Exited with 0 errors (100% type safe).
- `npm --prefix frontend run lint`: ESLint flat config passed with 0 errors.
