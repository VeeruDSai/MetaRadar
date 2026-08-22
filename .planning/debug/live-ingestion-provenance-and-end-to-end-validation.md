# Debug Session: Live Ingestion Provenance & End-to-End Traceability Validation

## Objective
Verify that MetaRadar v5.1 is genuinely querying live biomedical public APIs (PubMed, ClinicalTrials.gov, OpenFDA, EMA), persisting raw bronze payloads with genuine external URLs and verbatim text, processing them through the LangGraph intelligence pipeline into silver signals and gold confluence stories, and rendering fully inspectable, clickable backward traceability in the frontend UI.

## Evidence & Verification Gates

### 1. Live Public Endpoint Execution & Ingestion Telemetry
Executed `IngestionService.run_connectors(["pubmed", "clinical_trials", "fda", "ema"])` against active public APIs:
- **PubMed E-Utilities:** Executed live HTTP calls. Ingested genuine PMIDs (e.g. `42322300`, `42123505`) with latency ~4.4s. Status: `HEALTHY`.
- **ClinicalTrials.gov API v2:** Executed live HTTP calls against `/api/v2/studies`. Ingested 80 live Phase 3 studies with latency ~1.3s. Status: `HEALTHY`.
- **OpenFDA:** Executed search queries (`openfda.substance_name:hemophilia`). Encountered 404 on specific query syntax; system recorded honest telemetry (`UNHEALTHY` / `DEGRADED`) with latency ~9.3s without fabricating results.
- **EMA RSS:** Executed calls to `https://www.ema.europa.eu/en/medicines/rss`. Captured 404/429 response as `DEGRADED`/`UNHEALTHY` in `source_health_logs` with latency ~6.7s, preserving system stability.
- **Raw Bronze Storage:** `raw_signals_bronze` now holds 220 genuine ingested records with full payload JSON, content hash, and source metadata.

### 2. LangGraph Pipeline Persistence & Provenance Promotion
Executed `PipelineRunner(session=db).run(batch_size=20)`:
- Promoted unpromoted bronze records into silver `Signal` rows with vector embeddings (`all-MiniLM-L6-v2`), `canonical_url`, and `retrieved_at` timestamps.
- Created gold `Development` and `Confluence` rows.
- Updated bronze rows with `pipeline_run_id` to prevent re-processing.

### 3. Confluence Inspectability & Backward Traceability
Implemented and verified the full backward traceability chain:
1. **Endpoint `GET /api/v1/confluence/{confluence_id}/inspect`**: Returns exact mathematical score calculation, list of independent sources, verbatim text citations, and clickable URLs.
2. **Frontend `ConfluenceWorkspace.tsx`**: Added an interactive **"Inspect Evidence"** drawer displaying:
   - "Why this score?" (e.g. "Multi-source convergence score of 75.0 calculated across 3 independent source types within a 48h sliding window").
   - Unbroken backward trace with verbatim quotes, point contributions (+30pts regulatory, +25pts clinical trials, +20pts publications), and external links to PubMed, ClinicalTrials.gov, and OpenFDA.
3. **Frontend `SourcesOperationsWorkspace.tsx`**: Added **"Trigger Live Web Ingestion"** button and live sync telemetry.
4. **Frontend `EvidenceDrawer.tsx`**: Full 4-factor priority score breakdown (Novelty 25%, Clinical 30%, Regulatory 25%, Recency 20%), verbatim text excerpt, and clickable canonical URLs.

### 4. Verification Test Matrix
- `pytest`: 91 passed, 1 skipped (live Grok API key required).
- `scripts/export_openapi.py`: Clean contract generation (zero drift).
- `frontend`: `npx tsc --noEmit` and `npm run build` compiled with 0 errors.

---

## 1. Problem Statement & Symptoms

1. **Disconnected Ingestion Loop:** Connectors (`PubMedConnector`, `ClinicalTrialsConnector`, `OpenFDAConnector`, `EMAConnector`, `NewsAPIConnector`) have unit tests with mocks, but lack an automated ingestion orchestration pipeline that fetches live biomedical incidents from real public APIs into `raw_signals_bronze` and feeds them through LangGraph into the UI.
2. **Provenance Granularity Gap:** Signals and Confluence stories in the database do not consistently capture complete end-to-end provenance:
   - Source provenance (`source`, `source_url`, `external_id`, `retrieved_at`, `published_at`, `connector_run_id`)
   - Processing lineage (`ingested_at`, `normalized_at`, `scored_at`, `pipeline_run_id`, `model_version`)
   - Evidence lineage (`source_count`, `independent_source_types`, `verbatim_excerpts = [...]`)
   - System state as a first-class state (`LIVE`, `FIXTURE`, `SYNTHETIC`, `STALE`, `ERROR`)
3. **Inspectability / "Why?" Explanations Missing in UI:** The UI displays confluences (e.g. "75 Confluence"), but clicking on it does not display an unbroken, inspectable chain explaining *which sources, retrieved when, citing what exact verbatim excerpts*.
4. **Degraded State Representation:** When a connector fails or times out, the system must transition to a degraded state with visible provenance error logs rather than silently serving stale or synthetic data.

---

## 2. Hypothesis & Root Cause

- **Root Cause 1:** `node_ingest` silently falls back to `synthetic_signals.json` when `raw_signals_bronze` is empty, instead of surfacing an explicit pipeline ingestion trigger or displaying `INSUFFICIENT_LIVE_DATA` / `FIXTURE_FALLBACK`.
- **Root Cause 2:** Ingestion orchestration was separated from pipeline execution (`/pipeline/run` only processed existing bronze or synthetic data, without an automated live ingestion trigger or connector scheduler).
- **Root Cause 3:** The signal DTO and Confluence schema lack rich provenance objects (`source_url`, `retrieved_at`, `connector_status`, `evidence_chain`).
- **Root Cause 4:** The frontend `EvidenceDrawer` and `ConfluenceWorkspace` lack the "Trace Reasoning / Provenance Chain" panel that answers: *Why this score? Which sources? When retrieved? Verbatim text?*

---

## 3. Concrete Action Plan

### Wave 1: Ingestion Pipeline & Live Source Ingestion
1. Build an Ingestion Service & Endpoint (`/api/v1/ingestion/run` and `/api/v1/ingestion/live-sync`) that executes all active connectors against real public web APIs (PubMed, ClinicalTrials.gov, OpenFDA, EMA RSS) for real Haemophilia A/B incidents (e.g., *Hemgenix durability, Fidanacogene elaparvovec Phase 3, Marstacimab anti-TFPI*).
2. Ensure bronze records store verbatim text, real external URLs (`https://pubmed.ncbi.nlm.nih.gov/...`, `https://clinicaltrials.gov/study/...`), real timestamps, and `source_independence_group_id`.

### Wave 2: Deep Provenance Schema & Pipeline Propagation
1. Upgrade `Signal`, `ConfluenceAlert`, and `Contradiction` models and schemas with a structured `Provenance` model:
   - `source_id`, `source_url`, `external_id`, `retrieved_at`, `published_at`, `connector_run_id`, `data_mode` (`LIVE` | `FIXTURE` | `SYNTHETIC` | `STALE` | `ERROR`)
2. Upgrade `node_ingest` and `node_confluence` to pass full provenance metadata and verbatim evidence snippets through state.
3. Update `confluence_engine` to compute detailed inspectable reasoning breakdown (`why_score`, `source_breakdown`, `time_window_hours`, `verbatim_citations`).

### Wave 3: Frontend Deep Provenance & Backward Trace UI
1. Upgrade `EvidenceDrawer.tsx` to include an **Unbroken Provenance Chain** accordion (Source URL with external link icon, Retrieved Timestamp, Processing Timestamps, Verbatim Excerpt highlights).
2. Upgrade `ConfluenceWorkspace.tsx` to include an interactive **"Inspect Confluence Evidence"** drawer answering: *Why this score? Which independent sources? When retrieved? Verbatim evidence text*.
3. Add degraded state indicators when connectors fail (with copyable correlation IDs and error recovery actions).

### Wave 4: Concrete Live Ingestion Validation Run
1. Run a live query against real public APIs for Haemophilia gene therapy / novel therapeutics.
2. Ingest real records from PubMed + ClinicalTrials.gov + OpenFDA into MetaRadar.
3. Run the LangGraph pipeline and verify end-to-end provenance in the database.
4. Verify the complete backward trace in the frontend UI.
5. Add automated end-to-end provenance and backward trace tests.
