# Codebase Structure (STRUCTURE.md)

**Project:** MetaRadar — Autonomous Decision Intelligence Platform  
**Milestone:** v5.2  
**Last Updated:** 2026-08-27  

---

## 1. Directory Tree Overview

```
novonordisk/
├── backend/                        # FastAPI Backend Application
│   ├── app/
│   │   ├── api/v1/endpoints/       # REST API Route Handlers
│   │   │   ├── signals.py          # Signal list, detail, review, audit history
│   │   │   ├── athena.py           # Clinical reasoning Q&A + SSE streaming
│   │   │   ├── confluence.py       # Multi-source confluence alerts
│   │   │   ├── red_team.py         # Contradiction evaluations
│   │   │   ├── health.py           # Ready, models, connectors telemetry
│   │   │   ├── sources.py          # Source registry and health
│   │   │   └── calibration.py      # Stakeholder weight adjustments
│   │   ├── connectors/             # Source Ingestion Adapters
│   │   │   ├── base.py             # Abstract base connector + bronze persistence
│   │   │   ├── pubmed.py           # NCBI PubMed E-Utilities
│   │   │   ├── clinical_trials.py  # ClinicalTrials.gov API v2
│   │   │   ├── fda.py              # openFDA + FDA RSS
│   │   │   ├── ema.py              # EMA Medicines RSS
│   │   │   ├── newsapi.py          # NewsAPI JSON adapter
│   │   │   ├── fierce_pharma.py    # Fierce Pharma RSS adapter
│   │   │   └── et_pharma.py        # ET Pharma RSS adapter
│   │   ├── core/                   # Configuration & Domain Models
│   │   │   ├── config.py           # Environment settings
│   │   │   └── domain_config.py    # Pydantic models for haemophilia.yaml
│   │   ├── db/                     # Database Session & Migrations
│   │   │   ├── session.py          # AsyncSession & advisory locks
│   │   │   └── base.py             # Declarative base
│   │   ├── models/                 # SQLAlchemy 2.0 ORM Models
│   │   │   └── __init__.py         # Signal, Evidence, Development, AuditLog, Source, etc.
│   │   ├── services/               # Domain Business Logic
│   │   │   ├── provenance_urls.py  # Canonical URL construction & validation
│   │   │   ├── routing.py          # Stakeholder function routing & escalation
│   │   │   ├── scheduler.py        # Autonomous background ingestion scheduler
│   │   │   ├── deduplication.py    # Fingerprint generation & deduplication
│   │   │   ├── pii.py              # PII/PHI scrubbing regex engine
│   │   │   └── scoring.py          # Deterministic priority scoring formula
│   │   └── workflows/              # LangGraph Intelligence Pipeline
│   │       ├── graph.py            # 11-node graph definition
│   │       ├── runner.py           # Pipeline runner & state manager
│   │       └── nodes/              # Individual pipeline node implementations
│   └── requirements.txt            # Python dependencies
├── frontend/                       # Next.js 16 (App Router) Frontend
│   ├── app/                        # App Router Pages
│   │   ├── layout.tsx              # Root HTML & theme shell
│   │   ├── page.tsx                # Dashboard overview
│   │   ├── [section]/page.tsx      # Deep-dive workspace routes
│   │   └── signals/[signalId]/     # Full Signal Detail Workspace
│   ├── components/                 # React UI Components
│   │   ├── common/                 # Reusable Design System Primitives
│   │   │   ├── DemoOperatorSelector.tsx # 6-role demo persona selector
│   │   │   ├── DataModeBadge.tsx   # Live / Test Fixture badge
│   │   │   ├── ErrorState.tsx      # Error UI with correlation IDs
│   │   │   └── EvidenceDrawer.tsx  # Side drawer for deep evidence inspection
│   │   ├── signals/                # Signal Cards, Tables, Detail Workspaces
│   │   │   ├── SignalCard.tsx      # Signal card with priority counter & queue badge
│   │   │   └── SignalDetailWorkspace.tsx # 3-pillar workspace + audit history
│   │   ├── ui/                     # Interactive UI Elements (Stepper, Counter, etc.)
│   │   └── metaradar.tsx           # Navigation shell, header, footer
│   ├── lib/                        # Client Utilities & API Adapters
│   │   ├── api.ts                  # Typed REST fetchers (submitSignalReview, etc.)
│   │   ├── mappers.ts              # API payload to domain model mappers
│   │   └── hooks.ts                # Custom SWR / state hooks
│   └── types/                      # TypeScript Contract Definitions
│       └── api.ts                  # Canonical API contract (synced via export_openapi.py)
├── config/                         # YAML Domain Configurations
│   └── haemophilia.yaml            # Haemophilia disease area configuration
├── contracts/                      # OpenAPI JSON Schemas
│   └── openapi.json                # Live exported OpenAPI 3.1 contract
├── scripts/                        # Tooling & Verification Scripts
│   ├── export_openapi.py           # Dumps openapi.json & syncs api.ts
│   └── check-banned-classes.mjs    # Linter for banned Tailwind classes
└── tests/                          # Pytest Backend Test Suites (139 tests)
    ├── test_signal_routing_workflow.py # Review state machine tests
    ├── test_provenance.py          # Canonical URL & provenance tests
    ├── test_connector_health.py    # Connector registration & health tests
    └── test_truthfulness_and_invariants.py # Determinism & invariant gates
```
