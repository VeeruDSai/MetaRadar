---
phase: 11-productionization
plan: 11-05
subsystem: frontend-auth-and-workspace-integration
tags: [frontend, auth, csrf, credentials, persona-switcher, demo-operator, typescript, nextjs]
requires:
  - phase: 11-productionization
    plan: 11-01
    provides: Dual-timeout sessions & auth endpoints
  - phase: 11-productionization
    plan: 11-04
    provides: Operational workspaces and leadership summary endpoints
provides:
  - Hardened apiFetch with credentials: 'include' and automatic CSRF header injection on mutating requests
  - AuthContext providing reactive session state, role tracking, and seamless demo persona switching
  - PersonaSwitcher dropdown with role indicators and descriptions
  - Synchronized DemoOperatorSelector updating server sessions via demo-login API
  - Contract synchronization in frontend/types/api.ts and contracts/openapi.json
  - 100% successful Next.js 16 build and TypeScript compilation
affects: [frontend, auth, layout, api, persona]
key-files:
  created:
    - frontend/context/AuthContext.tsx
    - frontend/components/auth/PersonaSwitcher.tsx
  modified:
    - frontend/app/layout.tsx
    - frontend/lib/api.ts
    - frontend/components/common/DemoOperatorSelector.tsx
    - frontend/types/api.ts
    - contracts/openapi.json
    - scripts/export_openapi.py
---

# Plan 11-05 Summary: Frontend Auth Integration (`apiFetch` + CSRF + Persona Switcher)

## Executed Work
1. **Hardened `apiFetch` with CSRF & Credentials (`frontend/lib/api.ts`)**:
   - Added `credentials: "include"` by default on all requests.
   - Automatically attaches `X-CSRF-Token` header on mutating HTTP methods (`POST`, `PUT`, `DELETE`, `PATCH`) by reading `metaradar_csrf` cookie or fetching `/api/v1/auth/csrf`.
   - Added strongly-typed API client methods for `login`, `demoLogin`, `logout`, `getMe`, `getFunctionQueue`, `getFunctionStats`, `getCalibrationStatus`, and `getLeadershipSummary`.

2. **Reactive Authentication State (`frontend/context/AuthContext.tsx`)**:
   - Created `AuthProvider` and `useAuth()` hook managing current `user`, `role`, `isAuthenticated`, `isLoading`, `demoLogin`, `login`, and `logout`.
   - Automatically bootstraps active session or demo persona and persists selected role in `localStorage`.
   - Wrapped entire application in `frontend/app/layout.tsx`.

3. **Persona & Demo Role Switching**:
   - Created `frontend/components/auth/PersonaSwitcher.tsx` supporting 1-click role selection across all 7 roles (`MEDICAL_AFFAIRS`, `REGULATORY`, `SAFETY`, `MARKET_ACCESS`, `COMMUNICATIONS`, `LEADERSHIP`, `ADMIN`).
   - Integrated `DemoOperatorSelector` (`frontend/components/common/DemoOperatorSelector.tsx`) with `AuthContext` so changing the reviewer role immediately provisions a real backend session.

4. **Contract Synchronization & Verification**:
   - Updated `scripts/export_openapi.py`, `contracts/openapi.json`, and `frontend/types/api.ts`.
   - Verified `npx tsc --noEmit` passes with 0 errors.
   - Verified Next.js production build (`npm run build`) generates all routes cleanly.
