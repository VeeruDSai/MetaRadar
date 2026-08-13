# Integrations & API Surface

**Analysis Date:** 2026-08-13 (Refreshed Post-Stabilization Baseline)

> **Status note:** Backend API endpoints (`/api/v1/health`, `/health/ready`, `/health/models`, `/health/connectors`, `/signals`, `/overview`, `/athena`) are registered in `backend/app/main.py` and covered by an 18-point `pytest` suite. PII/PHI scrubbing and Grok privacy gating (`validate_privacy_gate`) are fully tested. Contradiction detection uses a 19-rule registry (Rules A–S) with priority gating, candidate capping, and caching. The frontend API contract is unified and auto-generated at `frontend/types/api.ts` with zero-diff drift verification in CI. External connectors (PubMed, ClinicalTrials.gov, OpenFDA, NewsAPI, EMA) use the `SourceConnector` abstract base (`backend/app/connectors/base.py`) with honest health status reporting, ready to be wired in Phase 1.

## Data Sources & External Integrations

| Source | Status | Implementation File | Configuration | Data Pipeline Destination |
|---|---|---|---|---|
| NCBI PubMed / E-utilities | **Scaffold / Honest Status** | `backend/app/api/v1/endpoints/health.py` | Keyless | `raw_signals_bronze` -> `signals` |
| ClinicalTrials.gov (v2) | **Scaffold / Honest Status** | `backend/app/api/v1/endpoints/health.py` | Keyless | `raw_signals_bronze` -> `signals` |
| NewsAPI | **Scaffold / Configured** | `backend/app/core/config.py` (`NEWSAPI_KEY`) | `NEWSAPI_KEY` | `raw_signals_bronze` -> `signals` |
| OpenFDA | **Scaffold / Honest Status** | `backend/app/api/v1/endpoints/health.py` | Keyless | `raw_signals_bronze` -> `signals` |
| EMA RSS | **Scaffold / Honest Status** | `backend/app/api/v1/endpoints/health.py` | Keyless | `raw_signals_bronze` -> `signals` |
| Congress Abstracts | **Scaffold / Honest Status** | `backend/app/api/v1/endpoints/health.py` | Keyless | `raw_signals_bronze` -> `signals` |
| Synthetic Signals | **Synthetic Provider** | `backend/app/api/v1/endpoints/signals.py` | Embedded | Fallback signal demonstration |

## Internal Provider & Security Integrations

- **Local Gemma 3 4B** (`google/gemma-3-4b-it`):
  - Abstracted via `GemmaProvider` (`backend/app/providers/gemma.py`). Returns structured reasoning payload and `ModelMetadataSchema`.
- **xAI Grok Fallback** (`grok-beta`):
  - Abstracted via `GrokProvider` (`backend/app/providers/grok.py`). Enforces strict `validate_privacy_gate`: only `PUBLIC` or `SYNTHETIC` payloads pass; `CONFIDENTIAL`, `PATIENT_IDENTIFIABLE`, or `UNKNOWN` payloads are blocked with `PermissionError`.
- **BART Degraded Mode** (`facebook/bart-large-cnn`):
  - Abstracted via `DegradedProvider` (`backend/app/providers/degraded.py`). Supports `SUMMARIZE` capability; `reasoning_available = False`, `actions_available = False`.
- **PII / PHI Scrubber**:
  - `PIIPHIScrubber` (`backend/app/services/pii.py`) scrubs email, phone, SSN, MRN, and patient DOB patterns using redaction tokens (`[EMAIL_REDACTED]`, `[PHONE_REDACTED]`, `[SSN_REDACTED]`, `[MRN_REDACTED]`, `[PATIENT_DOB_REDACTED]`).
- **Red-Team Contradiction Evaluator**:
  - `RedTeamNLIService` (`backend/app/services/redteam.py`) implements a 19-rule registry (`REDTEAM_RULES` A–S) covering dosing, safety, efficacy, and regulatory contradictions with priority gating (`HIGH`/`CRITICAL` only), candidate capping, and in-memory result caching.

## Contract Synchronization & Pipeline

```
Pydantic Schemas (backend/app/schemas/__init__.py)
  │
  ▼
FastAPI OpenAPI Schema (app.openapi())
  │
  ▼
contracts/openapi.json & frontend/types/api.ts (scripts/export_openapi.py)
  │
  ▼
Frontend Components (frontend/components/metaradar.tsx) & CI Drift Verification (.github/workflows/ci.yml)
```
