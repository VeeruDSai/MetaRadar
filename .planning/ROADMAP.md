# MetaRadar — Phase Roadmap

## Overview

- **Total Phases**: 9 focused phases
- **Target Domain**: Haemophilia within Rare Disease (Novo Nordisk GBS Hackathon 2026 Problem Statement #3)
- **Granularity**: Fine (focused, verifiable micro-phases matching 4-week timeline)

---

## Phase Breakdown

### Phase 1: Database Foundation & Compliance Schema
**Goal**: Initialize PostgreSQL 16 database with pgvector extension, deployment schema (`raw_signals_bronze`, `signals`, `entities`, `confluence_events`, `briefs`, `stakeholder_feedback`, `audit_log`), and GxP WORM audit triggers.
- **Requirements**: INGEST-02, DATA-01, DATA-04
- **Success Criteria**:
  1. Docker Compose launches PostgreSQL 16 container with `pgvector` enabled.
  2. Tables created cleanly with indices on timestamps, entity IDs, and role scores.
  3. `audit_log` permissions strictly revoke UPDATE and DELETE operations for application user.
- **Plans**: 1-2 plans

### Phase 2: Multi-Source Haemophilia Ingestion & Resilience Layer
**Goal**: Build async fetchers for PubMed, NewsAPI, ClinicalTrials.gov, FDA OpenFDA, EMA RSS, Reddit PRAW, and Congress abstract repositories with haemophilia query terms, tenacity retry logic, dedup, raw bronze persistence, and 500-signal synthetic demo fallback.
- **Requirements**: INGEST-01, INGEST-03, INGEST-04, INGEST-05, INGEST-06
- **Success Criteria**:
  1. Async fetchers fetch signals across public APIs concurrently without blocking.
  2. Verbatim JSON persisted in `raw_signals_bronze` before processing.
  3. `tenacity` retries API calls 3 times with exponential backoff on network errors.
  4. Duplicate signals (>80% title similarity) and non-haemophilia items filtered.
  5. Synthetic 500-signal fallback available offline for reliable demo.
- **Plans**: 2 plans

### Phase 3: B.Pharm Haemophilia Ontology & spaCy NER Pipeline
**Goal**: Integrate spaCy `en_core_sci_md` (ScispaCy) for entity extraction, B.Pharm-authored Haemophilia ontology lookup JSON (brand → generic → mechanism → treatment hierarchy → competitor graph), and PII scrubber.
- **Requirements**: NLP-01, NLP-02, DATA-05
- **Success Criteria**:
  1. `en_core_sci_md` extracts drug names (emicizumab, mim8, concizumab, Hemgenix), companies, indications, and trial phases.
  2. Extracted entities mapped against B.Pharm ontology dictionary.
  3. `pii_scrubber.py` redacts personal identifiers prior to persistence.
- **Plans**: 2 plans

### Phase 4: Summarization, Zero-Shot Classification & Function Scoring
**Goal**: Implement local DistilBART summarization, BART MNLI zero-shot signal classification into 6 haemophilia categories, and role-relevance scoring for 5 Novo Nordisk functions.
- **Requirements**: NLP-03, NLP-04, NLP-05
- **Success Criteria**:
  1. BART MNLI classifies signals into `gene_therapy_milestone`, `regulatory_decision`, `congress_publication`, `patient_access`, `competitor_pipeline`, `inhibitor_signal`.
  2. DistilBART generates concise 1-sentence summaries.
  3. Role relevance confidence scores (0.0 to 1.0) computed for Medical Affairs, Regulatory, Market Access, Commercial, and R&D.
- **Plans**: 2 plans

### Phase 5: Signal Confluence Engine & Evidence Chain
**Goal**: Build core Confluence Engine to detect cross-source entity convergence within a 48h window, assign alert priority levels, and generate traceable evidence chains.
- **Requirements**: CONF-01, CONF-02, CONF-03
- **Success Criteria**:
  1. Engine identifies ≥2 independent signal types converging on the same entity within 48 hours.
  2. Alerts assigned CRITICAL, HIGH, MEDIUM, or LOW priority.
  3. Complete evidence chain (Source URL, timestamp, excerpt, credibility score) attached to every insight.
- **Plans**: 2 plans

### Phase 6: pgvector Hybrid Search & Ask Athena RAG Interface
**Goal**: Generate 384-dimensional vector embeddings with `all-MiniLM-L6-v2`, implement hybrid search (pgvector + `pg_trgm`), and expose Ask Athena RAG endpoint.
- **Requirements**: CONF-04, DATA-02, DATA-03
- **Success Criteria**:
  1. `sentence-transformers/all-MiniLM-L6-v2` generates 384-dim embeddings stored in pgvector.
  2. Ask Athena RAG interface answers natural language questions over stored signals with grounded, non-hallucinated responses.
- **Plans**: 2 plans

### Phase 7: Stakeholder Calibration Service & Persona Feedback Loop
**Goal**: Implement `StakeholderCalibrationService`, review widget backend, synthetic stakeholder persona profiles (Dr. Meera, Arjun, Priya), and dynamic function scoring weight recalibration logic.
- **Requirements**: CALIB-01, CALIB-02, CALIB-03
- **Success Criteria**:
  1. Stakeholder review widget stores structured feedback (relevance 1-5, urgency 1-5, actionability).
  2. `StakeholderCalibrationService` updates role scoring weights based on persona ratings.
  3. Pre vs post calibration scores displayed side-by-side on dashboard.
- **Plans**: 2 plans

### Phase 8: Four-Question Dashboard & Signal Feed UI
**Goal**: Build Next.js 15 dashboard featuring Four-Question Panels (Q1: What changed?, Q2: Why does it matter?, Q3: Which function?, Q4: What action?), 5-role selector, Recharts trend chart, and source health bar.
- **Requirements**: UI-01, UI-02, UI-04, UI-06
- **Success Criteria**:
  1. Dashboard renders 4-panel framework cleanly.
  2. Panel 4 action bullets prefaced with *"Suggested — requires human review"*.
  3. Role selector filters feed seamlessly across Medical Affairs, Regulatory, Market Access, Commercial, and R&D.
  4. 7-day trend chart visualizes signal volume by type.
  5. Live source health bar shows green/yellow/red API status.
- **Plans**: 3 plans

### Phase 9: Confluence Alerts View, Entity Explorer & System Integration
**Goal**: Build Confluence Alerts view, Entity Explorer interface, calibration status footer, end-to-end integration, performance tuning, and backup demo video recording.
- **Requirements**: UI-03, UI-05, UI-07
- **Success Criteria**:
  1. Top strategic Confluence Alerts surface prominently above raw feeds.
  2. Entity Explorer allows browsing signals by drug (emicizumab, mim8) or competitor.
  3. Full Docker Compose stack boots end-to-end under 500ms cached response time.
  4. Demo video recorded as backup for presentation.
- **Plans**: 2 plans

---
*Roadmap updated for MetaRadar Haemophilia GSD project*
