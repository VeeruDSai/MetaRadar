---
phase: 11-productionization
plan: 11-03
subsystem: provenance-and-connectors
tags: [provenance, connectors, canonical-url, reachability, pubmed, clinical-trials, fda, ema, newsapi, fierce-pharma, et-pharma, biopharmadive]
requires:
  - phase: 11-productionization
    plan: 11-02
    provides: Server-side RBAC and review state machine
provides:
  - Full 8-Connector canonical URL and provenance resolution matrix
  - Direct article URL pass-through and landing page blocking for news/RSS connectors
  - Document-level URL resolution for regulatory filings (Drugs@FDA ApplNo, EMA EPAR)
  - 100% passing test coverage across all 8 connectors in tests/test_provenance.py and tests/test_connector_health.py
affects: [backend, connectors, provenance, testing]
key-files:
  modified:
    - backend/app/services/provenance_urls.py
    - tests/test_provenance.py
---

# Plan 11-03 Summary: Full 8-Connector Pharma Provenance & Reachability

## Executed Work
1. **Canonical Provenance Resolution Matrix (`backend/app/services/provenance_urls.py`)**:
   - Validated and tested canonical URL generation across all 8 live pharma connectors:
     1. `pubmed`: `https://pubmed.ncbi.nlm.nih.gov/{pmid}/`
     2. `clinical_trials`: `https://clinicaltrials.gov/study/{nct_id}`
     3. `fda`: Specific Drugs@FDA Application overview (`ApplNo=...`)
     4. `ema`: Specific European Public Assessment Report (`EPAR/...`)
     5. `newsapi`: Direct verified article URLs (generic portal/register landing pages strictly rejected)
     6. `fierce_pharma`: Direct verified Fierce Pharma article permalinks
     7. `et_pharma`: Direct verified Economic Times HealthWorld article permalinks
     8. `biopharmadive`: Direct verified BioPharma Dive article permalinks

2. **Connector Telemetry & Provenance Invariants**:
   - Verified that synthetic fixtures retain `provenance_status == "fixture"` and `data_mode == "test_fixture"`.
   - Verified that live connector items produce `provenance_status == "available"` when a valid document URL exists, and `missing_url` if generic portals are encountered without fallback.

3. **Automated Verification**:
   - All 21 tests in `tests/test_provenance.py` and `tests/test_connector_health.py` pass with 100% success.
