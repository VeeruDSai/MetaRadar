# MetaRadar Release Process

## Release Sequence

1. Pre-release quality gate verification (`tsc`, `eslint`, `next build`, `test_foundation.py`, `export_openapi.py`).
2. Pull Request review & CI build green.
3. Database migration execution (`alembic upgrade head`).
4. Container deployment (`docker compose up --build`).
5. Post-deployment health verification (`/api/v1/health/ready`).
