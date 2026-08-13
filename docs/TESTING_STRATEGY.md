# MetaRadar Testing Strategy

## Quality Gate Matrix

1. **Frontend Typecheck & Lint**: `tsc --noEmit` and `eslint .`
2. **Frontend Production Build**: `next build` with strict error checking.
3. **Backend Unit & Capability Verification**: `python tests/test_foundation.py`
4. **Contract Synchronization**: `python scripts/export_openapi.py` with git diff check.
5. **Database Migration Verification**: Alembic async schema verification.
6. **Container Readiness**: `docker compose config` validation.
