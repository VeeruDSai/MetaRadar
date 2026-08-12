# Technology Stack

**Analysis Date:** 2026-08-13

## Repository Nature (Important Context)

This repository is currently **specification-first**: it contains only documentation (`README.md`, `CLAUDE.md`, `docs/*.md`) describing the planned MetaRadar system. **No implementation code or package manifests exist yet.** Every technology below is *prescribed* by the canonical specification ([`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md)) and supporting docs. The prescribed stack is what any implementation must follow.

## Languages

**Primary (prescribed, backend):**
- Python 3.11 — backend API, workflow orchestration, NLP/ML pipeline (`docs/METARADAR_MASTER_PLAN_v5.0.md` §4, `docs/2_SRS_Software_Requirements_Specification.md` §3)

**Primary (prescribed, frontend):**
- TypeScript + React 19 — Next.js 15 App Router frontend (`README.md` "Technology Stack" table)

**Secondary:**
- SQL — PostgreSQL schema DDL (documented in `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §Schema)
- Bash — docker compose orchestration commands (`README.md` "Running with Docker")

## Runtime

**Environment:**
- Docker Desktop + Docker Compose — recommended full local stack (`README.md` "Prerequisites")
- Node.js 20.9+ (minimum for Next.js 15 install flow, per `README.md`)
- Python 3.11+ interpreter for backend services

**Package Manager:**
- npm (frontend) / pip or uv (backend) — not yet instantiated; no lockfiles present in repo
- Lockfile: **missing** (no `package.json`, `requirements.txt`, or `pyproject.toml` exists yet)

## Frameworks

**Core (prescribed):**
- FastAPI 0.110+ — async-first backend API, automatic OpenAPI docs (`CLAUDE.md` "Technology Stack", `docs/METARADAR_MASTER_PLAN_v5.0.md` §4)
- LangGraph 0.1+ — 10-node stateful workflow (`node_ingest → node_validate → node_nlp_extract → node_ontology_enrich → node_confluence → node_lifecycle → node_redteam → node_missing_signal → node_synthesize → node_calibrate`) (`docs/METARADAR_MASTER_PLAN_v5.0.md` §4)
- Next.js 15 (React 19, TypeScript) — App Router, Server Components, streaming (`README.md` Technical Architecture)
- TailwindCSS 4 + shadcn/ui — styling and component system (`CLAUDE.md` "Technology Stack")

**Data/State (prescribed):**
- TanStack Query v5 — server state, auto-caching, background revalidation (`CLAUDE.md`)
- Recharts + Framer Motion — visualizations and card animations (`CLAUDE.md`)

**Workers (prescribed):**
- Celery 5.3 — asynchronous ingestion pipeline
- APScheduler — 2-hour periodic fetch scheduler (`docs/METARADAR_MASTER_PLAN_v5.0.md` §4)

## AI / ML Models (Local by Default, Free — Zero API Cost)

**Prescribed by `CLAUDE.md` and `docs/2_SRS_Software_Requirements_Specification.md` §3/§4.2:**
- **Reasoning Layer (provider-agnostic, Master Plan v5.0 §13):** `google/gemma-3-4b-it` (Gemma 3 4B Instruct, Q4-quantized for CPU) as default **local** provider — Four-Question reasoning, narrative synthesis, AI-suggested actions, Ask Athena — via `LOCAL_LLM_MODEL` / `LOCAL_LLM_TASK` env vars; model-agnostic by design (any HuggingFace text-generation model swap-in). **Optional hosted provider: xAI Grok API** (`LLM_PROVIDER=xai|auto`, `XAI_API_KEY`/`XAI_MODEL`) gated by a mandatory external-LLM privacy gate (public/synthetic data only; JSON-Schema structured outputs; per-output model metadata). When no reasoning provider is available the system enters **degraded mode**: BART performs factual summarization only — it is NOT a reasoning-equivalent replacement, no unsupported interpretation is generated, and no AI action recommendation requiring reasoning is produced (`docs/2_SRS_Software_Requirements_Specification.md` FR-2.2.3A–G)
- **Batch Summarizer:** `facebook/bart-large-cnn` — CPU-fast seq2seq 1-sentence factual summaries (< 60s per 100 signals target); also the **safe degraded fallback: factual summarization only** when the reasoning LLM is unavailable (`SUMMARIZER_MODEL` / `SUMMARIZER_TASK`)
- **Contradiction Analysis:** `facebook/bart-large-mnli` — zero-shot NLI entailment/contradiction checks, flag threshold > 0.60 (`docs/METARADAR_MASTER_PLAN_v5.0.md` §6)
- **NER:** spaCy 3.7 `en_core_sci_md` — pharmaceutical entity extraction (drugs, companies, trial phases, indications); contributes to entity detection only — a dedicated PII/PHI detection + redaction layer is responsible for preventing sensitive information from being persisted (spaCy alone is not a guaranteed scrubber)
- **Embeddings:** `sentence-transformers/all-MiniLM-L6-v2` — 384-dim vectors via pgvector (`CLAUDE.md`)

## Key Dependencies

**Critical (prescribed):**
- LangGraph — orchestrates the 10-node intelligence workflow (the system's backbone)
- pgvector — 384-dim semantic search inside PostgreSQL (replaces standalone vector DBs like Weaviate — see `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md`)
- HuggingFace `transformers` pipeline — hosts all local models
- `httpx` — async HTTP client for external API ingestion
- `tenacity` — exponential backoff retry (3 retries: 2s, 4s, 8s) (`CLAUDE.md` "Resilience & Calibration")

**Infrastructure:**
- PostgreSQL 16 — primary ACID store + vector search (`README.md`)
- Redis 7 — hot-signal cache (2h TTL), rate limiting, session storage (`CLAUDE.md`)
- Docker Compose — single-file environment definition (`README.md` "Running with Docker")

## Configuration

**Environment:**
- Configured via `.env` (copied from `.env.example`) — never commit secrets (`README.md` "Configuration")
- Key vars: `APP_ENV`, `DATABASE_URL`, `REDIS_URL`, `NEWSAPI_KEY`, `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `LOCAL_LLM_TASK`, `XAI_API_KEY`, `XAI_MODEL`, `XAI_TIMEOUT`, `SUMMARIZER_MODEL`, `SUMMARIZER_TASK` (`docs/2_SRS_Software_Requirements_Specification.md` §4.2)
- All external API calls HTTPS with credentials via `.env` only, never in code (SRS NFR)

**Build:**
- No build config files exist yet (no `tsconfig.json`, `pyproject.toml`, `docker-compose.yml` in repo). All described in `README.md` "Project Structure" as the intended layout.

## Platform Requirements

**Development:**
- Git, Docker Desktop, Docker Compose, Node.js 20.9+, Python 3.11+ (`README.md` "Prerequisites")
- **Estimated** memory requirement to run Gemma 3 4B on CPU: ~2.6 GB weights (Q4-quantized) and roughly 4.5–7.5 GB RAM — planning estimates only; actual usage depends on the runtime, quantization implementation, context length, and system configuration (`docs/2_SRS_Software_Requirements_Specification.md`). Lighter alternative: `google/gemma-3-1b-it`; BART fallback for summarization

**Production:**
- Docker Compose stack: frontend `:3000`, backend `:8000`, PostgreSQL `:5432`, Redis `:6379` (`README.md` "Running with Docker")

## What NOT to Use (Explicit Decisions)

- **Weaviate** — replaced by pgvector (`CLAUDE.md`, `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md`)
- **OpenAI / Claude API keys** — not used; all inference runs locally by default, zero API cost (`CLAUDE.md`). Optional hosted reasoning (xAI Grok) is allowed only when explicitly enabled via `LLM_PROVIDER=xai|auto`, behind the external-LLM privacy gate (Master Plan §13.5)
- **LangChain** — rejected in `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md` (adds ~200MB overhead, over-abstracts for hackathon scope)

---

*Stack analysis: 2026-08-13*
