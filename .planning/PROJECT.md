# MetaRadar — Project Context

## What This Is

**MetaRadar** is a real-time metabolic disease competitive intelligence platform built for the **Novo Nordisk GBS Hackathon 2026** (Problem Statement #3: "From Inbox Noise to Strategic Signal").

It converts fragmented external signals — news, clinical literature, social media, regulatory filings — into role-specific, actionable intelligence for Novo Nordisk's Medical Affairs, Regulatory, and Commercial teams. The system detects early market signals in obesity, diabetes, and GLP-1 therapies by running a multi-agent LangGraph pipeline that ingests, enriches, confluences, and synthesizes intelligence automatically every 2 hours.

**Core Value:** A Novo Nordisk Medical Affairs analyst opens MetaRadar and immediately sees *"tirzepatide just got a regulatory win in Europe — here are 12 converging signals across clinical + regulatory + social channels, and here's what you should do next"* — with every claim traceable to its source, no hallucinations, no manual work.

## Team

- **Organization:** MS Ramaiah Institute of Technology (MSRIT)
- **CSE Team (us):** Builds all software — FastAPI backend, LangGraph agents, PostgreSQL schema, Next.js dashboard, Docker Compose
- **B.Pharm Team (domain experts):** Authors the pharma ontology JSON, validates signal taxonomy, reviews NER accuracy
- **Role split:** CSE = code, B.Pharm = domain content/QA

## Timeline

- **Hackathon deadline:** ~4 weeks
- **Week 1:** Foundation (DB schema, ingestion, NLP, ontology)
- **Week 2:** Intelligence layer (confluence engine, scoring, dashboard)
- **Week 3:** Advanced features (Ask Athena RAG, narrative briefs)
- **Week 4:** Polish, demo prep, compliance hardening

## Architecture (Settled)

- **Backend:** FastAPI + Python 3.11 (async-first)
- **Agents:** LangGraph (ingest → validate → nlp → confluence → synthesize → brief)
- **Database:** PostgreSQL 16 + pgvector (single DB) — Weaviate removed
- **Cache:** Redis 7 + tenacity/httpx retry
- **Task Queue:** Celery + Redis + APScheduler (2-hour fetch cycle)
- **NLP/NER:** spaCy 3.7 en_core_sci_md + medspacy
- **LLM:** Model-agnostic via LOCAL_LLM_MODEL env var (default: facebook/bart-large-cnn)
- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2
- **Frontend:** Next.js 15 + TypeScript + shadcn/ui + TailwindCSS 4 + TanStack Query v5
- **Deployment:** Docker Compose → Vercel + Render

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| pgvector instead of Weaviate | One less Docker container; same hybrid search | Final |
| LangGraph orchestration | Stateful multi-agent graph; role-specific branching | Final |
| Model-agnostic LLM (env var) | Zero API cost; swap BART/Gemma/Mistral with config change | Final |
| Bronze layer (raw_signals_bronze) | Pipeline replay on failure; zero data loss | Final |
| WORM audit log (21 CFR Part 11) | GxP compliance; append-only table | Final |
| Confluence Engine | Core differentiator; cross-source convergence detection | Final |

## Requirements

### Validated
(None yet — ship to validate)

### Active

**Core differentiators:**
- [ ] Signal Confluence Engine (CRITICAL/HIGH/MEDIUM/LOW alerts)
- [ ] B.Pharm Pharma Ontology (drug→brand→mechanism→manufacturer)
- [ ] Traceable Reasoning (evidence chain on every insight)
- [ ] Role-Specific Views (Medical Affairs / Regulatory / Commercial)
- [ ] LangGraph 6-agent pipeline

**Table stakes:**
- [ ] Multi-source ingestion (NewsAPI + PubMed minimum)
- [ ] Signal dedup, quality scoring, validation
- [ ] spaCy NER + ontology enrichment
- [ ] Model-agnostic summarization (BART default)
- [ ] PostgreSQL schema (signals, entities, confluence_events, briefs, raw_signals_bronze, audit_log)
- [ ] pgvector hybrid search (semantic + keyword)
- [ ] Redis caching + tenacity retry fallback
- [ ] Next.js dashboard (signal feed, trends, confluence alerts)
- [ ] Role filter, date range, search

**Extended (Week 3-4):**
- [ ] Ask Athena RAG query interface
- [ ] Narrative briefs (WHAT/WHY/ACTION)
- [ ] Temporal pattern matching
- [ ] ClinicalTrials.gov source
- [ ] Reddit sentiment

### Out of Scope
- Weaviate — replaced by pgvector
- GPT-4 / commercial LLMs — budget is zero
- Real Novo Nordisk internal data
- Mobile app

## Compliance (non-negotiable)
- WORM audit_log (21 CFR Part 11)
- PII scrubbing before storage
- Medical disclaimer on all AI output
- No hardcoded model names in codebase

## Source Documents
All architecture is in docs/ (1_GAP_ANALYSIS through 6_NOVO, plus deep-research-report.md)

## Evolution

This document evolves at phase transitions and milestone boundaries.

---
*Last updated: 2026-08-06 after initialization*
