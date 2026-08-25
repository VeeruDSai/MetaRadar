# External Integrations

**Analysis Date:** 2026-08-25

## APIs & External Services

**Biomedical Data Connectors** (located under `backend/app/connectors/`, derived from `SourceConnector` base class in `backend/app/connectors/base.py` with exponential backoff, jitter, bronze-layer ingestion, and per-source status tracking in `connector_states`):

- **PubMed (NCBI E-utilities)** - Biomedical publication signals
  - Implementation: `backend/app/connectors/pubmed.py` (`esearch.fcgi` + `efetch.fcgi` at `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/`)
  - Client: `httpx.AsyncClient` with bounded retries and rate limit handling
  - Auth: Optional `NCBI_API_KEY`, declared tool name `NCBI_TOOL` ("MetaRadar"), contact `NCBI_EMAIL` (`backend/app/core/config.py`)

- **ClinicalTrials.gov API v2** - Clinical trial registry signals
  - Implementation: `backend/app/connectors/clinical_trials.py` (`https://clinicaltrials.gov/api/v2/studies`)
  - Auth: None (public REST API v2)

- **OpenFDA (drugsfda endpoint)** - Drug regulatory approval, NDA/BLA supplement, and safety updates
  - Implementation: `backend/app/connectors/fda.py` (`https://api.fda.gov/drug/drugsfda.json`)
  - Auth: Optional `OPENFDA_API_KEY` for higher throughput

- **EMA (European Medicines Agency)** - European regulatory news and approvals via RSS feed
  - Implementation: `backend/app/connectors/ema.py` (default RSS `https://www.ema.europa.eu/en/medicines/rss`)
  - Auth: None (public RSS/XML feed)

- **NewsAPI** - Global pharmaceutical, clinical, and competitor intelligence news
  - Implementation: `backend/app/connectors/newsapi.py` (`https://newsapi.org/v2/everything`)
  - Auth: `NEWSAPI_KEY` or `NEWS_API_KEY` (mandatory for live news fetching; gracefully degraded with `CONFIGURATION_ERROR` status if missing)

**LLM Provider Fallback Matrix** (orchestrated by `ProviderFactory` in `backend/app/providers/factory.py`):

- **Local Gemma (Primary)** - High-fidelity reasoning and synthesis
  - Mode 1 (Containerized): Ollama sidecar (`http://localhost:11434`), serving `gemma3:4b`
  - Mode 2 (Embedded): `llama-cpp-python` loading quantized GGUF weights from `models/` directory with automatic GPU layer offload
  - Implementation: `backend/app/providers/gemma.py` (`GemmaProvider`)

- **xAI Grok (Hosted Cloud Fallback)** - High-capacity reasoning when enabled
  - Endpoint: `https://api.x.ai/v1/chat/completions` (model `grok-beta`)
  - Implementation: `backend/app/providers/grok.py` (`GrokProvider`)
  - Auth: `XAI_API_KEY` / `GROK_API_KEY`
  - Privacy Boundary Gate: Mandatory `validate_privacy_gate()` inspection rejecting any payload containing confidential, PII, or non-public clinical data

- **Degraded Fallback (Deterministic)** - Zero-dependency offline safety net
  - Implementation: `backend/app/providers/degraded.py`
  - Behavior: Factual extraction and bullet summarization ensuring zero downtime even under complete model failure

**Embeddings Service:**
- **fastembed (Local ONNX CPU Engine)** - `sentence-transformers/all-MiniLM-L6-v2` pinned to commit `e4bb823e5956b6277b069d276b978c48a73507c7`
- Implementation: `backend/app/services/embeddings.py` (384-dimensional dense vectors, lazy singleton, thread executor offloading)

## Data Storage & Caching

- **PostgreSQL 16 with pgvector:**
  - Connection: `DATABASE_URL` (`postgresql+asyncpg://...`) configured via `backend/app/core/config.py`
  - Client: SQLAlchemy 2.0 async engine in `backend/app/db/session.py` (pool size 10, max overflow 20, advisory locks for single-worker scheduler synchronization)
  - Medallion Architecture: `raw_signals_bronze` (immutable raw JSON) → `signals` (silver normalized records + pgvector embeddings) → `developments`, `confluences`, `contradictions`, `watch_items`, `calibration_*` (gold analytics entities)

- **Redis 7:**
  - Connection: `REDIS_URL` (`redis://localhost:6379/0`)
  - Purpose: Cache layer and optional fast key-value store

## Provenance & Canonical Linking

- **Provenance URL Resolver:**
  - Implementation: `backend/app/services/provenance_urls.py`
  - Resolves canonical source URLs for PMIDs (PubMed), NCT IDs (ClinicalTrials.gov), FDA application numbers (Drugs@FDA), and EMA authorization records
  - Guarantees end-to-end auditability and source traceability across all UI surfaces
