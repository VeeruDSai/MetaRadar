<!-- GSD:project-start source:PROJECT.md -->
## Project

**MetaRadar** is an intelligence radar that converts fragmented public signals into evidence-backed developments and role-specific actions, built for the **Novo Nordisk GBS Hackathon 2026** (Problem Statement #3: "From Inbox Noise to Strategic Signal | Pilot Area: Haemophilia within Rare Disease").

While conventional AI systems summarize documents, MetaRadar builds an evidence story around every key development in the haemophilia treatment landscape (from IV factor replacement to subcutaneous bispecific antibodies like emicizumab, concizumab, and mim8, and single-administration gene therapies like Hemgenix and Roctavian). It runs a **10-agent LangGraph pipeline** (Ingestion → Validation → NLP → Confluence → Lifecycle → Red-Team → Missing-Signal → Synthesis → Brief → Stakeholder Calibration) that feeds five intelligence mechanisms into a **Four-Question Framework**:
1. **What changed?** (Real-time signal feed, entity tags, multi-source confluence alerts)
2. **Why does it matter?** (Relevance breakdown, lifecycle position, red-team contradiction analysis, competitive context)
3. **Which Novo Nordisk function should review it?** (Calibrated role-routing badges with confidence scores)
4. **What action may be required?** (AI-suggested actions based on evidence, lifecycle, and missing-signal context, prefaced "Suggested — requires human review")

MetaRadar includes a **Stakeholder Calibration Loop (HITL)** that uses feedback from simulated Novo Nordisk stakeholder personas (Medical Affairs, Regulatory, Market Access) to dynamically recalibrate function scoring weights.

**Core Value:** A Novo Nordisk Medical Affairs analyst opens MetaRadar and sees an evidence-backed development story (*"Hemgenix 3-year gene therapy durability data just dropped at ASH — 3 converging signals across clinical + regulatory + patient channels, with real-world contradiction flags, lifecycle positioning, and missing submission warnings — here is why it matters and what action to take next"*) — with every claim traceable to public sources, zero hallucinations, and clear role-specific implications.
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Prescriptive Technology Stack
### Backend API
- **FastAPI 0.110+ (Python 3.11)**: Async-first, automatic OpenAPI documentation, high-throughput ASGI server (uvicorn/gunicorn).
### Agent Orchestration
- **LangGraph 0.1+**: Stateful 10-agent coordination graph (Ingestion → Validation → NLP → Confluence → Lifecycle → Red-Team → Missing-Signal → Synthesis → Brief → Stakeholder Calibration).
### Database & Vector Storage
- **PostgreSQL 16 + pgvector**: Unified relational (ACID) and 384-dimensional vector similarity search (`sentence-transformers/all-MiniLM-L6-v2`) in a single database.
### Cache & Task Queue
- **Redis 7**: Key-value caching for hot signals (2h TTL), rate limiting, user session storage.
- **Celery 5.3 + APScheduler**: Asynchronous ingestion pipeline and 2-hour periodic fetch scheduler.
### NLP & AI Models (All Local, Free)
- **spaCy 3.7 (en_core_sci_md)**: Local Named Entity Recognition (NER) for pharmaceutical entity extraction (drugs, companies, trial phases, indications).
- **DistilBART (sshleifer/distilbart-cnn-12-6)**: Local signal summarization (310MB).
- **BART MNLI (cross-encoder/nli-MiniLM2-L6-H768)**: Zero-shot classification for haemophilia signal types (120MB).
- **Sentence-Transformers (sentence-transformers/all-MiniLM-L6-v2)**: Local 384-dim vector embeddings (80MB).
- **RAG Interface**: "Ask Athena" semantic search over saved signals via pgvector + local LLM.
### Data Sources (All Public)
- **PubMed Central API**: Clinical literature & Phase 2/3 trial readouts.
- **NewsAPI**: Industry news & competitor press releases (500 free/day).
- **ClinicalTrials.gov API**: Trial status changes & new registrations.
- **FDA OpenFDA API**: Approvals & adverse event communications.
- **EMA RSS**: European approval decisions & CHMP opinions.
- **Reddit PRAW**: Patient & HCP community sentiment (r/hemophilia, r/raredisease).
- **Congress Abstract Repositories**: ASH, ISTH, WFH, EHA public abstracts.
- **Synthetic/Mock Fallback**: 500 pre-curated haemophilia signals for stable offline demo fallback.
### Resilience & Calibration
- **StakeholderCalibrationService**: HITL learning loop adjusting function relevance scoring weights based on stakeholder feedback ratings.
- **tenacity + httpx**: Exponential backoff retry logic (3 retries: 2s, 4s, 8s) for external APIs.
- **WORM Audit Trail**: Append-only `audit_log` PostgreSQL table compliant with GxP & 21 CFR Part 11 standards.
- **PII Scrubber**: spaCy-based PII/PHI detection and redaction before persistence.
### Frontend Dashboard
- **Next.js 15 (React 19, TypeScript)**: App Router with Server Components, streaming, and Four-Question Panel layout.
- **TailwindCSS 4 + shadcn/ui**: Modern component design system.
- **TanStack Query v5**: Server state management, auto-caching, and background revalidation.
- **Recharts + Framer Motion**: Interactive trend visualizations and smooth signal card animations.
## What NOT to Use
- **Weaviate**: Replaced by pgvector to simplify Docker Compose and database administration.
- **Commercial LLM API keys (OpenAI / Claude)**: All inference runs locally (zero API cost).
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
