<!-- refreshed: 2026-08-13 -->
# Architecture

**Analysis Date:** 2026-08-13

> **Current state:** Foundation-stage implementation. A FastAPI backend skeleton (`backend/app/`), a Next.js frontend skeleton (`frontend/src/`), an Alembic schema migration, generated API contracts, docker-compose wiring, and a CI pipeline exist. The 10-node LangGraph workflow, live source connectors, scheduler, and intelligence services are **specified but not yet implemented** — the canonical design in [`docs/METARADAR_MASTER_PLAN_v5.0.md`](../docs/METARADAR_MASTER_PLAN_v5.0.md) §4 is authoritative for what will be built. This document describes the implemented architecture first, then the prescribed design it scaffolds.

## System Overview

### Current (implemented)

```text
┌──────────────────────────────────────────────────────────────────┐
│                 Next.js 15 frontend skeleton                      │
│  frontend/src/app/sources/page.tsx · frontend/src/types/api.ts    │
└───────────────────────────────┬──────────────────────────────────┘
                                │  /api/v1 (REST, JSON)
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│                  FastAPI backend skeleton (v5.1.0)                │
│  backend/app/main.py — app + CORS + lifespan                      │
│  backend/app/api/v1/endpoints/health.py — health|ready|models|    │
│    connectors                                                     │
│  backend/app/core/config.py — pydantic-settings Settings          │
│  backend/app/core/domain_config.py — YAML config loader           │
│  backend/app/db/session.py — async SQLAlchemy engine + links      │
│  backend/app/models/__init__.py — 17-table ORM schema             │
│  backend/app/services/deduplication.py · redteam.py (seeds)       │
│  backend/app/providers/ — base | gemma | grok | degraded | factory│
│  backend/app/connectors/base.py — SourceConnector interface       │
└──────────┬──────────────────────────┬────────────────────────────┘
           │ asyncpg                  │ redis.asyncio
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│ PostgreSQL 16 +      │   │ Redis 7              │
│ pgvector (pg16 image)│   │ (docker-compose.yml) │
│ + HNSW vector index  │   │ /0 db                │
└──────────────────────┘   └──────────────────────┘
```

### Target (prescribed — Master Plan §4, once implemented)

```text
                    PUBLIC EXTERNAL SIGNALS
         LIVE: NCBI PubMed (E-utilities) · NewsAPI · ClinicalTrials.gov
         ADAPTER-READY: FDA · EMA · Congress (ASH/ISTH/WFH/EHA) · Reddit
         SYNTHETIC-DEMO: 500 curated labelled haemophilia signals
                                │
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│          10-NODE LANGGRAPH WORKFLOW (backend/app/workflows/)     │
│  ingest → validate → nlp_extract → ontology_enrich → confluence  │
│  → lifecycle → redteam → missing_signal → synthesize → calibrate │
│  (explicit termination: node_calibrate → END)                    │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│          FOUR-QUESTION DECISION INTERFACE (Next.js 15)           │
│  Q1 What changed? · Q2 Why it matters · Q3 Which function?       │
│  Q4 What action? + evidence chain + FACT/INTERPRETATION/         │
│  SPECULATION labels                                              │
└───────────────────────────────┬──────────────────────────────────┘
                                ▼
┌──────────────────────────────────────────────────────────────────┐
│  PostgreSQL 16 + pgvector (relational + 384-dim vector search)   │
│  Redis 7 (2h-TTL hot cache) · APScheduler (single, in-process)   │
└──────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Implemented (foundation)

| Component | Responsibility | File |
|-----------|----------------|------|
| FastAPI app | App factory, lifespan (domain config load), CORS, router wiring | `backend/app/main.py` |
| Settings | All env-driven configuration (DB, Redis, LLM provider, embeddings, CORS) | `backend/app/core/config.py` |
| DomainConfig | Loads + caches `config/haemophilia.yaml` into typed Pydantic models | `backend/app/core/domain_config.py` |
| Async DB session | Engine pool, session factory, `get_db` dependency, PostgreSQL advisory locks for single-execution scheduling | `backend/app/db/session.py` |
| ORM models | 17-table canonical entity schema (sources → audit_log), pgvector embedded column | `backend/app/models/__init__.py` |
| Pydantic schemas | API response contracts (Health*, Signal, Development, PipelineRun, ScoreBreakdown, ModelMetadata) | `backend/app/schemas/__init__.py` |
| Health endpoints | Liveness `/health`, readiness `/ready` (DB mandatory + non-blocking Redis), model/provider status `/models`, connector status `/connectors` | `backend/app/api/v1/endpoints/health.py` |
| Deduplication service | Deterministic fingerprints (pmid/nct/reg/hash), embedding-safe text chunking, `ON CONFLICT` upsert | `backend/app/services/deduplication.py` |
| Red-Team service | Priority-gated pairwise contradiction scan (currently mock rule-based; NLI model planned) | `backend/app/services/redteam.py` |
| LLM provider layer | `LLMProvider` interface + capability matrix + data classification; Gemma (local) / Grok (hosted, privacy-gated) / BART degraded providers + `ProviderFactory` fallback chain | `backend/app/providers/*.py` |
| Connector interface | Shared `SourceConnector` base + `RawSignalPayload`/`ConnectorStatus` contracts; concrete adapters not yet implemented | `backend/app/connectors/base.py` |
| Alembic migration | Initial v5.1 schema: 17 tables, `vector`/`pg_trgm` extensions, partial unique indexes, HNSW index | `backend/alembic/versions/001_initial_v51_schema.py` |
| Domain config data | Haemophilia diseases, 7 assets, 7 signal types, 9 lifecycle stages, 6 functions, baseline routing matrix | `config/haemophilia.yaml` |
| Contract export | Generates `contracts/openapi.json` + `frontend/src/types/api.ts` from the FastAPI app | `scripts/export_openapi.py` |
| Foundation tests | Script-based verification of DomainConfig, dedup fingerprinting, provider fallback chain | `tests/test_foundation.py` |
| CI | Python 3.11 + requirements install, runs foundation tests, enforces contract sync via `git diff` | `.github/workflows/ci.yml` |
| Docker Compose | postgres (pgvector/pg16) · redis (7-alpine) · backend · frontend + optional `backend-gpu` profile; healthchecks & dependencies | `docker-compose.yml` |

### Planned (prescribed, not yet present)

| Component | Responsibility | Planned location per specs |
|-----------|----------------|------|
| LangGraph workflow | 10-node StateGraph with typed `IntelligenceState`, reducers for accumulating fields, `node_calibrate → END` | `backend/app/workflows/` + node files |
| Source connectors | PubMed/NewsAPI/ClinicalTrials.gov live adapters; FDA/EMA/Congress/Reddit adapter-ready; synthetic fallback; `tenacity` retries (2s/4s/8s) | `backend/app/connectors/<source>.py` |
| APScheduler | Single in-process scheduler: 2h fetch, nightly digest, on-demand recalibration (Celery deliberately NOT used) | in-process inside FastAPI |
| Intelligence services | Confluence detection (48h/≥3 types), lifecycle FSM tracker, missing-signal + watch rules, StakeholderCalibrationService (HITL) | `backend/app/services/*` |
| spaCy NER + ontology enrichment | `en_core_sci_md` entity extraction; haemophilia ontology mapping | `backend/app/nlp/`, `backend/app/ontology/` |
| Frontend app | Four-Question dashboard, signal feed, lifecycles, red-team, watch items, calibration widget; TanStack Query + Tailwind | `frontend/src/app/*`, `frontend/src/components/` |
| Dockerfiles | `backend/Dockerfile` and `frontend/Dockerfile` (referenced by compose, not yet authored) | `backend/Dockerfile`, `frontend/Dockerfile` |

## Pattern Overview

**Overall:** Event-sourced signal pipeline — public signals are treated as *evidence events belonging to developing stories*, orchestrated by a stateful LangGraph workflow (Master Plan §4). The implemented foundation already encodes the core model: signals persist verbatim to a bronze layer, carry deterministic fingerprints for dedup, and route through a provider-agnostic reasoning layer.

**Key Characteristics (verified in code):**
- **Raw-signal replay:** `raw_signals_bronze` table persists `raw_payload` verbatim with `content_hash` and `connector_version` (`backend/app/models/__init__.py:125`)
- **Deterministic dedup before any AI:** `generate_fingerprint()` prefers stable IDs (pmid/nct/reg), falls back to normalized title+publisher+date+company+asset SHA-256 (`backend/app/services/deduplication.py:11`)
- **Idempotent persistence:** `upsert_signal()` uses PostgreSQL `ON CONFLICT DO UPDATE` on the unique fingerprint (`backend/app/services/deduplication.py:52`)
- **Immutable baseline vs calibrated output:** `signal_routing` stores `baseline_*` (immutable AI outputs) alongside `calibrated_*` fields so calibration is auditable (BEFORE/AFTER) (`backend/app/models/__init__.py:204`)
- **Provider-agnostic reasoning:** LangGraph nodes must never call a model directly; `ProviderFactory.execute_task()` resolves `Gemma → Grok (privacy-gated) → BART degraded` based on required `ProviderCapability` (`backend/app/providers/factory.py:18`)
- **Honest degraded mode:** `DegradedProvider` supports only `SUMMARIZE`; `reasoning_available=false` and `actions_available=false` propagate to the UI via `ModelMetadataSchema` (`backend/app/providers/degraded.py`)
- **WORM audit:** `audit_log` table is append-only by design (`CREATE | UPDATE | ROUTE | CALIBRATE` actions) (`backend/app/models/__init__.py:250`)
- **One engine → six functions:** baseline routing matrix in `config/haemophilia.yaml` maps signal_types to primary/secondary functions (Medical Affairs, Regulatory, Safety, Market Access, Communications, Leadership)

## Layers

**Frontend Layer:**
- Purpose: Decision-first UI — Four-Question panels, signal cards, connector health
- Location: `frontend/src/`
- Contains (current): `app/sources/page.tsx` (static page), `types/api.ts` (generated contracts). Planned: `components/`, `lib/` (API client + query hooks), full App Router pages
- Depends on: FastAPI via `/api/v1`
- Used by: stakeholder personas (Medical Affairs, Regulatory, etc.)

**API Layer:**
- Purpose: Expose pipeline results + health/diagnostics
- Location: `backend/app/api/v1/endpoints/`
- Contains: `health.py` (4 GET endpoints). Versioned under `/api/v1`
- Depends on: `core/config.py`, `db/session.py`, `schemas/`
- Used by: frontend, Docker healthchecks, CI

**Domain/Config Layer:**
- Purpose: Typed, env-driven and YAML-driven configuration
- Location: `backend/app/core/`
- Contains: `config.py` (Settings), `domain_config.py` (DomainConfig loader with module-level cache)
- Used by: all layers via `from app.core.config import settings`

**Persistence Layer:**
- Purpose: Raw replay, normalized signals, entities, routing/calibration, audit
- Location: PostgreSQL 16 + pgvector (`docker-compose.yml`), ORM in `backend/app/models/__init__.py`, async session in `backend/app/db/session.py`
- Contains: 17 tables; 384-dim `Vector` column + HNSW cosine index on `signals.embedding` (migration `001_initial_v51_schema.py:195`)
- Used by: all layers

**Provider Layer (reasoning/NLP):**
- Purpose: Model-agnostic intelligence generation
- Location: `backend/app/providers/`
- Contains: `LLMProvider` base + capability/data-classification enums, Gemma/Grok/Degraded implementations, `ProviderFactory`
- Depends on: `core/config.py`, `schemas/`
- Used by (planned): `node_synthesize`, Ask Athena

## Data Flow

### Primary Signal Path (prescribed — INGEST → VALIDATE → UNDERSTAND → ANALYZE → SYNTHESIZE → CALIBRATE → BRIEF)

1. **INGEST** — `node_ingest` runs all enabled `SourceConnector` adapters via `httpx` async clients; every raw payload persisted verbatim to `raw_signals_bronze` before transformation (Master Plan §4.1). *Implementation seed:* connector contract in `backend/app/connectors/base.py`.
2. **VALIDATE** — `node_validate` filters short text (<50 chars), non-English, out-of-scope; deterministic dedup + source-independence classification; PII/PHI scrub before persistence. *Implementation seed:* `backend/app/services/deduplication.py`.
3. **UNDERSTAND** — `node_nlp_extract` (spaCy `en_core_sci_md` NER: drugs, companies, indications, trial IDs) → `node_ontology_enrich` (maps entities against the haemophilia ontology, e.g. Hemlibra → emicizumab → Roche).
4. **ANALYZE** — four parallel intelligence mechanisms:
   - `node_confluence`: 48h rolling window, ≥3 distinct signal types; congress/publication signals first check for an existing `development_id` (NEW EVIDENCE vs NEW DEVELOPMENT)
   - `node_lifecycle`: asset state machine `announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`; every event records `event_type · event_date · development_id · source_id`
   - `node_redteam`: pairwise NLI contradiction checks (BART MNLI); *implementation seed:* priority-gated candidate filtering in `backend/app/services/redteam.py`
   - `node_missing_signal`: FSM lag rules + stakeholder WATCH rules → `watch_items` with guarded wording ("Watch for… / Not observed yet")
5. **SYNTHESIZE** — `node_synthesize`: evidence-sufficiency gate → F-I-S (Fact/Interpretation/Speculation) labels → Four-Question brief via the provider-agnostic reasoning layer (Gemma → Grok → BART degraded). *Implementation seed:* `backend/app/providers/factory.py`.
6. **CALIBRATE** — `node_calibrate`: `StakeholderCalibrationService` updates function-scoring weights from feedback; **explicit termination `node_calibrate → END`** (never implicit).
7. **BRIEF** — role-specific formatted output: `primary_function` + `secondary_functions[]` + `routing_reason`, previewed via the Four-Question framework in the UI.

### Current runtime flow (as implemented today)

1. Client hits `GET /` or `GET /api/v1/health` → `backend/app/main.py:53` / `backend/app/api/v1/endpoints/health.py`
2. `GET /api/v1/health/ready` runs `SELECT 1` on postgres (mandatory) and non-blocking Redis ping → returns `ready|degraded` (`backend/app/api/v1/endpoints/health.py:22`)
3. `GET /api/v1/models` and `/connectors` report configured provider/connector state from `settings` + hardcoded source roster (`backend/app/api/v1/endpoints/health.py:54`)
4. `scripts/export_openapi.py` regenerates `contracts/openapi.json` + `frontend/src/types/api.ts`; CI fails if `api.ts` drifts (`.github/workflows/ci.yml:31`)

**State Management:**
- Authoritative state: PostgreSQL (async sessions via `get_db` in `backend/app/db/session.py:30`)
- Cache (planned): Redis 2h-TTL hot cache (`REDIS_URL` in `backend/app/core/config.py:20`)
- Pipeline state (planned): LangGraph `IntelligenceState` TypedDict with typed reducers for accumulating lists and replacement semantics for scalars (SDD §2.3 — `docs/3_SOFTWARE_DESIGN_DOCUMENT.md:454`)

## LangGraph Workflow (planned — node by node)

State contract and wiring are fully specified in `docs/3_SOFTWARE_DESIGN_DOCUMENT.md:442-504` and Master Plan §4. Not yet implemented in `backend/app/` (no `workflows/` package exists yet).

| Node | Reads (state) | Writes (state) | Persists to | Notes |
|------|--------------|----------------|-------------|-------|
| `ingest` | — | `raw_signals` | `raw_signals_bronze` | Parallel connectors; append reducer |
| `validate` | `raw_signals` | `validated_signals` | `signals` (pre-NLP) | quality, dedup, source-independence, PII scrub |
| `nlp_extract` | `validated_signals` | `extracted_entities` | — | spaCy `en_core_sci_md` |
| `ontology_enrich` | `extracted_entities` | `ontology_entities` | — | maps to haemophilia ontology |
| `confluence` | `ontology_entities` | `confluent_stories` | `developments`, `confluences` | 48h/≥3 types; dev-link decision (linked/possibly_linked/unlinked) |
| `lifecycle` | `confluent_stories` | `lifecycle_events` | `lifecycle_events` | FSM advance; `event_type/event_date/development_id/source_id` |
| `redteam` | `lifecycle_events` | `redteam_flags` | — | pairwise NLI (BART MNLI); modular `RedTeamRule` registry |
| `missing_signal` | `lifecycle_events` | `missing_signals` | `watch_items` | FSM lag rules + stakeholder watch rules |
| `synthesize` | pooled evidence | `role_briefs` | `signal_routing` (baseline) + `evidence` | evidence-sufficiency gate → F-I-S labels → Four-Question brief via `ProviderFactory` |
| `calibrate` | `role_briefs` + `calibration_feedback` | `model_metadata`, `errors` | `signal_routing` (calibrated), `calibration_feedback`, `audit_log` | HITL weight update; **explicit `node_calibrate → END`** |

Graph shape: linear chain `ingest → validate → nlp → confluence → lifecycle → red_team → missing_signal → synthesize → brief → calibrate`, `set_entry_point("ingest")`, `set_finish_point("calibrate")` (SDD §2.3). Failure semantics: per-node error boundaries, `recursion_limit` configured, one node's failure does not kill the pipeline.

## Backend API Design

**Framework:** FastAPI 0.110+ (`backend/requirements.txt`), ASGI via uvicorn.

**Versioning:** All endpoints under `/api/v1` (`API_V1_STR` in `backend/app/core/config.py:15`; routers mounted with `prefix=f"{settings.API_V1_STR}/..."` in `backend/app/main.py:50`). OpenAPI schema served at `/api/v1/openapi.json`.

**Router structure (current):**
- `backend/app/api/v1/endpoints/health.py` — `APIRouter()` with 4 GET endpoints, mounted at `/api/v1/health` with tag `"Health & Diagnostics"`
- No other routers registered in `backend/app/main.py:50`

**Auth:** None implemented. Prescribed: lightweight API token for the hackathon prototype (SDD). The current app exposes read-only health endpoints with no auth.

**CORS:** Configurable via `CORS_ORIGINS` env (default `http://localhost:3000`); middleware added only when non-empty (`backend/app/main.py:40`).

**Response contracts:** All handlers declared with `response_model` from `backend/app/schemas/__init__.py` (HealthResponse, HealthReadyResponse, HealthModelsResponse, HealthConnectorsResponse).

**Contract sync:** `scripts/export_openapi.py` imports `app.main.app`, dumps `openapi.json` to `contracts/`, and overwrites `frontend/src/types/api.ts` with a static template mirror (kept in sync by `.github/workflows/ci.yml` via `git diff --exit-code`). **Note:** the TS generator in `scripts/export_openapi.py` is a static template, not a schema-driven codegen.

**Planned endpoints (per SDD; not yet implemented):** `/api/v1/signals` (role-filtered feed), `/api/v1/feedback` (stakeholder calibration), plus ingestion/status/intelligence endpoints.

## Frontend Architecture

**Framework:** Next.js 15 (App Router), React 19, TypeScript 5 (`frontend/package.json`). Tailwind CSS 3.4 (devDependency — note: the project CLAUDE.md prescribes Tailwind 4, not yet upgraded).

**Structure (current):**
- `frontend/src/app/sources/page.tsx` — only page; static server component rendering hardcoded connector cards (no data fetching yet)
- `frontend/src/types/api.ts` — generated TypeScript interfaces mirroring the OpenAPI schema (Signal, Development, Health*, ModelMetadata, ScoreBreakdown)
- No `app/layout.tsx`, `app/page.tsx`, `components/`, `lib/`, `next.config.*`, `tsconfig.json`, or Tailwind config files present yet

**Prescribed blueprints (from `docs/4_UI_DESIGN_DOCUMENT.md`):**
- Routes: `/dashboard` (Four-Question panels), `/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/athena` (Ask Athena RAG), `/briefs`, `/digest`
- Data fetching: TanStack Query v5 (`@tanstack/react-query` already in `frontend/package.json`) — server-state caching + background revalidation; API base `NEXT_PUBLIC_API_BASE_URL` (set in `docker-compose.yml`)
- Styling: Tailwind + shadcn/ui component system; `bento-card` class referenced in `frontend/src/app/sources/page.tsx` implies a local CSS utility convention to be established
- Visualization: Recharts + Framer Motion + lucide-react; `clsx` + `tailwind-merge` for component class merging (all declared in `frontend/package.json`)

**Type sharing:** single source of truth is the FastAPI app → exported by `scripts/export_openapi.py` to both `contracts/openapi.json` and `frontend/src/types/api.ts`.

## Database Schema Overview

ORM source of truth: `backend/app/models/__init__.py` (17 models); migration: `backend/alembic/versions/001_initial_v51_schema.py` (creates extensions, tables, partial unique indexes, HNSW index).

| Group | Tables | Purpose |
|-------|--------|---------|
| Pipeline bookkeeping | `pipeline_runs` | run status, trigger (scheduled/manual/test), signal counters, error summary JSONB |
| Source catalog | `sources` | source_id PK, freshness_class (real_time/near_real_time/delayed/batch/adapter_ready/synthetic), syndication_group, quota, last_success/last_error |
| Domain entities | `companies`, `assets`, `trials`, `developments`, `events` | canonical entity layer; assets FK→companies; developments FK→assets/companies; events/lifecycle_events FK→developments |
| Evidence & raw layer | `raw_signals_bronze`, `evidence` | verbatim replay (`raw_payload` JSONB, content_hash, unique(source_id, external_id)); evidence excerpts FK→raw signal |
| Normalized signals | `signals` | fingerprint + pmid/nct_id/regulatory_id/canonical_url partial unique indexes; facts/interpretation/speculation JSONB; priority; score_breakdown; **pgvector `embedding` (384-dim) + HNSW index**; model/scoring/prompt versioning columns |
| Routing & calibration | `signal_routing`, `calibration_feedback` | immutable `baseline_*` vs `calibrated_*`; feedback ratings 1–5 with action_appropriate |
| Watch & audit | `watch_items`, `audit_log` | stakeholder watch rules with status vocabulary; append-only audit (entity_name/entity_id/action/performed_by/details JSONB) |

**Postgres extensions enabled:** `vector` (pgvector), `pg_trgm` (migration). **Vector index:** HNSW cosine ops, `m=16, ef_construction=64` on `signals.embedding`.

**Connection:** async engine with `pool_size=10, max_overflow=20, pool_pre_ping=True` (`backend/app/db/session.py:10`); advisory lock helpers `try_advisory_lock`/`release_advisory_lock` ready for scheduler single-execution protection.

## Cross-Cutting Concerns

**Logging:** stdlib `logging` with INFO level, format `%(asctime)s [%(levelname)s] %(name)s: %(message)s`, configured in `backend/app/main.py:9`. WORM `audit_log` table for CREATE/UPDATE/ROUTE/CALIBRATE actions (engineering analogy — no 21 CFR Part 11 / GxP claim).

**Audit/traceability:** every AI output intended to carry `model_metadata` (provider, mode, fallback_used, fallback_reason, latency_ms — `backend/app/schemas/__init__.py:7`); scoring/calibration/embedding/prompt versions stored per signal (`backend/app/models/__init__.py:187-191`).

**PII/PHI:** prescribed detection + redaction layer before persistence in `node_validate`; low-confidence content rejected/quarantined; a dedicated scrubber layer, spaCy NER is not a guaranteed scrubber (Master Plan §4.2). Not yet implemented.

**Security:** no auth in place; CORS restricted to `CORS_ORIGINS`; `.env` gitignored (template only at `.env.example`); secrets never committed; `docker-compose.yml` uses dev credentials only.

**External-LLM privacy gate:** mandatory for any hosted Grok call — only `PUBLIC`/`SYNTHETIC` classifications allowed (`backend/app/providers/grok.py` `validate_privacy_gate`; `DataClassification` enum in `backend/app/providers/base.py:15`).

**Observability:** liveness/readiness/model/connector health endpoints implemented (`backend/app/api/v1/endpoints/health.py`); `run_id`/`signal_id`/`model_request_id` correlation prescribed (Master Plan §14.14).

**Resilience:** `tenacity` exponential backoff (2s/4s/8s) prescribed for connectors; provider fallback chain implemented (`backend/app/providers/factory.py`); advisory locks for scheduler exclusivity; `pool_pre_ping` for DB.

## Tradeoffs / Decisions

| Decision | Rationale | Where encoded |
|----------|-----------|---------------|
| pgvector instead of Weaviate | One DB for relational + vector; simpler compose; HNSW index | `001_initial_v51_schema.py`, `docker-compose.yml` |
| Single in-process APScheduler, **no Celery** | 4-service compose footprint; heavy runs offloaded via asyncio/thread-pool; advisory locks guard single execution | `backend/app/db/session.py`, docker-compose (no worker service) |
| Default local LLM (Gemma 3 4B on local GPU), optional Grok, BART degraded | Zero API cost; privacy; never-crash fallback; `LLM_PROVIDER=local\|xai\|auto` | `backend/app/providers/factory.py`, `backend/app/core/config.py:30` |
| Deterministic dedup before AI | Stable ID-based fingerprints prevent double-counting; syndication never inflates evidence | `backend/app/services/deduplication.py` |
| Contract-first frontend types | Generated `api.ts` synced by CI; drift fails the build | `scripts/export_openapi.py`, `.github/workflows/ci.yml` |
| Immutable baseline vs calibrated outputs | Auditable BEFORE/AFTER for stakeholder calibration demo | `signal_routing` model |
| Verbatim bronze-layer persistence | Replayable ingestion; zero data loss on NLP failure | `raw_signals_bronze` |
| Health endpoints with non-blocking Redis | Dashboard/CI availability independent of cache | `backend/app/api/v1/endpoints/health.py:22` |

## Architectural Constraints

- **Threading:** async-first (FastAPI ASGI, asyncpg, `redis.asyncio`); local model inference runs off the event loop via thread-pool/`asyncio.to_thread` (prescribed); Gemma GPU budget on RTX 3050 4GB VRAM with `LLM_DEVICE`/`LLM_DTYPE`/context limits — never-crash fallback chain
- **Global state:** module-level `settings` singleton (`backend/app/core/config.py:54`) and `_domain_config_cache` (`backend/app/core/domain_config.py:57`) — the only two module-level singletons today
- **No autonomous decisions:** AI suggests → human reviews → human decides; controlled action vocabulary; degraded mode never fabricates reasoning
- **Data boundaries:** public + synthetic only; external LLM transmission gated by privacy classification
- **Contract discipline:** `frontend/src/types/api.ts` and `contracts/openapi.json` are generated artifacts — edit `backend/app/` schemas, then run `scripts/export_openapi.py`
- **Circular imports:** none observed; `app.db.session.Base` is imported by `app.models`, which is imported by services — keep `app/db/session.py` free of model imports

## Anti-Patterns (to avoid)

### Failing to regenerate contracts after schema changes
**What happens:** Schema changes in `backend/app/schemas/` or endpoints are not reflected in `frontend/src/types/api.ts`.
**Why it's wrong:** CI `git diff --exit-code` fails; frontend types drift silently during local dev.
**Do this instead:** Run `python scripts/export_openapi.py` after every API schema change (`.github/workflows/ci.yml` enforces this).

### Adding a connector by modifying `node_ingest`
**What happens:** Each new source becomes a bespoke branch in the ingestion node.
**Why it's wrong:** Violates the "adding a source requires a new adapter only" contract (Master Plan §14.3).
**Do this instead:** Implement a subclass of `SourceConnector` (`backend/app/connectors/base.py`) exposing `fetch_latest()`, declare `source_id`/`freshness_class`, and register it — `node_ingest` never changes.

### Routing the same signal to everyone
**What happens:** Broadcast-style routing recreates inbox noise.
**Why it's wrong:** Contradicts "not every signal needs to go to everyone" and the calibration loop.
**Do this instead:** Use `primary_function` + `secondary_functions[]` + per-function relevance scores + `routing_reason` from the seeded matrix in `config/haemophilia.yaml`; let calibration adjust weights.

## Error Handling

**Strategy:** per-node error boundaries in the workflow (planned); provider `try/except` cascade with explicit `logger.warning` on each fallback step (`backend/app/providers/factory.py`); readiness endpoint degrades rather than failing (`backend/app/api/v1/endpoints/health.py:45`); `tenacity` backoff (2s/4s/8s) prescribed for external APIs.

**Patterns:**
- Provisioning failures logged, app still starts (`backend/app/main.py:23`)
- DB failures → `rollback() → raise` in `get_db` (`backend/app/db/session.py:34`), readiness reports `degraded`
- Redis failures → non-blocking warning, never kills readiness (`backend/app/api/v1/endpoints/health.py:36-43`)
- Provider failures → fallback chain, never crash

---

*Architecture analysis: 2026-08-13*