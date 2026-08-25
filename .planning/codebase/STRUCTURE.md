# Codebase Structure

**Analysis Date:** 2026-08-25

## Directory Layout

```
novonordisk/                         # MetaRadar v5.1 monorepo root
├── backend/                         # FastAPI Python backend
│   ├── alembic/                     # Database migrations (env.py + versions/ 001–012)
│   ├── alembic.ini                  # Alembic migration configuration
│   ├── app/
│   │   ├── api/                     # HTTP API layer
│   │   │   ├── deps.py              # Auth and rate-limiting dependencies
│   │   │   └── v1/endpoints/        # 10 REST routers (health, signals, pipeline, etc.)
│   │   ├── connectors/              # External life-science source connectors (5 + base)
│   │   ├── core/                    # App settings, domain YAML parser, logging, middleware
│   │   ├── db/                      # DB session factory, pooling, advisory locks, seeding
│   │   ├── models/                  # SQLAlchemy ORM models in __init__.py
│   │   ├── providers/               # LLM provider implementations (Gemma, Grok, Degraded)
│   │   ├── schemas/                 # Pydantic schemas and DTOs
│   │   ├── services/                # 16 domain business logic services
│   │   ├── workflows/               # LangGraph pipeline (state, graph, runner, 11 nodes)
│   │   └── main.py                  # FastAPI application entry point
│   ├── requirements.txt             # Python dependencies
│   └── Dockerfile                   # Backend container definition
├── frontend/                        # Next.js 16 App Router UI
│   ├── app/                         # App Router pages and global CSS
│   │   ├── [section]/page.tsx       # Dynamic workspace section router
│   │   ├── signals/[signalId]/      # Deep-link signal detail page
│   │   ├── globals.css              # CSS variables, design tokens, light/dark themes
│   │   ├── layout.tsx               # Root HTML shell, fonts, providers
│   │   └── page.tsx                 # Default index redirect
│   ├── components/                  # UI components and domain workspaces
│   │   ├── calibration/             # Probabilistic calibration & reliability UI
│   │   ├── common/                  # Reusable badges, error/empty/loading states
│   │   ├── confluence/              # Multi-source confluence & topic clustering
│   │   ├── contradictions/          # Contradiction detection & evidence conflict UI
│   │   ├── developments/            # Strategic developments & event trackers
│   │   ├── effects/                 # Ambient background & particle effects
│   │   ├── functions/               # Functional tools & pipeline execution widgets
│   │   ├── intelligence/            # Athena multi-evidence synthesis chat & insights
│   │   ├── missing-signals/         # Surveillance gap analysis workspace
│   │   ├── observability/           # System health, connector telemetry, scheduler logs
│   │   ├── settings/                # Domain config viewer & user preferences
│   │   ├── signals/                 # Signal feed, filtering, and detail drawers
│   │   ├── sources/                 # Source connector health & status overview
│   │   ├── theme/                   # Theme toggle and color mode providers
│   │   ├── ui/                      # Base UI / shadcn primitive components
│   │   └── metaradar.tsx            # Main shell component
│   ├── lib/                         # API client, custom hooks, utilities, mappers
│   ├── types/                       # Shared TypeScript types (synced api.ts)
│   ├── package.json                 # Pinned frontend dependencies (pnpm)
│   ├── tsconfig.json                # Strict TypeScript configuration
│   └── eslint.config.mjs            # ESLint flat config
├── config/
│   └── haemophilia.yaml             # Domain single source of truth configuration
├── contracts/
│   └── openapi.json                 # Exported OpenAPI 3.1 contract specification
├── tests/                           # Pytest test suite (25 test files)
├── scripts/                         # Utility scripts (check-banned-classes, export_openapi)
├── docs/                            # Governance, SRS, SDD, UI specs, and process rules
├── data/
│   └── synthetic_signals.json       # Synthetic baseline dataset
├── models/                          # Local GGUF quantized models directory
├── docker-compose.yml               # Multi-container local deployment definition
├── setup.py                         # Environment bootstrapper
├── start.py                         # Unified service orchestrator
├── pytest.ini                       # Test suite runner configuration
├── AGENTS.md                        # AI agent operating standards
└── GEMINI.md                        # Gemini process standards
```

## Directory Details

- **`backend/app/api/v1/endpoints/`**: Router modules for `health`, `signals`, `intelligence`, `registry`, `observability`, `cache`, `pipeline`, `ingestion`, `search`, and `feedback`.
- **`backend/app/connectors/`**: `base.py` (abstract connector interface), `pubmed.py`, `clinical_trials.py`, `fda.py`, `ema.py`, `newsapi.py`.
- **`backend/app/services/`**: 16 dedicated service modules encapsulating domain scoring, vector search, calibration, PII filtering, canonical URL resolution, and routing.
- **`backend/app/workflows/nodes/`**: 11 modular node functions executed in sequence by the LangGraph pipeline runner.
- **`frontend/components/`**: Clean modular domain workspaces eliminating monolithic sprawl.
- **`tests/`**: Centralized test suite testing API contracts, database transactions, provider failovers, privacy boundaries, and LangGraph workflow invariants.
