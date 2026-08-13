# MetaRadar CI/CD Standards

GitHub Actions CI workflow (`.github/workflows/ci.yml`) enforces:
1. Python backend tests (`python tests/test_foundation.py`).
2. OpenAPI contract drift check (`python scripts/export_openapi.py`).
3. Frontend typecheck (`pnpm exec tsc --noEmit`).
4. Frontend lint (`pnpm lint`).
5. Frontend production build (`pnpm build`).
