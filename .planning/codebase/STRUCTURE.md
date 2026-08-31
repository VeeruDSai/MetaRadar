# Codebase Structure

**Analysis Date:** 2026-09-01

## Directory Layout

```
MetaRadar/
├── backend/                  # FastAPI Backend Service
│   ├── alembic/              # Database migration scripts & env.py
│   │   └── versions/         # Migration versions (DDL scripts)
│   ├── app/                  # Application core package
│   │   ├── api/              # API layer & versioned route endpoints
│   │   │   └── v1/endpoints/ # Router modules (health, signals, auth, search, etc.)
│   │   ├── connectors/       # Data ingestion connectors (PubMed, FDA, EMA, News)
│   │   ├── core/             # Configuration, logging, security, and middleware
│   │   ├── data/             # Synthetic reference data & seeds
│   │   ├── db/               # SQLAlchemy async engine, session, and seed runner
│   │   ├── models/           # Declarative database models (Postgres + pgvector)
│   │   ├── providers/        # LLM inference providers (Gemma GGUF, Grok, BART)
│   │   ├── schemas/          # Pydantic v2 validation models & request/responses
│   │   ├── services/         # Business logic (scoring, calibration, redteam, vector)
│   │   └── workflows/        # LangGraph 11-node intelligence pipeline & nodes
│   ├── Dockerfile            # Container definition for backend service
│   └── requirements.txt      # Python dependencies
├── frontend/                 # Next.js 16 + React 19 Frontend Application
│   ├── app/                  # Next.js App Router (layout, pages, dynamic routes)
│   │   ├── [section]/        # Dynamic section router (dashboard, calibration, etc.)
│   │   └── signals/          # Signal feed & detailed individual signal pages
│   ├── components/           # UI components, workspaces, widgets, and shaders
│   │   ├── auth/             # Persona switcher & authentication UI
│   │   ├── calibration/      # Stakeholder weight calibration workspace
│   │   ├── common/           # Shared badges, logos, drawers, empty states
│   │   ├── confluence/       # Multi-source confluence workspace
│   │   ├── contradictions/   # Medical claim contradiction detector
│   │   ├── developments/     # Asset development lifecycle timeline
│   │   ├── effects/          # Star-portal WebGL / Canvas shader buttons
│   │   ├── intelligence/     # Ask Athena LLM reasoning chat workspace
│   │   ├── observability/    # Activity stream & system health monitoring
│   │   ├── signals/          # Signal cards, score explainers, red team widgets
│   │   └── ui/               # Base UI primitives, counters, animated elements
│   ├── context/              # React context providers (AuthContext)
│   ├── lib/                  # REST API client, error handlers, custom hooks, utils
│   ├── public/               # Static assets & SVG icons
│   ├── types/                # TypeScript interface definitions (api.ts)
│   ├── Dockerfile            # Container definition for frontend service
│   ├── package.json          # Node dependencies and scripts
│   └── tsconfig.json         # TypeScript configuration
├── config/                   # Domain configuration & disease ontology (haemophilia.yaml)
├── contracts/                # OpenAPI canonical contract (openapi.json)
├── models/                   # Local GGUF model binaries (Gemma 3 4B)
├── scripts/                  # Utilities, parity checkers, migration runners
├── tests/                    # Pytest test suite (unit, integration, e2e, RBAC)
├── .planning/                # GSD project plans, roadmap, state, and codebase map
├── docker-compose.yml        # Multi-container local orchestration
├── setup.py                  # Zero-config environment setup automation
└── start.py                  # Unified process runner with real-time telemetry
```

## Directory Purposes

**`backend/app/api/v1/endpoints/`:**
- Purpose: HTTP request routing and API parameter serialization.
- Contains: Route handlers for signals (`signals.py`), search (`search.py`), authentication (`auth.py`), ingestion (`ingestion.py`), observability (`observability.py`), feedback (`feedback.py`), intelligence (`intelligence.py`), pipeline (`pipeline.py`), registry (`registry.py`), cache (`cache.py`), health (`health.py`).
- Key files: `signals.py`, `intelligence.py`, `ingestion.py`.

**`backend/app/connectors/`:**
- Purpose: External API integration and web scrapers for biomedical data sources.
- Contains: Base connector class and source-specific fetching logic with rate limiting and retry handling.
- Key files: `pubmed.py`, `clinical_trials.py`, `fda.py`, `ema.py`, `newsapi.py`, `biopharma_dive.py`, `et_pharma.py`, `fierce_pharma.py`.

**`backend/app/workflows/nodes/`:**
- Purpose: 11 LangGraph intelligence pipeline node implementations.
- Contains: Transformation nodes that process raw incoming signals into structured gold signals.
- Key files: `ingest.py`, `validate.py`, `embed.py`, `nlp_extract.py`, `ontology.py`, `confluence.py`, `lifecycle.py`, `redteam.py`, `missing_signal.py`, `synthesize.py`, `calibrate.py`.

**`backend/app/services/`:**
- Purpose: Core algorithms, domain math, and background task execution.
- Contains: FastEmbed vector embedding (`embeddings.py`), stakeholder scoring (`scoring.py`, `calibration.py`), deduplication (`deduplication.py`), scheduler (`scheduler.py`), vector query (`vector_query.py`), domain config (`domain_config.py`), PII scrubbing (`pii.py`), provenance (`provenance_urls.py`), redteam (`redteam.py`), confluence (`confluence.py`), auth (`auth_service.py`).
- Key files: `scheduler.py`, `calibration.py`, `vector_query.py`.

**`frontend/components/`:**
- Purpose: Domain-specific UI workspaces and interactive modules.
- Contains: Workspaces for signals, calibration, confluence, contradictions, Athena intelligence, observability, and settings.
- Key files: `metaradar.tsx`, `intelligence/AthenaWorkspace.tsx`, `signals/SignalCard.tsx`.

## Key File Locations

**Entry Points:**
- Backend API: `backend/app/main.py`
- Frontend Shell: `frontend/app/layout.tsx` & `frontend/app/page.tsx`
- Process Runner: `start.py`
- Setup Script: `setup.py`

**Configuration:**
- Backend Settings: `backend/app/core/config.py`
- Disease Area & Ontology: `config/haemophilia.yaml`
- Frontend Next Config: `frontend/next.config.mjs`
- Database Migrations: `backend/alembic.ini`

**Core Logic & Workflows:**
- LangGraph Pipeline Graph: `backend/app/workflows/graph.py`
- LLM Provider Factory: `backend/app/providers/factory.py`
- Vector Embeddings: `backend/app/services/embeddings.py`

**Testing & Contracts:**
- Python Tests: `tests/` (30 test files)
- OpenAPI Contract: `contracts/openapi.json`
- Frontend Banned Classes Check: `scripts/check-banned-classes.mjs`
- Schema Parity Check: `scripts/generate_parity_matrix.py`

## Naming Conventions

**Files:**
- Backend Python: `snake_case.py` (e.g., `vector_query.py`, `domain_config.py`)
- Frontend Components: `PascalCase.tsx` (e.g., `SignalCard.tsx`, `AthenaWorkspace.tsx`)
- Frontend Utilities & Hooks: `camelCase.ts` (e.g., `api.ts`, `hooks.ts`, `utils.ts`)
- Configuration / Domain YAML: `snake_case.yaml` (e.g., `haemophilia.yaml`)

**Directories:**
- Backend: `snake_case` (e.g., `backend/app/api/v1/endpoints/`)
- Frontend Components: `kebab-case` (e.g., `components/missing-signals/`, `components/effects/star-portal/`)

## Where to Add New Code

**New Ingestion Connector:**
- Connector Implementation: `backend/app/connectors/[source_name].py` (subclass `BaseConnector` from `base.py`)
- Register in Connector Registry: `backend/app/api/v1/endpoints/registry.py` & `backend/app/services/scheduler.py`
- Connector Test: `tests/test_ingestion.py`

**New API Endpoint / Feature:**
- Route Handler: `backend/app/api/v1/endpoints/[feature].py`
- Mount Router: `backend/app/main.py`
- Pydantic Schema: `backend/app/schemas/[feature].py`
- Business Logic: `backend/app/services/[feature].py`
- Frontend TypeScript Type: `frontend/types/api.ts`
- Frontend API Client Call: `frontend/lib/api.ts`
- Frontend UI Component: `frontend/components/[feature]/[Feature]Workspace.tsx`
- Backend Test: `tests/test_[feature].py`

**New Intelligence Pipeline Node:**
- Node Function: `backend/app/workflows/nodes/[node_name].py`
- Wire in Graph: `backend/app/workflows/graph.py`
- State Definition: `backend/app/workflows/state.py`
- Pipeline Test: `tests/test_intelligence_nodes.py`

## Special Directories

**`models/`:**
- Purpose: Stores local GGUF quant models (e.g. `gemma-3-4b-it-Q4_K_M.gguf`).
- Generated: Downloaded via `setup.py --download-model` or `scripts/download_model.py`.
- Committed: No (gitignored, contains large binary files >2 GB).

**`logs/`:**
- Purpose: Local runtime execution logs for backend and frontend.
- Generated: Created automatically by `start.py`.
- Committed: No (gitignored).

**`.planning/`:**
- Purpose: GSD workflow planning artifacts, roadmap, execution state, and codebase map.
- Generated: Created and maintained by GSD commands.
- Committed: Yes (persists project memory across sessions).

---

*Structure analysis: 2026-09-01*