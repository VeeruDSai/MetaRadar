---
status: resolved
trigger: "/gsd-debug Authentication Error HTTP 403 Request to /signals?limit=50&all_functions=true failed (403): Forbidden: Only LEADERSHIP and ADMIN roles can access all_functions=true AND Network Disconnected 0: Failed to execute 'fetch' on 'Window': Failed to read the 'signal' property from 'RequestInit': Failed to convert value to 'AbortSignal'."
created: 2026-08-28
updated: 2026-08-28
---

# Debug Session: Signals RBAC 403 Forbidden & AbortSignal RequestInit TypeError

## Symptoms
1. **HTTP 403 Forbidden on `/signals?limit=50&all_functions=true`**: Navigating to the Signals page (`/signals`) as any standard/functional persona (such as the default `MEDICAL_AFFAIRS` role) resulted in `Authentication Error HTTP 403: {"detail":"Forbidden: Only LEADERSHIP and ADMIN roles can access all_functions=true"}`.
2. **Network Disconnected 0 / AbortSignal TypeError**: Clicking the "Retry" button on the error state banner caused `Failed to execute 'fetch' on 'Window': Failed to read the 'signal' property from 'RequestInit': Failed to convert value to 'AbortSignal'`.

## Root Cause Analysis
1. **Unconditional `all_functions: true` in `SignalList.tsx`**:
   - `SignalList.tsx` hardcoded `all_functions: true` in the query params object sent to `fetchSignals()`.
   - The backend RBAC rules in `backend/app/api/v1/endpoints/signals.py` strictly restrict `all_functions=true` to `LEADERSHIP`, `ADMIN`, and `DEVELOPER` roles.
   - When non-privileged personas (such as the default demo role `MEDICAL_AFFAIRS`) visited the Signals view, the backend correctly rejected the query with `HTTP 403 Forbidden`.
2. **`MouseEvent` Passed as `signal?: AbortSignal` on Retry Click**:
   - `ErrorState.tsx` wired retry buttons with `onClick={onRetry}` without wrapping in a zero-argument arrow function.
   - When a user clicked "Retry", React passed the Synthetic `MouseEvent` as the first argument to `loadSignals(signal?: AbortSignal)`.
   - `loadSignals` forwarded this `MouseEvent` to `fetchSignals(params, signal)` -> `apiFetch(endpoint, undefined, signal)`.
   - In `frontend/lib/api.ts`, `apiFetch` checked `if (signal !== undefined)` and assigned `fetchOptions.signal = signal` (which was the `MouseEvent` object).
   - The browser's native `Window.fetch()` threw `TypeError: Failed to read the 'signal' property from 'RequestInit': Failed to convert value to 'AbortSignal'`.

## Key Changes & Fixes Applied
1. **Role-Aware Query Filtering in [SignalList.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/signals/SignalList.tsx)**:
   - Integrated `useAuth()` to check current role permissions (`LEADERSHIP`, `ADMIN`, `DEVELOPER`).
   - Dynamically included `all_functions: true` only when the active persona is privileged, allowing functional users (`MEDICAL_AFFAIRS`, `REGULATORY`, etc.) to query their scoped signals seamlessly without 403 errors.
   - Defensive validation for `signal` inside `loadSignals` to guarantee only genuine `AbortSignal` instances are forwarded.
2. **Strict `AbortSignal` Validation in [frontend/lib/api.ts](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/lib/api.ts)**:
   - Updated `apiFetch` and `fetchCsrfToken` to enforce `if (typeof AbortSignal !== 'undefined' && signal instanceof AbortSignal)` before populating `fetchOptions.signal`.
3. **Safe Event Decoupling in [ErrorState.tsx](file:///c:/Users/OM%20Prakash/Documents/novonordisk/frontend/components/common/ErrorState.tsx)**:
   - Updated `ErrorState` retry buttons to execute `onClick={() => onRetry?.()}` so click events are not forwarded to retry handlers.

## Verification Evidence
- **TypeScript Gate**: `npx tsc --noEmit` exited with code 0 (zero type errors).
- **Backend RBAC Test Suite**: `pytest tests/test_rbac.py` and full test suite passing.
