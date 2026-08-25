# Codebase Concerns

**Analysis Date:** 2026-08-25

## Technical Debt

**1. Residual Shell Monolith in `metaradar.tsx`:**
- **Description:** Although domain workspaces have been modularized under `frontend/components/` (`signals/`, `confluence/`, `calibration/`, `observability/`, etc.), `frontend/components/metaradar.tsx` remains a large orchestration component.
- **Impact:** Moderate state duplication across top-level views and complex prop passing.
- **Remediation:** Further decouple top-level workspace state into dedicated React contexts or URL search params.

**2. Endpoint Layer Complexity in `backend/app/api/v1/endpoints/signals.py`:**
- **Description:** `signals.py` encompasses signal listing, overview aggregation, detail serialization, review actions, and Athena evidence validation.
- **Impact:** High cognitive load and duplicated serialization logic.
- **Remediation:** Extract serialization and transformation helpers into dedicated converter schemas or service layers.

**3. In-Memory Rate Limiting:**
- **Description:** `backend/app/api/deps.py` enforces client rate limits using an in-process dictionary (`_rate_buckets`).
- **Impact:** Limits do not scale across multiple uvicorn worker processes and are reset on restart.
- **Remediation:** Move rate-limit state tracking to Redis via the existing `REDIS_URL` connection.

**4. Migration Chain History:**
- **Description:** 12 sequential Alembic migrations exist in `backend/alembic/versions/` (001 through 012).
- **Impact:** Historical patches for column widening and dropped unique constraints create a multi-step upgrade path for new environments.
- **Remediation:** Consider consolidating/squashing migrations prior to future major version releases.

## Operational & Performance Risks

**1. External Life-Science API Rate Limits & Availability:**
- **Description:** Connectors interface with public external services (NCBI PubMed, ClinicalTrials.gov v2, OpenFDA, EMA RSS).
- **Mitigation:** Exponential backoff with jitter is implemented in `backend/app/connectors/base.py`, and failures degrade gracefully without crashing the pipeline.

**2. Local LLM Inference Latency on Low-Spec Hardware:**
- **Description:** Running Gemma 3 4B on CPU-only machines can introduce latency in the `nlp_extract` and `synthesize` pipeline nodes.
- **Mitigation:** The pipeline supports automatic GPU offload (`LLM_GPU_LAYERS`), background batch execution via `runner.py`, and a deterministic Degraded mode fallback.

## Security & Privacy Guardrails

**1. Cloud Provider Privacy Boundary:**
- **Description:** When Grok cloud fallback is enabled (`ENABLE_GROK_FALLBACK=true`), requests must never contain private or unscrubbed clinical data.
- **Enforcement:** Enforced at the architectural boundary by `validate_privacy_gate()` in `backend/app/providers/grok.py` and guarded by `tests/test_privacy_boundary.py`.

**2. Design Token & Class Safety:**
- **Description:** Prevention of hardcoded arbitrary hex colors or banned Tailwind utility classes (`slate-*`).
- **Enforcement:** Enforced in CI via `node scripts/check-banned-classes.mjs`.
