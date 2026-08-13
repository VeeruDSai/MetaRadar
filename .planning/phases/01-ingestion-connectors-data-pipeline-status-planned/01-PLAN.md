# Phase 1 Plan: Ingestion Connectors & Data Pipeline

> **Phase Status:** PLANNED — ready for execution
> **Target Branch:** `feature/phase-1-ingestion`
> **Specification Authority:** `docs/METARADAR_MASTER_PLAN_v5.0.md` §4 (node_ingest/node_validate) · `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §2.1 · `docs/2_SRS_Software_Requirements_Specification.md` §3.1
> **Context Source:** `.planning/phases/01-ingestion-connectors-data-pipeline-status-planned/01-CONTEXT.md`

---

## 1. Goal & Scope

Implement production-grade `SourceConnector` adapters for five external sources: NCBI PubMed E-utilities, ClinicalTrials.gov APIv2, NewsAPI, OpenFDA, and EMA RSS. Persist verbatim raw payloads into `raw_signals_bronze` (append-only, immutable provenance). Wire the deterministic deduplication and source-independence layer that runs **before** any Phase 2 Confluence step. Deliver per-connector incremental state tracking, honest quota/run observability, and a 15-point ingest pytest suite.

**Phase 1 is bronze-only.** Promotion of bronze rows into the canonical `signals`/`evidence` layer is Phase 2. Connectors do not generate intelligence and do not bypass the entity/evidence layer.

---

## 2. Requirements & Verification Matrix

| ID | Requirement | Implementation Target | Verification Command | Status |
|---|---|---|---|---|
| REQ-P1-1 | PubMed connector: async, quota-free, incremental, haemophilia query profiles | `backend/app/connectors/pubmed.py` | `pytest tests/test_ingestion.py::test_pubmed_connector` | PLANNED |
| REQ-P1-2 | ClinicalTrials.gov connector: async, APIv2, incremental, NCT-fingerprinted | `backend/app/connectors/clinical_trials.py` | `pytest tests/test_ingestion.py::test_clinical_trials_connector` | PLANNED |
| REQ-P1-3 | NewsAPI connector: quota-aware (100 req/day), DEGRADED on exhaustion, rolling window | `backend/app/connectors/newsapi.py` | `pytest tests/test_ingestion.py::test_newsapi_connector` | PLANNED |
| REQ-P1-4 | OpenFDA connector: async, adapter-ready status, regulatory fingerprinting | `backend/app/connectors/fda.py` | `pytest tests/test_ingestion.py::test_fda_connector` | PLANNED |
| REQ-P1-5 | EMA RSS connector: adapter-ready, XML parse, regulatory-id fingerprint | `backend/app/connectors/ema.py` | `pytest tests/test_ingestion.py::test_ema_connector` | PLANNED |
| REQ-P1-6 | Bronze layer: verbatim raw_payload JSONB, SHA-256 content_hash, unique (source_id, external_id) | `backend/app/models/__init__.py` (existing) + Alembic migration | `pytest tests/test_ingestion.py::test_bronze_persistence` | PLANNED |
| REQ-P1-7 | Deduplication: fingerprint priority chain (pmid -> nct -> reg -> hash), skip + log on collision | `backend/app/services/deduplication.py` (extend) | `pytest tests/test_ingestion.py::test_deduplication` | PLANNED |
| REQ-P1-8 | Source-independence classifier: cross_source_group_id assigned from fingerprint + entity overlap | `backend/app/services/source_independence.py` (new) | `pytest tests/test_ingestion.py::test_source_independence` | PLANNED |
| REQ-P1-9 | connector_state table: per-connector per-profile last_success, cursor, next_run | Alembic migration + `backend/app/models/__init__.py` | `pytest tests/test_ingestion.py::test_connector_state` | PLANNED |
| REQ-P1-10 | Incremental run: rolling window + first-run backfill + force-backfill replay (append-only) | All connectors via base class + state table | `pytest tests/test_ingestion.py::test_incremental_fetch` | PLANNED |
| REQ-P1-11 | Honest run status: SUCCESS / PARTIAL / DEGRADED / FAILED per pipeline_runs + connector_state | `backend/app/connectors/base.py` (extend) | `pytest tests/test_ingestion.py::test_run_status_states` | PLANNED |
| REQ-P1-12 | haemophilia.yaml query blocks: per-source, multi-profile, asset synonyms, cross-source rules | `config/haemophilia.yaml` + `domain_config.py` extended | `pytest tests/test_ingestion.py::test_domain_config_query_blocks` | PLANNED |
| REQ-P1-13 | `/health/connectors` honest status: quota_remaining, last_success, last_error per source | `backend/app/api/v1/endpoints/health.py` (extend) | `pytest tests/test_ingestion.py::test_health_connectors_endpoint` | PLANNED |
| REQ-P1-14 | PII scrub runs before bronze persistence | `backend/app/services/pii.py` (existing) called at intake | `pytest tests/test_ingestion.py::test_pii_scrub_at_intake` | PLANNED |
| REQ-P1-15 | All previous 18 Phase 0 tests continue to pass | `tests/` (existing suite) | `pytest -v` (18 + 15 = 33 total) | PLANNED |

---

## 3. Architecture & Design Decisions

All decisions are captured in `01-CONTEXT.md` (D-01 through D-26). Key anchors:

- **D-01/D-06:** Connectors are isolated, idempotent, observable, replayable. Never generate intelligence.
- **D-02/D-23:** Bronze rows are append-only, provenance-preserving. `raw_payload` = verbatim source response.
- **D-03:** Dedup and source-independence run before Confluence (Phase 2).
- **D-08/D-10:** Per-source YAML query blocks in `config/haemophilia.yaml`; multi-profile per source.
- **D-11/D-13:** `connector_state` table (DB-persisted, Alembic migration); force-backfill replay = append new rows.
- **D-15/D-17:** Fingerprint priority chain from existing `generate_fingerprint` + cross-source classifier emits `cross_source_group_id`.
- **D-19:** Retry/backoff built into connector base using `httpx` (no new dependencies; tenacity NOT added).
- **D-20:** NewsAPI: quota-aware, halts on exhaustion, reports DEGRADED.

---

## 4. Implementation Plan

### Wave 1 — Foundation (branch, schema, config extensions)

#### 4.1 Create Feature Branch
```
git checkout -b feature/phase-1-ingestion origin/feature/stabilization-baseline
```

#### 4.2 Extend `config/haemophilia.yaml` with Connector Query Blocks

Add a top-level `connectors:` key and `cross_source:` key:

```yaml
connectors:
  pubmed:
    freshness_class: batch
    backfill_days: 180
    rolling_window_days: 30
    max_results_per_profile: 200
    profiles:
      - id: haemophilia_clinical
        queries:
          - "haemophilia AND (emicizumab OR fitusiran OR marstacimab OR concizumab)"
          - "haemophilia gene therapy AND (Hemgenix OR Roctavian OR fidanacogene)"
      - id: haemophilia_safety
        queries:
          - "haemophilia inhibitor safety"
      - id: competitive_news
        queries:
          - "mim8 OR fitusiran OR concizumab clinical trial"

  clinical_trials:
    freshness_class: near_real_time
    backfill_days: 365
    rolling_window_days: 30
    max_results_per_profile: 500
    profiles:
      - id: haemophilia_trials
        conditions: ["hemophilia A", "hemophilia B", "haemophilia"]
        interventions: ["emicizumab", "fitusiran", "marstacimab", "concizumab", "mim8", "fidanacogene", "etranacogene"]
      - id: novo_pipeline
        sponsor_keywords: ["Novo Nordisk"]
        conditions: ["hemophilia A", "hemophilia B"]

  newsapi:
    freshness_class: delayed
    quota_per_day: 100
    backfill_days: 30
    rolling_window_days: 7
    profiles:
      - id: haemophilia_market
        query: "haemophilia OR hemophilia (Roche OR CSL OR Novo OR Sanofi OR BioMarin)"
        language: en
      - id: gene_therapy_news
        query: "gene therapy haemophilia hemophilia"
        language: en

  fda:
    freshness_class: adapter_ready
    base_url: "https://api.fda.gov/drug/drugsfda.json"
    backfill_days: 365
    rolling_window_days: 30
    profiles:
      - id: haemophilia_approvals
        search_terms: ["hemophilia", "haemophilia", "emicizumab", "fitusiran", "etranacogene"]

  ema:
    freshness_class: adapter_ready
    rss_url: "https://www.ema.europa.eu/en/medicines/rss"
    backfill_days: 365
    rolling_window_days: 30
    profiles:
      - id: haemophilia_ema
        keywords: ["haemophilia", "hemophilia", "emicizumab", "fitusiran"]

cross_source:
  group_assignment:
    title_similarity_threshold: 0.85
    date_window_hours: 48
    entity_overlap_min: 2
```

#### 4.3 Extend `domain_config.py` with ConnectorConfig Models

Add Pydantic models: `ConnectorQueryProfile`, `ConnectorConfig`, `CrossSourceGroupConfig`, `CrossSourceConfig`. Extend `DomainConfig` with optional `connectors: Dict[str, ConnectorConfig] = {}` and `cross_source: Optional[CrossSourceConfig] = None`. Backward-compatible — existing config without these keys loads without error.

#### 4.4 Alembic Migration: `connector_state` table + `cross_source_group_id` column

New migration `backend/alembic/versions/xxxx_phase1_connector_state_and_cross_source.py`:

```python
# Up:
op.create_table("connector_state",
    sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
    sa.Column("source_id", sa.String(100), nullable=False),
    sa.Column("profile_id", sa.String(100), nullable=False),
    sa.Column("last_success", sa.DateTime(timezone=True), nullable=True),
    sa.Column("cursor", sa.Text, nullable=True),
    sa.Column("next_run_after", sa.DateTime(timezone=True), nullable=True),
    sa.Column("first_run_completed", sa.Boolean, nullable=False, server_default="false"),
    sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    sa.UniqueConstraint("source_id", "profile_id", name="uq_connector_state_source_profile"),
)
op.add_column("raw_signals_bronze",
    sa.Column("cross_source_group_id", postgresql.UUID(as_uuid=True), nullable=True))
```

Also add `ConnectorState` ORM model to `backend/app/models/__init__.py`.

---

### Wave 2 — Connector Base & Core Live Sources (PubMed + ClinicalTrials)

#### 4.5 Extend `backend/app/connectors/base.py`

Add to `SourceConnector`:

```python
from dataclasses import dataclass, field
from typing import Optional, List, Literal

RunStatus = Literal["SUCCESS", "PARTIAL", "DEGRADED", "FAILED"]

@dataclass
class ProfileRunResult:
    profile_id: str
    status: RunStatus
    fetched: int = 0
    new_rows: int = 0
    duplicates: int = 0
    errors: int = 0
    duration_s: float = 0.0
    error_detail: Optional[str] = None
```

New methods on `SourceConnector`:
- `async def _fetch_with_retry(url, params, headers) -> httpx.Response` — bounded exponential backoff + jitter (max `max_retries=3`, base `1.5s`); raises `ConnectorFetchError` after exhaustion
- `async def run_profile(session, profile_id, force_backfill=False) -> ProfileRunResult` — abstract, overridden per connector
- `async def run_all_profiles(session, force_backfill=False) -> List[ProfileRunResult]` — calls all profiles, resolves consolidated status
- `_resolve_run_status(results: List[ProfileRunResult]) -> RunStatus` — all OK=SUCCESS; some OK=PARTIAL; quota-blocked=DEGRADED; all failed=FAILED
- `async def _persist_bronze(session, payloads, pipeline_run_id) -> tuple[int, int]` — returns (new_rows, duplicates); catches UniqueViolation silently
- `async def _read_connector_state(session, profile_id) -> Optional[ConnectorState]`
- `async def _write_connector_state(session, profile_id, last_success, cursor, first_run_completed)`

#### 4.6 `backend/app/connectors/pubmed.py` — PubMedConnector

```python
class PubMedConnector(SourceConnector):
    source_id = "pubmed"
    freshness_class = "batch"
    BASE_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    BASE_EFETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
```

`run_profile` contract:
1. Read `ConnectorState` — determine date window (first run: backfill_days; subsequent: since last_success; force: backfill_days)
2. For each query in profile: `esearch.fcgi?db=pubmed&term={q}&datetype=pdat&mindate={from}&maxdate={today}&retmax=200&retmode=json`
3. Collect + deduplicate PMIDs across queries
4. Batch `efetch.fcgi?db=pubmed&id={pmids}&retmode=xml&rettype=abstract` (200 per batch; 350ms between batches)
5. Parse XML with `xml.etree.ElementTree` — extract PMID, title, abstract, journal, pub_date, MeSH terms
6. PII-scrub abstract via `PIIPHIScrubber.scrub()`
7. Fingerprint: `generate_fingerprint(pmid=pmid)` -> `"pmid:{pmid}"`
8. `content_hash = sha256(f"{pmid}:{abstract_text}".encode()).hexdigest()`
9. Persist via `_persist_bronze`; update `ConnectorState`

Tolerates missing fields (title/abstract/pubdate may be absent).

#### 4.7 `backend/app/connectors/clinical_trials.py` — ClinicalTrialsConnector

```python
class ClinicalTrialsConnector(SourceConnector):
    source_id = "clinical_trials"
    freshness_class = "near_real_time"
    BASE_URL = "https://clinicaltrials.gov/api/v2/studies"
```

`run_profile` contract:
- Query APIv2 with condition + intervention filters + `lastUpdatePostDate` range
- Paginate via `nextPageToken` until exhausted (max per config)
- Extract: NCT ID, title, status, sponsor, phase, dates, interventions, conditions
- Fingerprint: `generate_fingerprint(nct_id=nct_id)` -> `"nct:{NCTXXXXXXXX}"`
- Store verbatim JSON study object as `raw_payload`

#### 4.8 `backend/app/connectors/newsapi.py` — NewsAPIConnector

```python
class NewsAPIConnector(SourceConnector):
    source_id = "newsapi"
    freshness_class = "delayed"
    BASE_URL = "https://newsapi.org/v2/everything"
```

Quota contract:
- Before each request: read `quota_remaining` from `ConnectorState.cursor` (JSON-encoded `{"quota_remaining": N, "quota_window_date": "YYYY-MM-DD"}`)
- If `quota_remaining <= 0` and `quota_window_date == today`: return `ProfileRunResult(status="DEGRADED", fetched=0)` immediately
- If `settings.NEWSAPI_KEY is None`: return `ProfileRunResult(status="DEGRADED", error_detail="NEWSAPI_KEY not set")`
- After each response: update `quota_remaining` from `X-RateLimit-Remaining` header
- Fingerprint: normalized title+publisher+date hash (no PMID/NCT for news articles)

#### 4.9 `backend/app/connectors/fda.py` — OpenFDAConnector

```python
class OpenFDAConnector(SourceConnector):
    source_id = "fda"
    freshness_class = "adapter_ready"
    BASE_URL = "https://api.fda.gov/drug/drugsfda.json"
```

- Query `drugsfda.json` with `search=openfda.substance_name:{term}` for each search term
- Extract: application_number (-> regulatory_id), brand_name, sponsor_name, action_date
- Fingerprint: `generate_fingerprint(regulatory_id=application_number)` -> `"reg:{application_number}"`
- Store verbatim JSON as `raw_payload`

#### 4.10 `backend/app/connectors/ema.py` — EMARSSConnector

```python
class EMARSSConnector(SourceConnector):
    source_id = "ema"
    freshness_class = "adapter_ready"
```

- Fetch RSS feed via `httpx`; parse with `xml.etree.ElementTree`
- Filter items by keyword match (title + description vs profile keywords)
- Extract: guid (-> regulatory_id), title, description, published_date, link
- Fingerprint: `generate_fingerprint(regulatory_id=guid_normalized)` -> `"reg:{guid}"`
- Store verbatim XML fragment (JSON-encoded string) as `raw_payload`

#### 4.11 `backend/app/connectors/__init__.py` — Connector Registry

```python
from .pubmed import PubMedConnector
from .clinical_trials import ClinicalTrialsConnector
from .newsapi import NewsAPIConnector
from .fda import OpenFDAConnector
from .ema import EMARSSConnector

ALL_CONNECTORS = [
    PubMedConnector(),
    ClinicalTrialsConnector(),
    NewsAPIConnector(),
    OpenFDAConnector(),
    EMARSSConnector(),
]
```

---

### Wave 3 — Deduplication Extension & Source-Independence Classifier

#### 4.12 Extend `backend/app/services/deduplication.py`

Backward-compatible additions only:

```python
DuplicationResult = Literal["new", "duplicate"]

async def check_and_persist_bronze(
    session: AsyncSession,
    payload: RawSignalPayload,
    pipeline_run_id: Optional[uuid.UUID] = None,
) -> DuplicationResult:
    """
    Attempts to insert a RawSignalBronze row.
    Returns 'duplicate' (and logs) on (source_id, external_id) collision.
    Never raises on collision — immutable original row is preserved.
    """
```

#### 4.13 `backend/app/services/source_independence.py` (NEW)

```python
class SourceIndependenceClassifier:
    """
    Classifies cross-source identity BEFORE Confluence (Phase 2).
    Emits cross_source_group_id for node_confluence consumption.
    """
    def __init__(self, config: CrossSourceConfig): ...

    async def classify(
        self,
        session: AsyncSession,
        fingerprint: str,
        title: str,
        published_at: datetime,
        entities: List[str],
    ) -> Optional[str]:
        """
        Returns UUID group_id string.
        Matches existing group if title_similarity >= threshold AND entity_overlap >= min
        within date_window_hours; else creates new group.
        """
```

Algorithm:
1. Query `raw_signals_bronze` rows within `date_window_hours` of `published_at` (excluding same `fingerprint`)
2. For each candidate: compute normalized token overlap ratio between titles
3. If `ratio >= threshold` AND shared entity count `>= entity_overlap_min`: assign candidate's `cross_source_group_id`
4. Else: generate `str(uuid.uuid4())` as new group ID
5. Update `raw_signals_bronze.cross_source_group_id` for the current row

---

### Wave 4 — Health Endpoint Extension

#### 4.14 Extend `backend/app/api/v1/endpoints/health.py`

Wire live connector instances:

```python
from app.connectors import ALL_CONNECTORS

@router.get("/connectors", response_model=HealthConnectorsResponse)
async def health_connectors(session: AsyncSession = Depends(get_async_session)):
    statuses = []
    for connector in ALL_CONNECTORS:
        status = connector.get_status()  # reads from ConnectorState table via session
        statuses.append({
            "source_id": status.source_id,
            "status": status.status,
            "freshness_class": connector.freshness_class,
            "quota_remaining": status.quota_remaining,
            "last_success": status.last_success,
            "last_error": status.last_error,
        })
    return HealthConnectorsResponse(connectors=statuses)
```

`get_status()` in base must accept optional `session` parameter and read `ConnectorState` for accurate `last_success`/`quota_remaining` rather than returning only in-memory fields.

> [!NOTE]
> Zero new Python dependencies. `xml.etree.ElementTree` handles both PubMed XML and EMA RSS. Only add a dependency if stdlib is genuinely insufficient after implementation attempt.

---

### Wave 5 — Test Suite

#### 4.15 `tests/test_ingestion.py` — 15-Point Ingest Test Suite

All tests: `pytest-asyncio`, `unittest.mock.patch` / `AsyncMock` — **no live API calls in CI**.

| Test ID | Test Name | What It Verifies |
|---|---|---|
| T-P1-01 | `test_pubmed_connector` | `PubMedConnector.run_profile` parses mocked esearch/efetch XML -> `RawSignalPayload` with `pmid:` fingerprint |
| T-P1-02 | `test_pubmed_pii_scrub` | `PIIPHIScrubber.scrub` called on abstract before bronze persist |
| T-P1-03 | `test_clinical_trials_connector` | `ClinicalTrialsConnector.run_profile` paginates mocked APIv2 JSON -> NCT-fingerprinted payloads |
| T-P1-04 | `test_newsapi_connector` | `NewsAPIConnector.run_profile` returns payloads; `quota_remaining` tracked from mock response header |
| T-P1-05 | `test_newsapi_quota_exhaustion` | When `quota_remaining=0`: `ProfileRunResult(status="DEGRADED", fetched=0)` — no raise |
| T-P1-06 | `test_fda_connector` | `OpenFDAConnector.run_profile` parses mocked FDA JSON -> `reg:` fingerprinted bronze rows |
| T-P1-07 | `test_ema_connector` | `EMARSSConnector.run_profile` parses mocked RSS XML -> `reg:` fingerprinted bronze rows |
| T-P1-08 | `test_bronze_persistence` | `check_and_persist_bronze` writes `RawSignalBronze` with correct `content_hash` and verbatim `raw_payload` |
| T-P1-09 | `test_deduplication_skip` | Second call with same `(source_id, external_id)` returns `"duplicate"`; does not raise; original row unchanged |
| T-P1-10 | `test_source_independence_new_group` | First signal -> new UUID `cross_source_group_id` assigned |
| T-P1-11 | `test_source_independence_existing_group` | Signal with high title similarity + entity overlap -> existing group ID returned |
| T-P1-12 | `test_connector_state_incremental` | After `run_profile`, `ConnectorState.last_success` updated; second run uses rolling window (not backfill) |
| T-P1-13 | `test_run_status_states` | All-OK -> SUCCESS; one DEGRADED -> PARTIAL; all failed -> FAILED |
| T-P1-14 | `test_health_connectors_endpoint` | `GET /api/v1/health/connectors` returns all 5 sources with `freshness_class`, `quota_remaining`, `status` |
| T-P1-15 | `test_domain_config_query_blocks` | `get_domain_config()` loads extended `haemophilia.yaml` -> `config.connectors["pubmed"].profiles` accessible |

All 15 must pass alongside 18 Phase 0 tests (33 total green).

---

## 5. File Manifest

### New Files

| File | Description |
|---|---|
| `backend/app/connectors/pubmed.py` | PubMedConnector — NCBI E-utilities async adapter |
| `backend/app/connectors/clinical_trials.py` | ClinicalTrialsConnector — APIv2 async adapter |
| `backend/app/connectors/newsapi.py` | NewsAPIConnector — quota-aware async adapter |
| `backend/app/connectors/fda.py` | OpenFDAConnector — adapter-ready FDA regulatory source |
| `backend/app/connectors/ema.py` | EMARSSConnector — adapter-ready EMA RSS XML parser |
| `backend/app/connectors/__init__.py` | Connector registry (ALL_CONNECTORS) |
| `backend/app/services/source_independence.py` | SourceIndependenceClassifier — cross-source group assignment |
| `backend/alembic/versions/xxxx_phase1_connector_state_and_cross_source.py` | Alembic migration: `connector_state` table + `cross_source_group_id` on `raw_signals_bronze` |
| `tests/test_ingestion.py` | 15-point ingest pytest suite |

### Modified Files

| File | What Changes |
|---|---|
| `backend/app/connectors/base.py` | Add retry, `ProfileRunResult`, `run_profile`, `run_all_profiles`, `_persist_bronze`, `ConnectorState` I/O |
| `backend/app/models/__init__.py` | Add `ConnectorState` ORM; add `cross_source_group_id` to `RawSignalBronze` |
| `backend/app/core/domain_config.py` | Add `ConnectorQueryProfile`, `ConnectorConfig`, `CrossSourceConfig`; extend `DomainConfig` |
| `backend/app/services/deduplication.py` | Add `check_and_persist_bronze`, export `DuplicationResult` |
| `backend/app/api/v1/endpoints/health.py` | Wire `ALL_CONNECTORS` into `/health/connectors` |
| `config/haemophilia.yaml` | Add `connectors:` block and `cross_source:` config |

---

## 6. Engineering Standards Compliance

Per `docs/rules/ENGINEERING_STANDARDS.md` and `docs/rules/DEFINITION_OF_DONE.md`:

- **Type Safety:** All new modules fully type-annotated; no `Any` escape hatches
- **No fabricated telemetry:** `SUCCESS/PARTIAL/DEGRADED/FAILED` derived from real outcomes — never hardcoded
- **No secret leaks:** `NEWSAPI_KEY` from env only — never in YAML, never committed
- **PII/PHI:** `PIIPHIScrubber.scrub()` on all text content before bronze persistence
- **Idempotency:** Force-backfill appends new rows, never overwrites
- **Honest health:** `/health/connectors` reads live `ConnectorState` — no stale or fabricated values
- **Atomic commits:** One logical change per commit
- **Branch:** `feature/phase-1-ingestion` branched from `feature/stabilization-baseline`

---

## 7. Definition of Done (Phase 1)

Phase 1 is **COMPLETE** when ALL of the following gates pass with real command output:

```powershell
# Gate 1: All 33 tests pass (18 Phase 0 + 15 Phase 1)
pytest tests/ -v
# Expected: 33 passed

# Gate 2: TypeScript typecheck clean
cd frontend && pnpm exec tsc --noEmit
# Expected: 0 errors

# Gate 3: ESLint clean
pnpm exec eslint .
# Expected: 0 warnings, 0 errors

# Gate 4: Next.js build passes
pnpm build
# Expected: compiled successfully

# Gate 5: Alembic migration valid
cd ..\backend
python -c "from alembic.config import Config; from alembic import command; c = Config('alembic.ini'); command.check(c)"
# Expected: no errors

# Gate 6: Domain config loads with query blocks
python -c "from app.core.domain_config import get_domain_config; c = get_domain_config(); assert 'pubmed' in c.connectors; print('OK')"
# Expected: OK

# Gate 7: Docker Compose config validates
docker compose config
# Expected: valid, no warnings
```

> [!CAUTION]
> No gate may be marked PASS without the command having been run and producing the expected output. Fabricated PASS status violates `docs/rules/ENGINEERING_STANDARDS.md`.

---

## 8. Deferred (Out of Scope for Phase 1)

- **APScheduler polling loop** — connectors invoked on-demand; autonomous scheduler is Phase 2+
- **Bronze -> signals promotion** (`node_ingest` / `node_validate`) — Phase 2
- **Confluence detection** consuming `cross_source_group_id` — Phase 2
- **spaCy NER / ontology enrichment** — Phase 2 (`node_nlp_extract` / `node_ontology_enrich`)
- **500-signal synthetic fallback dataset** — deferred; may be scaffolded as a static JSON file but not wired

---

*Plan authored: 2026-08-13*
*Phase: 1 — Ingestion Connectors & Data Pipeline*
*Status: PLANNED — ready for execution on `feature/phase-1-ingestion`*
