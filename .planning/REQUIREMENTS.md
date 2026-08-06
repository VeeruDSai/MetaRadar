# MetaRadar — Requirements Specification

## v1 Requirements

### Data Ingestion & Resilience (INGEST)
- [ ] **INGEST-01**: System SHALL ingest signals asynchronously from NewsAPI and PubMed API.
- [ ] **INGEST-02**: System SHALL persist raw JSON API responses into aw_signals_bronze table before any processing for data replayability.
- [ ] **INGEST-03**: System SHALL implement 	enacity exponential backoff retry logic (3 attempts: 2s, 4s, 8s) for external HTTP calls.
- [ ] **INGEST-04**: System SHALL deduplicate signals using fuzzy title matching (>80% similarity threshold).
- [ ] **INGEST-05**: System SHALL validate signal quality (rejecting text < 50 chars, non-English, or missing essential fields).

### NLP & Intelligence Processing (NLP)
- [ ] **NLP-01**: System SHALL extract pharmaceutical entities (drugs, companies, indications, clinical trial phases) using spaCy (en_core_sci_md) and medspacy.
- [ ] **NLP-02**: System SHALL enrich extracted entities against the B.Pharm-authored ontology dictionary (drug → brand → mechanism → manufacturer → competitor).
- [ ] **NLP-03**: System SHALL classify signals into types (clinical_success, safety_concern, competitive_move, regulatory_change, access_issue) using acebook/bart-large-mnli.
- [ ] **NLP-04**: System SHALL generate 1-line signal summaries using a model-agnostic HuggingFace pipeline configured via LOCAL_LLM_MODEL environment variable.
- [ ] **NLP-05**: System SHALL compute role-relevance scores (0.0 to 1.0) for Medical Affairs, Regulatory, and Commercial teams.

### Intelligence Core & Confluence (CONF)
- [ ] **CONF-01**: System SHALL detect cross-source signal confluence when ≥2 independent signal types converge on the same entity within a 48-hour window.
- [ ] **CONF-02**: System SHALL assign confluence alert levels (CRITICAL, HIGH, MEDIUM, LOW) based on signal type convergence matrix.
- [ ] **CONF-03**: System SHALL attach a complete, traceable evidence chain (Source, URL, Timestamp, Excerpt) to every insight and alert.

### Database & Vector Storage (DATA)
- [ ] **DATA-01**: System SHALL maintain PostgreSQL 16 schema (aw_signals_bronze, signals, entities, confluence_events, riefs, udit_log).
- [ ] **DATA-02**: System SHALL compute and store 768-dimensional vector embeddings using sentence-transformers/all-MiniLM-L6-v2 in pgvector.
- [ ] **DATA-03**: System SHALL execute hybrid search combining pgvector cosine distance and pg_trgm lexical matching.
- [ ] **DATA-04**: System SHALL enforce WORM (Write Once Read Many) append-only logging on udit_log table for 21 CFR Part 11 compliance.
- [ ] **DATA-05**: System SHALL execute spaCy PII/PHI scrubbing before database persistence.

### User Interface & Dashboard (UI)
- [ ] **UI-01**: System SHALL render a responsive Next.js 15 dashboard with role selection (Medical Affairs, Regulatory, Commercial).
- [ ] **UI-02**: System SHALL display top strategic Confluence Alerts above the general signal feed.
- [ ] **UI-03**: System SHALL render expandable Signal Cards showing summary, tags, scores, and expandable evidence chain.
- [ ] **UI-04**: System SHALL render a non-suppressible <DisclaimerBadge /> ("Auto-generated — verify clinically before use") on all AI summaries.
- [ ] **UI-05**: System SHALL render a 7-day signal volume trend chart using Recharts.
- [ ] **UI-06**: System SHALL provide an [Export Audit Trail] UI action for exporting compliance audit logs.

## v2 Requirements (Deferred to Milestone 2)
- [ ] **ADV-01**: Ask Athena RAG conversational query interface (/api/v1/query).
- [ ] **ADV-02**: Executive Narrative Briefs generation (/api/v1/briefs).
- [ ] **ADV-03**: Temporal pattern stage matching (pre-approval surge, access crisis).
- [ ] **ADV-04**: Reddit sentiment analysis data pipeline.
- [ ] **ADV-05**: ClinicalTrials.gov API fetcher integration.

## Out of Scope
- Integration with live Novo Nordisk internal databases or proprietary intranets.
- Commercial LLM APIs requiring paid subscription keys (GPT-4, Claude API).
- Deployment of standalone Weaviate vector database containers.
- Native mobile applications (iOS/Android).

## Traceability Matrix

| Requirement | Phase | Status |
|-------------|-------|--------|
| **INGEST-01** | Phase 2 | Pending |
| **INGEST-02** | Phase 1 | Pending |
| **INGEST-03** | Phase 2 | Pending |
| **INGEST-04** | Phase 2 | Pending |
| **INGEST-05** | Phase 2 | Pending |
| **NLP-01** | Phase 3 | Pending |
| **NLP-02** | Phase 3 | Pending |
| **NLP-03** | Phase 4 | Pending |
| **NLP-04** | Phase 4 | Pending |
| **NLP-05** | Phase 4 | Pending |
| **CONF-01** | Phase 5 | Pending |
| **CONF-02** | Phase 5 | Pending |
| **CONF-03** | Phase 5 | Pending |
| **DATA-01** | Phase 1 | Pending |
| **DATA-02** | Phase 6 | Pending |
| **DATA-03** | Phase 6 | Pending |
| **DATA-04** | Phase 1 | Pending |
| **DATA-05** | Phase 3 | Pending |
| **UI-01** | Phase 8 | Pending |
| **UI-02** | Phase 9 | Pending |
| **UI-03** | Phase 8 | Pending |
| **UI-04** | Phase 8 | Pending |
| **UI-05** | Phase 8 | Pending |
| **UI-06** | Phase 7 | Pending |
