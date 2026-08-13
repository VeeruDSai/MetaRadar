# Integrations

**Analysis Date:** 2026-08-13

> **Status note:** All external data-source integrations exist only as **scaffold/planning artifacts**. The only connector code is the abstract `SourceConnector` base class ([`backend/app/connectors/base.py`](backend/app/connectors/base.py)) whose `fetch_latest()` raises `NotImplementedError`. Connector "status" reported by `GET /api/v1/health/connectors` is **static/hardcoded** in [`backend/app/api/v1/endpoints/health.py`](backend/app/api/v1/endpoints/health.py). The **frontend does not call the backend at all** — [`frontend/lib/api.ts`](frontend/lib/api.ts) resolves every "API" function against [`frontend/lib/mock-data.ts`](frontend/lib/mock-data.ts) with artificial delays (360–700 ms). PostgreSQL+pgvector and Redis connections are the only *real* infrastructure integrations implemented.

## Data Sources (External APIs)

| Source | Status | Evidence in code | How configured | What it feeds |
|---|---|---|---|---|
| NCBI PubMed / E-utilities | **Planned** | `source_id="pubmed", status="active", freshness="near_real_time"` hardcoded in [`backend/app/api/v1/endpoints/health.py`](backend/app/api/v1/endpoints/health.py); no connector class | — (keyless) | `node_ingest` → `RawSignalPayload` → `raw_signals_bronze` → `signals` (per Master Plan; **no code path exists**) |
| ClinicalTrials.gov (v2) | **Planned** | `source_id="clinical_trials", status="active"` hardcoded (health.py); no connector | — (keyless) | Same pipeline (per Master Plan; not wired) |
| NewsAPI | **Planned** | `NEWSAPI_KEY` in [`backend/app/core/config.py`](backend/app/core/config.py); `quota_remaining=100` hardcoded in health.py; no connector | `NEWSAPI_KEY` env var (developer tier: 100 req/day, 24h delay) | Industry news & competitor press releases (per Master Plan; not wired) |
| FDA OpenFDA | **Planned** | `source_id="fda", status="adapter_ready", freshness="batch"` hardcoded (health.py); no connector | — (keyless) | Approvals & adverse-event communications (per Master Plan; not wired) |
| EMA RSS | **Planned** | `source_id="ema", status="adapter_ready", freshness="batch"` hardcoded (health.py); no connector (no feedparser dep) | — | EU decisions & CHMP opinions (per Master Plan; not wired) |
| Congress abstracts (ASH/ISTH/WFH/EHA) | **Planned** | `source_id="congress", status="adapter_ready"` hardcoded (health.py); no connector | — (public repositories) | Congress presentation/abstract signals (per Master Plan; not wired) |
| Reddit PRAW (r/hemophilia, r/raredisease) | **Not implemented at all** | **Absent from code** — not in health.py, not in requirements, no imports | `(prescribed env only, none in code)` | Patient/HCP community sentiment (documented only) |
| Synthetic 500-signal dataset | **Mocked/Planned** | `source_id="synthetic", status="active"` hardcoded (health.py); **no 500-record dataset file exists** in the repo | — | Offline demo fallback; only `frontend/lib/mock-data.ts` exists (4 hand-written signals) |

**Sources surface (static, for reference):** `GET /api/v1/health/connectors` returns hardcoded `ConnectorHealthStatus` entries for 7 sources (PubMed, ClinicalTrials.gov, NewsAPI, FDA, EMA, congress, synthetic). Two frontend surfaces duplicate this: the legacy `frontend/src/app/sources/page.tsx` (hardcoded card grid) and the new `frontend/app/[section]/page.tsx` → `GenericPage` placeholder for `/sources`.

## Internal Services

**LLM / AI provider chain** ([`backend/app/providers/`](backend/app/providers/)) — the only "integration-like" layer with real logic:

- **Local Gemma 3 4B** (`google/gemma-3-4b-it`) — **Simulated** ([`backend/app/providers/gemma.py`](backend/app/providers/gemma.py)): canned intelligence output; no model loaded. Configured via `LLM_PROVIDER=local`, `LLM_DEVICE` (`auto`|`cpu`|`cuda:0`), `LLM_DTYPE=int4`, `MAX_CONTEXT_TOKENS=2048`, `MAX_OUTPUT_TOKENS=512`
- **xAI Grok** (`grok-beta`) — **Simulated + real privacy gate** ([`backend/app/providers/grok.py`](backend/app/providers/grok.py)): transmission blocked unless `ENABLE_GROK_FALLBACK=true` AND `XAI_API_KEY` set AND `DataClassification ∈ {PUBLIC, SYNTHETIC}`. No HTTP call is made — the gate is the real part, the response is canned. Configured via `XAI_API_KEY`, `ENABLE_GROK_FALLBACK` (default `false`)
- **BART degraded** (`facebook/bart-large-cnn`) — **Simulated** ([`backend/app/providers/degraded.py`](backend/app/providers/degraded.py)): naive truncation, `mode="degraded_factual"`, reasoning/actions explicitly disabled
- **Fallback chain** ([`backend/app/providers/factory.py`](backend/app/providers/factory.py)): `execute_task(capability, evidence, task, classification)` → Gemma → Grok (gated) → Degraded BART; provider + mode surfaced via `ModelMetadataSchema` in every response
- **Contradiction analysis** — **Mocked** ([`backend/app/services/redteam.py`](backend/app/services/redteam.py)): pairwise rule-based flag (same asset, different type), in-memory cache, `rule="EVIDENCE_CONTRADICTION"`, `confidence=0.85`. Prescribed `facebook/bart-large-mnli` zero-shot NLI **not implemented**

**PostgreSQL 16 + pgvector** — **Implemented (real):**
- Async SQLAlchemy engine ([`backend/app/db/session.py`](backend/app/db/session.py)): `DATABASE_URL`, pool_pre_ping, `pg_try_advisory_lock`/`pg_advisory_unlock` helpers
- Full schema via Alembic migration [`backend/alembic/versions/001_initial_v51_schema.py`](backend/alembic/versions/001_initial_v51_schema.py) (`vector` + `pg_trgm` extensions, HNSW vector index, 17 tables, partial unique indexes on pmid/nct_id/regulatory_id/fingerprint/canonical_url)
- Real dedup upsert path: [`backend/app/services/deduplication.py`](backend/app/services/deduplication.py) `upsert_signal()` (ON CONFLICT DO UPDATE)
- Readiness check: `SELECT 1` in `GET /api/v1/health/ready`

**Redis 7** — **Partial (connection only):**
- `redis.asyncio` ping with 2s timeout in `GET /api/v1/health/ready` (non-blocking)
- **No caching, rate-limiting, or session code uses Redis yet** (prescribed: 2h TTL hot-signal cache)

**Frontend data layer** — **Mocked:**
- [`frontend/lib/api.ts`](frontend/lib/api.ts) exports `getOverview`, `getSignals`, `getTrends`, `getHealth`, `getSources`, `askAthena` — all resolve to `mock-data.ts` after a `setTimeout` delay; no HTTP, no `NEXT_PUBLIC_API_BASE_URL` usage (the env var is only set in [`docker-compose.yml`](docker-compose.yml))
- Type contracts: `frontend/types/api.ts` (mock domain types: `Signal`, `DashboardOverview`, `AthenaResponse`…) vs `frontend/src/types/api.ts` (auto-generated OpenAPI contract — currently **unused** by the new UI)

## Integration Patterns

- **Retry:** **Not implemented** — `tenacity` is prescribed (3 retries: 2s, 4s, 8s) but absent from `backend/requirements.txt` and unused in code
- **Auth:** env-var credentials only (`NEWSAPI_KEY`, `XAI_API_KEY`) via `pydantic-settings` ([`backend/app/core/config.py`](backend/app/core/config.py)); no API auth middleware on the FastAPI app; the only real gate is the per-provider external-LLM privacy check ([`backend/app/providers/grok.py`](backend/app/providers/grok.py))
- **Cache:** URL configured (`REDIS_URL`); **no cache reads/writes implemented**
- **Rate limiting:** not implemented; quota is a display field only (`quota_remaining` on `Source`/`ConnectorHealthStatus`, hardcoded 100 for NewsAPI)
- **CORS:** real middleware in [`backend/app/main.py`](backend/app/main.py) from `CORS_ORIGINS` (default `http://localhost:3000`; compose passes none — default applies)
- **Health/degradation signaling:** liveness `/health`, readiness `/health/ready` (DB mandatory, Redis non-blocking), `/health/models` (provider config), `/health/connectors` (static statuses) — all in [`backend/app/api/v1/endpoints/health.py`](backend/app/api/v1/endpoints/health.py)
- **Contract sync:** [`scripts/export_openapi.py`](scripts/export_openapi.py) writes `contracts/openapi.json` + `frontend/src/types/api.ts`; CI fails on drift (`.github/workflows/ci.yml`)
- **Observability:** stdlib `logging` only ([`backend/app/main.py`](backend/app/main.py)); `audit_log` table exists in schema but nothing writes to it

## Known Gaps

1. **Zero live data connectors** — PubMed, ClinicalTrials.gov, NewsAPI, OpenFDA, EMA RSS, congress all unimplemented; `SourceConnector.fetch_latest()` raises `NotImplementedError` (base class only, [`backend/app/connectors/base.py`](backend/app/connectors/base.py))
2. **Reddit (PRAW) entirely absent** — not even a health-status placeholder; documented only in the Master Plan / README
3. **Synthetic dataset missing** — health endpoint claims the 500-signal synthetic suite is "active"; no data file exists in the repo (only 4 in-memory mock signals in `frontend/lib/mock-data.ts`)
4. **Frontend↔backend disconnection** — the new UI renders entirely from mock data; `lib/api.ts` never calls `http://localhost:8000/api/v1`; the auto-generated contract (`frontend/src/types/api.ts`) is not consumed by any component
5. **No ingest/pipeline execution** — `pipeline_runs` table and advisory locks exist, but no scheduler (APScheduler absent) and no fetch→validate→persist code path
6. **LLM providers simulated** — no `transformers`/model weights; Grok never makes an HTTP call; embedding generation absent (pgvector column never populated)
7. **NewsAPI quota surface is hardcoded** — `quota_remaining=100` in health.py, not read from live state
8. **Dockerfiles missing** — `docker compose up --build` fails for both `backend` and `frontend` services (referenced in [`docker-compose.yml`](docker-compose.yml), files absent)
9. **Retry/backoff absent** — `tenacity` not installed; external callers will have no resilience once connectors are built
10. **No observability** — no error tracking, no metrics; `audit_log` table unused; health connector statuses are hardcoded rather than derived from real connector state

---

*Integration audit: 2026-08-13*
