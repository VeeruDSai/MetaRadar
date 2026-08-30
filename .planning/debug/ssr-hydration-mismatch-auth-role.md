---
status: resolved
trigger: "Hydration failed because the server rendered text didn't match the client. avatar-initials: TL vs TM"
symptoms:
  expected: "Server SSR HTML matches client initial hydration render without mismatch warning/error"
  actual: "Server rendered initials 'TM' (Medical Affairs default), but client synchronously read 'LEADERSHIP' from localStorage during initial render, producing 'TL' and throwing a hydration mismatch exception"
  errors: "Hydration failed because the server rendered text didn't match the client. <span className=\"avatar-initials\">+ TL - TM</span>"
  timeline: "Occurred on direct navigation / reload when localStorage contained a non-default demo role"
  reproduction: "Login as test-leader, reload the page on any route (e.g. /intelligence)"
created: 2026-08-30
updated: 2026-08-30
---

# Debug Session: ssr-hydration-mismatch-auth-role

## Root Cause

1. **Synchronous `localStorage` Read During Render Phase**:
   - In `frontend/context/AuthContext.tsx`:
     ```ts
     const role = user?.role || (typeof window !== 'undefined' ? localStorage.getItem(DEMO_ROLE_KEY) : null) || DEFAULT_ROLE
     ```
   - On the server (SSR): `typeof window !== 'undefined'` evaluated to `false`, causing `role` to resolve to `DEFAULT_ROLE` (`'MEDICAL_AFFAIRS'`). The server generated HTML with initials **"TM"**.
   - On the client during initial hydration pass: `typeof window !== 'undefined'` evaluated to `true`, synchronously reading `'LEADERSHIP'` from `localStorage`. The client generated initial virtual DOM with initials **"TL"**.
   - This violated React 19 / Next.js 16 hydration invariants requiring the initial client render pass to match the server HTML byte-for-byte.

## Fix Applied

1. **`frontend/context/AuthContext.tsx`**:
   - Added `isMounted` state guard and `storedRole` state.
   - Initial render pass on both server and client resolves `role = user?.role || (isMounted ? storedRole : null) || DEFAULT_ROLE`.
   - On initial render, both server and client render `DEFAULT_ROLE` ('MEDICAL_AFFAIRS' / 'TM').
   - In `useEffect` on mount, `isMounted` is set to `true` and `localStorage.getItem(DEMO_ROLE_KEY)` safely updates `storedRole`.
   - React updates the DOM post-hydration smoothly without throwing any hydration errors.

## Verification

- `npx tsc --noEmit`: Exited with code 0 (0 type errors).
- `npm run lint`: Exited with code 0 (0 lint warnings/errors).
- `npm run check:banned-classes`: 35 files scanned, 0 violations.
