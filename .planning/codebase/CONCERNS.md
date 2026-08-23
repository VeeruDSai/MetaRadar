---
doc_type: codebase-map
focus: concerns
analysis_date: 2026-08-23
---

# Concerns & Technical Debt

**Analysis Date:** 2026-08-23

## Resolved Technical Debt

- **Autonomous Persistent Scheduler**: Replaced manual-only pipeline trigger with an autonomous background scheduler (`SourceScheduler` in `backend/app/services/scheduler.py`) using native asyncio loops and PostgreSQL advisory locks.
- **Truthful Source Health Model**: Fixed the false-degradation issue where clean API runs with 0 new records were labeled `DEGRADED`. Implemented canonical `NO_NEW_DATA` state and automatic `last_success` updates.
- **Legacy Artifact Cleanup**: Deleted obsolete `frontend/package-lock.json` in favor of canonical `pnpm-lock.yaml`. Deleted legacy `frontend/src/` directory to eliminate dual-types confusion.
- **Multi-Feed Adapter Architecture**: Added FDA MedWatch RSS, FDA Drug Safety RSS, EMA EPARs, EMA Orphan Designations RSS, and ClinicalTrials.gov `dataTimestamp` tracking with change event detection.
- **Deterministic Relevance Gate**: Implemented `RelevanceGate` (`backend/app/services/relevance.py`) to reject noise before expensive downstream AI processing.

## Current Concerns & Production Hardening Items

### 1. Authentication & Authorization (Medium — Production Readiness)
- API endpoints currently do not require user authentication (designed for local hackathon demo).
- Recommended: Implement JWT / OAuth2 bearer token authentication before deploying to multi-tenant or shared cloud infrastructure.

### 2. Live Network Rate-Limiting & Quota Scaling (Low–Medium)
- NewsAPI has a strict 100 req/day quota on developer keys (handled with graceful fallback).
- PubMed and openFDA have elevated rate limits when using API keys (`NCBI_API_KEY`, `OPENFDA_API_KEY`). Ensure keys are configured in production environment secrets.

### 3. Vector Database Scaling (Low)
- FastEmbed 384-dimensional embeddings are indexed in PostgreSQL using pgvector HNSW indexes.
- As the bronze corpus expands beyond tens of thousands of items, monitor query latency and tune `ef_search` / `m` parameters as needed.

### 4. Continuous Deployment & Migrations
- Alembic migrations (`001` through `006`) are verified and clean.
- In production, execute `alembic upgrade head` via a pre-deployment step rather than relying on application bootstrap.
