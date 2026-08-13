# Phase 1: Ingestion Connectors & Data Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-13
**Phase:** 1-Ingestion Connectors & Data Pipeline
**Areas discussed:** Governing connector contract, Query strategy per source, Incrementality & run tracking, Deduplication policy, Failure/quota handling, Bronze persistence details

---

## Governing Connector Contract

| Option | Description | Selected |
|--------|-------------|----------|
| (user-provided directive) | Production-grade connector contract — isolated, idempotent, source-specific, incrementally runnable, quota-aware, observable, replayable; immutable provenance-preserving raw payloads; dedup before Confluence; honest SUCCESS/PARTIAL/DEGRADED/FAILED status; query config in domain layer, secrets in env; no connector generates intelligence or bypasses entity/evidence layer; conform to Master Plan v5.1 | ✓ |

**User's choice:** Provided as a governing directive when selecting gray areas.
**Notes:** This is the architectural anchor for the entire phase. Captured as D-01 .. D-07.

---

## Query Strategy per Source

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit per-source YAML blocks | Each source gets an explicit query block in config/haemophilia.yaml; connectors execute config, not invented queries | ✓ |
| Shared term set auto-fanned | Single shared haemophilia term set fanned into each source's query format | |
| Rolling window + backfill | Configurable rolling window (~30d) for normal runs; wide window for first-run backfill; subsequent incremental | ✓ |
| Fixed window every run | Fixed window (e.g., 7d) regardless of prior state | |
| Multiple query profiles per source | Profiles like trial signals, regulatory, competitive run independently | ✓ |
| Single evolving query per source | One query per source that evolves | |

**User's choice:** Explicit per-source YAML blocks; rolling window + backfill; multiple query profiles.
**Notes:** Development/asset synonyms (emicizumab, Hemgenix, mim8) are core terms across all sources. Captured as D-08 .. D-10.

---

## Incrementality & Run Tracking

| Option | Description | Selected |
|--------|-------------|----------|
| DB table connector_state | Per-connector (per-profile) last-run state in a dedicated table; survives restarts, queryable, auditable | ✓ |
| Local JSON state files | Simple per-connector JSON files; not queryable, fragile in containers | |
| Config-driven wide first run | First run uses a wide explicit backfill window; then switches to rolling incremental; force-backfill flag for replay | ✓ |
| No backfill | Only rolling window from day one | |
| Force-backfill flag, append-only | Replay via flag re-fetches regardless of state, writes new bronze rows (immutable append) | ✓ |
| Replay overwrites bronze rows | Replay overwrites previous raw rows | |
| SUCCESS with 0 new | Empty runs report SUCCESS with 0 new signals and update last_success | ✓ |
| Separate empty status | Zero-new runs report a distinct status | |

**User's choice:** DB table connector_state; config-driven wide first run; force-backfill append-only; SUCCESS with 0 new.
**Notes:** Captured as D-11 .. D-14.

---

## Deduplication Policy

| Option | Description | Selected |
|--------|-------------|----------|
| Extend existing chain | Extend generate_fingerprint priority chain (pmid:/nct:/reg:/hash) as canonical unique key + dedicated cross-source classifier | ✓ |
| New scheme | Independent dedup scheme separate from generate_fingerprint | |
| Skip + record hit | Existing fingerprint already in bronze → skip new row, record the hit, keep original immutable | ✓ |
| Partial update | Update enrichment fields but keep raw payload untouched | |
| Allow duplicates | Insert duplicate rows for every occurrence | |
| Dedicated cross-source classifier | Scores cross-source identity (normalized title + entity overlap + date proximity), emits cross_source_group_id, runs before Confluence; rules in domain config | ✓ |
| Source-isolated only | Treat each source as unique; defer cross-source to Phase 2 | |
| Chunk at ingestion | Keep chunk_text_for_embedding at ingestion; Phase 3 consumes chunks later | ✓ |
| Defer chunking | Defer entirely to embedding phase | |

**User's choice:** Extend existing chain; skip + record hit; dedicated cross-source classifier; chunk at ingestion.
**Notes:** Cross-source classifier introduces a new identity model (cross_source_group_id) the rest of the pipeline depends on. Captured as D-15 .. D-18.

---

## Failure / Quota Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Built-in retry | Hand-rolled bounded retry in connector base (max_retries, exp backoff + jitter, per-source config) on httpx — no new dep | ✓ |
| Tenacity dependency | Add tenacity for a richer retry DSL | |
| Quota-aware halt | NewsAPI checks remaining quota before fetch; halts until next window and reports DEGRADED with quota_remaining exposed | ✓ |
| Fetch regardless | Consumes quota blindly; failures surface after 429s | |
| Four-state resolution | SUCCESS/PARTIAL/DEGRADED/FAILED resolved from per-profile outcomes, persisted to pipeline_runs / connector_state | ✓ |
| Binary only | Binary success/failure per run | |
| Feed health endpoint | Run outcomes feed honest /health/connectors (quota_remaining, last_success, last_error, status) | ✓ |
| Log-only | Health stays static; connectors only log | |

**User's choice:** Built-in retry; quota-aware halt; four-state resolution; feed health endpoint.
**Notes:** Captured as D-19 .. D-22.

---

## Bronze Persistence Details

| Option | Description | Selected |
|--------|-------------|----------|
| Verbatim full response | raw_payload stores complete verbatim source response (header subset + body) — immutable, provenance-preserving | ✓ |
| Extracted fields only | Store only item-level extracted fields | |
| sha256 of payload | content_hash = sha256 of canonical external_id + verbatim payload bytes | ✓ |
| Reuse fingerprint | Reuse dedup fingerprint as content_hash | |
| Quarantine to bronze | Unparseable/failed payloads still get a bronze row (connector_version + parsing note), excluded from signal promotion | ✓ |
| Drop + log | Silently drop failed payloads, log only | |
| Bronze only in this phase | Phase 1 persists bronze rows only; promotion to signals/evidence is Phase 2 | ✓ |
| Promote to signals now | Also upsert into signals table now | |

**User's choice:** Verbatim full response; sha256 of payload; quarantine to bronze; bronze-only in Phase 1.
**Notes:** Captured as D-23 .. D-26.

---

## the agent's Discretion

- Concrete YAML schema shape for per-source query blocks.
- Exact `connector_state` column schema.
- Mapping of health/observability fields to `ConnectorStatus` vs `pipeline_runs`.
- Ingest test-scaffolding details (pytest).

## Deferred Ideas

- Full APScheduler polling scheduler (a lightweight run trigger may be in scope; full scheduler is a later-phase concern).
- Bronze → signals/evidence promotion (Phase 2 `node_ingest`/`node_validate`).
- Cross-source merge consumption in Confluence (Phase 2 `node_confluence`).