# Debug Session: Priority Scoring, Citations/Provenance, Sources Dedup, Seed Integrity & Favicon

**Status:** Investigating  
**Date:** 2026-08-21  
**Targets:** 
- `backend/app/db/seed.py`
- `backend/app/workflows/nodes/score.py`
- `backend/app/connectors/*.py`
- `backend/app/api/v1/endpoints/observability.py`
- `backend/app/api/v1/endpoints/registry.py`
- `frontend/app/favicon.ico` / `frontend/public/` / `frontend/app/layout.tsx`
- Red-Team, Missing Signals, Confluence, and Developments seed integrity

## Symptoms Reported by User
1. **Priority scores are 0**: Live signals and Overview cards show `0 pts`, and 4-factor score breakdown shows `0 / 0 / 0 / 0`.
2. **No option to check original source page (No citations / Source URL unavailable)**: Evidence drawer shows `SOURCE URL UNAVAILABLE` because synthetic/seeded records have UUIDs as external IDs with missing `canonical_url`s.
3. **Duplicate & Unhealthy Sources**: Sources page shows 8 sources instead of 5 canonical sources due to duplicate source keys (`clinical_trials` vs `clinicaltrials`, `ema` vs `ema_rss`).
4. **Placeholder Values in Red Team & Missing Signals**: Need authentic clinical/regulatory Haemophilia A/B datasets with real rules (A through S), real NLI confidence, and real timeline surveillance.
5. **v0 Favicon in Browser Tab**: Browser tab shows the `v0` logo instead of the MetaRadar icon.
