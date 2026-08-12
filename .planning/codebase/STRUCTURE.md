# Codebase Structure

**Analysis Date:** 2026-08-13

> **Current state:** The repository currently contains **documentation only** (specification-first). The planned implementation layout below is prescribed by `README.md` "Project Structure" and the SDD. Where new code will go is marked accordingly.

## Directory Layout (current)

```
novonordisk/                    # repo root (project name: MetaRadar)
├── CLAUDE.md                   # AI agent instructions: project, stack, conventions, GSD workflow
├── README.md                   # Full project README: problem, solution, architecture, stack, config, demo
├── docs/                       # All specification & research documentation
│   ├── METARADAR_MASTER_PLAN_v5.0.md      # CANONICAL master specification (authoritative)
│   ├── 1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md
│   ├── 2_SRS_Software_Requirements_Specification.md
│   ├── 3_SOFTWARE_DESIGN_DOCUMENT.md
│   ├── 4_UI_DESIGN_DOCUMENT.md
│   ├── 5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md
│   ├── 6_NOVO_NORDISK_ANALYSIS_AND_HACKATHON_INTELLIGENCE.md
│   ├── 7_PITCH_AND_PRESENTATION_NARRATIVE.md
│   ├── 8_CORRECTED_UNIFIED_PLAN.md
│   ├── 9_RISK_AND_GUARDRAILS.md
│   ├── Ishaaq_research-1.md               # B.Pharm domain research (treatment map)
│   ├── Sanjana_Rathore_research-5.md      # B.Pharm domain research (Medical Affairs perspective)
│   └── Usha_rathore_research.md           # B.Pharm domain research (evidence quality)
└── .planning/codebase/        # THIS codebase map (GSD-generated)
```

## Directory Purposes (current)

**Repository root:**
- Purpose: Project entry point
- Key files: `README.md` (overview + operational guide), `CLAUDE.md` (AI instructions with `<!-- GSD:... -->` blocks: project, stack, conventions, workflow)

**`docs/`:**
- Purpose: All specification, design, planning, and research documentation
- Contains: 13 markdown files — numbered spec docs (1–9) + 3 B.Pharm research files
- Key files: `METARADAR_MASTER_PLAN_v5.0.md` is **the sole authoritative spec**; all other docs are secondary/historical (each carries a note pointing to the master plan)

## Planned Implementation Layout (per `README.md` "Project Structure")

```
metaradar/
├── frontend/                 # Next.js 15 + React 19 + TS
│   ├── app/                  # App Router pages
│   ├── components/           # UI components (shadcn/ui)
│   ├── lib/                  # Shared frontend utilities
│   ├── public/
│   └── package.json
├── backend/                  # FastAPI (Python 3.11)
│   ├── app/
│   │   ├── api/              # REST endpoints
│   │   ├── agents/           # LangGraph workflow nodes
│   │   ├── intelligence/     # Confluence/Lifecycle/Red-Team/Missing-Signal engines
│   │   ├── ontology/         # Haemophilia knowledge graph
│   │   ├── models/           # SQLAlchemy/DB models
│   │   ├── services/         # narrative_synthesizer, calibration, etc.
│   │   └── main.py           # FastAPI entry
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── synthetic/            # 500-signal fallback dataset
│   └── ontology/             # ontology seed data
├── workers/                  # APScheduler jobs (single scheduler)
├── docker-compose.yml
├── .env.example
├── .gitignore
└── docs/                     # spec docs (already present)
```

## Key File Locations

**Entry Points (planned):**
- `backend/app/main.py`: FastAPI app (per SDD `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §2)
- `frontend/app/`: Next.js pages
- `workers/`: APScheduler 2h jobs (single scheduler; Celery removed per Master Plan §14.9)

**Configuration:**
- `.env.example` (template) + `.env` (gitignored, real secrets) — prescribed in `README.md` "Configuration"; SRS §4.2 defines the var table
- `docker-compose.yml` — service wiring (planned)

**Core Logic (planned):**
- `backend/app/intelligence/`: five mechanisms — confluence.py, lifecycle.py, redteam.py, missing_signal.py
- `backend/app/services/narrative_synthesizer.py`: reasoning-layer briefs via `LLMProvider` — Gemma local default / Grok hosted optional / BART degraded (SDD line ~620, Master Plan §13)
- `backend/app/services/`: `StakeholderCalibrationService` (calibration)
- `backend/app/agents/`: LangGraph node implementations

**Testing (planned):**
- `backend/tests/` — pytest suite (see `TESTING.md`)

## Naming Conventions

**Files (docs):**
- Numbered spec docs: `{N}_{TOPIC}.md` (e.g., `2_SRS_Software_Requirements_Specification.md`, `9_RISK_AND_GUARDRAILS.md`)
- Research docs: `{Author}_{topic}.md` (e.g., `Ishaaq_research-1.md`, `Sanjana_Rathore_research-5.md`)
- Version-stamped headers in every doc (e.g., "v2.1", "v3.0"); canonical doc carries "SOLE AUTHORITATIVE" banner

**Python (prescribed by docs):**
- `snake_case` module and function names (e.g., `node_nlp_extract`, `narrative_synthesizer.py`, `StakeholderCalibrationService` class CamelCase)
- LangGraph nodes prefixed `node_` (e.g., `node_ingest`, `node_confluence`) (`docs/METARADAR_MASTER_PLAN_v5.0.md` §4)

**Env vars:**
- UPPER_SNAKE (e.g., `DATABASE_URL`, `NEWSAPI_KEY`, `LLM_PROVIDER`, `LOCAL_LLM_MODEL`, `XAI_API_KEY`) — SRS §4.2

## Where to Add New Code

**New Feature (e.g., new intelligence mechanism):**
- Primary code: `backend/app/intelligence/` + LangGraph node in `backend/app/agents/`
- API endpoint: `backend/app/api/`
- UI: `frontend/app/` + `frontend/components/`
- Tests: `backend/tests/`

**New Connector (new public data source):**
- Implementation: `backend/app/agents/` (ingestion) — follow `httpx` async + `tenacity` retry + quota-awareness pattern (`CLAUDE.md` "Resilience & Calibration")
- Config: env var in `.env.example`; SRS §4.2 table

**New Ontology Entity (drug/company):**
- Seed: `data/ontology/` — versioned with `updated_by`, regression-tested (`docs/9_RISK_AND_GUARDRAILS.md` R15)

**New Document:**
- `docs/` following `{N}_{TOPIC}.md` numbering; add canonical-master-plan pointer note

## Special Directories

**`docs/`:**
- Purpose: Spec + research
- Generated: No (hand-authored)
- Committed: Yes

**`.planning/codebase/`:**
- Purpose: GSD codebase map (this directory)
- Generated: Yes (by `/gsd:map-codebase`)
- Committed: Yes (GSD commit on generation)

---

*Structure analysis: 2026-08-13*
