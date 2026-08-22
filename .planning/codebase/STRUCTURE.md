---
doc_type: codebase-map
focus: arch
analysis_date: 2026-08-22
---

# Project Structure

**Analysis Date:** 2026-08-22

## Root Layout

```
novonordisk/
├── backend/                  # FastAPI service (Python)
│   ├── alembic/              # Migrations: 001_initial_v51_schema … 006_widen_signals_external_id
│   ├── app/
│   │   ├── api/v1/endpoints/ # cache, feedback, health, ingestion, intelligence, observability, pipeline, registry, search, signals
│   │   ├── connectors/       # base + pubmed, clinical_trials, newsapi, fda, ema
│   │   ├── core/             # config.py, domain_config.py, logging.py, middleware.py
│   │   ├── db/               # session.py (engine/get_db/advisory locks), seed.py
│   │   ├── models/           # __init__.py — all 20 SQLAlchemy tables in one module
│   │   ├── providers/        # base, factory, gemma, grok, degraded
│   │   ├── schemas/          # Pydantic models (intelligence, registry, observability)
│   │   ├── services/         # scheduler, relevance, calibration, confluence, deduplication, embeddings(+_backfill), ingestion, pii, redteam, scoring, source_independence, vector_query
│   │   ├── workflows/        # graph.py (11 nodes), runner.py, state.py, nodes/*.py
│   │   └── main.py           # FastAPI entry point & lifespan scheduler manager
│   ├── Dockerfile
│   └── requirements.txt      # runtime AND test deps together
├── frontend/                 # Next.js 16 app (pnpm)
│   ├── app/                  # layout.tsx, page.tsx, globals.css
│   ├── components/           # 19 .tsx across 14 domain dirs: signals(2), common(4), ui, theme,
│   │                         # calibration, confluence, contradictions, developments, functions,
│   │                         # intelligence, missing-signals, observability, settings, sources + metaradar.tsx (root shell)
│   │                         # Note: SourcesOperationsWorkspace.tsx renders truthful health badges, tiers, scheduler metrics
│   ├── lib/                  # api.ts (typed client), errors.ts, hooks.ts, mappers.ts, utils.ts
│   ├── types/api.ts          # CANONICAL generated API types (from contracts/openapi.json)
│   ├── next.config.mjs       # images.unoptimized only
│   ├── package.json          # pnpm@9.15.5, node >=20.9.0
│   └── tsconfig.json         # strict TypeScript; `@/*` path alias
├── config/haemophilia.yaml   # Domain rules: assets, confluence thresholds, source tiers, query profiles
├── contracts/openapi.json    # Canonical OpenAPI 3.1 contract
├── data/synthetic_signals.json # 500-signal synthetic fallback dataset
├── docs/                     # Master plan v5.0, SRS, SDD, UI doc, risk/guardrails + docs/rules/* process standards
├── scripts/                  # export_openapi.py, check-banned-classes.mjs, generate_parity_matrix.py, apply_phase7_migrations.py, test_live_ingestion_e2e.py
├── tests/                    # 23 pytest files (root-level, NOT backend/tests)
├── logs/                     # start.py telemetry output
├── setup.py / start.py       # Bootstrap & unified launcher
├── pytest.ini                # testpaths=tests, pythonpath = backend .
├── docker-compose.yml        # postgres, redis, backend(+gpu profile), frontend, ollama
└── .env / .env.example       # secrets local-only
```

## Key Locations by Task

| Task | Files |
|---|---|
| Configure background ingestion scheduler | `backend/app/services/scheduler.py`, `backend/app/core/config.py` |
| Add/modify API endpoint | `backend/app/api/v1/endpoints/*.py`, schema in `backend/app/schemas/`, then run `python scripts/export_openapi.py` |
| Modify DB schema | New Alembic revision in `backend/alembic/versions/` + model in `backend/app/models/__init__.py` |
| Modify data connector / feed | `backend/app/connectors/`, register in `config/haemophilia.yaml` |
| Modify relevance filtering | `backend/app/services/relevance.py` |
| Change pipeline behavior | Node in `backend/app/workflows/nodes/`, wire in `graph.py`, state channels in `state.py` |
| Swap/configure LLM | `backend/app/core/config.py` env keys + `backend/app/providers/factory.py` chain |
| Domain/scoring rules | `config/haemophilia.yaml` (loaded via `backend/app/core/domain_config.py`) |
| Frontend feature | Component under `frontend/components/<domain>/`, API call via `frontend/lib/api.ts` |
| UI styling tokens | Theme system; banned classes enforced by `scripts/check-banned-classes.mjs` |

## Naming & Organization Conventions

- **Python**: snake_case modules/functions; PascalCase classes; node functions named `node_<step>`; tables plural snake_case; UUID PKs `<entity>_id`; version columns suffixed `_version`.
- **TypeScript/React**: PascalCase component files matching export (`SignalCard.tsx`); camelCase lib functions prefixed `get*` for fetchers; one component per file.
- **Contract Synchronization**: Generated types live exclusively in `frontend/types/api.ts` generated from `scripts/export_openapi.py`.
- **Tests**: `tests/test_<area>.py` mirrors the area under test.
