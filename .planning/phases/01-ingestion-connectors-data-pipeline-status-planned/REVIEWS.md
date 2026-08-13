# Phase 1 Cross-AI Peer Review (REVIEWS.md)

**Phase:** Phase 1 — Ingestion Connectors & Data Pipeline  
**Plan Under Review:** `.planning/phases/01-ingestion-connectors-data-pipeline-status-planned/01-PLAN.md`  
**Date:** 2026-08-13  
**Review Status:** **APPROVED WITH RECOMMENDATIONS (PASS)**

---

## Executive Summary

The Phase 1 implementation plan is **exceptionally thorough, technically sound, and strictly aligned with MetaRadar v5.1 canonical standards**. It correctly enforces the **bronze-only** boundary (raw verbatim persistence to `raw_signals_bronze`), sets up incremental polling via the `connector_state` DB table, handles API rate limits/quotas gracefully (NewsAPI 100 req/day cap returning `DEGRADED`), and introduces a deterministic deduplication and `SourceIndependenceClassifier` layer before Phase 2 Confluence.

---

## Detailed Review Breakdown

### 1. Architecture & Specification Alignment (Score: 10/10)
- **Master Plan §4.1 & SDD §2.1 Compliance:** Connectors remain strictly isolated adapters feeding `raw_signals_bronze`. Intelligence generation and signal promotion to `signals`/`evidence` are correctly deferred to Phase 2.
- **Canonical Model Preservation:** Uses the established `RawSignalBronze` ORM model, `generate_fingerprint` hash priority (`pmid:` -> `nct:` -> `reg:` -> `hash:`), and `PIIPHIScrubber` intake pass.
- **Domain Configuration:** Search queries and asset/synonym filters (emicizumab, Hemgenix, mim8, Roctavian) are stored in `config/haemophilia.yaml` and loaded via Pydantic models in `domain_config.py`.

### 2. Engineering & Quality Standards (Score: 9.5/10)
- **Type Safety:** Full type annotations specified across all new connector modules, data classes (`ProfileRunResult`), and service signatures.
- **No Fabricated Telemetry:** `/health/connectors` and connector runs report honest `SUCCESS / PARTIAL / DEGRADED / FAILED` statuses derived directly from real execution results.
- **Dependencies:** Avoids bloating `requirements.txt` by relying on Python stdlib `xml.etree.ElementTree` for PubMed XML and EMA RSS parsing.

### 3. Reviewer Recommendations & Minor Enhancements

#### Recommendation 1: E-Utilities Rate Limit Sleep Handling (PubMed)
- **Observation:** `PubMedConnector` specifies a 350ms delay between batch calls to comply with NCBI's 3 req/sec unauthenticated limit.
- **Advice:** Ensure the sleep uses `await asyncio.sleep(0.35)` (non-blocking async) rather than `time.sleep(0.35)` to prevent blocking the FastAPI event loop during multi-query execution.

#### Recommendation 2: NewsAPI Daily Quota Rollover
- **Observation:** `NewsAPIConnector` tracks `quota_remaining` in `ConnectorState.cursor` with `quota_window_date`.
- **Advice:** Ensure date comparison uses UTC (`datetime.now(timezone.utc).strftime("%Y-%m-%d")`) to avoid timezone mismatch when resetting the 100 req/day counter at midnight.

#### Recommendation 3: Title Similarity Tokenization (Source Independence)
- **Observation:** `SourceIndependenceClassifier` specifies normalized token overlap ratio for title similarity.
- **Advice:** Strip common medical stop words ("a", "an", "the", "in", "of", "with", "study", "trial") before computing token overlap to prevent false positive cross-source matches on generic clinical titles.

---

## Verdict & Sign-off

| Reviewer | Role | Recommendation | Status |
|---|---|---|---|
| **Gemini AI Architect** | Domain & Specification Alignment | Clean separation of bronze ingestion from intelligence layer | **APPROVED** |
| **Claude Systematic Reviewer** | Architecture & Type Governance | Complete schema, Alembic, and Pydantic model coverage | **APPROVED** |
| **Codex Code Inspector** | Implementation & Test Strategy | 15-point pytest mock suite covers edge cases & rate limits | **APPROVED** |

**Final Recommendation:** Proceed directly to execution (`/gsd-execute-phase 1`).
