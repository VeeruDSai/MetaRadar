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
│   │   ├── connectors/             # Source ingestion adapters (8 connectors)
│   │   │   ├── base.py             # Abstract BaseConnector + Bronze persistence
│   │   │   ├── biopharma_dive.py   # BioPharma Dive RSS news connector
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
│   │   │   ├── scheduler.py        # Background ingestion scheduler & governor
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
│   │   ├── common/                 # Reusable primitives (DemoOperatorSelector, Badges, Logo)
│   │   ├── confluence/             # Confluence radar workspace
│   │   ├── contradictions/         # Red-team contradiction workspace
│   │   ├── developments/           # Asset development timelines workspace
│   │   ├── effects/                # Shader animations and dynamic visual effects
│   │   ├── functions/              # Role-tailored functional review queues
│   │   ├── intelligence/           # Athena clinical Q&A workspace
│   │   ├── missing-signals/        # Regulatory and trial gap detection workspace
│   │   ├── observability/          # Activity stream and connector telemetry workspace
│   │   ├── settings/               # System configuration and provider workspace
│   │   ├── signals/                # Signal detail, list, explainer, counter-factuals
│   │   ├── sources/                # Source catalog and operations workspace
│   │   ├── theme/                  # Theme switching utilities
│   │   └── ui/                     # Accessible UI primitives (Buttons, Counter, Stepper)
│   ├── lib/                        # Client libraries & utilities
│   │   ├── api.ts                  # Type-safe API client
│   │   ├── errors.ts               # Structured ApiError classes
│   │   ├── mappers.ts              # Contract to UI model mappers
│   │   └── utils.ts                # Class merging and string helpers
│   ├── types/                      # TypeScript type definitions
│   │   └── api.ts                  # Generated & handcrafted DTO contracts
│   ├── Dockerfile                  # Production frontend container definition
│   └── package.json                # Frontend dependencies
├── models/                         # Local weights & README
├── scripts/                        # Automation & verification scripts
│   ├── check-banned-classes.mjs    # CSS token linter
│   ├── export_openapi.py           # Backend contract sync tool
│   ├── download_model.py           # FastEmbed model pre-fetcher
│   └── test_demo_scenarios_e2e.py  # 5-scenario demo journey test harness
├── tests/                          # Automated backend test suites (141 tests)
├── docker-compose.yml              # Local multi-service development compose
├── setup.py                        # Zero-config initial environment installer
└── start.py                        # Single-command dev runner
```

## Directory Purposes

**`backend/app/api/v1/endpoints/`:**
- Purpose: Contains route controllers for all public REST and SSE API endpoints.
- Contains: `signals.py`, `intelligence.py`, `health.py`, `observability.py`, etc.
- Key files: `signals.py`, `intelligence.py`

**`backend/app/connectors/`:**
- Purpose: Houses external data ingestion adapters with Bronze raw record persistence.
- Contains: `pubmed.py`, `clinical_trials.py`, `fda.py`, `ema.py`, `newsapi.py`, `fierce_pharma.py`, `et_pharma.py`, `biopharma_dive.py`.
- Key files: `base.py`

**`backend/app/workflows/`:**
- Purpose: 11-node LangGraph workflow processing raw documents into synthesized competitive signals.
- Contains: `runner.py`, `graph.py`, `state.py`, and `nodes/*.py`.
- Key files: `runner.py`, `nodes/synthesize.py`

**`frontend/components/`:**
- Purpose: React UI components divided into 9 intelligence workspaces and shared primitives.
- Contains: `signals/`, `confluence/`, `contradictions/`, `intelligence/`, `observability/`, etc.
- Key files: `metaradar.tsx`, `signals/SignalDetailWorkspace.tsx`

## Key File Locations

**Entry Points:**
- `backend/app/main.py`: FastAPI server entry point
- `frontend/app/layout.tsx` & `page.tsx`: Next.js shell and root dashboard
- `setup.py`: Zero-config environment setup script
- `start.py`: Multi-service launcher

**Configuration:**
- `config/haemophilia.yaml`: Haemophilia domain configuration
- `backend/app/core/config.py`: Backend settings
- `frontend/next.config.mjs`: Frontend build config

**Core Logic:**
- `backend/app/services/`: Core calculation and intelligence services
- `backend/app/workflows/nodes/`: Discrete LangGraph intelligence nodes
- `frontend/lib/api.ts`: Frontend client communication layer

**Testing:**
- `tests/`: Pytest suite (141 tests)
- `scripts/test_demo_scenarios_e2e.py`: End-to-end scenario verification harness

## Naming Conventions

**Files:**
- React components: `PascalCase.tsx`
- Frontend libraries/hooks: `camelCase.ts`
- Backend Python modules: `snake_case.py`
- Test files: `test_<module>.py`

**Directories:**
- Frontend component folders: `kebab-case` or lowercase (`missing-signals`, `signals`, `common`)
- Backend Python packages: `snake_case` (`api`, `core`, `models`, `services`, `workflows`)

## Where to Add New Code

**New Ingestion Source:**
- Adapter: `backend/app/connectors/<new_source>.py` (inheriting from `SourceConnector`)
- Registration: Register in `backend/app/connectors/__init__.py` and `backend/app/services/ingestion.py`
- Configuration: Add source definition to `config/haemophilia.yaml`
- Tests: Add connector tests to `tests/test_connector_health.py` and `tests/test_ingestion.py`

**New Intelligence Pipeline Step:**
- Node: `backend/app/workflows/nodes/<node_name>.py`
- State: Update `backend/app/workflows/state.py`
- Graph: Register node and edge in `backend/app/workflows/graph.py`
- Tests: Add node unit test in `tests/test_intelligence_nodes.py`

**New Workspace / UI Feature:**
- Workspace Component: `frontend/components/<workspace_name>/<WorkspaceName>Workspace.tsx`
- Navigation: Add tab/route in `frontend/components/metaradar.tsx`
- API client method: Add typed method to `frontend/lib/api.ts`

## Special Directories

**`.planning/`:**
- Purpose: Stores GSD memory, project specifications, roadmap, and phase execution records.
- Generated: Maintained by GSD workflow tools.
- Committed: Yes.

**`contracts/`:**
- Purpose: Canonical OpenAPI 3.1 specification exported from backend schemas.
- Generated: Yes (via `python scripts/export_openapi.py`).
- Committed: Yes.

---

*Structure analysis: 2026-08-27*
