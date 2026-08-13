# Codebase Structure & Directory Layout

**Analysis Date:** 2026-08-13 (Refreshed Post-Stabilization Baseline)

> **Current state:** Active Next.js 16 App Router tree consolidated under `frontend/app/` with canonical generated contract at `frontend/types/api.ts` and legacy pointer at `frontend/src/types/api.ts`. FastAPI backend modularized with async SQLAlchemy 2.0 models, async Alembic migration scaffolding, PII/PHI scrubber (`PIIPHIScrubber`), Red-Team 19-rule registry (`RedTeamNLIService`), and an 18-point `pytest` test suite (`tests/`). Infrastructure container images authored (`backend/Dockerfile`, `frontend/Dockerfile`).

## Repository Layout

```
novonordisk/                    # Repository Root (MetaRadar v5.1.0)
├── AGENTS.md                   # Repository agent process standards & enforcers
├── GEMINI.md                   # Repository Gemini process standards & enforcers
├── CLAUDE.md                   # AI developer guidelines
├── README.md                   # Project overview & quickstart
├── .env.example                # Environment configuration template
├── docker-compose.yml          # Container stack (postgres, redis, backend, frontend, gpu)
├── .github/
│   ├── workflows/ci.yml        # GitHub Actions CI workflow with least-privilege token
│   └── pull_request_template.md # Mandatory pull request template
├── backend/                    # FastAPI Backend (Python 3.11+)
│   ├── Dockerfile              # Multi-stage non-root container image
│   ├── requirements.txt        # Floor-pinned dependencies with pytest & async extensions
│   ├── alembic.ini             # Async Alembic configuration
│   ├── alembic/
│   │   ├── env.py              # Async Alembic runner
│   │   ├── script.py.mako      # Alembic migration script template
│   │   └── versions/
│   │       └── 001_initial_v51_schema.py   # Schema migration (17 tables + vector/pg_trgm + HNSW)
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI application factory & router registration
│       ├── api/
│       │   └── v1/
│       │       ├── __init__.py
│       │       └── endpoints/
│       │           ├── health.py        # /health, /health/ready, /health/models, /health/connectors
│       │           └── signals.py       # /signals, /overview, /athena
│       ├── core/
│       │   ├── config.py                # Pydantic Settings v2 configuration
│       │   └── domain_config.py         # YAML domain configuration loader
│       ├── db/
│       │   └── session.py               # Async SQLAlchemy engine & session factory
│       ├── models/
│       │   └── __init__.py              # 17 SQLAlchemy ORM models
│       ├── schemas/
│       │   └── __init__.py              # Pydantic response/request schemas
│       ├── services/
│       │   ├── deduplication.py         # Fingerprinting & text chunking
│       │   ├── pii.py                   # PIIPHIScrubber regex scrubbing
│       │   └── redteam.py               # RedTeamNLIService with 19-rule registry (Rules A–S)
│       ├── providers/
│       │   ├── base.py                  # LLMProvider base & capability matrix
│       │   ├── gemma.py                 # Local Gemma 3 4B provider
│       │   ├── grok.py                  # Hosted xAI Grok provider with privacy gate
│       │   ├── degraded.py              # Degraded BART fallback provider
│       │   └── factory.py               # ProviderFactory fallback chain
│       └── connectors/
│           └── base.py                  # SourceConnector abstract base class
├── frontend/                   # Next.js 16.3 Frontend
│   ├── Dockerfile              # Multi-stage Node 20 alpine build
│   ├── package.json            # Next 16.3, React 19, Tailwind 4, Framer Motion, Recharts
│   ├── pnpm-lock.yaml          # Pnpm lockfile (minimum-release-age=0)
│   ├── .pnpmrc                 # Local supply-chain policy
│   ├── .nvmrc                  # Node 20 pinned runtime
│   ├── eslint.config.mjs       # Native ESLint 10 flat config (@next/eslint-plugin-next)
│   ├── next.config.mjs         # strict TS check (ignoreBuildErrors: false)
│   ├── app/                    # Active App Router Tree
│   │   ├── layout.tsx          # Root layout
│   │   ├── page.tsx            # Redirects to /dashboard
│   │   ├── [section]/page.tsx  # Dynamic section route dispatcher
│   │   └── globals.css         # CSS-first Tailwind 4 design system
│   ├── components/
│   │   ├── metaradar.tsx       # UI Workspace (Shell, DashboardPage, SignalsPage, etc.)
│   │   └── ui/button.tsx       # Base UI/shadcn button component
│   ├── lib/
│   │   ├── api.ts              # API interface seam
│   │   ├── mock-data.ts        # Synthetic signal fixtures
│   │   └── utils.ts            # clsx & tailwind-merge wrapper
│   ├── types/
│   │   └── api.ts              # CANONICAL OpenAPI generated TypeScript contract
│   └── src/
│       └── types/
│           └── api.ts          # Legacy contract re-export pointer
├── contracts/
│   └── openapi.json            # OpenAPI 3.1 schema snapshot
├── config/
│   └── haemophilia.yaml        # Haemophilia domain specification
├── scripts/
│   └── export_openapi.py       # OpenAPI JSON & TypeScript contract generator
├── tests/                      # Dedicated Backend Pytest Test Suite
│   ├── pytest.ini              # Pytest configuration
│   ├── test_config.py          # Domain config & settings validation
│   ├── test_api_endpoints.py   # FastAPI endpoints verification
│   ├── test_provider_matrix.py # Cases A–F provider matrix fallback tests
│   ├── test_privacy_boundary.py# PII scrubbing & privacy gate bypass prevention
│   ├── test_redteam_behavior.py# Red-Team priority gating, capping, & caching
│   └── test_contract_drift.py  # OpenAPI to TypeScript contract drift validation
└── docs/                       # Specifications & Repository Process Rules
    ├── rules/                  # CANONICAL process standards (ENGINEERING, DOD, WORKFLOW, etc.)
    └── audits/                 # Audits & verification matrix
```