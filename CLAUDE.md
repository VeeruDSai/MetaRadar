<!-- GSD:project-start source:PROJECT.md -->
## Project

**MetaRadar** is a real-time metabolic disease competitive intelligence platform built for the **Novo Nordisk GBS Hackathon 2026** (Problem Statement #3: "From Inbox Noise to Strategic Signal").

It converts fragmented external signals — news, clinical literature, social media, regulatory filings — into role-specific, actionable intelligence for Novo Nordisk's Medical Affairs, Regulatory, and Commercial teams. The system detects early market signals in obesity, diabetes, and GLP-1 therapies by running a multi-agent LangGraph pipeline that ingests, enriches, confluences, and synthesizes intelligence automatically every 2 hours.

**Core Value:** A Novo Nordisk Medical Affairs analyst opens MetaRadar and immediately sees *"tirzepatide just got a regulatory win in Europe — here are 12 converging signals across clinical + regulatory + social channels, and here's what you should do next"* — with every claim traceable to its source, no hallucinations, no manual work.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

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
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
