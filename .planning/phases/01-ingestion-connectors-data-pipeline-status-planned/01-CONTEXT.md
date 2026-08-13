# Phase 1: Ingestion Connectors & Data Pipeline - Context

**Gathered:** 2026-08-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Implement production-grade `SourceConnector` adapters for five external sources (NCBI PubMed E-utilities, ClinicalTrials.gov API v2, NewsAPI, OpenFDA, EMA RSS), persist verbatim raw payloads into `raw_signals_bronze`, and wire the deterministic deduplication / source-independence layer that runs BEFORE the Phase 2 Confluence step. Deliver concrete connector modules, bronze-layer persistence, dedup integration, per-connector incremental state, and ingest tests (REQ-P1-1 through REQ-P1-6).

This phase defines the connector contract, not the intelligence pipeline. Connectors must never generate intelligence or bypass the canonical entity/evidence layer. Promotion of bronze rows into the `signals` layer is Phase 2 (`node_ingest`/`node_validate`).

</domain>

<decisions>
## Implementation Decisions

### Phase 1 Connector Contract (governing principles)
- **D-01:** Connectors are production-grade — each must be **isolated, idempotent, source-specific, incrementally runnable, quota-aware, observable, and replayable**. A connector that merely makes an API return data is not acceptable. — **Reversibility:** one-way — undoing means rewriting every adapter; this contract defines the architecture.
- **D-02:** Raw source payloads are **immutable and provenance-preserving**. Bronze rows are append-only; replay creates new rows rather than overwriting.
- **D-03:** Deterministic deduplication and source-independence detection run **before** Confluence (Phase 2). Connectors feed bronze; dedup classifies cross-source identity; nothing touches Confluence without that ordering.
- **D-04:** Connector failures are **isolated** and represented honestly as one of `SUCCESS / PARTIAL / DEGRADED / FAILED`. No fabricated health or run status.
- **D-05:** Search query/domain configuration belongs in the **haemophilia domain configuration layer** (`config/haemophilia.yaml`); **secrets belong in environment variables** (never in the domain YAML, never committed).
- **D-06:** Connectors must not generate intelligence and must never bypass the canonical entity/evidence layer. Promotion is Phase 2's concern.
- **D-07:** All implementation conforms to Master Plan v5.1, the canonical entity model, the LangGraph state contract, health/observability requirements, privacy guardrails, and repository engineering standards (`docs/rules/*`).

### Query strategy per source
- **D-08:** Queries are **explicit per-source YAML blocks** in `config/haemophilia.yaml` (per-source queries, not a shared auto-fanned term set). Connectors execute config — they do not invent queries. Development/asset synonyms (emicizumab, Hemgenix, mim8, Roctavian) are core terms used across sources. — **Reversibility:** costly — changing the query config schema touches domain config loader + every connector.
- **D-09:** Date-window policy is **rolling window + backfill**: a configurable rolling window (default ~30 days) for normal runs; a separate wide window for first-run backfill; subsequent runs fetch only since the last success.
- **D-10:** Each source manages **multiple query profiles** (e.g., trial signals, regulatory, competitive/development) run independently. Profiles are config-driven; richer coverage at the cost of more API calls per run.

### Incrementality & run tracking
- **D-11:** Per-connector incremental state (incl. per-profile) lives in a dedicated **DB table `connector_state`** (last_success, cursor/idate, next_run). Survives restarts, is queryable and auditable. — **Reversibility:** costly — adds a schema migration; all connectors read it for incremental fetch.
- **D-12:** First run per profile is a **config-driven wide backfill** (e.g., 180 days, window configured per source); after first success it switches to rolling-window incremental.
- **D-13:** Replay is enabled via a **force-backfill flag** (CLI/param) that re-fetches regardless of state and writes **new bronze rows (append-only)** — idempotency preserved.
- **D-14:** A run finding nothing new records **`SUCCESS` with 0 new signals** and updates last_success — observable, not alarming.

### Deduplication policy
- **D-15:** Dedup builds on the existing `generate_fingerprint` priority chain (`services/deduplication.py`): `pmid:` / `nct:` / `reg:` then normalized title+publisher+date+company+asset hash. Extended to remain the canonical unique key for the pipeline.
- **D-16:** On fingerprint collision (duplicate already in bronze), **skip the new row and record the hit** (increment a counter / log). The original immutable payload is preserved.
- **D-17:** Source-independence (REQ-P1-5) is a **dedicated cross-source classifier** that runs before Confluence, scoring cross-source identity (normalized title similarity + entity overlap + date proximity) and emitting a `cross_source_group_id`. Rules are stored in the domain config (`config/haemophilia.yaml`). — **Reversibility:** one-way — introduces a new identity model the rest of the pipeline (Phase 2+) depends on.
- **D-18:** Chunking happens **at ingestion** using the existing `chunk_text_for_embedding` (store chunked evidence when content exceeds max tokens); Phase 3 consumes the chunks later.

### Failure/quota handling
- **D-19:** Retry/backoff is **built into the connector base** (bounded max_retries, exponential backoff + jitter, per-source config) using existing `httpx` — no new dependency (no tenacity). Backward compatible with the pinned `httpx>=0.27.0`.
- **D-20:** Connectors are **quota-aware** (NewsAPI ~100 req/day dev cap): check remaining quota before fetching; NewsAPI halts until the next window (date rollover) and reports `DEGRADED`, exposing `quota_remaining` via `ConnectorStatus`.
- **D-21:** Run status is resolved as the four-state contract (`SUCCESS / PARTIAL / DEGRADED / FAILED`) from per-profile outcomes (e.g., some profiles OK + one quota-blocked → PARTIAL/DEGRADED), persisted to `pipeline_runs` / `connector_state`.
- **D-22:** Connector run outcomes feed the existing `/health/connectors` endpoint honestly — `quota_remaining`, `last_success`, `last_error`, `status` — no fabricated state.

### Bronze persistence details
- **D-23:** `raw_signals_bronze.raw_payload` stores the **complete verbatim source response** (header subset + body JSON/text) — immutable, provenance-preserving, exactly as the source returned it.
- **D-24:** `content_hash` is the **sha256 of the canonical external_id + verbatim payload bytes** (what `RawSignalPayload.raw_hash` encodes) — an integrity check for the immutable row.
- **D-25:** Unparseable/failed payloads are **quarantined to bronze** (row written with `connector_version` + parsing/status note), preserving evidence and integrity; excluded from signal promotion. Honest and replayable.
- **D-26:** Phase 1 is **bronze-only**. Promotion of bronze rows into the canonical `signals`/`evidence` layer stays in Phase 2 (`node_ingest`/`node_validate`). Connectors never bypass it.

### the agent's Discretion
- Concrete YAML schema shape for `config/haemophilia.yaml` query blocks (structure/names, so long as per-source + config-driven).
- Exact `connector_state` column schema (so long as it stores last_success, cursor/idate, next_run, per-profile).
- Choice of which health/observability fields map to `ConnectorStatus` vs `pipeline_runs`.
- Test-scaffolding details for ingest tests (framework = pytest; strategy at agent's discretion).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Master specification & engineering rules
- `docs/METARADAR_MASTER_PLAN_v5.0.md` §4.1 — Ingestion & Validation; the canonical phase-1 authority
- `docs/rules/ENGINEERING_STANDARDS.md` — non-negotiable quality/type-safety/telemetry rules
- `docs/rules/DEFINITION_OF_DONE.md` — DoD verification matrix required before declaring done
- `docs/rules/TESTING_STRATEGY.md` — mandatory test gates
- `docs/rules/SECURITY_STANDARDS.md` — zero secret leaks, PII/PHI scrubbing, privacy gate
- `docs/rules/DATA_AND_PRIVACY_STANDARDS.md` — payload classification and privacy boundary
- `docs/rules/OBSERVABILITY_STANDARDS.md` — honest health/readiness modeling
- `docs/rules/ARCHITECTURE_RULES.md` — approved stack, canonical entity model, LangGraph state contract
- `docs/rules/DEVELOPMENT_WORKFLOW.md` — branch workflow, atomic commits, PRs
- `docs/rules/CI_CD_STANDARDS.md` / `docs/rules/RELEASE_PROCESS.md` — CI and release gates

### Design & requirements specifications
- `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §2.1 — Data Ingestion Architecture
- `docs/2_SRS_Software_Requirements_Specification.md` §3.1 — Data Acquisition
- `docs/10_ARCHITECTURE_HARDENING_REPORT.md` — hardening decisions that shaped the baseline
- `docs/8_CORRECTED_UNIFIED_PLAN.md` — pipeline architecture alignment

### Domain configuration
- `config/haemophilia.yaml` — source of per-source query blocks, cross-source rules, asset/development synonyms (emicizumab, Hemgenix, mim8, Roctavian)
- `config/haemophilia.yaml` structure must stay consistent with `backend/app/core/domain_config.py` (YAML loader & validator)

### Existing code implementing the connector contract
- `backend/app/connectors/base.py` — `SourceConnector` abstract base, `RawSignalPayload`, `ConnectorStatus` (fetch_latest currently raises `NotImplementedError`)
- `backend/app/services/deduplication.py` — `generate_fingerprint`, `chunk_text_for_embedding`, `upsert_signal`
- `backend/app/models/__init__.py` — `RawSignalBronze` (`raw_signals_bronze`), `Signal` (`signals`), `PipelineRun` schemas
- `backend/app/core/config.py` — `Settings` (NEWSAPI_KEY, EMBEDDING_MAX_SEQ_LENGTH, RAW_SIGNAL_RETENTION_DAYS, etc.)
- `backend/app/api/v1/endpoints/health.py` — `/health/connectors` honest status endpoint
- `backend/app/core/domain_config.py` — YAML config loader/validator to extend for query blocks

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `SourceConnector` abstract base (`connectors/base.py`): `fetch_latest`, `get_status`, `ConnectorStatus`, `freshness_class` — the scaffold every adapter extends.
- `RawSignalPayload` (`connectors/base.py`): canonical bronze payload schema (source_id, source_type, external_id, title, content, url, published_at, retrieved_at, publisher, raw_hash).
- `generate_fingerprint` / `chunk_text_for_embedding` / `upsert_signal` (`services/deduplication.py`): dedup fingerprint chain, embedding chunking, and signal upsert (Phase 2 consumer).
- `RawSignalBronze` ORM model (`models/__init__.py`): `raw_signals_bronze` table with `raw_payload` JSONB, `content_hash`, `connector_version`, unique `(source_id, external_id)`.
- `Settings` (`core/config.py`): `NEWSAPI_KEY`, `RAW_SIGNAL_RETENTION_DAYS`, `EMBEDDING_MAX_SEQ_LENGTH` — env-driven config.
- `httpx>=0.27.0` already pinned in `backend/requirements.txt`.

### Established Patterns
- Async everything: `async def` + async SQLAlchemy (`db/session.py`), `httpx` async client, `redis.asyncio`.
- Pydantic v2 schemas + `pydantic-settings` env config with `extra="ignore"`.
- Honest health modeling (`/health/connectors`) — per-source status, quota_remaining, last_success, last_error.
- Alembic async migrations for schema additions (new `connector_state` table needs a migration).
- 18-point `pytest` suite pattern in `tests/` (config, endpoints, provider matrix, PII, privacy gate, redteam, contract drift).

### Integration Points
- Extend `config/haemophilia.yaml` + `domain_config.py` for per-source query blocks and cross-source rules.
- New `backend/app/connectors/pubmed.py`, `clinical_trials.py`, `newsapi.py`, `fda.py`, `ema.py`.
- New `connector_state` DB table via Alembic migration.
- Wire run outcomes into `backend/app/api/v1/endpoints/health.py` `/health/connectors`.
- Bronze row writes via the existing `raw_signals_bronze` ORM model and `db/session.py` async session.
- Cross-source classifier consumes `generate_fingerprint` output and emits `cross_source_group_id` for Phase 2 Confluence.

</code_context>

<specifics>
## Specific Ideas

- "Production-grade connector contract" — the user explicitly framed the phase as establishing a durable contract, not "merely make APIs return data": every connector isolated, idempotent, source-specific, incrementally runnable, quota-aware, observable, and replayable.
- All five discussed areas were settled via the recommended options (see decisions D-08 through D-26).
- No other specific references raised — remaining shape details are at the agent's discretion.

</specifics>

<deferred>
## Deferred Ideas

- **Scheduler/polling loop (APScheduler in-process)** — Phase 1 connectors are invoked on demand / via run orchestration; the autonomous polling scheduler itself belongs in a later phase (per STACK.md: "Scheduler: APScheduler in-process — Deferred to Phase 1 polling pipeline" — planning may scope a lightweight run trigger, but a full scheduler is out of this phase's core scope).
- Promotion of bronze rows into `signals`/`evidence` (Phase 2 `node_ingest`/`node_validate`).
- Cross-source merge consumption in Confluence detection (Phase 2 `node_confluence`).

None — discussion stayed otherwise within phase scope.

</deferred>

---

*Phase: 1-Ingestion Connectors & Data Pipeline*
*Context gathered: 2026-08-13*