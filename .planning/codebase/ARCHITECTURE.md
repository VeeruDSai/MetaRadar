---
doc_type: codebase-map
focus: arch
analysis_date: 2026-08-22
---

# Architecture

**Analysis Date:** 2026-08-22

## Architectural Pattern

MetaRadar v5.1 is an autonomous, continuous competitive intelligence radar built as a layered service architecture with an explicit workflow engine core:

- **Autonomous Background Layer**: Persistent scheduler (`SourceScheduler` in `backend/app/services/scheduler.py`) independently polling configured sources with jitter, backoff, and distributed PostgreSQL advisory locks.
- **Truthful Source Health Model**: Real-time state machine distinguishing `NO_NEW_DATA` from `DEGRADED`, `HEALTHY`, `STALE`, `FAILED`, `CONFIGURATION_ERROR`, and `NEVER_CONNECTED`.
- **First-Stage Relevance Filter**: Deterministic `RelevanceGate` (`backend/app/services/relevance.py`) filtering bronze documents before AI execution.
- **Decoupled Workflow Layer**: 11-stage LangGraph pipeline triggered strictly when new or updated records are detected.
- **Inference Layer**: Provider fallback chain (`Local Gemma 3 4B` → `Grok API (privacy-gated)` → `Degraded BART`).
- **Persistence Layer**: Async SQLAlchemy 2.0 with PostgreSQL 16 + pgvector and Redis 7 cache.

## Layers & Responsibilities

| Layer | Location | Responsibility |
|---|---|---|
| Ingestion & Schedulers | `backend/app/services/scheduler.py`, `backend/app/services/ingestion.py`, `backend/app/connectors/` | Continuous background polling, multi-feed source parsing, rate-limiting, advisory locking, bronze persistence |
| Truthful Health Model | `backend/app/connectors/base.py`, `backend/app/api/v1/endpoints/health.py`, `observability.py` | Accurate health telemetry, timestamp updates on clean syncs, zero fabricated statuses |
| Relevance Gate | `backend/app/services/relevance.py` | Deterministic classification (`DIRECTLY_RELEVANT`, `POTENTIALLY_RELEVANT`, `IRRELEVANT`) with explanation metadata |
| HTTP API | `backend/app/api/v1/endpoints/*.py` | Request/response validation schemas (`app/schemas/`), DB session dependency injection |
| Services | `backend/app/services/` | Calibration, confluence, deduplication, embeddings, pii scrubbing, redteam NLI, scoring, source independence, vector queries |
| Intelligence Workflow | `backend/app/workflows/graph.py`, `runner.py`, `state.py`, `nodes/*.py` | 11-node LangGraph pipeline executing semantic extraction, confluence, red-team contradictions, synthesis, and calibration |
| Providers | `backend/app/providers/` | Local Gemma GPU inference, Grok cloud fallback with privacy gate, BART degraded summarizer |
| Persistence | `backend/app/models/__init__.py` (20 tables), `backend/app/db/session.py`, `alembic/versions/` | Entity relational models, Vector(384) embeddings, advisory locks |
| Frontend | `frontend/app/page.tsx`, `frontend/components/<domain>/*.tsx`, `frontend/lib/api.ts` | Single-page radar workspace, source operations UI, typed API client |

## The 11-Node Intelligence Pipeline

Wired in `backend/app/workflows/graph.py`:

```
node_ingest → node_validate → node_embed → node_nlp_extract → node_ontology_enrich
→ node_confluence → node_lifecycle → node_redteam → node_missing_signal
→ node_synthesize → node_calibrate → END
```

State contract: `MetaRadarState` TypedDict in `backend/app/workflows/state.py` with explicit channel reducers (`replace_list` for signal deduplication, `merge_dicts` for metadata).

## Operational Radar Data Flow

1. **Continuous autonomous monitoring**: `SourceScheduler` fires connector tasks on configured intervals (CT.gov: 60m, PubMed: 60m, EMA: 30m, FDA: 30m, NewsAPI: 15m) with ±10% jitter.
2. **Distributed locking**: Task acquires PostgreSQL advisory lock (`try_advisory_lock`) to prevent duplicate runs across instances.
3. **Multi-feed fetch & bronze landing**:
   - ClinicalTrials.gov checks `dataTimestamp` metadata before fetching; diffs study changes.
   - openFDA queries Drugs@FDA and parses MedWatch / Drug Safety RSS feeds.
   - EMA parses Medicines RSS, EPARs updates, and Orphan designations.
   - PII/PHI scrubber sanitizes abstracts and text.
   - Raw payloads persisted immutably to `raw_signals_bronze` with SHA-256 content hashes and fingerprints.
4. **Truthful health telemetry**: Run status is resolved and persisted to `source_health_logs` and `sources` (`NO_NEW_DATA`, `HEALTHY`, `DEGRADED`, etc.). `last_success` is updated on every clean synchronization.
5. **Relevance Gate & Intelligence triggering**:
   - If `records_new == 0`: LangGraph pipeline is **not** executed (saving compute).
   - If `records_new > 0`: `RelevanceGate.evaluate()` filters bronze signals, and `PipelineRunner` triggers the 11-node graph on directly/potentially relevant records.
6. **Synthesis & Calibration**: Generates Four-Question briefs (Q1–Q4) with epistemic tags (`FACT`, `INTERPRETATION`, `SPECULATION`) and role-specific calibrated relevance scores.
