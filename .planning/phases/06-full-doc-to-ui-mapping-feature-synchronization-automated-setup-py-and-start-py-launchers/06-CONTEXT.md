# Phase 6: Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers - Context

**Gathered:** 2026-08-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Two coordinated workstreams deliver this phase:

1. **Doc-to-UI feature parity** — comprehensive audit + implementation of every page, button, control, and workflow specified in the UI Design Document, SRS, SDD, and Architecture Hardening Report against the real Next.js components and FastAPI endpoints. Includes an end-to-end documentation-to-feature matrix verification.
2. **Automation launchers** — `setup.py` (zero-config setup: dependencies, environment, DB + pgvector, migrations, seed data, Ollama model) and `start.py` (single-command unified launcher: FastAPI backend, Next.js frontend, Ollama, with live health-check telemetry).

**Scope guardrail (user-locked):** Parity means "build pages/controls where real data exists" — pages backed by existing DB tables get real read endpoints; controls that map cleanly to existing or cheap new endpoints get wired; everything else is explicitly deferred (NOT_WIRED/DEFERRED) and recorded in the parity matrix. No fabricated telemetry, no demo-mode labels, no invented metrics — consistent with AGENTS.md and prior phase decisions.

</domain>

<decisions>
## Implementation Decisions

### UI Parity Scope
- **D-01:** **Parity = pages where data exists.** Build the four new intelligence pages for real — Confluence Alerts, Lifecycle Timelines, Red-Team Contradictions, Missing Signals (`/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`) — because their DB tables exist (`Confluence`, `LifecycleEvent`, `Contradiction`, `WatchItem`, `Evidence`). Ask Athena already exists via `IntelligencePage`. **Deferred:** `/briefs` and `/digest` (they need new digest/compose endpoints — recorded in `<deferred>`). — **Reversibility:** costly — new pages + read endpoints + contract surface; undoing requires removing pages, endpoints, and the exported contract entries.
- **D-02:** **All five GenericPage placeholders get real content too** — Developments, Functions, Sources, Settings — alongside the new doc pages. Calibrate stays as the Phase 5 feedback-widget context (no new calibrate surface). This fills the current 8-section nav completely.
- **D-03:** **Sources = real source registry** (from the `sources` table + live `/health/connectors` status per source). **Settings = honest workspace controls only** (dark mode, polling interval, any real config knobs that exist) — no fake toggles. UI doc has no detailed spec for these two; "real content, honest controls" governs.

### Control-to-Endpoint Mapping
- **D-04:** **New read endpoints for new pages.** Add honest read-only endpoints for confluence, lifecycles, red-team, missing-signals, developments, and sources, each backed by the existing DB tables. Served via the existing `/api/v1` router pattern; contract flows through `scripts/export_openapi.py`. — **Reversibility:** costly — new public API surface + exported OpenAPI + generated TS types.
- **D-05:** **Wire what maps cleanly.** Controls get wired when they map to existing or cheap new endpoints: Apply Filter → `/signals` filters, Evidence-chain expand → evidence read, Refresh → existing polling. Anything needing a new complex backend service is recorded as NOT_WIRED/DEFERRED in the parity matrix rather than half-built.
- **D-06:** **Server-side filters on `GET /signals`.** Extend the existing endpoint with optional query params (severity/priority, entity/asset, date-range from/to, signal_type, source) powering the Apply Filter control + multi-select entity filter. Backward-compatible; contract updated via `export_openapi`. — **Reversibility:** costly — changes the canonical `/signals` contract and generated TS types.
- **D-07:** **Real cache-clear endpoint.** `POST /api/v1/cache/clear` flushes Redis cache keys / bumps the version, behind the confirmation modal from the UI doc (§4.4). Honest behavior, no fabricated "refreshed" claims. — **Reversibility:** costly — new endpoint on the public API surface; undo requires reverting endpoint + exported contract.

### Parity Verification Artifact
- **D-08:** **Matrix = living doc + contract-parity test.** `docs/FEATURE_PARITY_MATRIX.md` for humans AND a contract-parity test that walks the OpenAPI contract vs the doc-spec control list and fails on unmapped controls.
- **D-09:** **Matrix columns + status vocabulary.** Columns: `Doc spec (file + §)` → `Control/feature` → `Component` → `Endpoint` → `Status`. Status vocabulary: **WIRED** (implemented + gated), **PARTIAL** (partially wired), **NOT_WIRED** (exists in doc, deferred), **DEFERRED** (explicitly out). Honest per AGENTS.md — a row is only WIRED when proven by tsc/eslint/build/pytest gates.
- **D-10:** **Matrix generated from a structured manifest.** A YAML/JSON manifest of doc controls + wired status is the single source of truth; a generator script emits `docs/FEATURE_PARITY_MATRIX.md` (regenerable, low drift). Hand-editing the rendered matrix is not the maintenance path.

### Automation Launchers
- **D-11:** **setup.py is compose-driven.** Zero-config setup runs `docker compose up` for postgres/redis/ollama (services already composed), then applies Alembic migrations, seeds the synthetic dataset (`data/synthetic_signals.json`), and ensures the Ollama model. Environment built from `.env.example` with sensible defaults. Deterministic on the demo box. — **Reversibility:** costly — the launcher becomes the canonical on-ramp; rewiring later (e.g., native) means rewriting the script's core orchestration.
- **D-12:** **Ollama model auto-pull with `--skip-models` flag.** setup.py runs `ollama pull gemma3:4b` if the model is absent (with a clear progress line); `--skip-models` bypasses the multi-GB download for boxes that already cache weights. Model id `gemma3:4b` matches `OLLAMA_MODEL` / `LOCAL_LLM_MODEL` in `backend/app/core/config.py`.
- **D-13:** **start.py = compose DBs + host processes.** Launches `docker compose up -d postgres redis ollama` → backend (`uvicorn`, on host) → frontend (`next dev`, on host). **No Celery** — Celery was removed in Hardening Report A1; scheduling is in-process APScheduler. — **Reversibility:** costly — the launcher's process contract is the demo-day entry point; changing service topology requires script rewrite + compose edits.
- **D-14:** **Log capture + live status table.** Each child process streams to `logs/*.log` (e.g., `logs/backend.log`, `logs/frontend.log`); a health loop polls `/health/ready`, `/health/models`, and the frontend `/`, printing a status table (service, port, status, latency, model). Ctrl+C gracefully stops children (SIGTERM, then kill).
- **D-15:** **Host backend with honest fallback.** Backend runs on the host with GPU (RTX 3050). If GPU init fails, the existing never-crash provider chain (Gemma → Grok → BART degraded) handles it; start.py just surfaces the honest `/health/models` state — no fabricated health.

### the agent's Discretion
- Exact route paths + response shapes for the new read endpoints (confluence, lifecycles, red-team, missing-signals, developments, sources) — follow existing endpoint/service patterns.
- Exact `/signals` filter query-parameter names.
- Layout/navigation structure of the four new pages and the five placeholder sections (follow UI doc §3/§15 visual language + existing `metaradar.tsx` components).
- Manifest file location/format for the parity matrix and the generator script name.
- setup.py/start.py argument surface beyond the locked flags (`--skip-models`), plus log rotation/format details.
- `/cache/clear` response shape and exact Redis invalidation mechanism (flush vs version-bump).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Specifications (ROADMAP-mandated for Phase 6)
- `docs/4_UI_DESIGN_DOCUMENT.md` — §3 Page Specifications (Dashboard, Confluence Alerts, Lifecycle, Red-Team, Missing Signals, Ask Athena, Briefs, Digest), §4 Interactive Elements (4.1 Buttons, 4.2 Form Inputs, 4.3 Status Indicators, 4.4 Modals), §5 Visualizations, §8 Error & Empty States, §15 Four-Question Display Specifications
- `docs/2_SRS_Software_Requirements_Specification.md` §3 — User Interfaces & Functional Modules (the functional-module surface the parity audit checks)
- `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §2 — Architectural Layers & Contract Parity (backend contract surface for the new read endpoints)
- `docs/10_ARCHITECTURE_HARDENING_REPORT.md` §7 — Operational Runbooks & Tooling (setup/start automation rationale) and **A1 — Celery removed, single in-process APScheduler** (locked: start.py must NOT launch a Celery worker)
- `docs/METARADAR_MASTER_PLAN_v5.0.md` §3 (Four-Question Decision Interface) & §14 (v5.1 hardening / operational surface)

### Engineering rules (quality gates & governance)
- `docs/rules/ENGINEERING_STANDARDS.md` — type safety, honest execution telemetry, no fabricated behavior
- `docs/rules/TESTING_STRATEGY.md` — mandatory executable testing gates (pytest, tsc, eslint, next build, contract sync) that prove WIRED rows
- `docs/rules/ARCHITECTURE_RULES.md` — approved Next.js 16 + FastAPI + PostgreSQL 16 + Local Gemma stack (no silent architecture changes)
- `docs/rules/DEFINITION_OF_DONE.md` — complete DoD verification matrix
- `docs/rules/OBSERVABILITY_STANDARDS.md` — honest health/readiness modeling (start.py telemetry)
- `docs/rules/RELEASE_PROCESS.md` — release verification & deployment readiness

### Contract governance
- `contracts/openapi.json` — OpenAPI 3.1 schema snapshot; drift gate compares against it
- `frontend/types/api.ts` — canonical generated TS contract; MUST be regenerated via `scripts/export_openapi.py`, not hand-edited
- `scripts/export_openapi.py` — OpenAPI JSON + TypeScript contract generator; must stay 0-drift

### Existing code implementing the contracts
- `backend/app/api/v1/endpoints/signals.py` — `/signals` (D-06 filters), `/overview`, `/athena` (endpoint patterns for the new read endpoints)
- `backend/app/api/v1/endpoints/health.py` — `/health/ready`, `/health/models`, `/health/connectors` (Sources page + start.py telemetry sources)
- `backend/app/api/v1/endpoints/search.py`, `pipeline.py`, `feedback.py` — additional endpoint patterns
- `backend/app/models/__init__.py` — `Confluence`, `LifecycleEvent`, `Contradiction`, `WatchItem`, `Evidence`, `Source`, `Development` tables (back the new read endpoints)
- `backend/app/core/config.py` — `OLLAMA_MODEL=gemma3:4b`, `LOCAL_LLM_MODEL`, `LLM_DEVICE`, `LLM_DTYPE`, `DATABASE_URL`, `REDIS_URL` (setup/start env contract)
- `frontend/components/metaradar.tsx` — `Shell`, `DashboardPage`, `SignalsPage`, `IntelligencePage`, `SignalRow`, `SignalDrawer`, `Radar`, `TrendChart`, `KPI`, `Badge`, `Card`, `GenericPage` (pages to build on; `GenericPage` placeholders to replace)
- `frontend/app/[section]/page.tsx` — dynamic section dispatcher (new pages register here)
- `frontend/lib/api.ts` — mapper + live client seam; `frontend/lib/hooks.ts` — `useLiveData` polling hook
- `data/synthetic_signals.json` — synthetic fallback/seed dataset (setup.py seeding)

### Automation infrastructure
- `docker-compose.yml` — postgres (`pgvector/pgvector:pg16`), redis (`redis:7-alpine`), ollama (`ollama/ollama:latest`, `ollama_models` volume), backend, backend-gpu, frontend services
- `.env.example` — the env contract setup.py builds from
- `backend/Dockerfile`, `frontend/Dockerfile` — existing container images (host-process path in D-13 bypasses the app containers; DBs/ollama still run in compose)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`Confluence`, `LifecycleEvent`, `Contradiction`, `WatchItem`, `Evidence`, `Source`, `Development` ORM models** — already exist in `backend/app/models/__init__.py`; the new read endpoints are pure aggregation/serialization over these (mirror how `/signals` and `/overview` query).
- **`metaradar.tsx` component library** — `Card`, `Badge`, `SignalRow`, `SignalDrawer`, `Radar`, `TrendChart`, `KPI`, `GenericPage` give the new pages a consistent visual language without new UI primitives.
- **`useLiveData` polling hook** (`frontend/lib/hooks.ts`) — reuse for the new pages' data refresh (30s, visibility-aware per Phase 4 D-01/02).
- **Mapper pattern** (`frontend/lib/api.ts`) — backend-true contract → UI types; new pages consume the same seam.
- **`/health/ready`, `/health/models`, `/health/connectors`** — honest telemetry sources for both the Sources page and start.py's status table.
- **`docker-compose.yml`** — postgres/redis/ollama services already defined with healthchecks; setup.py/start.py orchestrate these rather than redefining them.
- **`OLLAMA_MODEL=gemma3:4b`** config — setup.py's `ollama pull` target; matches `LOCAL_LLM_MODEL`.

### Established Patterns
- **Contract governance:** every new/changed endpoint (D-04, D-06, D-07) MUST flow through `scripts/export_openapi.py` → `contracts/openapi.json` → `frontend/types/api.ts` to keep the contract-drift pytest green.
- **Strict quality gates:** `tsc --noEmit` 0 errors, ESLint flat config 0 errors, `next build` clean, `pytest -v` passing — these gates are what prove a parity-matrix row is WIRED (D-09).
- **Honest telemetry (AGENTS.md):** no fabricated data, no demo-mode labels, WIRED only when genuinely wired (D-05, D-07, D-09, D-15).
- **Hand-rolled minimal client** — no new data-fetching library; new page data flows through the existing `api.ts` + `useLiveData` pattern.
- **Async everything + fail-degrade** — new endpoints follow async SQLAlchemy; never take the whole app down.
- **Section dispatcher** (`frontend/app/[section]/page.tsx`) — new pages register here alongside existing real/placeholder sections.

### Integration Points
- New backend endpoints under `backend/app/api/v1/endpoints/` (confluence, lifecycles, red-team, missing-signals, developments, sources, cache-clear), registered in `backend/app/main.py` (repo has no `router.py`).
- `GET /signals` gains optional filter query params (D-06).
- `frontend/app/[section]/page.tsx` dispatcher + `frontend/components/metaradar.tsx` gain the new page components (replacing `GenericPage` for developments/functions/sources/settings).
- Parity manifest + generator script → `docs/FEATURE_PARITY_MATRIX.md` (D-10).
- `setup.py` and `start.py` at repo root orchestrating `docker compose` + host `uvicorn`/`next dev` + Alembic + seed + `ollama pull` (D-11..D-15).

</code_context>

<specifics>
## Specific Ideas

- **The demo-day on-ramp is start.py:** a single command (`python start.py`) brings up the whole radar on the RTX 3050 demo box with a live status table — that IS the Phase 6 demonstration of the automation workstream.
- **User-locked choices:** parity where data exists (not full doc-page sweep); all placeholders + new doc pages; Sources/Settings = real content + honest controls; new read endpoints for the new pages; wire what maps cleanly; server-side `/signals` filters; real cache-clear endpoint; matrix = doc + test, generated from a manifest with the WIRED/PARTIAL/NOT_WIRED/DEFERRED vocabulary; compose-driven setup with `--skip-models`; start.py = compose DBs + host processes with log capture + status table; host backend with honest provider-chain fallback; NO Celery (APScheduler in-process).
- **Ask Athena already exists** (via `IntelligencePage`) — the `/athena` doc page is not net-new work.

</specifics>

<deferred>
## Deferred Ideas

- **`/briefs` and `/digest` pages** (Narrative Briefs View + Weekly Intelligence Digest) — require new backend digest/compose endpoints not backed by existing tables; deferred to a future phase. Recorded as DEFERRED in the parity matrix.
- **Controls needing new complex backend services** — e.g., any doc control whose wiring requires a new non-trivial service; recorded as NOT_WIRED/DEFERRED in the parity matrix rather than half-built (D-05).
- **No other scope creep** — discussion stayed within phase scope.

</deferred>

---

*Phase: 6-Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers*
*Context gathered: 2026-08-18*