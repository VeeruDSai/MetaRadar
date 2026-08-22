---
doc_type: codebase-map
focus: arch
analysis_date: 2026-08-22
---

# Architecture

**Analysis Date:** 2026-08-22

## Pattern

Layered monolith with an explicit workflow engine core:

- **API layer** (thin FastAPI routers) → **Service layer** (domain logic) → **Workflow layer** (LangGraph pipeline) → **Persistence layer** (async SQLAlchemy + Postgres/pgvector, Redis cache).
- Provider abstraction for all AI inference (`backend/app/providers/`) with a strict fallback chain: Gemma → Grok (privacy-gated) → Degraded BART.
- Connector abstraction for all external data (`SourceConnector` in `backend/app/connectors/base.py`): bronze-only persistence, never generates intelligence.

## Layers & Responsibilities

| Layer | Location | Responsibility |
|---|---|---|
| HTTP API | `backend/app/api/v1/endpoints/*.py` | Request/response schemas (`app/schemas/`), dependency-injected DB session |
| Services | `backend/app/services/` | calibration, confluence, deduplication, embeddings (+backfill), ingestion, pii scrubbing, redteam NLI, scoring, source_independence, vector_query |
| Workflow | `backend/app/workflows/graph.py`, `runner.py`, `state.py`, `nodes/*.py` | 11-node LangGraph intelligence pipeline |
| Providers | `backend/app/providers/` | LLM capability matrix + fallback chain + model_metadata on every output |
| Connectors | `backend/app/connectors/` | 5 source adapters; bronze rows to `raw_signals_bronze`; per-profile `ConnectorState` cursors |
| Persistence | `backend/app/models/__init__.py` (20 tables), `backend/app/db/session.py`, `backend/app/db/seed.py`, `backend/alembic/versions/001–006` | Canonical entity/evidence schema, advisory locks |
| Frontend | `frontend/app/page.tsx` + `frontend/components/<domain>/*.tsx`, `frontend/lib/api.ts` | Single-page radar UI, typed API client |

## Entry Points

1. **Backend**: `backend/app/main.py` — FastAPI app factory via module-level `app`; lifespan logs domain-config load; middleware order: `CorrelationIdMiddleware` → CORS. Routers mounted under `/api/v1`.
2. **Frontend**: `frontend/app/layout.tsx` + `frontend/app/page.tsx` (App Router). A `frontend/app/[section]/` directory exists but is empty.
3. **Pipeline trigger**: `POST /api/v1/pipeline/run` → `backend/app/workflows/runner.py` executes the compiled graph.
4. **Ops launchers**: `setup.py` (bootstrap) and `start.py` (unified launcher, auto-applies Alembic migrations, streams live ingestion telemetry).

## The 11-Node Intelligence Pipeline

Wired explicitly linearly in `backend/app/workflows/graph.py`:

```
node_ingest → node_validate → node_embed → node_nlp_extract → node_ontology_enrich
→ node_confluence → node_lifecycle → node_redteam → node_missing_signal
→ node_synthesize → node_calibrate → END
```

State contract: `MetaRadarState` TypedDict in `backend/app/workflows/state.py` — typed channel reducers (`operator.add` accumulation, `replace_list` for `validated_signals` to prevent duplicate-append, `merge_dicts` for metadata maps). Backward-compat alias `IntelligenceState`.

## Data Flow

1. Connectors fetch raw payloads → PII/PHI scrubber (`app/services/pii.py`) → immutable bronze persist (`raw_signals_bronze`, content-hash dedup) → deterministic fingerprint dedup (`app/services/deduplication.py`).
2. Pipeline nodes validate → embed (384-dim fastembed into `signals.embedding`) → NLP extract → ontology enrich (haemophilia domain config from `config/haemophilia.yaml`) → confluence (multi-source convergence) → lifecycle FSM (`announced → … → post_market`) → red-team contradiction rules (19-rule registry) → missing-signal watch items → synthesize (Four-Question briefs Q1–Q4, FACT/INTERPRETATION/SPECULATION epistemic tags) → calibrate (stakeholder weights).
3. Every scored signal carries provenance columns: `data_mode`, `is_synthetic`, `confidence_type/rationale`, `provenance_status`, `model_metadata`, scoring/embedding/prompt version pins.

## Key Abstractions

- `LLMProvider` base + `ProviderCapability` / `DataClassification` enums (`backend/app/providers/base.py`); singleton `provider_factory` in `backend/app/providers/factory.py`.
- `SourceConnector` dataclass contract with `ProfileRunResult` telemetry (`SUCCESS/PARTIAL/DEGRADED/FAILED`).
- `get_domain_config()` — YAML-driven domain rules (no hard-coded haemophilia logic in code paths).
- Frontend: typed client functions per endpoint in `frontend/lib/api.ts`; DTO→view mapping isolated in `frontend/lib/mappers.ts`; error normalization in `frontend/lib/errors.ts`.

## API Surface (implemented routes)

`GET /overview`, `GET /signals`, `POST /athena` (`signals.py`); confluence/lifecycle/red-team/missing-signals views (`intelligence.py`); `/developments`, `/sources` registry; `/observability/activity`, `/sources/health`; `POST /cache/clear`; health trio `/ready`, `/models`, `/connectors`; plus pipeline, ingestion, search, feedback routers.

---

*Mapped as part of full-repo codebase analysis: 2026-08-22*
