# MetaRadar v5.1 — Trustworthy Intelligence Reconciliation & Platform Hardening Specification

> **Document ID:** `docs/11_TRUSTWORTHY_INTELLIGENCE_RECONCILIATION_AND_PLATFORM_HARDENING.md`  
> **Status:** ACTIVE REFERENCE STANDARD & ROADMAP PHASE 07 CANONICAL SPECIFICATION  
> **Version:** 5.1-TRUST  
> **Target System:** MetaRadar v5.1 (FastAPI + Next.js 16 + PostgreSQL 16/pgvector + LangGraph + Gemma 3 / Grok Fallback)  
> **Execution Mandate:** Unified Single-Wave Execution (Continuous end-to-end completion without pausing between sub-stages)

---

## Executive Summary

MetaRadar is designed as a near-real-time competitive intelligence radar for biopharma decision-makers. Its core value proposition is:
> *"A conventional AI system summarizes documents. MetaRadar builds an evidence story around a development."*

This specification serves as the binding reference standard for **Phase 07: Trustworthy Intelligence Reconciliation & Platform Hardening**. This initiative reconciles the codebase, eliminates all placeholder and fabricated telemetry, enforces strict data provenance, upgrades operational observability, refactors the frontend into modular bounded contexts, hardens backend computation and migrations, and guarantees that every UI element truthfully reflects real backend computation and connector state.

---

## 1. Non-Negotiable Product Principles

Every component, API endpoint, database query, workflow node, and UI view must strictly adhere to the following twelve non-negotiable principles:

1. **NEVER Fabricate Intelligence**: If evidence does not exist or has not been computed, report "Insufficient evidence" or "Not computed". Never manufacture claims, connections, or summaries.
2. **NEVER Display Hardcoded Metrics as Computed**: Every score, percentage, momentum rating, or confidence value must originate from an actual mathematical or algorithmic calculation.
3. **NEVER Display "LIVE" Without Active Verification**: A data connector or source is marked "LIVE" / "HEALTHY" only if it has connected and fetched data within its freshness window. Configured credentials do not equal a live connection.
4. **NEVER Display "Confidence" Without Explicit Semantics**: Every confidence score must declare its type, methodology, mathematical version, and input parameters. Simple arithmetic heuristics must never be labeled "AI Confidence".
5. **NEVER Mask Unknown States as 0**: Missing data, unavailable endpoints, insufficient evidence, or uncomputed states must be explicitly typed (`null`, `unavailable`, `not_computed`), never collapsed to `0` or `0%`.
6. **NEVER Mix Synthetic Data Silently**: Synthetic fixtures, seed records, and demo data must carry explicit metadata (`is_synthetic: true`, `data_mode: "recorded_demo"`) and must be clearly distinguishable in the UI.
7. **NEVER Present Placeholder Evidence as Real**: Static mockup claims (e.g. `"Primary evidence claim for CLAIM..."`) must be completely excised from ingestion, synthesis, red-team analysis, and vector storage.
8. **NEVER Mask Backend/Frontend Errors Behind Empty States**: An API failure or network timeout must render an informative error state with a correlation ID, retry trigger, and diagnostic metadata—never a misleading "No items found".
9. **EVERY Derived Intelligence Output Must Have Provenance**: Every signal, development, confluence, contradiction, and Athena response must trace directly to immutable Bronze payloads, source URLs, timestamps, and pipeline run IDs.
10. **EVERY Computation Must Be Versioned and Reproducible**: Scoring models, confluence clustering, and contradiction engines must record calculation versions and input identifiers to allow full deterministic auditability.
11. **EVERY Major User-Facing State Must Distinguish 8 Canonical States**:
    - `loading`: Computation or network fetch in flight.
    - `success`: Valid data returned and rendered.
    - `empty`: Valid query executed, 0 records match criteria.
    - `stale`: Last known valid state displayed, freshness threshold exceeded.
    - `degraded`: Fallback provider or cached response active.
    - `unavailable`: Dependency offline or unconfigured.
    - `error`: Request failed, actionable diagnostic presented.
    - `not_computed`: Algorithm has not run for this entity.
12. **Truth in Implementation**: If a feature is not implemented, do not simulate it with cosmetic UI components. Either implement the real end-to-end pipeline or cleanly remove/defer the route from production navigation.

---

## 2. Complete System Map & Discrepancy Matrix Framework

### 2.1 End-to-End System Trace
The platform operates as a continuous data and reasoning pipeline across all bounded contexts:

```
[External Sources: PubMed, ClinicalTrials, NewsAPI, OpenFDA, EMA RSS]
                       │
                       ▼
        [Source Connectors (Rate Limits, Quotas, Retries)]
                       │
                       ▼
        [Bronze Ingestion (raw_signals_bronze + SHA-256)]
                       │
                       ▼
        [LangGraph 10-Node Intelligence Engine]
        ├── Node 1: Ingest & Deduplicate
        ├── Node 2: Entity Extract (haemophilia.yaml)
        ├── Node 3: Vector Embed (FastEmbed 384-dim)
        ├── Node 4: Confluence Cluster (48h window)
        ├── Node 5: Lifecycle FSM (9 stages)
        ├── Node 6: Red-Team Contradictions (19 rules)
        ├── Node 7: Missing Signal Monitor
        ├── Node 8: Role-Tailored Strategic Action
        ├── Node 9: Athena Synthesis (Local Gemma / Grok fallback)
        └── Node 10: Calibrate & Persist (PostgreSQL + pgvector)
                       │
                       ▼
        [FastAPI Application Tier (Pydantic v2, Structured Logs, Correlation IDs)]
                       │
                       ▼
        [Frontend Typed API Client (contracts/openapi.json -> frontend/types/api.ts)]
                       │
                       ▼
        [Next.js 16 Bounded Context Components & Workspaces]
```

### 2.2 Core Discrepancy Audit Matrix
The audit must systematically evaluate every system surface against the 4-tier matrix:

| Documented Behavior | Actual Code Implementation | Expected Product Behavior | Required Engineering Fix |
|:---|:---|:---|:---|
| **Priority Score (0-100)** | Hardcoded or defaults to 0 on unmapped models | Computed multi-factor score with transparent weight breakdown | Implement `PriorityScoringService` with novelty, clinical, regulatory, and recency components; return `score_breakdown` |
| **Confluence Score** | Returns static 75 in overview endpoints | Dynamic clustering across $\ge 3$ independent source types in 48h | Connect overview to real `Confluence` database records and computation engine |
| **Confidence Semantics** | Generic float `confidence: 0.85` across schemas | Explicitly typed and explained confidence metadata | Define `ConfidenceType` enum (`extraction`, `classification`, `heuristic`, `model`, `human`); expose method and version |
| **Source Health & "LIVE"** | Static `"LIVE"` badge displayed if connector is configured | Health reflects actual HTTP success, latency, error count, and last fetch timestamp | Persist real connector telemetry to `source_health_logs` table; display `HEALTHY`, `STALE`, `DEGRADED`, `ERROR` |
| **Athena Intelligence** | Static evidence strings returned during vector fallback | Actual pgvector cosine similarity retrieval with verbatim excerpts | Bind Athena directly to retrieved `Evidence` records; enforce FACT / INFERENCE / SUGGESTION taxonomy |
| **Red-Team Claims** | Mock excerpts (`"Primary claim for CLAIM..."`) | Actual verbatim source excerpts extracted from bronze records | Populate `claim_a_excerpt` and `claim_b_excerpt` from real linked evidence |
| **Missing Signals** | Synthetic percentages as overdue confidence | Finite state machine with monitoring windows and overdue day counts | Model states: `WITHIN_WINDOW`, `DUE`, `OVERDUE`, `SATISFIED`, `SUPPRESSED`, `INSUFFICIENT_DATA` |
| **Stakeholder Calibration** | GET requests mutate database; feedback reapplied infinitely | Idempotent runs with unapplied feedback lifecycle | Model `CalibrationRun` entity; mark feedback as `applied`; prevent GET side-effects |
| **Frontend Architecture** | Monolithic `metaradar.tsx` handling mixed concerns | Clean bounded context directories in `frontend/components/` | Modularize into `signals/`, `confluence/`, `contradictions/`, `observability/`, etc. |

---

## 3. Data Truthfulness & Synthetic Data Governance

### 3.1 Metadata Separation Schema
Every raw bronze record, normalized signal, evidence snippet, development, and derived intelligence item must declare its provenance and data mode:

```python
class DataMode(str, Enum):
    LIVE = "live"
    RECORDED_DEMO = "recorded_demo"
    TEST_FIXTURE = "test_fixture"
    BENCHMARK = "benchmark"

class ProvenanceStatus(str, Enum):
    VERIFIED_SOURCE = "verified_source"
    DERIVED_COMPUTATION = "derived_computation"
    SYNTHETIC_SIMULATION = "synthetic_simulation"
```

### 3.2 Ingestion & API Rules
- Live ingestion pipelines reject any payload marked with `is_synthetic: true` unless running in explicit local demo mode (`ENV=demo`).
- API responses include `is_synthetic: bool`, `data_mode: str`, and `provenance_status: str`.
- UI renders a high-visibility badge for non-live data:
  - `RECORDED DEMO DATA`: Amber border with tooltip explaining that the data is an archived scenario (e.g. Haemophilia A durability scenario).
  - `LIVE DATA`: Clean verified green badge displaying the exact timestamp of last source retrieval.

---

## 4. Intelligence Data Model & Provenance

### 4.1 Canonical Signal Entity
```python
class SignalIntelligence(BaseModel):
    id: UUID
    title: str
    content: str
    signal_type: str
    source_id: str
    source_name: str
    source_url: Optional[str]
    source_identifier: Optional[str]
    published_at: datetime
    retrieved_at: datetime
    processed_at: datetime
    freshness: str
    data_mode: DataMode
    is_synthetic: bool
    evidence_ids: List[UUID]
    confidence: float
    confidence_type: ConfidenceType
    confidence_rationale: str
    score: Optional[float]
    score_breakdown: Optional[Dict[str, float]]
    scoring_version: str
    processing_status: str
    pipeline_run_id: Optional[UUID]
    created_at: datetime
```

### 4.2 Derived Intelligence Provenance
All derived models (`ConfluenceAlert`, `ContradictionResult`, `MissingSignalWatch`, `AthenaResponse`) must contain:
- `calculation_version: str` (e.g. `confluence_v2.1`, `redteam_nli_v1.4`)
- `input_signal_ids: List[UUID]` / `evidence_ids: List[UUID]`
- `computed_at: datetime` (UTC)
- `computation_status: str` (`computed`, `insufficient_evidence`, `degraded`)

---

## 5. Scoring & Confluence Engines

### 5.1 Priority Scoring Engine
Priority scores ($P \in [0, 100]$) are calculated deterministically:
$$P = w_{\text{nov}} \cdot S_{\text{nov}} + w_{\text{clin}} \cdot S_{\text{clin}} + w_{\text{reg}} \cdot S_{\text{reg}} + w_{\text{rec}} \cdot S_{\text{rec}}$$

- **Novelty ($S_{\text{nov}}$)**: Distance to nearest semantic neighbor in vector space.
- **Clinical Significance ($S_{\text{clin}}$)**: Mention of primary endpoints, Factor VIII/IX expression levels, inhibitor emergence, or pivotal trial phases.
- **Regulatory Relevance ($S_{\text{reg}}$)**: PDUFA dates, CHMP opinions, CRLs, breakthrough designations, or black box warnings.
- **Recency ($S_{\text{rec}}$)**: Exponential decay function based on elapsed hours since publication.

If any factor cannot be evaluated due to missing fields, the API returns `score: null` and `status: "not_computed"` with an explanation.

### 5.2 Confluence Engine
Confluence represents multi-source corroboration. A valid confluence alert requires:
- $\ge 3$ independent signal sources (e.g., ClinicalTrials.gov + PubMed + EMA Press).
- Signals published within a sliding convergence window (typically 48 hours).
- Matching canonical biomedical entities (e.g., Asset: *Mim8*, Indication: *Haemophilia A*).

The UI displays the exact contribution of each source and links directly to each supporting evidence item.

---

## 6. Athena AI & Red-Team Intelligence

### 6.1 Athena RAG & Privacy Guardrails
1. **Retrieval**: Questions trigger pgvector HNSW cosine similarity search over chunked `Evidence` records ($K=5$, similarity threshold $\ge 0.72$).
2. **Zero Fabrication**: If no chunks meet the threshold, Athena responds:
   > *"No sufficiently relevant evidence was found in the indexed sources to answer this question."*
3. **Response Taxonomy**: Generated text must categorize bullet points:
   - `[FACT]`: Direct statements with linked source citations `[Source: NCT04204161]`.
   - `[INFERENCE]`: Logical extrapolations derived by the model from factual premises.
   - `[SUGGESTION]`: Recommended strategic actions for stakeholder functions.
4. **Privacy Gate**: All queries pass through `PIIPHIScrubber` prior to sending to external providers (xAI Grok fallback).

### 6.2 Red-Team Contradiction Engine
- Every detected contradiction must link two concrete evidence records (`claim_a_id`, `claim_b_id`) with verbatim excerpts.
- Contradiction rules map to the 19 canonical clinical rules (e.g., Rule A: Efficacy Durability Contradiction, Rule B: Safety/Adverse Event Discrepancy).
- Synthetic placeholder claims are prohibited.

---

## 7. Operational Observability & Source Health

### 7.1 Structured Logging Standard
All log messages across backend services, connectors, workflow nodes, and API routes must be emitted in structured JSON:

```json
{
  "timestamp": "2026-08-20T12:00:00.000Z",
  "level": "INFO",
  "service": "metaradar-backend",
  "event": "connector.fetch_completed",
  "request_id": "req-982a-4f",
  "trace_id": "tr-771b-2c",
  "pipeline_run_id": "run-0191-44",
  "component": "ClinicalTrialsConnector",
  "duration_ms": 342,
  "status": "success",
  "records_fetched": 14,
  "records_accepted": 12,
  "records_rejected": 2,
  "error_code": null,
  "data_mode": "live"
}
```

### 7.2 Correlation IDs
- FastApi middleware generates or propagates `X-Request-ID` and `X-Correlation-ID`.
- Frontend API client sends `X-Request-ID` with every fetch and displays it in all error notifications and modals.
- Backend background tasks assign a persistent `pipeline_run_id` across all 10 LangGraph nodes.

### 7.3 Canonical Source Health States
- `HEALTHY`: Successful fetch within expected polling window; error rate 0%.
- `DEGRADED`: High latency (>3000ms) or non-fatal parse errors.
- `STALE`: Freshness window exceeded without new data.
- `RATE_LIMITED`: HTTP 429 received; exponential backoff active with retry timestamp.
- `AUTH_FAILED`: HTTP 401/403 received; credentials require operational attention.
- `ERROR`: Unhandled exception or repeated connection timeouts.
- `DISABLED`: Connector administratively disabled in settings.
- `NEVER_CONNECTED`: Connector initialized but no connection attempted yet.

---

## 8. Frontend Architecture & Error UX

### 8.1 Modular Bounded-Context Directory Layout
Refactor frontend components out of monolithic files into distinct domain packages:

```
frontend/
├── app/
│   ├── layout.tsx
│   ├── page.tsx                  # Overview
│   ├── signals/page.tsx          # Signals Workspace
│   ├── confluence/page.tsx       # Confluences Workspace
│   ├── contradictions/page.tsx   # Red-Team Workspace
│   ├── missing-signals/page.tsx  # Missing Signals Workspace
│   ├── developments/page.tsx     # Developments Registry
│   ├── intelligence/page.tsx     # Athena AI Workspace
│   ├── functions/page.tsx        # Stakeholder Functions Workspace
│   ├── calibration/page.tsx      # Calibration Workspace
│   ├── sources/page.tsx          # Operations & Sources
│   ├── activity/page.tsx         # System Health & Activity Stream
│   └── settings/page.tsx         # Configuration Workspace
├── components/
│   ├── layout/                   # Shell, Navigation, TopNav, FilterBar
│   ├── ui/                       # Base-Nova buttons, badges, modals, drawers
│   ├── signals/                  # SignalCard, SignalTable, SignalFilter
│   ├── confluence/               # ConfluenceRadar, ConfluenceBreakdown
│   ├── contradictions/           # ContradictionCard, ClaimCompareDrawer
│   ├── missing-signals/          # WatchTimeline, WatchStateBadge
│   ├── developments/             # DevelopmentFSM, StageTimeline
│   ├── intelligence/             # AthenaChat, EvidenceQuote, FactTag
│   ├── functions/                # FunctionRadar, RelevanceMatrix
│   ├── calibration/              # WeightAdjustmentTable, RunHistory
│   ├── sources/                  # SourceStatusCard, HealthIndicator
│   ├── observability/            # ActivityStream, LogViewer, TraceDrawer
│   └── common/                   # ErrorState, EmptyState, LoadingState, EvidenceDrawer
└── lib/
    ├── api/                      # Typed REST clients with AbortController
    ├── hooks/                    # useLiveData, useCorrelationId, useSystemHealth
    ├── mappers/                  # Strict DTO mappers (zero 'any')
    ├── errors/                   # AppError, NetworkError, APIError classes
    └── telemetry/                # Client-side performance and error telemetry
```

### 8.2 Standardized Error & Diagnostic UX
- Every view implements a dedicated `ErrorState` card showing:
  - Concise human-readable error title and message.
  - Timestamp of failure.
  - Active Correlation ID (`req-XXXX-XXXX`) with a 1-click copy button.
  - Interactive "Retry Request" trigger.
  - Expandable Technical Diagnostics panel (status code, endpoint URI, duration).
- No unhandled network exceptions or blank white screens.

---

## 9. Comprehensive Testing & Failure Injection

### 9.1 Required Testing Suites
1. **Unit & Invariant Suite**: Tests validating zero fabrication, strict mathematical scoring, honest health states, and immutable calibration runs.
2. **Contract Synchronization Suite**: Verifies that `contracts/openapi.json` and `frontend/types/api.ts` have 0 drift against FastAPI endpoints.
3. **Failure-Injection Suite**: Simulates external API timeouts (PubMed, ClinicalTrials), HTTP 429 rate limits, malformed RSS feeds, database disconnects, Redis cache downtime, and Ollama/LLM offline states.
4. **Frontend Component & Accessibility Suite**: Tests component states (`loading`, `empty`, `error`, `stale`), keyboard navigation (Tab/Enter/Escape), ARIA attributes, and color-independent status badges.

---

## 10. Single-Wave Execution Protocol

**CRITICAL DIRECTIVE**:
Phase 07 is structured as a **single, continuous execution wave**. Engineering work does not pause for review between sub-stages. The implementing agent will proceed sequentially through all audit, backend, database, frontend, observability, testing, and documentation tasks until the entire platform satisfies the 100% verification criteria.

### Sub-Stage Execution Checklist
- [ ] **Stage 1 (Codebase Audit)**: Scan repository for hardcoded scores, placeholder strings, and fake "LIVE" badges.
- [ ] **Stage 2 (Database & Models)**: Add provenance fields, `DataMode`, `CalibrationRun` lifecycle, and Alembic migrations.
- [ ] **Stage 3 (Scoring & Confluence)**: Implement real `PriorityScoringService` and dynamic confluence aggregation.
- [ ] **Stage 4 (Athena & Red-Team)**: Bind Athena to pgvector evidence; remove mock contradiction claims.
- [ ] **Stage 5 (Sources & Observability)**: Build real connector health tracking, structured logging, and correlation ID middleware.
- [ ] **Stage 6 (Frontend Refactor)**: Modularize components into bounded context folders; build `EvidenceDrawer`, `ErrorState`, `ActivityStream`.
- [ ] **Stage 7 (Workspaces Hardening)**: Hardwire Functions, Calibrate, Settings, Sources, and Activity workspaces.
- [ ] **Stage 8 (Contract & Build Sync)**: Regenerate OpenAPI contract and TypeScript types; enforce zero TypeScript/ESLint warnings.
- [ ] **Stage 9 (Testing & Failure Injection)**: Execute full test suite including failure simulations.
- [ ] **Stage 10 (Codebase Map Update)**: Reconcile all files in `.planning/codebase/` and produce the Final Implementation Report.
