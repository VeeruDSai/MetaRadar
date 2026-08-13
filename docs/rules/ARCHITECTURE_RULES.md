# MetaRadar v5.1 Architecture Rules

> **Authoritative Specification Note**: `METARADAR_MASTER_PLAN_v5.0.md` serves as the baseline domain reference spec. The v5.1 Hardening Architecture (`docs/10_ARCHITECTURE_HARDENING_REPORT.md` and `docs/rules/`) is the active, authoritative implementation standard.

1. **Frontend Layout**: Active Next.js 16 App Router tree under `frontend/app/` is the canonical layout.
2. **Backend Services**: Modular FastAPI architecture (`app/api/v1/endpoints/`, `app/services/`, `app/providers/`).
3. **Database Layer**: PostgreSQL 16 + pgvector. Async SQLAlchemy models match Alembic migrations.
4. **LLM Fallback Chain**: Local Gemma -> Grok Hosted Fallback (Privacy Gated) -> Degraded BART Mode (Summarize Only).
5. **Canonical Contract**: FastAPI OpenAPI -> `contracts/openapi.json` -> `frontend/types/api.ts`.