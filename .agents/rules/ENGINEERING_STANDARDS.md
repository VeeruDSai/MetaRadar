# MetaRadar Global Engineering Standards

> Permanent Operating Baseline for MetaRadar v5.1 Architecture

## 1. Core Principles

1. **Non-Negotiable Software Quality**: No code shall be merged or committed that breaks type safety, lint checks, or automated verification.
2. **Honesty & Telemetry Verification**: Systems must report true execution status. Mocking, fallbacks, or synthetic data must be explicitly labeled.
3. **Privacy First**: Sensitive data (PII/PHI) must be scrubbed at the boundary before persistence or external provider transmission.
4. **Resilience & Graceful Degradation**: Core features must degrade gracefully (e.g. Local Gemma -> Grok fallback -> BART degraded factual mode) without hard crashing.

## 2. Technical Stack Boundaries

- **Frontend**: Next.js 16 App Router (`frontend/app/`), React 19, Tailwind CSS v4, TypeScript.
- **Backend**: FastAPI 0.115, Pydantic v2, Python 3.11+, Async SQLAlchemy 2.0.
- **Database**: PostgreSQL 16 + `pgvector` + `pg_trgm`, Redis 7.
- **Contract Pipeline**: FastAPI OpenAPI -> `contracts/openapi.json` -> `frontend/src/types/api.ts`.
