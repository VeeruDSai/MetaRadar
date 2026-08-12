<!-- GSD:project-start source:PROJECT.md -->
## Project

**MetaRadar** is a near-real-time competitive intelligence radar that converts fragmented public signals into evidence-backed developments and role-specific actions, built for the **Novo Nordisk GBS Hackathon 2026** (Problem Statement #3: "From Inbox Noise to Strategic Signal | Pilot Area: Haemophilia within Rare Disease").

> **Master Specification:** The sole canonical and authoritative specification for this repository is [METARADAR_MASTER_PLAN_v5.0.md](file:///c:/Users/OM%20Prakash/Documents/novonordisk/docs/METARADAR_MASTER_PLAN_v5.0.md). All other documentation files are secondary historical references and must not override the Master Plan.

While conventional AI systems summarize documents, MetaRadar builds an evidence story around every key development in the haemophilia treatment landscape (from IV factor replacement to subcutaneous bispecific antibodies like emicizumab, concizumab, and mim8, and single-administration gene therapies like Hemgenix and Roctavian). It runs a **10-node LangGraph workflow** (`INGEST → VALIDATE → UNDERSTAND → ANALYZE (Confluence, Lifecycle, Red-Team, Missing-Signal) → SYNTHESIZE → CALIBRATE → BRIEF`) that feeds five intelligence mechanisms into a **Four-Question Framework**:
1. **What changed?** (Near-real-time signal feed, entity tags, multi-source confluence alerts)
2. **Why does it matter?** (Relevance breakdown, lifecycle position, red-team contradiction analysis, competitive context)
3. **Which Novo Nordisk function should review it?** (Calibrated role-routing badges with confidence scores for Medical Affairs)
4. **What action may be required?** (AI-suggested actions based on evidence, lifecycle, and missing-signal context, prefaced "Suggested — requires human review")

MetaRadar includes a **Stakeholder Calibration Prototype (HITL)** that uses feedback from simulated Novo Nordisk stakeholder personas (Medical Affairs, Regulatory, Market Access) to dynamically recalibrate function scoring weights.

**Core Value:** A Novo Nordisk Medical Affairs analyst opens MetaRadar and sees an evidence-backed development story (*"Hemgenix 3-year gene therapy durability data just dropped at ASH — 3 converging signals across clinical + regulatory + patient channels, with real-world contradiction flags, lifecycle positioning, and missing submission warnings — here is why it matters and what action to take next"*) — with every claim traceable to public sources, zero hallucinations, and clear role-specific implications.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Prescriptive Technology Stack
### Backend API
- **FastAPI 0.110+ (Python 3.11)**: Async-first, automatic OpenAPI documentation, high-throughput ASGI server (uvicorn/gunicorn).
### Workflow Orchestration
- **LangGraph 0.1+**: Stateful 10-node coordination workflow (`node_ingest → node_validate → node_nlp_extract → node_ontology_enrich → node_confluence → node_lifecycle → node_redteam → node_missing_signal → node_synthesize → node_calibrate`).
### Database & Vector Storage
- **PostgreSQL 16 + pgvector**: Unified relational (ACID) and 384-dimensional vector similarity search (`sentence-transformers/all-MiniLM-L6-v2`) in a single database.
### Cache & Task Queue
- **Redis 7**: Key-value caching for hot signals (2h TTL), rate limiting, user session storage.
- **Celery 5.3 + APScheduler**: Asynchronous ingestion pipeline and 2-hour periodic fetch scheduler.
### NLP & AI Models (Local by Default, Free)
- **Reasoning Layer (provider-agnostic, Master Plan §13)**: Default local **Gemma 3 4B Instruct (`google/gemma-3-4b-it`)** for narrative synthesis, Four-Question reasoning, suggested actions, and Ask Athena; **optional hosted xAI Grok API** (`LLM_PROVIDER=local|xai|auto`) behind a mandatory external-LLM privacy gate (public/synthetic data only, JSON-Schema structured outputs, per-output model metadata); safe degraded mode via BART — factual summarization only, never reasoning-equivalent.
- **spaCy 3.7 (en_core_sci_md)**: Local Named Entity Recognition (NER) for pharmaceutical entity extraction (drugs, companies, trial phases, indications).
- **BART (facebook/bart-large-cnn)**: Local factual signal summarization (CPU-friendly); also the safe degraded fallback when the reasoning LLM is unavailable — **factual summarization only, NOT a reasoning-equivalent replacement**.
- **BART MNLI (`facebook/bart-large-mnli`)**: Zero-shot classification for haemophilia signal types AND Red-Team contradiction entailment (one local model, two jobs; canonical per SRS `NLI_MODEL`).
- **Sentence-Transformers (sentence-transformers/all-MiniLM-L6-v2)**: Local 384-dim vector embeddings (80MB).
- **RAG Interface**: "Ask Athena" semantic search over saved signals via pgvector + local LLM.
### Data Sources (All Public)
- **NCBI PubMed / E-utilities**: PubMed literature retrieval (clinical literature & Phase 2/3 trial readouts). PubMed Central (PMC) full-text services are an OPTIONAL/EXTENSION, not the same endpoint.
- **NewsAPI**: Industry news & competitor press releases (Developer/free tier: 100 req/day, development/testing only, 24h article delay — not real-time, not for production).
- **ClinicalTrials.gov API**: Trial status changes & new registrations.
- **FDA OpenFDA API**: Approvals & adverse event communications.
- **EMA RSS**: European approval decisions & CHMP opinions.
- **Reddit PRAW**: Patient & HCP community sentiment (r/hemophilia, r/raredisease).
- **Congress Abstract Repositories**: ASH, ISTH, WFH, EHA public abstracts.
- **Synthetic/Mock Fallback**: 500 pre-curated haemophilia signals for stable offline demo fallback.
### Resilience & Calibration
- **StakeholderCalibrationService**: HITL learning loop adjusting function relevance scoring weights based on stakeholder feedback ratings.
- **tenacity + httpx**: Exponential backoff retry logic (3 retries: 2s, 4s, 8s) for external APIs.
- **WORM Audit Trail**: Append-only `audit_log` PostgreSQL table inspired by electronic-record traceability principles (engineering design analogy — MetaRadar does NOT claim 21 CFR Part 11 or GxP regulatory compliance).
- **PII/PHI Layer**: dedicated PII/PHI detection and redaction before persistence (spaCy NER contributes to entity detection but is not a guaranteed scrubber; low-confidence content is rejected/quarantined).
### Frontend Dashboard
- **Next.js 15 (React 19, TypeScript)**: App Router with Server Components, streaming, and Four-Question Panel layout.
- **TailwindCSS 4 + shadcn/ui**: Modern component design system.
- **TanStack Query v5**: Server state management, auto-caching, and background revalidation.
- **Recharts + Framer Motion**: Interactive trend visualizations and smooth signal card animations.
## What NOT to Use
- **Weaviate**: Replaced by pgvector to simplify Docker Compose and database administration.
- **OpenAI / Claude API keys**: Not used — default inference runs locally (zero API cost). Optional hosted reasoning (xAI Grok) is allowed ONLY when explicitly enabled via `LLM_PROVIDER=xai|auto`, behind the external-LLM privacy gate (Master Plan §13.5).
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture mapped in `.planning/PROJECT.md` and `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`.
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
