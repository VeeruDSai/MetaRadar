# MetaRadar — Phase Roadmap

## Overview

- **Total Phases**: 9 focused phases
- **Requirements Covered**: 23 v1 requirements (100% coverage)
- **Granularity**: Fine (focused, verifiable micro-phases)

---

## Phase Breakdown

### Phase 1: Database Foundation & Compliance Schema
**Goal**: Initialize PostgreSQL 16 database, install pgvector extension, and deploy core schema tables including bronze raw storage and WORM audit log.
- **Requirements**: INGEST-02, DATA-01, DATA-04
- **Success Criteria**:
  1. Docker Compose successfully launches PostgreSQL 16 container with pgvector extension enabled.
  2. Tables aw_signals_bronze, signals, entities, confluence_events, riefs, and udit_log are created cleanly.
  3. udit_log permissions strictly revoke UPDATE and DELETE operations for the application user.
- **Plans**: 1-2 plans

### Phase 2: Ingestion & Resilience Layer
**Goal**: Implement async multi-source fetchers for NewsAPI and PubMed with retry logic, deduplication, and raw bronze persistence.
- **Requirements**: INGEST-01, INGEST-03, INGEST-04, INGEST-05
- **Success Criteria**:
  1. Async fetchers fetch signals from NewsAPI and PubMed in parallel without blocking.
  2. Raw responses are saved verbatim to aw_signals_bronze before processing.
  3. 	enacity handles simulated network errors with 3-step exponential backoff retries.
  4. Duplicate signals (>80% title similarity) and low-quality items (<50 chars, non-English) are filtered out.
- **Plans**: 2 plans

### Phase 3: Pharma Ontology & NER Extraction Pipeline
**Goal**: Integrate spaCy NER, medspacy, PII scrubber, and B.Pharm-authored JSON ontology lookup.
- **Requirements**: NLP-01, NLP-02, DATA-05
- **Success Criteria**:
  1. en_core_sci_md extracts drug names, companies, indications, and clinical phases accurately.
  2. Extracted entities are enriched against local pharma ontology JSON.
  3. pii_scrubber.py redacts any personal identifiers prior to database persistence.
- **Plans**: 2 plans

### Phase 4: Model-Agnostic Summarization & Classification
**Goal**: Implement local signal classification and model-agnostic LLM summarization pipeline.
- **Requirements**: NLP-03, NLP-04, NLP-05
- **Success Criteria**:
  1. acebook/bart-large-mnli classifies signals into 5 standardized categories.
  2. LOCAL_LLM_MODEL environment variable dynamically initializes HuggingFace summarization pipeline without hardcoded model references.
  3. Role relevance scores (0.0-1.0) are computed for Medical Affairs, Regulatory, and Commercial.
- **Plans**: 2 plans

### Phase 5: Signal Confluence Engine & Evidence Chain
**Goal**: Build the core Confluence Engine to detect cross-source entity convergence and construct traceable evidence chains.
- **Requirements**: CONF-01, CONF-02, CONF-03
- **Success Criteria**:
  1. Confluence Engine identifies ≥2 independent signal types converging on an entity within a 48h window.
  2. Alerts are assigned CRITICAL, HIGH, MEDIUM, or LOW urgency based on signal matrix.
  3. Traceable evidence chains (Source, URL, Timestamp, Excerpt) are generated for all alerts.
- **Plans**: 2 plans

### Phase 6: Embeddings & pgvector Hybrid Search
**Goal**: Generate 768-dimensional local embeddings and implement pgvector + pg_trgm hybrid search query engine.
- **Requirements**: DATA-02, DATA-03
- **Success Criteria**:
  1. sentence-transformers/all-MiniLM-L6-v2 generates 768-dim embeddings stored in pgvector column.
  2. SQL queries execute hybrid search (alpha=0.6 semantic distance + 0.4 keyword similarity) in <1 second.
- **Plans**: 1 plan

### Phase 7: FastAPI REST API & Compliance Audit Interceptor
**Goal**: Expose backend REST endpoints (/api/v1/signals, /api/v1/confluence, /api/v1/health) and wire audit logging middleware.
- **Requirements**: UI-06
- **Success Criteria**:
  1. FastAPI endpoints serve signals, confluence alerts, and health telemetry cleanly.
  2. User action overrides automatically record audit trail entries in udit_log.
  3. Audit trail export endpoint outputs GxP-compliant JSON logs.
- **Plans**: 2 plans

### Phase 8: Next.js 15 Dashboard & Signal Feed UI
**Goal**: Build the Next.js frontend dashboard, signal cards with clinical disclaimers, trend charts, and role switching.
- **Requirements**: UI-01, UI-03, UI-04, UI-05
- **Success Criteria**:
  1. Next.js 15 dashboard renders signal cards sorted by relevance score.
  2. Every AI summary displays a non-suppressible <DisclaimerBadge /> label.
  3. Recharts renders 7-day signal volume trend line chart dynamically.
  4. Role selector filters content seamlessly between Medical Affairs, Regulatory, and Commercial.
- **Plans**: 2-3 plans

### Phase 9: Confluence Alerts View & End-to-End Integration
**Goal**: Render top strategic Confluence Alerts view, integrate backend and frontend, and conduct full system verification.
- **Requirements**: UI-02
- **Success Criteria**:
  1. Confluence Alerts view surfaces converging strategic alerts prominently above raw feeds.
  2. Full Docker Compose environment boots end-to-end without errors.
  3. Demonstration scenarios (API failure retry, role switching, evidence chain expansion) pass 100%.
- **Plans**: 2 plans

---
*Roadmap generated for MetaRadar GSD project*
