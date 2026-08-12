# External Integrations

**Analysis Date:** 2026-08-13

> **Status note:** This repository is specification-first (docs only). All integrations below are *prescribed* by the canonical spec ([`docs/METARADAR_MASTER_PLAN_v5.0.md`](docs/METARADAR_MASTER_PLAN_v5.0.md) §5) and are to be implemented with `httpx` async clients + `tenacity` retry (3 retries: 2s, 4s, 8s). No connector code exists yet.

## APIs & External Services

**Live data sources (MVP — 3 must be live on demo day, per SRS AC-1):**
- **NCBI PubMed / E-utilities** — PubMed literature retrieval via NCBI E-utilities (esearch/efetch/esummary), for scientific publications, clinical evidence, trial readouts. Keyless REST. Used by `node_ingest`. **PubMed Central (PMC) APIs/services for eligible full-text content are an OPTIONAL/EXTENSION** — they are not the same endpoint as PubMed literature retrieval and are not claimed as implemented unless they are.
- **NewsAPI** — industry news, press releases, competitor announcements. **Developer/free tier: 100 requests/day** — quota-aware connector; **development/testing use only** (NewsAPI's Developer plan is not for production/internal deployment); articles on the Developer plan have a **24-hour delay** (do NOT claim real-time). Auth: `NEWSAPI_KEY` env var. Official pricing: https://newsapi.org/pricing. If the quota is exhausted: fall back to Redis cache → bronze DB → synthetic dataset.
- **ClinicalTrials.gov API (v2)** — trial registrations, status changes, protocol amendments. Free, keyless. (`README.md` "Data Sources")

**Adapter-ready sources (connector scaffolds + rate limits; not claimed as fully live):**
- **FDA openFDA API** — approvals, adverse-event communications
- **EMA RSS** — European approval decisions, CHMP opinions
- **Congress archives** — ASH, ISTH, WFH, EHA public abstracts
- **Reddit (PRAW)** — patient & HCP community sentiment (`r/hemophilia`, `r/raredisease`); lowest source credibility tier, weighted accordingly

**Synthetic fallback:**
- **500-signal curated, deterministic, labelled haemophilia dataset** — offline demos, API-failure protection, rate-limit protection, reproducible testing. Flagged `is_synthetic=true`, never presented as real (`README.md` "Synthetic Fallback").

**Optional hosted reasoning (NOT a data source):**
- **xAI Grok API** — OPTIONAL hosted reasoning provider (Master Plan §13). Only active when `LLM_PROVIDER=xai|auto`; default `local` mode requires no external key. Every Grok call passes a mandatory **external-LLM privacy gate** — only public/synthetic prototype data may be sent; blocked content falls back to local Gemma → BART degraded → source-only. Responses use **JSON-Schema structured outputs** (https://docs.x.ai/developers/model-capabilities/text/structured-outputs) plus application-level semantic/evidence validation. Data handling: xAI does not train on API I/O without explicit permission; requests/responses are retained ~30 days (encrypted, abuse auditing) unless stricter arrangements apply (https://docs.x.ai/developers/faq/security). Auth: `XAI_API_KEY` env var. Grok is NEVER a data source — PubMed/ClinicalTrials.gov/etc. remain the pipeline inputs (Master Plan §13.4/§13.6).

## Data Storage

**Databases:**
- PostgreSQL 16 + pgvector extension — single DB for relational + 384-dim vector search (`CLAUDE.md`)
  - Connection: `DATABASE_URL` (e.g. `postgresql://metauser:metapass@postgres:5432/metaradar`)
  - Client: SQLAlchemy/asyncpg (prescribed by SDD `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`)
  - Key tables (planned): `signals`, `entities`, `raw_signals_bronze` (verbatim replay), `calibration_history`, WORM `audit_log` (append-only, **inspired by electronic-record traceability principles** — an engineering design analogy; MetaRadar does NOT claim 21 CFR Part 11 or GxP regulatory compliance)

**File Storage:**
- Local filesystem only (planned) — no object storage service

**Caching:**
- Redis 7 — hot-signal cache (2h TTL), API rate limiting, session storage
  - Connection: `REDIS_URL` (e.g. `redis://redis:6379`)

## Authentication & Identity

**Auth Provider:**
- Custom lightweight auth — SDD shows an API token check raising `HTTPException(401, "Invalid credentials")` (`docs/3_SOFTWARE_DESIGN_DOCUMENT.md`); hackathon-scope, no external IdP

**Stakeholder personas (calibration demo):**
- Simulated personas (Medical Affairs, Regulatory, Safety/PV, Market Access, Medical Communications, Leadership) — NOT real Novo Nordisk data (`README.md` "Stakeholder Calibration")

## Monitoring & Observability

**Error Tracking:**
- None prescribed (hackathon scope)

**Logs:**
- Application logs + per-source health status and data-freshness indicators in UI (<5min / 2h / 24h / >24h) (`docs/9_RISK_AND_GUARDRAILS.md` R5/R11)
- WORM `audit_log` for calibration and ontology changes

## CI/CD & Deployment

**Hosting:**
- Docker Compose (local-first); services: frontend `:3000`, backend `:8000`, PostgreSQL `:5432`, Redis `:6379` (`README.md` "Running with Docker")

**CI Pipeline:**
- None yet. Gap Analysis prescribes a CI/CD pipeline with unit tests + 0-bug gate (`docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md` §G10 area). Not implemented.

## Environment Configuration

**Required env vars** (`README.md` "Configuration", `docs/2_SRS_Software_Requirements_Specification.md` §4.2):
- `APP_ENV` — application environment
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `NEWSAPI_KEY` — NewsAPI credential (the only paid-key external *data* API)
- `LLM_PROVIDER` — reasoning provider mode (`local` default / `xai` / `auto`)
- `LOCAL_LLM_MODEL` / `LOCAL_LLM_TASK` — local reasoning LLM (`google/gemma-3-4b-it`, `text-generation`)
- `XAI_API_KEY` / `XAI_MODEL` / `XAI_TIMEOUT` — optional hosted Grok (only when `LLM_PROVIDER=xai|auto`; privacy-gated)
- `SUMMARIZER_MODEL` / `SUMMARIZER_TASK` — batch summarizer (`facebook/bart-large-cnn`, `summarization`)

**Secrets location:**
- `.env` (gitignored) — never committed; `.env.example` committed as template (`docs/9_RISK_AND_GUARDRAILS.md` R14, EV-4)

## Source Freshness & Delay Notes

- **NewsAPI Developer tier:** articles are delayed by up to 24 hours; the 2-hour polling schedule does NOT eliminate source-side delay. Source freshness (`published_at`, fetch timestamp) must be displayed in the UI. NewsAPI is one source among several — critical regulatory/trial information should preferably come from authoritative sources (FDA/EMA/ClinicalTrials.gov) when available.
- **NCBI PubMed / E-utilities:** literature indexing lag applies; `source_date` reflects the publication/event date, `fetched_at` the ingestion time.

## Webhooks & Callbacks

**Incoming:**
- None

**Outgoing:**
- None — the system polls public APIs on a 2-hour schedule (Celery + APScheduler) rather than receiving webhooks (`docs/METARADAR_MASTER_PLAN_v5.0.md` §5)

---

*Integration audit: 2026-08-13*
