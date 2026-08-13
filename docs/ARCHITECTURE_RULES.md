# MetaRadar Architecture Rules

1. **Frontend**: Active v0 Next.js 16 tree under `frontend/app/` is the canonical layout.
2. **Backend**: FastAPI modular architecture (`app/api/v1/endpoints/`, `app/services/`, `app/providers/`).
3. **Database**: PostgreSQL 16 + pgvector. Async SQLAlchemy models match Alembic migrations.
4. **LLM Chain**: Local Gemma -> Grok Fallback -> Degraded BART.
