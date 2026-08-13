# Phase 2: LangGraph 10-Node Intelligence Engine - Context

**Gathered:** 2026-08-14  
**Status:** Ready for planning  

<domain>
## Phase Boundary

Build the stateful 10-node LangGraph intelligence workflow (`node_ingest` through `node_calibrate -> END`) managing the canonical `IntelligenceState` TypedDict state contract. Deliver the complete node sequence:
1. `node_ingest`: Bounded batch reading from `raw_signals_bronze` with synthetic fallback.
2. `node_validate`: Deduplication, PII/PHI scrubbing, and source-independence classification.
3. `node_nlp_extract`: Hybrid regex + dictionary entity extractor with optional spaCy fallback.
4. `node_ontology_enrich`: Haemophilia domain ontology enrichment via `config/haemophilia.yaml`.
5. `node_confluence`: 48h rolling window / $\ge 3$ signal type convergence detection & development linking.
6. `node_lifecycle`: 9-stage asset finite state machine with immutable event history logging.
7. `node_redteam`: 19-rule pairwise contradiction checking via `RedTeamNLIService` (Rules A–S).
8. `node_missing_signal`: Inactivity lag alert calculation & 5-state stakeholder WATCH rule evaluation.
9. `node_synthesize`: Evidence-sufficiency check, Q1–Q4 Four-Question generation with `[FACT]`/`[INTERPRETATION]`/`[SPECULATION]` epistemic tags via `ProviderFactory`.
10. `node_calibrate`: Stakeholder calibration feedback integration, dynamic weight updates, and explicit `END` termination.

**In Scope:**
- Full 10-node LangGraph pipeline compilation and execution graph (`backend/app/workflows/`).
- `IntelligenceState` TypedDict with typed reducers (`Annotated[list, operator.add]`).
- Entity resolution, ontology mapping, confluence detection, lifecycle state machine, red-team contradiction evaluation, missing signal tracking, Four-Question synthesis formatting, and calibration routing.
- Fast, deterministic unit and integration test suite (`tests/test_workflows/` / `tests/test_intelligence_nodes.py`).

**Out of Scope / Future Phases:**
- Real 384-dim sentence-transformers embedding generation and pgvector HNSW DB indexing (Phase 3: REQ-P3-1, REQ-P3-2).
- Real GPU-quantized local Gemma 3 4B execution and live Grok network API key validation (Phase 3: REQ-P3-3, REQ-P3-4; Phase 2 executes against mock/local provider instances via `ProviderFactory`).
- Next.js frontend UI components and real-time dashboard rendering (Phase 4: REQ-P4-1 through REQ-P4-4).
- Interactive stakeholder feedback UI and final Hackathon demo story rehearsals (Phase 5: REQ-P5-1 through REQ-P5-3).

</domain>

<decisions>
## Implementation Decisions

### Area 1: Pipeline Execution, State Reducers & Trigger Mode
- **D-01:** The 10-node LangGraph pipeline executes in-process asynchronously, invokable via FastAPI endpoint (`/api/v1/pipeline/run`), APScheduler cron, and direct async Python callers. Execution status is tracked honestly in `pipeline_runs` table (`queued -> running -> completed/failed`).
- **D-02:** `IntelligenceState` is implemented as a standard `TypedDict` with explicit typed reducers (`Annotated[list, operator.add]`) for accumulating entities, signals, events, contradictions, alerts, and errors, with replacement semantics for scalar metadata (`pipeline_run_id`, `status`, `execution_time`, `calibration_weights`).
- **D-03:** `node_ingest` queries unpromoted bronze records (`processed = false`) in bounded batches (default 50–100 records per run) to ensure predictable memory footprint, with automated fallback to the pre-curated 500-signal synthetic dataset if bronze is empty.
- **D-04:** Every node is wrapped with an isolated try/except error boundary that captures exceptions, appends structured error logs to `state['errors']`, and sets node status (`SUCCESS / DEGRADED / FAILED`), ensuring partial node errors do not crash the entire pipeline.

### Area 2: NLP Extraction & Entity Resolution Strategy
- **D-05:** `node_nlp_extract` uses a hybrid extraction engine combining fast regex and dictionary-based matching against `config/haemophilia.yaml` with graceful optional spaCy fallback, ensuring zero-crash execution across resource-constrained environments.
- **D-06:** `node_ontology_enrich` maps extracted entities to canonical IDs, target mechanisms, modalities, inhibitor classifications, and competitor profiles using `config/haemophilia.yaml` domain definitions.
- **D-07:** Unmapped or emerging biomedical entities are preserved without rejecting the signal, tagged with `is_known_ontology = False`, and logged into `state['unmapped_entities']` for auditable tracking.
- **D-08:** Entity extraction extracts 5 core dimensions: (1) Asset/Drug names and synonyms, (2) Companies and Sponsors, (3) Disease and Inhibitor Status (Hem A/B, with/without inhibitors), (4) Clinical Trial NCT IDs and Phases, and (5) Clinical Biomarkers (e.g. ABR, Factor VIII/IX expression levels).

### Area 3: Confluence Clustering & Development Linking
- **D-09:** `node_confluence` clusters signals by canonical `asset_id` (or primary `disease`) over a rolling 48-hour window, requiring $\ge 3$ distinct `signal_type` sources to trigger a `ConfluenceStory` with weighted severity $S = \sum (w_{type} \times \text{credibility})$.
- **D-10:** Development resolution uses a two-tier linking heuristic: first attempts matching by clinical trial NCT ID or `asset_id` + `indication` against active developments in state/database to attach as an `Event` in an existing development chain; only initializes a new `Development` if no match exists.
- **D-11:** `node_lifecycle` executes a formal 9-stage finite state machine (`announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued`) with monotonic forward progression validation.
- **D-12:** Every lifecycle progression logs an immutable `Event` record (`event_type`, `event_date`, `development_id`, `signal_id`, `confidence`), preserving a complete chronological evidence trail from trial registry to regulatory filing.

### Area 4: Missing-Signal Detection & Stakeholder Watch Rules
- **D-13:** `node_missing_signal` calculates silence lag $\Delta t$ against domain thresholds configured in `config/haemophilia.yaml` (e.g. Phase 3 to regulatory submission lag), emitting a `MissingSignalAlert` with confidence $C = \min(0.40 + 0.002 \times \Delta t_{\text{silence}}, 0.95)$.
- **D-14:** Stakeholder-defined WATCH rules operate under a strict 5-state lifecycle: `watching` $\rightarrow$ `new_evidence_detected` / `no_new_evidence` / `watch_expired` / `human_review_required`, persisted in `watch_rules` and pipeline state.
- **D-15:** All missing-signal alerts strictly follow non-deterministic phrasing guardrails: *"Watch for..."*, *"Expected/possible next evidence"*, *"Not observed yet during the configured monitoring window"* — strictly prohibiting definitive claims of failure or secret cancellation.
- **D-16:** `node_redteam` contradiction outputs (evaluated across Rules A–S via `RedTeamNLIService`) feed into `node_missing_signal` to cross-reference conflicting claims against unexpected development silence.

### Area 5: Four-Question Synthesis & Role-Specific Brief Routing
- **D-17:** `node_synthesize` enforces an evidence-sufficiency gate: signals failing minimum evidence thresholds are restricted to verified factual excerpts labeled *"Insufficient evidence to support an interpretation — human review requested"*; signals passing sufficiency proceed to full synthesis via `ProviderFactory`.
- **D-18:** Four-Question briefs are strictly structured into Q1 (What changed?), Q2 (Why does it matter?), Q3 (Which function is impacted?), and Q4 (What action is recommended?), with every statement explicitly tagged with `[FACT]`, `[INTERPRETATION]`, or `[SPECULATION]`.
- **D-19:** Function routing calculates relevance scores (0.0–1.0) and role-tailored strategic recommendations across all 6 stakeholder functions: Medical Affairs, Regulatory, Safety/PV, Market Access, Medical Communications, and Leadership.
- **D-20:** `node_calibrate` applies stakeholder calibration feedback weights (`StakeholderCalibrationService`), updates routing thresholds, persists finalized `RoleBrief` and `Signal` records, and explicitly terminates the graph at `END` (`node_calibrate -> END`).

### Developer's Discretion
- Exact function names and modular file layout within `backend/app/workflows/` (e.g. `graph.py`, `state.py`, `nodes/*.py`).
- Internal helper utility signatures for string normalization and regex tokenization.
- Test fixture composition and mock data scenarios for unit testing all 10 nodes.

</decisions>

<canonical_refs>
## Canonical References

**Downstream planning and execution agents MUST consult these authorities:**

### Master Architecture & Design Specifications
- `docs/METARADAR_MASTER_PLAN_v5.0.md` §4 (10-Node LangGraph Execution Breakdown) & §12 (Domain Rules)
- `docs/3_SOFTWARE_DESIGN_DOCUMENT.md` §2.3 (Workflow State Machine)
- `docs/5_REFINED_ARCHITECTURE_AND_GITHUB_ANALYSIS.md` (LangGraph Multi-Agent Architecture)
- `docs/8_CORRECTED_UNIFIED_PLAN.md` §3 (Pipeline Architecture & Node Chain)
- `docs/rules/ARCHITECTURE_RULES.md` (Approved Tech Stack & Entity Architecture)
- `docs/rules/ENGINEERING_STANDARDS.md` (Code Quality & Honest Telemetry)
- `docs/rules/DEFINITION_OF_DONE.md` (DoD Verification Matrix)

### Domain & Configuration
- `config/haemophilia.yaml` (Haemophilia A/B assets, synonyms, inhibitor categories, lag thresholds, red-team rules)
- `backend/app/core/domain_config.py` (Haemophilia YAML parser & schema validator)

### Existing Codebase Assets & Integration Points
- `backend/app/models/__init__.py` (`RawSignalBronze`, `Signal`, `Development`, `Event`, `Contradiction`, `WatchRule`, `MissingSignalAlert`, `RoleBrief`, `PipelineRun`)
- `backend/app/services/redteam.py` (`RedTeamNLIService` with Rules A–S)
- `backend/app/services/pii.py` (`PIIPHIScrubber`)
- `backend/app/services/deduplication.py` (`generate_fingerprint`, `chunk_text_for_embedding`)
- `backend/app/services/source_independence.py` (`SourceIndependenceClassifier`)
- `backend/app/providers/factory.py` (`ProviderFactory`, `GemmaProvider`, `GrokProvider`, `DegradedProvider`)
- `backend/app/api/v1/endpoints/health.py` (Health & Readiness Observability)

</canonical_refs>

<code_context>
## Code Context & Target Layout

Target file layout for Phase 2 implementation:
```
backend/app/workflows/
├── __init__.py
├── state.py              # IntelligenceState TypedDict, reducers, initial state factory
├── graph.py              # StateGraph definition, node addition, edge wiring (node_ingest -> ... -> node_calibrate -> END)
├── nodes/
│   ├── __init__.py
│   ├── ingest.py         # node_ingest: batch read bronze / synthetic fallback
│   ├── validate.py       # node_validate: dedup, PII scrubbing, source independence
│   ├── nlp_extract.py    # node_nlp_extract: regex/dictionary entity extraction
│   ├── ontology.py       # node_ontology_enrich: map to config/haemophilia.yaml
│   ├── confluence.py     # node_confluence: 48h/≥3 signal confluence + development linking
│   ├── lifecycle.py      # node_lifecycle: 9-stage asset state machine & event logging
│   ├── redteam.py        # node_redteam: 19-rule contradiction checking (Rules A-S)
│   ├── missing_signal.py # node_missing_signal: lag detection & 5-state watch rules
│   ├── synthesize.py     # node_synthesize: evidence gate, Q1-Q4 generation, epistemic tags
│   └── calibrate.py      # node_calibrate: calibration updates, role briefs, route to END
└── runner.py             # PipelineRunner: async execution wrapper with pipeline_runs tracking
```

</code_context>
