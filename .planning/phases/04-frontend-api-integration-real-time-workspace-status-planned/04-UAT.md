---
status: testing
phase: 04-frontend-api-integration-real-time-workspace-status-planned
source:
  - .planning/phases/04-frontend-api-integration-real-time-workspace-status-planned/04-01-SUMMARY.md
  - .planning/phases/04-frontend-api-integration-real-time-workspace-status-planned/04-02-SUMMARY.md
  - .planning/phases/04-frontend-api-integration-real-time-workspace-status-planned/04-03-SUMMARY.md
started: 2026-08-18T02:40:00.000Z
updated: 2026-08-18T02:40:00.000Z
---

## Current Test

number: 1
name: Cold Start & Backend API Live Aggregations
expected: |
  Start the backend (e.g. `uvicorn app.main:app --reload`). Navigating to `GET /api/v1/overview` and `GET /api/v1/signals` returns valid JSON with active signal counts and signal lists with no synthetic fallback dictionary errors.
awaiting: user response

## Tests

### 1. Cold Start & Backend API Live Aggregations
expected: Start the backend. Navigating to `GET /api/v1/overview` and `GET /api/v1/signals` returns valid JSON with active signal counts and signal lists with no synthetic fallback dictionary errors.
result: pending

### 2. Live Polling & Visibility-Aware Refresh
expected: The frontend periodically refreshes workspace overview data on a 30s cadence. Switching away from the browser tab pauses the timer, and returning to the tab triggers an immediate refresh.
result: pending

### 3. Live Dashboard & Signals Severity Filtering
expected: The Dashboard displays live KPIs (Active signals, Monitored assets, Confluence index, Source feeds), Radar alignment, and Trend chart. On the Signals page, filtering by severity (Critical, High, Medium, Low) updates visible counts, and clicking a row opens the SignalDrawer.
result: pending

### 4. ⌘K Semantic Vector Search Modal
expected: Pressing `⌘K` or `Ctrl+K` (or clicking the topbar search button) opens the search dialog. Typing keywords queries the 384-dim semantic index with match percentage score badges, and selecting a result opens the SignalDrawer.
result: pending

### 5. Ask Athena Strategic Synthesis & Error Handling
expected: Navigating to the Intelligence page and submitting a question (or clicking a preset prompt) shows a thinking indicator, then displays the synthesized answer with a confidence score badge.
result: pending

### 6. Honest Telemetry & Degraded Mode Warning
expected: The footer displays live backend readiness and active model provider. All synthetic demo labels have been removed, and if Redis is offline, a non-blocking amber system notice is displayed.
result: pending

## Summary

total: 6
passed: 0
issues: 0
pending: 6
skipped: 0

## Gaps

[none yet]
