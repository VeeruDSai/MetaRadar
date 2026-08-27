---
status: investigating
trigger: "all the high or critical signals have a priority score of 50 even now, even now PUBMED won't lead me to the source article. also i don't see Fierce Pharma, BioPharma Dive, and ET Pharma India source in the sources page and i don't see any signals either."
created: 2026-08-28
updated: 2026-08-28
---

# Debug Session: Signal Detail Priority Score, PubMed Link in Detail/Card, and Phase 10 Sources (Fierce Pharma, BioPharma Dive, ET Pharma) in Sources Page

## Symptoms
1. High / Critical signals still display a score of 50 (specifically inspecting detail view and cards).
2. PubMed source click does not navigate to the external article.
3. Sources page (/sources) does not display Fierce Pharma, BioPharma Dive, and ET Pharma India, and no signals exist for these 3 sources.

## Hypotheses
1. `SignalDetailWorkspace.tsx` or `SignalDetailHeader` or `SignalCard.tsx` has a fallback `50` or reads a different field (e.g., `signal.priority_score`, `signal.score_breakdown?.total_score` vs `signal.score_breakdown?.total`).
2. In `SignalDetailWorkspace.tsx`, the PubMed link button may use `signal.url` instead of `signal.canonical_url`, or the frontend link handler prevents default navigation or checks for internal paths.
3. In `SourcesWorkspace.tsx` and `backend/app/api/v1/endpoints/sources.py` (or `/health/connectors`), the sources list endpoint only returns sources from the database or connector registry. If `seed.py` seeded them but the backend was not restarted or `SourcesWorkspace.tsx` queries a different endpoint, or there are no signal rows with `source_id in ('fierce_pharma', 'biopharma_dive', 'et_pharma')`, they won't appear.
