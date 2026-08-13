<!-- refreshed: 2026-08-13 -->
# Architecture Specification & System Topology

**Analysis Date:** 2026-08-13 (Refreshed Post-Stabilization Baseline)

> **Current state:** Active Next.js 16 frontend under `frontend/app/` with strict TypeScript checking (`typescript: { ignoreBuildErrors: false }`), ESLint 10 flat config, Tailwind 4, Framer Motion, and Base UI/shadcn components. FastAPI backend (`backend/app/`) with Pydantic v2 schemas, async SQLAlchemy 2.0 ORM, async Alembic migration scaffolding, PII/PHI scrubber (`PIIPHIScrubber`), Red-Team 19-rule registry (`RedTeamNLIService`), LLM provider capability matrix (Local Gemma -> Grok fallback -> Degraded BART), and an 18-point `pytest` test suite. OpenAPI TypeScript contract is unified and auto-generated at `frontend/types/api.ts` with 0-diff drift validation. Dockerfiles authored for backend and frontend.

## System Topology & Architecture Diagram

```text
┌────────────────────────────────────────────────────────────────────┐
│            Next.js 16.3 Frontend (App Router, Tailwind 4)           │
│  frontend/app/layout.tsx · app/page.tsx (→ /dashboard)             │
│  frontend/app/[section]/page.tsx (dynamic route dispatcher)         │
│  frontend/components/metaradar.tsx ('use client' UI components)    │
│  frontend/types/api.ts (Canonical OpenAPI generated contract)      │
└──────────────────────────────┬─────────────────────────────────────┘
                               │   /api/v1 (REST, JSON) — CORS :3000
                               ▼
┌────────────────────────────────────────────────────────────────────┐
│                  FastAPI Backend Architecture (v5.1.0)              │
│  backend/app/main.py — FastAPI app factory + CORS                   │
│  backend/app/api/v1/endpoints/ — /health, /signals, /overview, /athena │
│  backend/app/core/config.py — pydantic-settings Settings            │
│  backend/app/core/domain_config.py — YAML config loader             │
│  backend/app/db/session.py — async SQLAlchemy engine                │
│  backend/app/models/__init__.py — SQLAlchemy ORM schema             │
│  backend/app/services/pii.py — PIIPHIScrubber regex service         │
│  backend/app/services/redteam.py — RedTeamNLIService (Rules A–S)    │
│  backend/app/services/deduplication.py — Fingerprinting & chunking │
│  backend/app/providers/ — LLM provider abstraction & fallback chain │
│  backend/app/connectors/base.py — SourceConnector interface         │
└──────────┬──────────────────────────┬──────────────────────────────┘
           │ asyncpg                  │ redis.asyncio
           ▼                          ▼
┌──────────────────────┐   ┌──────────────────────┐
│ PostgreSQL 16 +      │   │ Redis 7              │
│ pgvector (pg16 image)│   │ (docker-compose.yml) │
│ + HNSW vector index  │   │ /0 db                │
└──────────────────────┘   └──────────────────────┘
```

## Component Matrix

### Backend Components

| Component | File Path | Responsibility |
|---|---|---|
| FastAPI Application | `backend/app/main.py` | App factory, CORS middleware, lifespan events, router mounting |
| Application Settings | `backend/app/core/config.py` | Environment-driven `Settings` using Pydantic Settings v2 |
| Domain Config Loader | `backend/app/core/domain_config.py` | YAML loader & validator for asset, signal, & routing configuration |
| Database Session | `backend/app/db/session.py` | Async SQLAlchemy 2.0 engine, pool configuration, advisory locks |
| ORM Models | `backend/app/models/__init__.py` | 17 SQLAlchemy models with timezone-aware datetimes and metadata |
| Pydantic Schemas | `backend/app/schemas/__init__.py` | Pydantic response/request models with UTC datetime defaults |
| Health Diagnostics | `backend/app/api/v1/endpoints/health.py` | Honest `/health`, `/health/ready`, `/health/models`, `/health/connectors` |
| Signals & Athena API | `backend/app/api/v1/endpoints/signals.py` | Endpoints for `/signals`, `/overview`, and `/athena` |
| PII / PHI Scrubber | `backend/app/services/pii.py` | Regex scrubbing for raw/nested PII & data classification |
| Red-Team Optimizer | `backend/app/services/redteam.py` | 19-rule contradiction evaluation (Rules A–S) with priority gating |
| Deduplication | `backend/app/services/deduplication.py` | Fingerprinting (pmid, nct, reg, sha256) & 256-token chunking |
| Provider Chain | `backend/app/providers/*.py` | Local Gemma -> Grok fallback -> Degraded BART provider matrix |
| Alembic Scaffold | `backend/alembic/env.py` | Async Alembic migration engine scaffold |

### Frontend Components

| Component | File Path | Responsibility |
|---|---|---|
| Root Layout | `frontend/app/layout.tsx` | HTML shell, font declarations, theme provider |
| Section Dispatcher | `frontend/app/[section]/page.tsx` | Dynamic App Router dispatcher for all top-level sections |
| Workspace Shell & Pages | `frontend/components/metaradar.tsx` | Client workspace (`Shell`, `DashboardPage`, `SignalsPage`, etc.) |
| Canonical Contract | `frontend/types/api.ts` | Auto-generated OpenAPI TypeScript contract |
| Legacy Contract Pointer | `frontend/src/types/api.ts` | Re-exports from `frontend/types/api.ts` |
| Design System | `frontend/app/globals.css` | CSS-first Tailwind 4 design system with `@theme inline` tokens |
| Lint Config | `frontend/eslint.config.mjs` | Native ESLint 10 flat config with `@next/eslint-plugin-next` |

## Data Flow & Contract Pipeline

```
Backend Pydantic Schemas (backend/app/schemas/__init__.py)
  │
  ▼
FastAPI OpenAPI Generator (app.openapi())
  │
  ▼
scripts/export_openapi.py
  ├──> contracts/openapi.json
  └──> frontend/types/api.ts (Canonical Contract)
          ▲
          └── frontend/src/types/api.ts (Re-export Pointer)
```

## Quality & Security Enforcement

- **Strict Type Checking**: `frontend/next.config.mjs` enforces `typescript: { ignoreBuildErrors: false }`.
- **Flat Lint Config**: `frontend/eslint.config.mjs` enforces ESLint 10 flat rules across the frontend codebase.
- **Backend Test Suite**: 18-point `pytest` suite tests configuration, API endpoints, provider matrix, PII scrubbing, privacy gate bypass prevention, Red-Team gating, and contract drift.
- **Continuous Integration**: `.github/workflows/ci.yml` runs `pytest -v`, verifies contract sync, and executes frontend `tsc`, `lint`, and `build` gates with least-privilege `permissions: contents: read`.