# Features Research — MetaRadar

## Feature Breakdown

### Table Stakes (Must-Have for Hackathon Demo)
1. **Multi-Source Ingestion**: Asynchronous data fetchers for NewsAPI (500/day free limit) and PubMed API.
2. **Quality Scoring & Deduplication**: Fuzzy title matching (>80% similarity threshold) and quality validation (>50 char length, English language).
3. **Pharma NER & Ontology Validation**: spaCy entity extraction enriched against B.Pharm-authored JSON dictionary (drug → brand → mechanism → manufacturer → competitor).
4. **Model-Agnostic Signal Summarization**: 1-line (<50 char) AI summary generated via local HuggingFace model with non-suppressible clinical disclaimer.
5. **Role-Relevance Scoring & Filtering**: Multi-role filtering tailored to Medical Affairs, Regulatory, and Commercial priorities.
6. **Unified PostgreSQL + pgvector Storage**: Schema for raw bronze signals, processed signals, entities, and vector embeddings.
7. **Next.js Competitive Dashboard**: Interactive UI with role selection, date filtering, 7-day trend chart, and signal cards.

### Differentiators (Core Value Drivers)
1. **Signal Confluence Engine**: Detects when ≥2 independent signal types (clinical, regulatory, social, competitive) converge on the same entity within a 48-hour window to elevate alert status (CRITICAL / HIGH / MEDIUM / LOW).
2. **Traceable Reasoning Evidence Chain**: Every signal and alert displays a complete source trace (Source → URL → Timestamp → Excerpt) to ensure zero hallucination.
3. **GxP WORM Audit Trail**: 21 CFR Part 11 compliant append-only log capturing all user actions (score overrides, taxonomy edits, signal dismissals).

### Extended Features (Week 3-4 Scope)
1. **Ask Athena Conversational RAG**: Natural language query interface over pgvector hybrid search.
2. **Executive Narrative Briefs**: Role-tailored WHAT / WHY / RECOMMENDED ACTION intelligence summaries per entity.
3. **Temporal Pattern Matching**: Automated competitive timeline matching (e.g., pre-approval surge, access crisis).
4. **Additional Data Sources**: Reddit sentiment ingestion and ClinicalTrials.gov registry integration.

### Anti-Features (Deliberately NOT Building)
- Real Novo Nordisk internal proprietary data.
- Hardcoded LLM model names or proprietary paid API reliance.
- Separate vector database deployment (Weaviate).
