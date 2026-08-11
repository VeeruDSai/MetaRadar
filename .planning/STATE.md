# MetaRadar — Project Memory & State

## Current Position

- **Milestone**: 1 (v1 MVP — Greenfield Initialization)
- **Current Phase**: Phase 1 (Database Foundation & Compliance Schema)
- **Phase Status**: Ready to plan Phase 1
- **Domain Focus**: Haemophilia within Rare Disease (Novo Nordisk GBS Hackathon 2026 Problem Statement #3)

## Progress Summary

| Phase | Description | Status | Plans |
|-------|-------------|--------|-------|
| 1 | Database Foundation & Compliance Schema | Pending | 0/2 |
| 2 | Multi-Source Haemophilia Ingestion & Resilience Layer | Pending | 0/2 |
| 3 | B.Pharm Haemophilia Ontology & spaCy NER Pipeline | Pending | 0/2 |
| 4 | Summarization, Zero-Shot Classification & Function Scoring | Pending | 0/2 |
| 5 | Signal Confluence Engine & Evidence Chain | Pending | 0/2 |
| 6 | pgvector Hybrid Search & Ask Athena RAG Interface | Pending | 0/2 |
| 7 | Stakeholder Calibration Service & Persona Feedback Loop | Pending | 0/2 |
| 8 | Four-Question Dashboard & Signal Feed UI | Pending | 0/3 |
| 9 | Confluence Alerts View, Entity Explorer & System Integration | Pending | 0/2 |

## Decisions & Memory Log

- **2026-08-06**: Project initialized via `/gsd-new-project`.
- **2026-08-06**: Settled tech stack: FastAPI, LangGraph, PostgreSQL 16 + pgvector, Redis 7, spaCy, Next.js 15, shadcn/ui.
- **2026-08-11**: **CONCEPT NOTE ALIGNMENT:** Shifted domain focus to **Haemophilia within Rare Disease** (pilot area).
- **2026-08-11**: Adopted **Four-Question Framework UX**: Panel 1 (What changed?), Panel 2 (Why does it matter?), Panel 3 (Which function?), Panel 4 (What action?).
- **2026-08-11**: Established **6-Agent LangGraph Pipeline**: Ingestion → Validation → NLP → Confluence → Synthesis → Brief.
- **2026-08-11**: Added **Stakeholder Calibration Loop (HITL)** with `StakeholderCalibrationService` and synthetic persona profiles (Dr. Meera, Arjun, Priya).
- **2026-08-11**: Expanded data sources: PubMed, NewsAPI, ClinicalTrials.gov, OpenFDA, EMA RSS, Reddit PRAW, Congress abstract archives, and 500-signal synthetic demo fallback dataset.
- **2026-08-11**: Expanded roles to 5 Novo Nordisk functions: Medical Affairs, Regulatory, Market Access, Commercial, and R&D.
