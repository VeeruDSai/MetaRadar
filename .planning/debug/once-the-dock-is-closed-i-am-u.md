---
status: resolved
trigger: "once the dock is closed, i am unable to open it again, the implementation is not proper.[Image 1] [Image 2]"
symptoms:
  expected: "Dock opens with animation when opened after being closed"
  actual: "Unable to open the dock again once closed"
  errors: "No errors visible in console or browser"
  timeline: "Recently broke — was working before"
  reproduction: "Click button to open dock"
created: 2026-08-30
updated: 2026-08-30
---

# Debug Session: once-the-dock-is-closed-i-am-u

## Root Cause

Commit `9458ec6` ("feat(ui): redesign login page, integrate 3d holographic profile modal, and overhaul dock navigation") introduced two interrelated bugs that make the dock un-openable once collapsed/closed.

### Bug 1 — Desktop collapse dead-end (primary)
- `.sidebar.collapsed .dock-toggle-btn { display: none; }` hides the dock toggle button when the sidebar is collapsed
- `.menu-button { display: none; }` hides the topbar menu button on desktop (>900px)
- The `dock-toggle-btn` is the only visible expand control; when the sidebar is collapsed, it disappears
- Result: once collapsed on desktop, there is NO visible button to expand the sidebar — a dead-end

### Bug 2 — Breakpoint mismatch (768px vs 900px)
- CSS media query: `@media (max-width: 900px)` styles sidebar as off-screen (`transform: translateX(-100%)`)
- JS toggle handler: `window.innerWidth < 768` decides between `setOpen` (mobile) and `setIsCollapsed` (desktop)
- On screens between 768px–900px: CSS hides sidebar off-screen, but JS toggles `isCollapsed` (width) instead of `open` (visibility)
- Result: sidebar stays off-screen because `sidebar-open` class is never applied

## Fix Applied

1. **`frontend/app/globals.css`**: Removed `.sidebar.collapsed .dock-toggle-btn { display: none; }` — the dock toggle button now remains visible inside the collapsed sidebar
2. **`frontend/components/metaradar.tsx`**: Changed `window.innerWidth < 768` to `window.innerWidth < 900` — matches the CSS media query breakpoint

## Files Changed

- `frontend/app/globals.css` — removed hidden expand button rule
- `frontend/components/metaradar.tsx` — fixed breakpoint mismatch (768 → 900)

## Eliminated

- No console errors
- No React rendering bugs
- No CSS specificity issues
- No animation library conflicts
- No z-index conflicts
- No SignalDrawer or AnimatePresence interference
