# Codebase Structure

**Analysis Date:** 2026-08-27

## Directory Layout

```
novonordisk/
├── .github/                        # CI/CD Workflows
│   └── workflows/
│       └── ci.yml                  # Unified GitHub Actions test & build pipeline
├── .planning/                      # GSD Milestone & Architecture Memory
│   ├── PROJECT.md                  # Project charter, vision, and active milestone
│   ├── STATE.md                    # Current execution state and phase history
│   ├── codebase/                   # 7 Structured codebase mapping documents
│   └── phases/                     # Historical and active phase plan directories
├── backend/                        # FastAPI Application & Intelligence Engine
│   ├── alembic/                    # Database migration scripts
│   ├── app/
│   │   ├── api/v1/endpoints/       # REST API route handlers
│   │   │   ├── cache.py            # Cache invalidation endpoints
│   │   │   ├── feedback.py         # Stakeholder calibration feedback endpoints
│   │   │   ├── health.py           # Readiness, models, and connector health endpoints
│   │   │   ├── ingestion.py        # Trigger live connector ingestion
│   │   │   ├── intelligence.py     # Athena Q&A, confluence, contradictions, lifecycles
│   │   │   ├── observability.py    # Ingestion activity streams and telemetry
│   │   │   ├── pipeline.py         # Manual pipeline execution runner
│   │   │   ├── registry.py         # Sources, assets, and companies registry
│   │   │   ├── search.py           # Vector and hybrid semantic search
│   │   │   └── signals.py          # Signal list, detail, 4-question view, review workflow
│   │   ├── connectors/             # Source ingestion adapters
│   │   │   ├── base.py             # Abstract BaseConnector + Bronze persistence
│   │   │   ├── clinical_trials.py  # ClinicalTrials.gov API v2 connector
│   │   │   ├── ema.py              # EMA Medicines RSS feed connector
│   │   │   ├── et_pharma.py        # ET Pharma RSS feed connector
│   │   │   ├── fda.py              # openFDA and MedWatch connector
│   │   │   ├── fierce_pharma.py    # Fierce Pharma RSS feed connector
│   │   │   ├── newsapi.py          # NewsAPI JSON commercial news connector
│   │   │   └── pubmed.py           # NCBI PubMed E-Utilities connector
│   │   ├── core/                   # Global configuration & security
│   │   │   ├── config.py           # Pydantic BaseSettings & env parsing
│   │   │   ├── domain_config.py    # Disease domain configuration loader
│   │   │   ├── logging.py          # Structlog JSON configuration
│   │   │   ├── middleware.py       # Correlation ID ASGI middleware
│   │   │   └── redact.py           # PII/PHI automated log scrubber
│   │   ├── db/                     # Async database sessions & seed data
│   │   │   ├── seed.py             # Database seed data initializer
│   │   │   └── session.py          # Async engine, sessionmaker, and advisory locks
│   │   ├── models/                 # SQLAlchemy 2.0 ORM models
│   │   │   └── __init__.py         # Signal, Evidence, Development, AuditLog, etc.
│   │   ├── providers/              # LLM reasoning providers
│   │   │   ├── base.py             # Abstract LLMProvider interface
│   │   │   ├── degraded.py         # Deterministic factual fallback provider
│   │   │   ├── factory.py          # Provider factory with fallback chain
│   │   │   ├── gemma.py            # Local Ollama Gemma 3 4B provider
│   │   │   └── grok.py             # xAI Grok provider with privacy gate
│   │   ├── schemas/                # Pydantic request/response DTOs
│   │   │   ├── intelligence.py     # Signal, Review, Athena, and Confluence schemas
│   │   │   └── registry.py         # Source and Asset schemas
│   │   ├── services/               # Core business logic services
│   │   │   ├── authority.py        # Source authority calculation
│   │   │   ├── calibration.py      # Stakeholder weight calibration
│   │   │   ├── confluence.py       # Multi-source confluence clustering
│   │   │   ├── deduplication.py    # Content hashing and fingerprinting
│   │   │   ├── embeddings.py       # FastEmbed 384-dim embedding generator
│   │   │   ├── ingestion.py        # Orchestrated source ingestion
│   │   │   ├── pii.py              # PII/PHI regex scrubbing service
│   │   │   ├── provenance_urls.py  # Canonical URL validation & resolution
│   │   │   ├── redteam.py          # Contradiction detection engine (Rules A-S)
│   │   │   ├── routing.py          # Stakeholder routing & escalation rules
│   │   │   ├── scheduler.py        # Background ingestion scheduler
│   │   │   └── scoring.py          # Priority scoring & time-decay engine
│   │   └── workflows/              # LangGraph 11-node intelligence pipeline
│   │       ├── graph.py            # LangGraph state graph definition
│   │       ├── runner.py           # Pipeline runner & state manager
│   │       ├── state.py            # MetaRadarState TypedDict
│   │       └── nodes/              # Pipeline node implementations (11 nodes)
│   ├── Dockerfile                  # Production backend container definition
│   └── requirements.txt            # Python dependencies
├── config/                         # Domain Knowledge Configurations
│   └── haemophilia.yaml            # Haemophilia disease area configuration
├── contracts/                      # OpenAPI 3.1 Schemas
│   └── openapi.json                # Exported backend OpenAPI 3.1 contract
├── frontend/                       # Next.js 16 (App Router) Frontend
│   ├── app/                        # App Router routing tree
│   │   ├── [section]/page.tsx      # Dynamic deep-dive workspace routes
│   │   ├── signals/[signalId]/     # Dedicated Signal Detail Workspace
│   │   ├── globals.css             # Theme custom properties and typography
│   │   ├── layout.tsx              # Root HTML, navigation shell, and theme provider
│   │   └── page.tsx                # Radar Dashboard Overview
│   ├── components/                 # React UI components
│   │   ├── calibration/            # Stakeholder calibration workspace
│   │   ├── common/                 # Reusable UI primitives (DemoOperatorSelector, Badges)
│   │   ├── confluence/             # Confluence radar workspace
│   │   ├── contradictions/         # Red-team contradiction workspace
│   │   ├── developments/           # Asset development timelines workspace
│   │   ├── functions/              # Role-tailored functional review queues
│   │   ├── intelligence/           # Athena clinical Q&A workspace
│   │   ├── missing-signals/        # Regulatory and trial gap detection workspace
│   │   ├── observability/          # Activity stream and connector telemetry workspace
│   │   ├── settings/               # System and LLM settings workspace
│   │   ├── signals/                # Signal cards, lists, and detail view
│   │   ├── sources/                # Source operations and health workspace
│   │   ├── theme/                  # ThemeProvider
│   │   ├── ui/                     # Primitives (buttons, counters, steppers)
│   │   └── metaradar.tsx           # Primary header, navigation bar, and footer
│   ├── lib/                        # Client-side libraries and utilities
│   │   ├── api.ts                  # Typed REST API client
│   │   ├── errors.ts               # ApiError class and error handler
│   │   ├── hooks.ts                # Custom React state hooks
│   │   ├── mappers.ts              # DTO to domain model mappers
│   │   └── utils.ts                # Class merging and formatting utilities
│   ├── public/                     # Static assets and icons
│   ├── types/                      # TypeScript type contracts
│   │   └── api.ts                  # Canonical API contract (synced with openapi.json)
│   ├── Dockerfile                  # Production frontend container definition
│   ├── eslint.config.mjs           # ESLint 10 flat configuration
│   ├── next.config.mjs             # Next.js 16 configuration (Turbopack, strict gates)
│   ├── package.json                # Frontend dependencies and scripts
│   └── tsconfig.json               # Strict TypeScript compiler options
├── scripts/                        # Automation and verification tooling
│   ├── check-banned-classes.mjs    # Linter for banned Tailwind utility classes
│   ├── download_model.py           # HuggingFace / Ollama model downloader
│   ├── export_openapi.py           # Dumps openapi.json & syncs frontend/types/api.ts
│   └── generate_parity_matrix.py   # Computes document-to-code parity matrix
├── tests/                          # Automated backend test suites (139 tests)
│   ├── test_api_endpoints.py
│   ├── test_calibration_service.py
│   ├── test_config.py
│   ├── test_connector_health.py
│   ├── test_contract_drift.py
│   ├── test_ingestion.py
│   ├── test_intelligence_nodes.py
│   ├── test_observability.py
│   ├── test_parity_matrix.py
│   ├── test_privacy_boundary.py
│   ├── test_provenance.py
│   ├── test_redteam_behavior.py
│   ├── test_retrieval.py
│   ├── test_signal_decision_refinement.py
│   ├── test_signal_routing_workflow.py
│   └── test_truthfulness_and_invariants.py
├── setup.py                        # Single-command zero-config environment setup
└── start.py                        # Single-command parallel development runner
```

## Directory Purposes

**`backend/app/api/v1/endpoints/`:**
- Purpose: HTTP controllers and route dispatchers.
- Contains: FastAPI APIRouters validating inputs with Pydantic and invoking domain services.
- Key files: `signals.py`, `intelligence.py`, `health.py`, `observability.py`.

**`backend/app/connectors/`:**
- Purpose: External biomedical and industry news data extractors.
- Contains: Concrete implementations of `BaseConnector` for PubMed, CT.gov, FDA, EMA, NewsAPI, Fierce Pharma, and ET Pharma.
- Key files: `base.py`, `clinical_trials.py`, `pubmed.py`, `fierce_pharma.py`.

**`backend/app/workflows/`:**
- Purpose: LangGraph 11-node competitive intelligence pipeline.
- Contains: Graph state schema (`state.py`), builder (`graph.py`), and execution runner (`runner.py`).
- Key files: `graph.py`, `runner.py`, `nodes/synthesize.py`.

**`frontend/components/`:**
- Purpose: React 19 UI workspaces organized by intelligence domain.
- Contains: 9 dedicated workspace folders plus shared UI primitives.
- Key files: `signals/SignalDetailWorkspace.tsx`, `common/DemoOperatorSelector.tsx`, `metaradar.tsx`.

## Key File Locations

**Entry Points:**
- Backend API: `backend/app/main.py`
- Frontend UI: `frontend/app/layout.tsx`, `frontend/app/page.tsx`
- Setup Launcher: `setup.py`
- Start Launcher: `start.py`

**Configuration:**
- Environment Settings: `backend/app/core/config.py`
- Disease Area Domain: `config/haemophilia.yaml`
- Frontend Build Config: `frontend/next.config.mjs`
- Design Tokens: `frontend/app/globals.css`

**Core Logic:**
- Pipeline Graph: `backend/app/workflows/graph.py`
- Review State Machine & Routing: `backend/app/services/routing.py`, `backend/app/api/v1/endpoints/signals.py`
- Canonical URL Resolution: `backend/app/services/provenance_urls.py`
- Red-Team Engine: `backend/app/services/redteam.py`

**Testing:**
- Pytest Root: `tests/`
- Pytest Configuration: `pytest.ini`
- Banned Classes Linter: `scripts/check-banned-classes.mjs`

## Naming Conventions

**Files:**
- Backend Python modules: `snake_case.py` (e.g. `provenance_urls.py`, `et_pharma.py`)
- Frontend React components: `PascalCase.tsx` (e.g. `DemoOperatorSelector.tsx`, `SignalCard.tsx`)
- Frontend utility & hook files: `camelCase.ts` (e.g. `api.ts`, `mappers.ts`, `hooks.ts`)
- Unit test files: `test_<feature>.py` (e.g. `test_provenance.py`, `test_signal_routing_workflow.py`)

**Directories:**
- Backend packages: `snake_case` (e.g. `api/v1/endpoints`, `workflows/nodes`)
- Frontend component folders: `kebab-case` or `lower_case` (e.g. `missing-signals`, `signals`, `common`)

## Where to Add New Code

**New Ingestion Connector:**
- Implementation: Create `backend/app/connectors/<source_name>.py` inheriting from `BaseConnector`.
- Registration: Register in `backend/app/connectors/__init__.py`, `backend/app/services/scheduler.py`, and `backend/app/api/v1/endpoints/ingestion.py`.
- Health Telemetry: Add source model default in `backend/app/models/__init__.py` and tests in `tests/test_connector_health.py`.

**New Intelligence Workspace:**
- Component: Create `frontend/components/<workspace_name>/<WorkspaceName>Workspace.tsx`.
- Route: Map section in `frontend/app/[section]/page.tsx` and add navigation item in `frontend/components/metaradar.tsx`.

**New Pipeline Node:**
- Implementation: Create `backend/app/workflows/nodes/<node_name>.py`.
- Integration: Add node to `backend/app/workflows/graph.py` and update `MetaRadarState` in `backend/app/workflows/state.py`.
- Tests: Add verification suite in `tests/test_intelligence_nodes.py`.

## Special Directories

**`.planning/`:**
- Purpose: GSD workflow state, project memory, and codebase documentation.
- Generated: Maintained by GSD commands.
- Committed: Yes.

**`contracts/`:**
- Purpose: Contains `openapi.json` generated by `scripts/export_openapi.py`.
- Generated: Yes.
- Committed: Yes.

---

*Structure analysis: 2026-08-27*
