# Research Summary — MetaRadar

## Key Findings

### Technology Stack
- **Backend**: FastAPI + LangGraph + PostgreSQL 16 (pgvector) + Redis 7.
- **NLP/LLM**: spaCy en_core_sci_md + model-agnostic local HuggingFace summarizer (LOCAL_LLM_MODEL).
- **Resilience**: 	enacity retry library + aw_signals_bronze replay layer.
- **Frontend**: Next.js 15 + TailwindCSS 4 + shadcn/ui + TanStack Query v5.

### Table Stakes
- Multi-source ingestion (NewsAPI, PubMed).
- Deduplication & quality scoring.
- Pharma NER + B.Pharm ontology lookup.
- Model-agnostic 1-line summarization.
- Next.js role-filtered dashboard.

### Core Differentiators
- **Signal Confluence Engine**: Cross-source convergence detection (≥2 signal types in 48h).
- **Traceable Reasoning**: Complete evidence chain on all insights.
- **GxP WORM Audit Trail**: 21 CFR Part 11 compliant append-only audit log.
- **Model-Agnostic Flexibility**: Configurable local LLM via environment variables.
