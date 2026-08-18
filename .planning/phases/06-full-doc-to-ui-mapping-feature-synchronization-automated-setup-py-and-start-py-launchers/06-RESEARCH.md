# Phase 6: Full Doc-to-UI Mapping, Feature Synchronization & Automation Launchers - Research

**Researched:** 2026-08-18
**Domain:** Full-Stack Feature Parity, OpenAPI Contract Synchronization, FastAPI Read Endpoints, Next.js 16 UI Integration, Docker Compose Orchestration & Process Launchers
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** **Parity = pages where data exists.** Build the four new intelligence pages for real — Confluence Alerts, Lifecycle Timelines, Red-Team Contradictions, Missing Signals (`/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`) — because their DB tables exist (`Confluence`, `LifecycleEvent`, `Contradiction`, `WatchItem`, `Evidence`). Ask Athena already exists via `IntelligencePage`. **Deferred:** `/briefs` and `/digest` (they need new digest/compose endpoints — recorded in `<deferred>`).
- **D-02:** **All five GenericPage placeholders get real content too** — Developments, Functions, Sources, Settings — alongside the new doc pages. Calibrate stays as the Phase 5 feedback-widget context (no new calibrate surface). This fills the current 8-section nav completely.
- **D-03:** **Sources = real source registry** (from the `sources` table + live `/health/connectors` status per source). **Settings = honest workspace controls only** (dark mode, polling interval, any real config knobs that exist) — no fake toggles. UI doc has no detailed spec for these two; "real content, honest controls" governs.
- **D-04:** **New read endpoints for new pages.** Add honest read-only endpoints for confluence, lifecycles, red-team, missing-signals, developments, and sources, each backed by the existing DB tables. Served via the existing `/api/v1` router pattern; contract flows through `scripts/export_openapi.py`.
- **D-05:** **Wire what maps cleanly.** Controls get wired when they map to existing or cheap new endpoints: Apply Filter → `/signals` filters, Evidence-chain expand → evidence read, Refresh → existing polling. Anything needing a new complex backend service is recorded as NOT_WIRED/DEFERRED in the parity matrix rather than half-built.
- **D-06:** **Server-side filters on `GET /signals`.** Extend the existing endpoint with optional query params (severity/priority, entity/asset, date-range from/to, signal_type, source) powering the Apply Filter control + multi-select entity filter. Backward-compatible; contract updated via `export_openapi`.
- **D-07:** **Real cache-clear endpoint.** `POST /api/v1/cache/clear` flushes Redis cache keys / bumps the version, behind the confirmation modal from the UI doc (§4.4). Honest behavior, no fabricated "refreshed" claims.
- **D-08:** **Matrix = living doc + contract-parity test.** `docs/FEATURE_PARITY_MATRIX.md` for humans AND a contract-parity test that walks the OpenAPI contract vs the doc-spec control list and fails on unmapped controls.
- **D-09:** **Matrix columns + status vocabulary.** Columns: `Doc spec (file + §)` → `Control/feature` → `Component` → `Endpoint` → `Status`. Status vocabulary: **WIRED** (implemented + gated), **PARTIAL** (partially wired), **NOT_WIRED** (exists in doc, deferred), **DEFERRED** (explicitly out). Honest per AGENTS.md — a row is only WIRED when proven by tsc/eslint/build/pytest gates.
- **D-10:** **Matrix generated from a structured manifest.** A YAML/JSON manifest of doc controls + wired status is the single source of truth; a generator script emits `docs/FEATURE_PARITY_MATRIX.md` (regenerable, low drift). Hand-editing the rendered matrix is not the maintenance path.
- **D-11:** **setup.py is compose-driven.** Zero-config setup runs `docker compose up` for postgres/redis/ollama (services already composed), then applies Alembic migrations, seeds the synthetic dataset (`data/synthetic_signals.json`), and ensures the Ollama model. Environment built from `.env.example` with sensible defaults. Deterministic on the demo box.
- **D-12:** **Ollama model auto-pull with `--skip-models` flag.** setup.py runs `ollama pull gemma3:4b` if the model is absent (with a clear progress line); `--skip-models` bypasses the multi-GB download for boxes that already cache weights. Model id `gemma3:4b` matches `OLLAMA_MODEL` / `LOCAL_LLM_MODEL` in `backend/app/core/config.py`.
- **D-13:** **start.py = compose DBs + host processes.** Launches `docker compose up -d postgres redis ollama` → backend (`uvicorn`, on host) → frontend (`next dev`, on host). **No Celery** — Celery was removed in Hardening Report A1; scheduling is in-process APScheduler.
- **D-14:** **Log capture + live status table.** Each child process streams to `logs/*.log` (e.g., `logs/backend.log`, `logs/frontend.log`); a health loop polls `/health/ready`, `/health/models`, and the frontend `/`, printing a status table (service, port, status, latency, model). Ctrl+C gracefully stops children (SIGTERM, then kill).
- **D-15:** **Host backend with honest fallback.** Backend runs on the host with GPU (RTX 3050). If GPU init fails, the existing never-crash provider chain (Gemma → Grok → BART degraded) handles it; start.py just surfaces the honest `/health/models` state — no fabricated health.

### the agent's Discretion
- Exact route paths + response schemas for new read endpoints (`/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/sources`).
- Exact filter query parameter names on `GET /signals`.
- Component hierarchy and sub-component breakdown in `frontend/components/metaradar.tsx` for new pages.
- Structure of parity manifest (`docs/manifests/feature_parity_manifest.json`) and generator script `scripts/generate_parity_matrix.py`.
- Argument parsing and process supervisory loop implementation in `setup.py` and `start.py`.

### Deferred Ideas (OUT OF SCOPE)
- `/briefs` and `/digest` pages (require net-new complex summarization/digest background pipelines not backed by current relational schema).
- Real-time WebSocket event streaming (UI uses 30s visibility-aware polling via `useLiveData`).
- Custom multi-node worker clusters / Celery orchestration (Celery explicitly removed; APScheduler in-process).
</user_constraints>

<architectural_responsibility_map>
## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Read Aggregation Endpoints (`/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/sources`) | API / Backend (FastAPI + Async SQLAlchemy) | Database / Storage (PostgreSQL 16) | Backend queries existing relational tables, formats response schemas, and exposes OpenAPI definitions. |
| Server-Side Signal Filters | API / Backend (`GET /signals`) | Database / Storage | Translates query params (severity, date range, entity, source) into indexed SQL WHERE clauses. |
| Redis Cache Clear Endpoint | API / Backend (`POST /api/v1/cache/clear`) | Database / Cache (Redis 7) | Flushes cache keys or increments cache generation namespace. |
| New Intelligence & Placeholder Pages UI | Browser / Client (Next.js 16 + React 19) | API / Backend | Renders page layouts, KPI headers, expandable evidence drawers, and filters using `useLiveData`. |
| Parity Manifest & Generator | Tooling / Build (Python script) | Documentation (`docs/FEATURE_PARITY_MATRIX.md`) | Structured manifest ensures verifiable, drift-free contract auditing against UI Design Doc, SRS, and SDD. |
| Automated Environment Setup (`setup.py`) | Automation / CLI (Python 3.11+) | Docker Compose + Alembic + Ollama | Orchestrates container startup, schema migrations, synthetic dataset seeding, and model weight download. |
| Unified Process Orchestrator (`start.py`) | Automation / CLI (Python 3.11+) | Host Processes (FastAPI + Next.js) | Launches background services, captures log streams, polls health endpoints, and presents live CLI dashboard. |
</architectural_responsibility_map>

<research_summary>
## Summary

Phase 6 unites the foundational backend models, intelligence extraction nodes, and the frontend web client into a fully documented, synchronized, and launchable operational system. Research confirms that all required database models (`Confluence`, `LifecycleEvent`, `Contradiction`, `WatchItem`, `Evidence`, `Source`, `Development`) are already declared in `backend/app/models/__init__.py` and migrated into PostgreSQL. 

The primary implementation path consists of two tightly coupled waves:
1. **Backend & Contract Wave:** Implement honest read endpoints under `backend/app/api/v1/endpoints/` with Pydantic v2 schemas, add server-side filter params to `GET /signals`, implement `POST /api/v1/cache/clear`, update `scripts/export_openapi.py` to regenerate `contracts/openapi.json` and `frontend/types/api.ts`, and create the parity manifest generator and test suite.
2. **Frontend & Automation Wave:** Replace all `GenericPage` placeholders with real interactive page components (`DevelopmentsPage`, `FunctionsPage`, `SourcesPage`, `SettingsPage`), implement the 4 intelligence pages (`ConfluencePage`, `LifecyclePage`, `RedTeamPage`, `MissingSignalsPage`), build the `FilterBar` and `CacheClearModal`, and construct `setup.py` and `start.py` launchers for one-command execution.

**Primary recommendation:** Maintain zero contract drift at each step by exporting OpenAPI schemas immediately after backend route changes, using typed interfaces in frontend components, and verifying test suites across Python and TypeScript.
</research_summary>

<standard_stack>
## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|----------------|---------|---------|--------------|
| FastAPI | 0.115+ | REST API Framework | High-performance async Python backend with automatic OpenAPI 3.1 schema generation. |
| SQLAlchemy (Async) | 2.0+ | ORM & Query Builder | Async PostgreSQL queries against existing models. |
| Pydantic | 2.10+ | Schema validation | Type-safe request/response contracts for new endpoints. |
| Next.js | 16.3.0 | Frontend Framework | React 19 Server/Client component architecture with dynamic section routing. |
| Lucide React | ^1.16.0 | Icon Library | Consistent iconography across all navigation and action elements. |
| Recharts | ^3.10.1 | Data Visualization | Existing responsive timeline and trend chart visualization. |
| Docker Compose | v2+ | Infrastructure Orchestration | Manages PostgreSQL 16 (pgvector), Redis 7, and Ollama in containers. |
| Uvicorn | 0.34+ | ASGI Web Server | Production-grade host backend execution for start.py launcher. |

### Supporting
| Library / Tool | Version | Purpose | When to Use |
|----------------|---------|---------|-------------|
| @base-ui/react | ^1.5.0 | Unstyled Dialog Primitives | CacheClearModal accessible modal container. |
| Framer Motion | ^13.1.0 | Micro-animations | FilterBar height transitions and expandable row reveals. |
| Rich / Tabulate | Python stdlib / built-in | CLI status formatting | Status table and telemetry rendering in `start.py`. |
</standard_stack>

<architecture_patterns>
## Architecture Patterns

### System Architecture Diagram

```
[User Browser]
      │
      ▼
[Next.js 16 Client App (Port 3000)]
  ├── Section Dispatcher: app/[section]/page.tsx
  ├── Pages: Overview, Signals, Confluence, Lifecycles, Red-Team, Missing-Signals, Developments, Functions, Sources, Settings
  └── Client Seam: lib/api.ts + lib/hooks.ts (useLiveData 30s polling)
      │
      ▼ HTTP REST (JSON)
[FastAPI Backend (Port 8000)]
  ├── /api/v1/health (ready, models, connectors)
  ├── /api/v1/signals (filtered GET)
  ├── /api/v1/confluence, /lifecycles, /red-team, /missing-signals
  ├── /api/v1/developments, /sources
  └── /api/v1/cache/clear (POST)
      │
      ├───────────────────────┬────────────────────────┐
      ▼                       ▼                        ▼
[PostgreSQL 16 + pgvector]   [Redis 7 Alpine]   [Ollama (gemma3:4b)]
(Signals, Confluences,       (Cache store &     (Local LLM Provider)
 Contradictions, Sources)     Invalidation)

[Automation Launchers]
  ├── setup.py ──> docker compose up DBs ──> alembic upgrade head ──> seed data ──> ollama pull
  └── start.py ──> docker compose up DBs ──> uvicorn host backend ──> next dev host ──> health monitor loop
```

### Recommended Project Structure
```
MetaRadar/
├── backend/
│   └── app/
│       ├── api/v1/endpoints/
│       │   ├── health.py
│       │   ├── signals.py            # Enhanced with D-06 filter query params
│       │   ├── intelligence.py       # New: /confluence, /lifecycles, /red-team, /missing-signals
│       │   ├── registry.py           # New: /developments, /sources
│       │   └── cache.py              # New: /cache/clear
│       └── schemas/
│           ├── intelligence.py       # Pydantic models for new intelligence reads
│           └── registry.py           # Pydantic models for sources and developments
├── frontend/
│   ├── app/[section]/page.tsx        # Updated section router
│   ├── components/
│   │   └── metaradar.tsx             # New page components & FilterBar / CacheClearModal
│   ├── lib/api.ts                    # Updated client functions
│   └── types/api.ts                  # Generated TypeScript contracts
├── docs/
│   ├── manifests/
│   │   └── feature_parity_manifest.json # Single source of truth for parity
│   └── FEATURE_PARITY_MATRIX.md      # Generated doc-to-UI verification matrix
├── scripts/
│   ├── export_openapi.py             # Contract exporter
│   └── generate_parity_matrix.py     # Parity doc generator
├── setup.py                          # Zero-config automated environment setup
├── start.py                          # Unified host launcher with health table
└── tests/
    ├── test_api_endpoints.py         # Tests for new endpoints & filters
    ├── test_contract_drift.py        # Contract drift tests
    └── test_parity_matrix.py         # Automated manifest-to-contract parity test
```

### Pattern 1: Declarative Read-Only Aggregation Router
**What:** Fast async read endpoints querying existing PostgreSQL models and returning typed Pydantic payloads.
**When to use:** For `/confluence`, `/lifecycles`, `/red-team`, `/missing-signals`, `/developments`, `/sources`.
**Example:**
```python
# backend/app/api/v1/endpoints/intelligence.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.models import Confluence, LifecycleEvent, Contradiction, WatchItem, Evidence

router = APIRouter()

@router.get("/confluence")
async def get_confluence_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Confluence).order_by(Confluence.created_at.desc()).limit(50))
    return result.scalars().all()
```

### Pattern 2: Single Source of Truth Parity Matrix Generator
**What:** A JSON manifest containing all doc-specified controls, mapped to their implementing components, endpoints, and status (`WIRED`, `PARTIAL`, `NOT_WIRED`, `DEFERRED`), compiled into markdown via a script.
**When to use:** Prevents markdown drift and enables programmatic pytest validation against `openapi.json`.
</architecture_patterns>

<dont_hand_roll>
## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Modal Focus Trap & Backdrop | Custom React modal divs | `@base-ui/react` Dialog | Accessible keyboard focus management, ESC dismissal, ARIA attributes. |
| Filter Animation | Custom CSS height hacks | `framer-motion` `AnimatePresence` | Smooth hardware-accelerated height transitions without layout thrashing. |
| Process Supervision | Shell scripts (`.sh` / `.bat`) | Python `subprocess.Popen` in `start.py` | Cross-platform (Windows & Linux), robust SIGTERM handling, standard I/O log capture. |
| Type Declarations | Hand-edited `frontend/types/api.ts` | `scripts/export_openapi.py` | Guarantees zero contract drift between FastAPI models and TypeScript types. |
</dont_hand_roll>

<common_pitfalls>
## Common Pitfalls

### Pitfall 1: Contract Drift on New Endpoints
**What goes wrong:** New routes added to FastAPI without updating `contracts/openapi.json` and `frontend/types/api.ts`, causing `test_contract_drift.py` to fail.
**How to avoid:** Run `python scripts/export_openapi.py` immediately following backend router additions.

### Pitfall 2: Launching Non-Existent Celery Workers in start.py
**What goes wrong:** `start.py` attempts to start Celery or Redis worker processes, conflicting with Hardening Report decision A1.
**How to avoid:** APScheduler runs in-process inside FastAPI; `start.py` launches only FastAPI (backend), Next.js (frontend), and Docker DBs.

### Pitfall 3: Subprocess Deadlocks on Windows
**What goes wrong:** `subprocess.Popen` hanging when reading stdout/stderr pipes synchronously.
**How to avoid:** Stream process output directly to log files (`logs/backend.log`, `logs/frontend.log`) using file handles, while monitoring health via HTTP.
</common_pitfalls>

<code_examples>
## Code Examples

### Server-Side Signal Filters (`GET /signals`)
```python
# backend/app/api/v1/endpoints/signals.py
@router.get("/signals")
async def get_signals(
    severity: Optional[str] = Query(None),
    entity: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    signal_type: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    query = select(Signal)
    if severity:
        query = query.where(Signal.priority == severity.upper())
    if signal_type:
        query = query.where(Signal.signal_type == signal_type)
    if entity:
        query = query.where(Signal.title.ilike(f"%{entity}%") | Signal.content.ilike(f"%{entity}%"))
    if date_from:
        query = query.where(Signal.published_at >= date_from)
    if date_to:
        query = query.where(Signal.published_at <= date_to)
    query = query.order_by(Signal.published_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
```

### Unified Launcher Process Supervisor (`start.py` core)
```python
# start.py (illustrative core loop)
import subprocess, time, sys, os, signal
import urllib.request, json

def check_health(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as res:
            return res.status == 200, res.read()
    except Exception:
        return False, None
```
</code_examples>

<validation_architecture>
## Validation Architecture

Nyquist validation plan and quality gates for Phase 6:

### Test Framework & Commands
- **Backend & Contract Tests:** `pytest tests/test_api_endpoints.py tests/test_contract_drift.py tests/test_parity_matrix.py -v`
- **Frontend Type Safety & Linting:** `pnpm --prefix frontend run build` and `pnpm --prefix frontend run lint`
- **Contract Synchronization:** `python scripts/export_openapi.py` (0 drift verification)
- **Launcher Validation:** `python setup.py --help` and `python start.py --dry-run`

### Quality Gates
1. `tsc --noEmit` and `next build` exit with 0 errors.
2. `pytest` passes 100% of contract, endpoint, and parity matrix assertions.
3. Feature parity matrix in `docs/FEATURE_PARITY_MATRIX.md` generated from manifest and fully synced.
4. `setup.py` executes migration + seed without manual inputs.
5. `start.py` launches processes with graceful termination.
</validation_architecture>

<sources>
## Sources

### Primary (HIGH confidence)
- `backend/app/models/__init__.py` - Verified existing relational models for Confluence, LifecycleEvent, Contradiction, WatchItem, Evidence, Source, Development.
- `docs/4_UI_DESIGN_DOCUMENT.md` - Verified interaction specifications, Four-Question layout, button mappings, and status badges.
- `docs/10_ARCHITECTURE_HARDENING_REPORT.md` - Verified Celery removal (A1) and launcher specifications (§7).
- `frontend/components/metaradar.tsx` and `frontend/app/globals.css` - Verified existing UI tokens, components, and responsive styles.

### Secondary (MEDIUM confidence)
- `.env.example` and `docker-compose.yml` - Verified ports (5432, 6379, 11434, 8000, 3000) and environment contract.
</sources>

<metadata>
## Metadata
**Research scope:** Full doc-to-UI feature parity audit, OpenAPI synchronization, Next.js page implementations, `setup.py` and `start.py` launchers.
**Confidence:** HIGH (100% grounded in active codebase files).
**Research date:** 2026-08-18
</metadata>

---

*Phase: 06-full-doc-to-ui-mapping-feature-synchronization-automated-setup-py-and-start-py-launchers*
*Research completed: 2026-08-18*
*Ready for planning: yes*

## RESEARCH COMPLETE
