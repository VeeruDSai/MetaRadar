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

**Prescribed critical-path coverage** (`docs/METARADAR_MASTER_PLAN_v3.0.md` §10, `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md`):
- Ingestion connectors, entity extraction, confluence clustering, calibration service, lifecycle, red-team, missing-signal, watch/routing — minimum 60% coverage for unit + integration

## Mocking

**Framework:** pytest-mock / `unittest.mock` (prescribed implicitly; no code yet).

**Patterns:**
- Mock external APIs (`httpx` responses) for connector tests — never hit live APIs in unit tests
- Mock the reasoning LLM; test the degraded path explicitly (Gemma unavailable → BART factual summarization only — no reasoning-equivalent output, degraded mode flagged) (`docs/9_RISK_AND_GUARDRAILS.md` R6)
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

**The five hackathon success metrics** (`docs/METARADAR_MASTER_PLAN_v3.0.md` §10) double as acceptance tests — **targets to be demonstrated by the implementation, not current results**:
1. **Source-linked summaries = 100%** (EV-1) — every high-priority insight carries source name/URL/date/type/excerpt/evidence level/confidence/timestamp/label
2. **Classification accuracy ≥ 85%** (EV-2/EV-2b/EV-13) — B.Pharm-labelled validation set; report accuracy, precision, recall, confusion matrix; false-positive test cases (cardiac "gene therapy", engineering "mim8")
3. **Top-signal discovery ≤ 5 min** — reproducible 100-signal batch vs manual baseline
4. **Confidential/patient data = 0** (EV-4) — audit scan, PII scrubber unit test, `.env` not in repo
5. **Calibrated improvement** (EV-6) — routing agreement uplift ≥ 10 points before/after feedback

**Additional EV checks:** dedup >80% similarity control (EV-8), congress/publication miscoupling controls (EV-9), controlled-vocabulary conformance (EV-14), AC-15 watch-rule scenario (`docs/8_CORRECTED_UNIFIED_PLAN.md` §10)

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
- Simulate LLM load failure → assert **degraded mode**: BART performs factual summarization ONLY; no unsupported interpretation; no reasoning-based action recommendation; degraded mode flagged and logged (R6)
- Simulate PII-containing input → assert the dedicated PII/PHI detection + redaction layer produces `[REDACTED:LABEL]` before persistence, or rejects/quarantines on low detection confidence (R14)

---

*Testing analysis: 2026-08-13*
