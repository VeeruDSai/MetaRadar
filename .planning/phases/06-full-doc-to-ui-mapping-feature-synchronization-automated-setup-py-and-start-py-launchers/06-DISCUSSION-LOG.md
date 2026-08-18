# Phase 6: Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-18
**Phase:** 6-full-doc-to-ui-mapping-feature-synchronization-automated-setup-py-and-start-py-launchers
**Areas discussed:** UI parity scope, Control-to-endpoint mapping, Parity verification artifact, Automation launchers

---

## UI Parity Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full parity — build all doc pages | Build confluence, lifecycles, red-team, missing-signals, briefs, digest as new real pages (+ real developments/functions/settings). Largest effort. | |
| Parity where data exists (Recommended) | Build pages whose data exists in backend endpoints/tables; defer briefs and digest. | ✓ |
| Consolidate into existing sections | Keep 8 current sections; fold doc pages into existing sections as tabs. | |

**User's choice:** Parity where data exists
**Notes:** Data exists in DB tables for confluence/lifecycle/red-team/missing-signal (Confluence, LifecycleEvent, Contradiction, WatchItem) — but no read endpoints exist yet; Ask Athena already exists via IntelligencePage.

| Option | Description | Selected |
|--------|-------------|----------|
| All placeholders + new doc pages (Recommended) | Developments, Functions, Sources, Settings get real content; Calibrate stays Phase 5 feedback widget. | ✓ |
| New intelligence pages only | Focus only on 4 new intelligence pages; leave placeholders. | |
| Existing sections first | Prioritize existing placeholder sections over new doc pages. | |

**User's choice:** All placeholders + new doc pages

| Option | Description | Selected |
|--------|-------------|----------|
| Real content, honest controls (Recommended) | Sources = source registry + /health/connectors; Settings = honest controls only. | ✓ |
| Minimal version | Sources = connector health only; Settings = stub. | |
| Defer both | Both stay placeholders. | |

**User's choice:** Real content, honest controls

---

## Control-to-Endpoint Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Add read endpoints for new pages (Recommended) | New read-only endpoints for confluence/lifecycles/red-team/missing-signals/developments/sources backed by existing DB tables. | ✓ |
| Client-side only | Reuse /signals + /overview; compute views client-side. | |
| Read endpoints + run trigger | Also allow frontend to trigger pipeline run when empty. | |

**User's choice:** Add read endpoints for new pages

| Option | Description | Selected |
|--------|-------------|----------|
| Wire what maps cleanly (Recommended) | Apply Filter → /signals filters, Clear Cache → cache-clear endpoint, Evidence chain expand → evidence read, Refresh → polling. | ✓ |
| Everything incl. new services | Implement every doc control incl. new backend services. | |
| Existing endpoints only | Only wire controls whose endpoints exist today; others stay disabled. | |

**User's choice:** Wire what maps cleanly

| Option | Description | Selected |
|--------|-------------|----------|
| Server-side filters on /signals (Recommended) | Optional query params (severity/entity/date-range/signal_type/source); backward-compatible. | ✓ |
| Client-side filtering | Filter in mapper; filter state lost on 30s poll. | |
| Separate filter endpoint | Dedicated /signals/filter endpoint. | |

**User's choice:** Server-side filters on /signals

| Option | Description | Selected |
|--------|-------------|----------|
| Real cache-clear endpoint (Recommended) | POST /api/v1/cache/clear flushing Redis keys / version bump + confirmation modal. | ✓ |
| Frontend-only refetch | Honest no-op triggering frontend refetch only. | |
| Defer both | Not wired in Phase 6. | |

**User's choice:** Real cache-clear endpoint

---

## Parity Verification Artifact

| Option | Description | Selected |
|--------|-------------|----------|
| Living matrix doc (Recommended) | Hand-maintained FEATURE_PARITY_MATRIX.md as living table. | |
| Contract-parity test | Test walking OpenAPI contract vs doc-spec control list. | |
| Doc + test | Living matrix doc for humans + contract-parity test for CI. | ✓ |

**User's choice:** Doc + test

| Option | Description | Selected |
|--------|-------------|----------|
| Column + status vocabulary (Recommended) | Doc spec → Control/feature → Component → Endpoint → Status (WIRED/PARTIAL/NOT_WIRED/DEFERRED). | ✓ |
| Binary status only | WIRED vs NOT_WIRED only. | |
| Exhaustive per-element rows | Every UI doc §4/§5/§15 element its own row. | |

**User's choice:** Column + status vocabulary

| Option | Description | Selected |
|--------|-------------|----------|
| Generate from a manifest (Recommended) | Structured YAML/JSON manifest as single source of truth; generator emits the doc. | ✓ |
| Hand-maintained doc | Hand-write and maintain FEATURE_PARITY_MATRIX.md. | |

**User's choice:** Generate from a manifest

---

## Automation Launchers

| Option | Description | Selected |
|--------|-------------|----------|
| Compose-driven setup (Recommended) | setup.py orchestrates docker compose + alembic + seed + ollama pull; env from .env.example. | ✓ |
| Native install | pip/brew/apt native installs, no Docker. | |
| Verify + guide only | Prints commands for user to run. | |

**User's choice:** Compose-driven setup

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-pull with --skip-models (Recommended) | setup.py ollama pull gemma3:4b if missing, with --skip-models opt-out. | ✓ |
| Verify-only for models | Check + warn if missing, never download. | |
| Fail if missing | Fail setup with instructions. | |

**User's choice:** Auto-pull with --skip-models

| Option | Description | Selected |
|--------|-------------|----------|
| Compose DBs + host processes (Recommended) | compose up postgres/redis/ollama → uvicorn (host) → next dev (host). No Celery (APScheduler in-process). | ✓ |
| Fully containerized | Everything via docker compose up. | |
| Command guide only | Prints commands, no orchestration. | |

**User's choice:** Compose DBs + host processes

| Option | Description | Selected |
|--------|-------------|----------|
| Log capture + status table (Recommended) | Child stdout/stderr to logs/*.log; health loop prints status table; Ctrl+C graceful stop. | ✓ |
| Terminal-only output | Stream to terminal, print final healthy line. | |
| Health monitor only | Only health-check loop printing URLs. | |

**User's choice:** Log capture + status table

| Option | Description | Selected |
|--------|-------------|----------|
| Host backend, honest fallback (Recommended) | uvicorn on host with GPU; never-crash provider chain handles GPU failure; start.py surfaces honest /health/models. | ✓ |
| Containerized backend-gpu | Use pre-built backend-gpu container. | |
| CPU default | LLM_DEVICE=cpu by default. | |

**User's choice:** Host backend, honest fallback

---

## the agent's Discretion

- Exact route paths + response shapes for new read endpoints (confluence, lifecycles, red-team, missing-signals, developments, sources).
- Exact `/signals` filter query-parameter names.
- Layout/navigation structure of new pages and placeholder-section implementations.
- Parity-manifest file location/format and generator script name.
- setup.py/start.py argument surface beyond `--skip-models`, log rotation/format.
- `/cache/clear` response shape and Redis invalidation mechanism.

## Deferred Ideas

- `/briefs` and `/digest` pages (need new digest/compose endpoints) — DEFERRED in parity matrix.
- Controls needing new complex backend services — NOT_WIRED/DEFERRED in parity matrix.