# MetaRadar — Requirements Specification

## Core MVP Requirements (v1)

### Multi-Source Ingestion & Resilience (INGEST)
- [ ] **INGEST-01**: System SHALL asynchronously fetch signals from PubMed, NewsAPI, ClinicalTrials.gov, OpenFDA, EMA RSS, Reddit PRAW (r/hemophilia, r/raredisease), and Congress abstract repositories using haemophilia query terms.
- [ ] **INGEST-02**: System SHALL persist raw JSON API responses into `raw_signals_bronze` table before processing for data replayability.
- [ ] **INGEST-03**: System SHALL implement `tenacity` exponential backoff retry logic (3 attempts: 2s, 4s, 8s) for external HTTP requests.
- [ ] **INGEST-04**: System SHALL deduplicate signals using fuzzy title matching (>80% similarity threshold).
- [ ] **INGEST-05**: System SHALL validate signal quality (rejecting text <50 chars, non-English, or non-haemophilia signals).
- [ ] **INGEST-06**: System SHALL maintain a 500-signal pre-curated synthetic demo dataset for stable offline demo fallback.

### NLP & Haemophilia Domain Processing (NLP)
- [ ] **NLP-01**: System SHALL extract pharmaceutical entities (drugs, companies, indications, clinical phases, trial IDs) using spaCy `en_core_sci_md` (ScispaCy).
- [ ] **NLP-02**: System SHALL enrich extracted entities against the B.Pharm-authored Haemophilia ontology dictionary (brand → generic → mechanism → treatment paradigm hierarchy → competitor graph).
- [ ] **NLP-03**: System SHALL classify signals into types (gene_therapy_milestone, regulatory_decision, congress_publication, patient_access, competitor_pipeline, inhibitor_signal) using `cross-encoder/nli-MiniLM2-L6-H768`.
- [ ] **NLP-04**: System SHALL generate 1-sentence signal summaries using local DistilBART (`sshleifer/distilbart-cnn-12-6`).
- [ ] **NLP-05**: System SHALL compute role-relevance confidence scores (0.0 to 1.0) for 5 Novo Nordisk functions: Medical Affairs, Regulatory, Market Access, Commercial, and R&D.

### Intelligence Core, Confluence & RAG (CONF)
- [ ] **CONF-01**: System SHALL detect cross-source signal confluence when ≥2 independent signal types converge on the same haemophilia entity within a 48-hour window.
- [ ] **CONF-02**: System SHALL assign confluence alert levels (CRITICAL, HIGH, MEDIUM, LOW) based on signal convergence matrix.
- [ ] **CONF-03**: System SHALL attach a complete, traceable evidence chain (Source URL, Published Date, Excerpt, Credibility Score) to every insight and alert.
- [ ] **CONF-04**: System SHALL provide "Ask Athena" RAG natural language interface allowing semantic search and grounded answering over stored signals using pgvector.

### Stakeholder Calibration Loop (CALIB)
- [ ] **CALIB-01**: System SHALL provide a Stakeholder Review UI widget allowing simulated personas (Medical Affairs, Regulatory, Market Access) to submit structured feedback (relevance 1-5, urgency 1-5, actionability).
- [ ] **CALIB-02**: System SHALL implement `StakeholderCalibrationService` to dynamically recalibrate function scoring weights based on aggregated feedback.
- [ ] **CALIB-03**: System SHALL display pre-calibration vs post-calibration score comparisons (e.g. "Pre: 0.60 | Post: 0.88") on dashboard to demonstrate learning.

### Database, Compliance & Vector Storage (DATA)
- [ ] **DATA-01**: System SHALL maintain PostgreSQL 16 schema (`raw_signals_bronze`, `signals`, `entities`, `confluence_events`, `briefs`, `stakeholder_feedback`, `audit_log`).
- [ ] **DATA-02**: System SHALL compute and store 384-dimensional vector embeddings using `sentence-transformers/all-MiniLM-L6-v2` in pgvector.
- [ ] **DATA-03**: System SHALL execute hybrid search combining pgvector cosine distance and `pg_trgm` lexical matching.
- [ ] **DATA-04**: System SHALL enforce WORM (Write Once Read Many) append-only logging on `audit_log` table for GxP / 21 CFR Part 11 compliance.
- [ ] **DATA-05**: System SHALL execute spaCy PII/PHI scrubbing before database persistence.

### Four-Question Dashboard & User Interface (UI)
- [ ] **UI-01**: System SHALL render a responsive Next.js 15 dashboard structured around the Four-Question Framework:
  - **Panel 1 — What Changed?**: Real-time signal feed with entity tags & signal type badges.
  - **Panel 2 — Why Does It Matter?**: Relevance breakdown, 2-sentence AI explanation, confluence alert, & competitive context.
  - **Panel 3 — Which Function Should Review It?**: Role-routing badges with confidence percentages.
  - **Panel 4 — What Action May Be Required?**: Max 3 AI-suggested action bullets prefaced *"Suggested — requires human review"*.
- [ ] **UI-02**: System SHALL render a Role Selector supporting 5 pre-filtered views (Medical Affairs, Regulatory, Market Access, Commercial, R&D).
- [ ] **UI-03**: System SHALL display a Confluence Alert Feed for top strategic multi-source convergence events.
- [ ] **UI-04**: System SHALL render an interactive 7-day signal volume trend chart categorized by haemophilia signal type using Recharts.
- [ ] **UI-05**: System SHALL render an Entity Explorer interface to browse signals linked to specific drugs (emicizumab, mim8, Hemgenix) or competitors.
- [ ] **UI-06**: System SHALL display a Live Data Source Health status panel (green/yellow/red with last fetch timestamp).
- [ ] **UI-07**: System SHALL display Calibration Status in dashboard footer ("Calibrated from X feedback items | Last: Y ago").

---

## Out of Scope
- Internal Novo Nordisk proprietary data or intranet integrations.
- Paid commercial LLM APIs (GPT-4, Claude API).
- Mobile apps (iOS/Android).
- Unreviewed automated execution of suggested actions (human review is strictly required).

---

## Requirements Traceability Matrix

| Requirement | Phase | Status |
|-------------|-------|--------|
| **INGEST-01..06** | Phase 2 | Pending |
| **NLP-01..02** | Phase 3 | Pending |
| **NLP-03..05** | Phase 4 | Pending |
| **CONF-01..03** | Phase 5 | Pending |
| **CONF-04** | Phase 6 | Pending |
| **CALIB-01..03** | Phase 7 | Pending |
| **DATA-01..05** | Phase 1 & 6 | Pending |
| **UI-01..07** | Phase 8 & 9 | Pending |

---
*Last updated: August 2026 after Concept Note alignment*
