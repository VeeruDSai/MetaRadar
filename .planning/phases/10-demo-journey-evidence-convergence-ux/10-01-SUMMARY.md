---
phase: 10-demo-journey-evidence-convergence-ux
plan: 10-01
subsystem: connectors-and-scheduler
tags: [biopharmadive, newsapi, quota-governor, connectors, scheduler, health]
requires:
  - phase: 09-signal-workflow-rss-connectors
    provides: Fierce Pharma + ET Pharma RSS connectors, review state machine
provides:
  - BioPharmaDiveRSSConnector (8th connector) connected to official RSS feed
  - Active domain config registration for biopharmadive in haemophilia.yaml
  - Adaptive NewsAPI quota governor in SourceScheduler (throttles to 90m and pauses at <15)
  - Full connector health and registration test coverage
affects: [backend, connectors, scheduler, domain_config]
key-files:
  created:
    - backend/app/connectors/biopharma_dive.py
  modified:
    - backend/app/connectors/__init__.py
    - config/haemophilia.yaml
    - backend/app/services/scheduler.py
    - tests/test_connector_health.py
---

# Plan 10-01 Summary: BioPharma Dive RSS Connector & Adaptive NewsAPI Quota Governor

## Executed Work
1. **BioPharma Dive RSS Connector**:
   - Implemented `BioPharmaDiveRSSConnector` at `backend/app/connectors/biopharma_dive.py` using stdlib `xml.etree.ElementTree` parsing and domain keyword filtering for active feed `https://www.biopharmadive.com/feeds/news/`.
   - Exported and registered `BioPharmaDiveRSSConnector` in `backend/app/connectors/__init__.py` as the **8th official connector**.
2. **Domain Configuration Upgrade**:
   - Upgraded `biopharmadive` from `status: configured_no_feed` to active in `config/haemophilia.yaml` with `tier: 3`, `freshness_class: delayed`, `rss_url`, and `haemophilia_biopharmadive` profile.
3. **Adaptive NewsAPI Quota Governor**:
   - Updated `SourceScheduler` in `backend/app/services/scheduler.py` to inspect `connector.quota_remaining` before execution.
   - When quota is below 15, automatic background cycles are paused with status `HEALTHY (QUOTA_PRESERVED)` and backoff is set to 90 minutes to prevent quota exhaustion during live demonstrations.
4. **Testing & Invariants**:
   - Added `test_discovery_connectors_registered` (asserting all 8 connectors), `test_biopharmadive_domain_config_registration`, `test_biopharmadive_rss_parsing`, and `test_newsapi_quota_governor_logic` in `tests/test_connector_health.py`.
   - All 141 backend tests pass.
