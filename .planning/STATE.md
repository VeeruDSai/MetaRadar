# MetaRadar — Project Memory & State

## Current Position

- **Milestone**: 1 (v1 MVP — Greenfield Initialization)
- **Current Phase**: Phase 1 (Database Foundation & Compliance Schema)
- **Phase Status**: Ready to plan Phase 1

## Progress Summary

| Phase | Description | Status | Plans |
|-------|-------------|--------|-------|
| 1 | Database Foundation & Compliance Schema | Pending | 0/2 |
| 2 | Ingestion & Resilience Layer | Pending | 0/2 |
| 3 | Pharma Ontology & NER Extraction Pipeline | Pending | 0/2 |
| 4 | Model-Agnostic Summarization & Classification | Pending | 0/2 |
| 5 | Signal Confluence Engine & Evidence Chain | Pending | 0/2 |
| 6 | Embeddings & pgvector Hybrid Search | Pending | 0/1 |
| 7 | FastAPI REST API & Compliance Audit Interceptor | Pending | 0/2 |
| 8 | Next.js 15 Dashboard & Signal Feed UI | Pending | 0/3 |
| 9 | Confluence Alerts View & End-to-End Integration | Pending | 0/2 |

## Decisions & Memory Log

- **2026-08-06**: Project initialized via /gsd-new-project.
- **2026-08-06**: Settled tech stack: FastAPI, LangGraph, PostgreSQL 16 + pgvector, Redis 7, spaCy, Next.js 15, shadcn/ui.
- **2026-08-06**: Model-agnostic LLM strategy established using LOCAL_LLM_MODEL env var (default: acebook/bart-large-cnn).
- **2026-08-06**: WORM udit_log (21 CFR Part 11) and aw_signals_bronze replay tables added to core schema.
