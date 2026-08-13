# Integrations

**Analysis Date:** 2026-08-13

> **Status note:** All external data-source integrations exist only as **scaffold/planning artifacts**. The only connector code is the abstract `SourceConnector` base class ([`backend/app/connectors/base.py`](backend/app/connectors/base.py)) whose `fetch_latest()` raises `NotImplementedError`. Connector "status" currently reported is **static/hardcoded** in the health endpoint and the sources page. Database (PostgreSQL+pgvector) and Redis connections are the only *real* infrastructure integrations implemented.

## Data Sources (External APIs)

| Source | Status | Evidence in code | Configured via |
|---|---|---|---|
| NCBI PubMed / E-utilities | **Planned** | `source_id="pubmed", status="active"` hardcoded in [`backend/app/api/v1/endpoints/health.py`](backend/app/api/v1/endpoints/health.py); no connector | — (keyless) |
| ClinicalTrials.gov (v2) | **Planned** | `source_id="clinical_trials", status="active"` hardcoded (health.py); no connector | — (keyless) |
| NewsAPI | **Planned** | `NEWSAPI_KEY` in [`backend/app/core/config.py`](backend/app/core/config.py) + `.env.example`; `quota_remaining=100` hardcoded in health.py and `frontend/src/app/sources/page.tsx`; no connector | `NEWSAPI_KEY` |
| FDA OpenFDA | **Planned** | `source_id="fda", status="adapter_ready", freshness_class="batch"` hardcoded (health.py); no connector | — (keyless) |
| EMA RSS | **Planned** | `source_id="ema", status="adapter_ready"` hardcoded (health.py); no connector (no feedparser) | — |
| Congress abstracts (ASH/ISTH/WFH/EHA) | **Planned** | `source_id="congress", status="adapter_ready"` hardcoded (health.py); no connector | — |
| Reddit PRAW (r/hemophilia, r/raredisease) | **Planned (Master Plan only)** | **Absent from code entirely** — not in health endpoint, not in requirements, no imports | `(prescribed env, none in code)` |
| Synthetic 500-signal dataset | **Planned** | `source_id="synthetic", status="active"` hardcoded (health.py); **no dataset file exists** in the repo | — |

**What feeds what (per Master Plan §5, unimplemented):** each connector would feed `node_ingest` → `RawSignalPayload` → `raw_signals_bronze` dedup → `signals`. Current code supports the *persistence half* (dedup `fingerprint` + `upsert_signal` in [`backend/app/services/deduplication.py`](backend/app/services/deduplication.py), `Signal`/`RawSignalBronze` tables in [`backend/app/models/__init__.py`](backend/app/models/__init__.py)) but has no fetch layer.

**Sources surface (static, for reference):** `GET /api/v1/health/connectors` ([`backend/app/api/v1/endpoints/health.py`](backend/app/api/v1/endpoints/health.py)) returns hardcoded `ConnectorHealthStatus` entries; `frontend/src/app/sources/page.tsx` duplicates the same 6 cards with hardcoded text.

## LLM / AI Provider Integrations ("Internal Services")

These are internal provider abstractions, not external data sources, but they are the only "integration-like" layer with real logic:

- **Local Gemma 3 4B** (`google/gemma-3-4b-it`) — **Simulated** ([`backend/app/providers/gemma.py`](backend/app/providers/gemma.py)): canned intelligence output; no model loaded. Configured via `LLM_PROVIDER=local`, `LLM_DEVICE`, `LLM_DTYPE=int4`, `MAX_CONTEXT_TOKENS`, `MAX_OUTPUT_TOKENS`
- **xAI Grok** (`grok-beta`) — **Simulated + real privacy gate** ([`backend/app/providers/grok.py`](backend/app/providers/grok.py)): transmission blocked unless `ENABLE_GROK_FALLBACK=true`, `XAI_API_KEY` set, and `DataClassification` ∈ {PUBLIC, SYNTHETIC}. No HTTP call made. Configured via `XAI_API_KEY`, `ENABLE_GROK_FALLBACK` (default `false`)
- **BART degraded** (`facebook/bart-large-cnn`) — **Simulated** ([`backend/app/providers/degraded.py`](backend/app/providers/degraded.py)): naive truncation, `degraded_factual` mode, reasoning/actions explicitly disabled
- **Fallback chain** ([`backend/app/providers/factory.py`](backend/app/providers/factory.py)): `execute_task(capability, evidence, task, classification)` → Gemma → Grok (gated) → Degraded BART; provider + mode surfaced in `ModelMetadataSchema`/`model_metadata`
- **Contradiction analysis** — **Mocked** ([`backend/app/services/redteam.py`](backend/app/services/redteam.py)): pairwise rule-based flag (same asset, different type), in-memory cache, `rule="EVIDENCE_CONTRADICTION"`, `confidence=0.85`. Prescribed `facebook/bart-large-mnli` zero-shot NLI **not implemented**

## Internal Services / Infrastructure (Implemented)

**PostgreSQL 16 + pgvector** — real integration:
- Async SQLAlchemy engine ([`backend/app/db/session.py`](backend/app/db/session.py)): `DATABASE_URL`, pool_pre_ping, advisory-lock helpers for single-execution scheduling
- Full schema via Alembic migration [`backend/alembic/versions/001_initial_v51_schema.py`](backend/alembic/versions/001_initial_v51_schema.py) (`vector` + `pg_trgm` extensions, HNSW vector index, 17 tables, partial unique indexes on pmid/nct_id/regulatory_id/fingerprint/canonical_url)
- Readiness check: `SELECT 1` in `GET /api/v1/health/ready`

**Redis 7** — partial integration:
- Client tested in `GET /api/v1/health/ready` (`redis.asyncio`, 2s timeout, non-blocking)
- **No caching, rate-limiting, or session code uses Redis yet** (prescribed: 2h TTL hot-signal cache)

## Integration Patterns

- **Retry:** **Not implemented** — `tenacity` is prescribed (3 retries: 2s, 4s, 8s) but absent from `backend/requirements.txt` and unused in code
- **Auth:** env-var credentials only (`NEWSAPI_KEY`, `XAI_API_KEY`) via `pydantic-settings` ([`backend/app/core/config.py`](backend/app/core/config.py)); no API auth middleware on the FastAPI app; per-provider privacy gate for external LLM ([`backend/app/providers/grok.py`](backend/app/providers/grok.py))
- **Cache:** schema + URL configured (`REDIS_URL`); no cache reads/writes implemented
- **Rate limiting:** not implemented; quota is only a display field (`quota_remaining` on `Source`/`ConnectorHealthStatus`, hardcoded 100 for NewsAPI)
- **CORS:** real middleware in [`backend/app/main.py`](backend/app/main.py) from `CORS_ORIGINS` (default `http://localhost:3000`)
- **Health/degradation signaling:** liveness `/health`, readiness `/health/ready` (DB mandatory, Redis non-blocking), `/health/models` (provider config), `/health/connectors` (static statuses) — all in [`backend/app/api/v1/endpoints/health.py`](backend/app/api/v1/endpoints/health.py)

## CI/CD & Contract Generation

- **CI:** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) — Python 3.11, install requirements, run `tests/test_foundation.py`, verify `frontend/src/types/api.ts` stays in sync with OpenAPI via `scripts/export_openapi.py`
- **Contract:** `contracts/openapi.json` exports 5 paths; `frontend/src/types/api.ts` is generated (hardcoded template in the script, `DO NOT EDIT DIRECTLY` header)
- **Deployment:** docker-compose local-first only; both `backend/Dockerfile` and `frontend/Dockerfile` are **missing** (compose build is currently broken)

## Known Gaps

1. **Zero live data connectors** — PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS, congress, Reddit all unimplemented; `SourceConnector.fetch_latest()` raises `NotImplementedError` (base class only, [`backend/app/connectors/base.py`](backend/app/connectors/base.py))
2. **Reddit (PRAW) entirely absent** — not even a health-status placeholder; prescribed only in the Master Plan / README
3. **Synthetic dataset missing** — health endpoint claims the 500-signal synthetic suite is "active"; no JSON/CSV/SQL data file exists in the repo
4. **No ingest/pipeline execution** — `pipeline_runs` table and advisory locks exist, but no scheduler (APScheduler absent) and no fetch→validate→persist code path
5. **LLM providers simulated** — no `transformers`/model weights; Grok never makes an HTTP call; embedding generation absent (pgvector column never populated)
6. **NewsAPI quota surface is hardcoded** — `quota_remaining=100` in health.py and the frontend sources page, not read from any live state
7. **Dockerfiles missing** — `docker compose up --build` fails for both `backend` and `frontend` services
8. **Retry/backoff absent** — `tenacity` not installed; external callers will have no resilience once connectors are built
9. **No observability** — logging is stdlib `logging` only ([`backend/app/main.py`](backend/app/main.py)); no error tracking, no metrics; `audit_log` table exists in schema but nothing writes to it

---

*Integration audit: 2026-08-13*