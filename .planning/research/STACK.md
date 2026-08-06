# Stack Research — MetaRadar

## Prescriptive Technology Stack

### Backend API
- **FastAPI 0.110+ (Python 3.11)**: Async-first, automatic OpenAPI documentation, high-throughput ASGI server (uvicorn/gunicorn).

### Agent Orchestration
- **LangGraph 0.1+**: Stateful multi-agent graph coordination (ingest → validate → nlp → confluence → synthesize → brief).

### Database & Vector Storage
- **PostgreSQL 16 + pgvector**: Unified relational (ACID) and 768-dimensional vector similarity search in a single database. Eliminates vector DB overhead.

### Cache & Task Queue
- **Redis 7**: Key-value caching for hot signals (2h TTL), rate limiting, user session storage.
- **Celery 5.3 + APScheduler**: Distributed task queue for asynchronous ingestion and periodic (2-hour) fetch triggers.

### NLP & AI Models
- **spaCy 3.7 (en_core_sci_md) + medspacy**: Local Named Entity Recognition (NER) for pharmaceutical entity extraction (drugs, companies, indications).
- **Sentence-Transformers (sentence-transformers/all-MiniLM-L6-v2)**: Local 768-dim embeddings generation (80MB).
- **Summarization/LLM (LOCAL_LLM_MODEL)**: Model-agnostic HuggingFace pipeline configured via environment variables. Default: acebook/bart-large-cnn. Swappable to Gemma 2B, Mistral 7B, Phi-3, TinyLlama without code changes.
- **Classification**: acebook/bart-large-mnli (zero-shot classification for signal types).

### Resilience & Compliance
- **tenacity + httpx**: Exponential backoff retry logic (3 retries: 2s, 4s, 8s) for external APIs.
- **WORM Audit Trail**: Append-only udit_log PostgreSQL table compliant with FDA 21 CFR Part 11 and GxP standards.
- **PII Scrubber**: spaCy-based PII/PHI detection and redaction before database persistence.

### Frontend Dashboard
- **Next.js 15 (React 19, TypeScript)**: App Router with Server Components and dynamic streaming.
- **TailwindCSS 4 + shadcn/ui**: Modern component design system.
- **TanStack Query v5**: Server state management, auto-caching, and background revalidation.
- **Recharts + Framer Motion**: Interactive trend visualizations and smooth signal card animations.

## What NOT to Use
- **Weaviate**: Replaced by pgvector to reduce container complexity and unified database maintenance.
- **OpenAI / Commercial API keys**:  budget requirement — all models must run locally or via open-source free tiers.
