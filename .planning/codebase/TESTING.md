# Testing Patterns

**Analysis Date:** 2026-08-13

> **Status note:** No test code exists yet (specification-first repo). Every statement below is **planned / prescribed / a target / an acceptance test** — nothing here describes an existing test, measured coverage, or verified behavior. A B.Pharm-labelled evaluation dataset is a core deliverable of the hackathon (≥85% classification accuracy target).

## Test Framework

**Runner (prescribed):**
- pytest + pytest-asyncio (async pipeline nodes) — config at `backend/tests/` (planned)
- Coverage: pytest-cov

**Assertion Library:**
- pytest assertions (built-in)

**Run Commands (prescribed by `docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md`):**
```bash
pytest tests/ -v --cov=services     # All tests with coverage
pytest tests/ -v                    # All tests
pytest tests/ -v --cov=services --cov-report=html   # Coverage report
```

## Test File Organization

**Location:**
- `backend/tests/` — separate from source (planned, per `README.md` "Project Structure")

**Naming:**
- `test_{module}.py` convention (SDD samples: `test_entity_extraction.py`, `test_confluence_detection.py`, `test_lifecycle_tracking.py`, `test_redteam_contradiction.py` — see `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §testing)

## Test Structure

**Suite Organization (prescribed by SDD):**
- Unit Tests ~70% · Integration Tests ~25% · (remaining E2E/demo checks) — `docs/3_SOFTWARE_DESIGN_DOCUMENT.md`

**Patterns:**
- Async pipeline nodes tested with `@pytest.mark.asyncio` — e.g., entity extraction, full signal processing, confluence detection, lifecycle tracking, red-team contradiction (SDD samples)

**Prescribed critical-path coverage** (`docs/METARADAR_MASTER_PLAN_v5.0.md` §10, `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md`):
- Ingestion connectors, entity extraction, confluence clustering, calibration service, lifecycle, red-team, missing-signal, watch/routing — minimum 60% coverage for unit + integration

## Mocking

**Framework:** pytest-mock / `unittest.mock` (prescribed implicitly; no code yet).

**Patterns:**
- Mock external APIs (`httpx` responses) for connector tests — never hit live APIs in unit tests
- Mock the reasoning providers; test the full provider chain explicitly (per `LLM_PROVIDER`: Gemma → Grok → BART degraded factual summarization only — no reasoning-equivalent output, degraded mode flagged) (`docs/9_RISK_AND_GUARDRAILS.md` R6, SRS FR-2.2.3B/C, EV-19)
- Mock stakeholder feedback for calibration service tests

**What to Mock:**
- External HTTP calls, model inference, time/scheduler

**What NOT to Mock:**
- Ontology mapping logic (must run against the real `data/ontology/` seed)
- Confluence/Lifecycle state transitions (real FSM logic, deterministic inputs)

## Fixtures and Factories

**Test Data:**
- 500-signal synthetic dataset (`data/synthetic/`) is the canonical test corpus — deterministic, labelled (disease · patient type · signal type · priority · impacted function), `is_synthetic=true` (`README.md` "Synthetic Fallback")
- B.Pharm-labelled evaluation dataset for classification metrics (SDD, SRS)

**Location:**
- `data/synthetic/` (planned) — shared between demo mode and tests

## Coverage

**Requirements (two distinct metrics — not contradictory):**
- **Overall project target: > 80% total test coverage** across the test suite (`docs/1_GAP_ANALYSIS_AND_OPTIMIZATIONS.md` line ~1331)
- **Critical-path minimum: ≥ 60% unit + integration coverage** on the critical pipeline components (ingestion, entity extraction, confluence clustering, calibration, lifecycle, red-team, missing-signal, watch/routing) (`docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md`)
- SDD: prescribed 70% unit / 25% integration split of the suite

> All coverage figures are **targets to be demonstrated by the implementation** — the repository currently contains specifications only, no tests exist yet.

**View Coverage:**
```bash
pytest tests/ -v --cov=services
```

## Test Types

**Unit Tests:**
- Individual LangGraph nodes and services: entity extraction (spaCy), confluence clustering, lifecycle FSM, red-team NLI (mocked model), calibration weight updates, watch-rule state machine

**Integration Tests:**
- Full signal processing path (ingest → validate → extract → enrich → intelligence → synthesize) on synthetic fixtures (SDD sample)
- Database integration (PostgreSQL + pgvector, WORM audit log append-only behavior)

**E2E Tests (planned/rehearsal):**
- Fallback-cascade demo rehearsal (planned): network off → synthetic fallback; `docker-compose up` on clean machine; 1000-signal load test (`docs/8_CORRECTED_UNIFIED_PLAN.md` §11)
- Not a formal framework (Playwright/Selenium not prescribed)

## Evaluation Metrics (Hackathon-Specific, Prescribed)

**The five hackathon success metrics** (`docs/METARADAR_MASTER_PLAN_v5.0.md` §10) double as acceptance tests — **targets to be demonstrated by the implementation, not current results**:
1. **Source-linked summaries = 100%** (EV-1) — every high-priority insight carries source name/URL/date/type/excerpt/evidence level/confidence/timestamp/label
2. **Classification accuracy ≥ 85%** (EV-2/EV-2b/EV-13) — B.Pharm-labelled validation set; report accuracy, precision, recall, confusion matrix; false-positive test cases (cardiac "gene therapy", engineering "mim8")
3. **Top-signal discovery ≤ 5 min** — reproducible 100-signal batch vs manual baseline
4. **Confidential/patient data = 0** (EV-4) — audit scan, PII scrubber unit test, `.env` not in repo
5. **Calibrated improvement** (EV-6) — routing agreement uplift ≥ 10 points before/after feedback

**Additional EV checks:** dedup >80% similarity control (EV-8), congress/publication miscoupling controls (EV-9), controlled-vocabulary conformance (EV-14), AC-15 watch-rule scenario, provider fallback chain (EV-19), external-LLM privacy gate (EV-20) (`docs/8_CORRECTED_UNIFIED_PLAN.md` §9)

## Common Patterns

**Async Testing:**
```python
# Prescribed by SDD samples
@pytest.mark.asyncio
async def test_full_signal_processing():
    result = await pipeline.process(fixture_signal)
    assert result.evidence_sufficient is True
```

**Error/Resilience Testing (planned failure-injection tests — targets, not existing results):**
- Simulate API 429/500 → assert graceful fallback to cache → bronze → synthetic (R11); the acceptance target is graceful degradation during tested connector failures, not an untested "never crashes" guarantee
- Simulate reasoning-provider failures → assert the configured provider chain (Gemma → Grok in xai/auto → BART degraded factual mode); if no reasoning provider is available assert **degraded mode**: BART performs factual summarization ONLY; no unsupported interpretation; no reasoning-based action recommendation; degraded mode flagged and logged (R6, EV-19)
- Simulate PII-containing input → assert the dedicated PII/PHI detection + redaction layer produces `[REDACTED:LABEL]` before persistence, or rejects/quarantines on low detection confidence (R14)

### Provider Fallback Tests (prescribed — Master Plan §13, SRS FR-2.2.3A–G, EV-19/EV-20)

Ten failure-injection scenarios (targets to be demonstrated by the implementation, not existing results):

| # | Scenario | Expected behavior |
|---|---|---|
| 1 | Gemma available | Gemma used (output_mode=reasoning) |
| 2 | Gemma unavailable | Grok used (in `xai`/`auto` modes) |
| 3 | Gemma + Grok unavailable | BART degraded factual summary; UI label "AI reasoning unavailable — showing source-grounded factual summary" |
| 4 | Grok API key missing | BART degraded (`fallback_reason=missing_api_key`) |
| 5 | Grok timeout | BART degraded (`fallback_reason=api_timeout`) |
| 6 | Grok schema-invalid response | retry once → fallback (`fallback_reason=schema_invalid`) |
| 7 | Grok semantic/evidence validation fails | reject/fallback (fabricated entity or unknown source ID → `fallback_reason=evidence_invalid`) |
| 8 | PII/PHI or confidential content detected | external call blocked by privacy gate → local Gemma / BART degraded / source-only (EV-20) |
| 9 | Offline mode | cached/synthetic data served; zero external calls |
| 10 | BART degraded output | UI correctly labels degraded mode; model metadata recorded (FR-2.2.3F) |

Each provider test records: `provider_used` · `fallback_triggered` · `fallback_reason` · `latency` · `schema_valid` · `evidence_valid` · `output_mode` (reasoning/degraded_factual).

---

*Testing analysis: 2026-08-13*
