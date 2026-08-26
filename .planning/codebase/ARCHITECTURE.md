# System Architecture (ARCHITECTURE.md)

**Project:** MetaRadar — Autonomous Decision Intelligence Platform  
**Milestone:** v5.2  
**Last Updated:** 2026-08-27  

---

## 1. High-Level Architectural Blueprint

MetaRadar is built as a **multi-tiered autonomous decision intelligence system** designed to transform unstructured clinical, regulatory, and commercial signals into verified organizational actions.

```
┌───────────────────────────────────────────────────────────────────────────┐
│                           PRESENTATION LAYER                              │
│  Next.js 16 (Turbopack) • App Router • Design Tokens • Demo Operator UI   │
│  Decision Intelligence Workspace (Evidence | Interpretation | Action)     │
└─────────────────────────────────────▲─────────────────────────────────────┘
                                      │ REST API / SSE Streams
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                          FASTAPI APPLICATION TIER                         │
│  Signals API • Athena Q&A • Confluence • Red Team • Review & Audit Router │
└─────────────────────────────────────▲─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                   11-NODE LANGGRAPH INTELLIGENCE PIPELINE                 │
│  1. Ingest → 2. Validate/PII → 3. Extract NLP → 4. Ontology Enrich →      │
│  5. Embed (pgvector) → 6. Confluence → 7. Lifecycle → 8. Red Team →       │
│  9. Missing Signal Gap → 10. Synthesize Action → 11. Calibrate Feedback   │
└─────────────────────────────────────▲─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                           DATA & STORAGE LAYER                            │
│  PostgreSQL 16 (Bronze, Silver, Gold, AuditLog) • pgvector (384 dims)     │
│  Redis Cache • Domain Configuration (haemophilia.yaml)                    │
└─────────────────────────────────────▲─────────────────────────────────────┘
                                      │
┌─────────────────────────────────────▼─────────────────────────────────────┐
│                       INGESTION CONNECTOR TIER                            │
│  PubMed • ClinicalTrials.gov • openFDA • EMA • NewsAPI • Fierce Pharma    │
│  ET Pharma • Autonomous Background Scheduler (Advisory Locks)             │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Subsystems

### A. Provenance Traceability & URL Resolution
- Every signal maintains an unbroken provenance trail from raw source ingest to UI rendering.
- `resolve_canonical_provenance()` enforces document-specific URL resolution (PubMed IDs, NCT study links, Drugs@FDA approval records, EMA EPARs, Fierce/ET Pharma direct article links).
- Generic landing pages (`newsapi.org/register`, `fda.gov`, `ema.europa.eu`) are blocked and rejected rather than presented as evidence links.

### B. 3-Pillar Decision Intelligence Model
Every signal is presented through 3 strictly separated trust boundaries:
1. **Original Evidence:** Verbatim factual excerpt, source authority tier (`Authoritative` vs. `Discovery`), and verified primary source link.
2. **AI Interpretation:** Clinical & strategic significance, forward projections, and model attribution (`Local Gemma 3`).
3. **Suggested Action:** Target organizational destination queue, recommended operational directive, and decision priority score.

### C. Review State Machine & Immutable Audit Log
- **State Machine:** `UNREVIEWED` → `IN_REVIEW` (Acknowledge) → `REVIEWED` (Approve/Reject) → `ACTION_REQUIRED` (Evidence Request) → `ACTIONED` (Roadmap Decision) / `DISMISSED`.
- **Database Persistence:** Real mutations on `Signal.review_status`, `Signal.reviewed_by`, `Signal.review_decision`, and `Signal.resulting_action`.
- **Audit Logging:** Every state change writes an immutable `AuditLog` row recording entity ID, actor persona, timestamp, and details payload.

### D. Autonomous Ingestion & Background Scheduler
- `SourceScheduler` manages independent asynchronous workers for all 7 active connectors.
- Uses PostgreSQL advisory locks to prevent overlapping ingestion runs across multi-worker environments.
- Implements exponential backoff and jitter for transient API failures.
