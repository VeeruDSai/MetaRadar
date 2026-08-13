# Phase 2: LangGraph 10-Node Intelligence Engine — Execution Plan

**Phase:** 2 — LangGraph 10-Node Intelligence Engine  
**Status:** PLANNED  
**Branch:** `feature/phase-2-langgraph-engine`  
**Requirements:** REQ-P2-1 through REQ-P2-9  
**Context:** `.planning/phases/02-langgraph-10-node-intelligence-engine/02-CONTEXT.md`  

---

## Objective

Build the stateful 10-node LangGraph intelligence workflow (`node_ingest` → `node_calibrate → END`) with the canonical `MetaRadarState` TypedDict state contract. This is the core intelligence layer that transforms raw `raw_signals_bronze` records into structured `Signal`, `Development`, `Event`, `Contradiction`, `WatchItem`, and `SignalRouting` records — delivering Four-Question role-specific briefs via a `ProviderFactory`.

---

## Pre-Conditions (Must Verify Before Starting)

- [ ] Git branch `feature/phase-2-langgraph-engine` created from `feature/stabilization-baseline`
- [ ] `pytest -v` → 18/18 pass (baseline intact)
- [ ] `npx tsc --noEmit` → 0 errors
- [ ] `langgraph` package available (`pip show langgraph` — install if missing)

---

## Plan Waves

### Wave 1 — State Contract & Package Scaffold (REQ-P2-1)

**Goal:** Create the `backend/app/workflows/` package with the canonical state definition, reducers, and initial state factory that all 10 nodes share.

---

#### PLAN A — `backend/app/workflows/__init__.py`

**New file.** Package init exporting the public API.

```
Exports: MetaRadarState, create_initial_state, build_graph, PipelineRunner
```

**Implementation:**
```python
from app.workflows.state import MetaRadarState, create_initial_state
from app.workflows.graph import build_graph
from app.workflows.runner import PipelineRunner

__all__ = ["MetaRadarState", "create_initial_state", "build_graph", "PipelineRunner"]
```

---

#### PLAN B — `backend/app/workflows/state.py`

**New file.** `MetaRadarState` TypedDict with typed reducers.

**Canonical state fields (from Master Plan §14.6):**

| Field | Type | Reducer | Purpose |
|---|---|---|---|
| `pipeline_run_id` | `str` | replace | Correlates to `PipelineRun.pipeline_run_id` |
| `raw_signals` | `Annotated[list[dict], operator.add]` | accumulate | Bronze batch payloads from `node_ingest` |
| `validated_signals` | `Annotated[list[dict], operator.add]` | accumulate | Post-dedup, post-PII signals from `node_validate` |
| `extracted_entities` | `Annotated[list[dict], operator.add]` | accumulate | NLP entity dicts from `node_nlp_extract` |
| `ontology_entities` | `Annotated[list[dict], operator.add]` | accumulate | Enriched entities from `node_ontology_enrich` |
| `developments` | `Annotated[list[dict], operator.add]` | accumulate | Development upserts from `node_confluence` |
| `scored_signals` | `Annotated[list[dict], operator.add]` | accumulate | Signals with severity scores |
| `confluent_stories` | `Annotated[list[dict], operator.add]` | accumulate | `ConfluenceStory` dicts from `node_confluence` |
| `lifecycle_events` | `Annotated[list[dict], operator.add]` | accumulate | `LifecycleEvent` records from `node_lifecycle` |
| `redteam_flags` | `Annotated[list[dict], operator.add]` | accumulate | Contradiction flags from `node_redteam` |
| `missing_signals` | `Annotated[list[dict], operator.add]` | accumulate | Watch alerts from `node_missing_signal` |
| `unmapped_entities` | `Annotated[list[dict], operator.add]` | accumulate | Novel entities not in ontology (D-07) |
| `role_briefs` | `Annotated[list[dict], operator.add]` | accumulate | Q1–Q4 role briefs from `node_synthesize` |
| `calibration_feedback` | `Annotated[list[dict], operator.add]` | accumulate | Input feedback records for `node_calibrate` |
| `model_metadata` | `Annotated[list[dict], operator.add]` | accumulate | `ModelMetadataSchema` records per synthesis call |
| `errors` | `Annotated[list[dict], operator.add]` | accumulate | Structured node error records (D-04) |
| `calibration_weights` | `dict[str, float]` | replace | Current function scoring weights |
| `node_statuses` | `dict[str, str]` | replace | Per-node `SUCCESS/DEGRADED/FAILED` status map |
| `batch_size` | `int` | replace | Bronze batch size for this run |
| `signals_processed` | `int` | replace | Count updated by `node_ingest` |

**`create_initial_state()`** factory returns a `MetaRadarState` dict with all list fields as `[]`, all scalars at defaults, and `calibration_weights` seeded from `ScoringWeights` defaults.

**Implementation details:**
```python
import operator
from typing import Annotated, TypedDict
from uuid import UUID

class MetaRadarState(TypedDict):
    pipeline_run_id: str
    raw_signals: Annotated[list[dict], operator.add]
    validated_signals: Annotated[list[dict], operator.add]
    # ... (all fields per table above)
    calibration_weights: dict[str, float]
    node_statuses: dict[str, str]
    batch_size: int
    signals_processed: int

def create_initial_state(
    pipeline_run_id: str,
    batch_size: int = 50,
    calibration_weights: dict[str, float] | None = None,
) -> MetaRadarState: ...
```

**UAT:** Calling `create_initial_state("run-123")` returns a valid TypedDict with all list fields empty, `node_statuses == {}`, and `calibration_weights` present.

---

#### PLAN C — `backend/app/workflows/graph.py`

**New file.** Assembles the `StateGraph`, adds all 10 nodes, and wires edges in sequence.

```python
from langgraph.graph import StateGraph, END
from app.workflows.state import MetaRadarState
from app.workflows.nodes import (
    node_ingest, node_validate, node_nlp_extract, node_ontology_enrich,
    node_confluence, node_lifecycle, node_redteam, node_missing_signal,
    node_synthesize, node_calibrate,
)

def build_graph() -> StateGraph:
    graph = StateGraph(MetaRadarState)
    graph.add_node("node_ingest", node_ingest)
    graph.add_node("node_validate", node_validate)
    graph.add_node("node_nlp_extract", node_nlp_extract)
    graph.add_node("node_ontology_enrich", node_ontology_enrich)
    graph.add_node("node_confluence", node_confluence)
    graph.add_node("node_lifecycle", node_lifecycle)
    graph.add_node("node_redteam", node_redteam)
    graph.add_node("node_missing_signal", node_missing_signal)
    graph.add_node("node_synthesize", node_synthesize)
    graph.add_node("node_calibrate", node_calibrate)
    graph.add_edge("node_ingest", "node_validate")
    graph.add_edge("node_validate", "node_nlp_extract")
    graph.add_edge("node_nlp_extract", "node_ontology_enrich")
    graph.add_edge("node_ontology_enrich", "node_confluence")
    graph.add_edge("node_confluence", "node_lifecycle")
    graph.add_edge("node_lifecycle", "node_redteam")
    graph.add_edge("node_redteam", "node_missing_signal")
    graph.add_edge("node_missing_signal", "node_synthesize")
    graph.add_edge("node_synthesize", "node_calibrate")
    graph.add_edge("node_calibrate", END)
    graph.set_entry_point("node_ingest")
    return graph.compile()
```

**UAT:** `build_graph()` returns a compiled runnable without error. Graph has exactly 10 nodes and terminates at `END`.

---

### Wave 2 — Data Ingestion & Validation Nodes (REQ-P2-2)

**Goal:** Implement `node_ingest` and `node_validate` — the bronze-to-validated signal pipeline bridge.

---

#### PLAN D — `backend/app/workflows/nodes/__init__.py`

**New file.** Package init re-exporting all 10 node functions.

---

#### PLAN E — `backend/app/workflows/nodes/ingest.py` (node_ingest)

**New file.** Queries `raw_signals_bronze` for unprocessed records (via `processed = False` marker or separate logic), falls back to synthetic dataset if empty.

**Logic:**
1. Accept `state: MetaRadarState` — read `batch_size` (default 50).
2. Query `RawSignalBronze` where `processed` is not yet flagged — use `pipeline_run_id IS NULL` as proxy (since no `processed` column exists on model yet — add a `processed: bool = False` column or query by absence of `signal` FK, per agent discretion).
3. Deserialize `raw_payload` JSONB into normalized dicts with keys: `source_id`, `external_id`, `content`, `title`, `published_at`, `signal_type`, `url`.
4. If 0 rows returned → load `backend/app/data/synthetic_signals.json` (500-record fallback); if file missing, emit a `DEGRADED` status and 0 `raw_signals`.
5. Update `state['pipeline_run_id']`, `state['signals_processed']`, `state['node_statuses']['node_ingest']`.
6. Wrap in try/except → on error append `{"node": "node_ingest", "error": str(e), ...}` to `state['errors']`, set `node_statuses['node_ingest'] = "FAILED"`.

**Returns:** `{"raw_signals": [...], "signals_processed": N, "node_statuses": {"node_ingest": "SUCCESS"}, ...}`

**DB Session handling:** Accept optional `AsyncSession` via `config` or use a lightweight sync fallback when no session is injectable (node functions must be callable without DB in test mode).

**UAT:**
- With empty bronze → loads synthetic fallback, returns ≥1 signal.
- With bronze records present → returns those records, `signals_processed` == count.
- With DB error → returns `errors` list with `node_ingest` entry, `FAILED` status, `raw_signals == []`.

---

#### PLAN F — `backend/app/workflows/nodes/validate.py` (node_validate)

**New file.** Filters, deduplicates, PII-scrubs, and source-independence-classifies `raw_signals`.

**Logic:**
1. Accept `state['raw_signals']` list.
2. Filter: skip signals with `content` length < 50 chars (Master Plan §14.2 node_validate rule).
3. Language check: retain only signals where `content` appears to be English (simple heuristic: ASCII proportion > 0.85).
4. PII scrub each signal's `content` via `PIIPHIScrubber.scrub()` from `app.services.pii`.
5. Deduplication: call `generate_fingerprint()` from `app.services.deduplication` for each signal; skip if fingerprint already seen in this run.
6. Source-independence: tag each signal with `cross_source_group_id` if available from `raw_signals_bronze.cross_source_group_id`, else `None` (full DB classify is Phase 1 concern; Phase 2 reads existing values).
7. Collect validated signals into `validated_signals` list, each dict including `fingerprint` and `cross_source_group_id`.
8. Error boundary: per-signal errors are logged and the signal is dropped; node sets status based on overall outcome.

**UAT:**
- Short content signal (<50 chars) is filtered out.
- Duplicate fingerprint (same PMID) → second occurrence dropped.
- PII-containing signal (`"Patient John Smith SSN 123-45-6789"`) → content scrubbed in output.
- Valid signals → in `validated_signals`.

---

### Wave 3 — NLP Extraction & Ontology Enrichment (REQ-P2-3)

**Goal:** `node_nlp_extract` and `node_ontology_enrich` — entity recognition and domain enrichment pipeline.

---

#### PLAN G — `backend/app/workflows/nodes/nlp_extract.py` (node_nlp_extract)

**New file.** Hybrid entity extraction combining regex patterns + dictionary lookups.

**Entity extraction — 5 dimensions (D-08):**

1. **Assets/Synonyms** — regex/dictionary scan of signal `content` + `title` against all `AssetConfig.generic_name`, `brand_name`, and synonym lists from `haemophilia.yaml`. Returns `asset_id` (canonical) + `display_name` + confidence.
2. **Companies/Sponsors** — regex scan for company names from all `AssetConfig.company` values + additional known Novo Nordisk, Roche, CSL, BioMarin, Sanofi keywords. Returns `company_name`.
3. **Disease/Inhibitor Status** — regex for "haemophilia A/B", "hemophilia A/B", "with inhibitors", "without inhibitors", "inhibitor patient". Returns `disease_id`, `inhibitor_status`.
4. **Clinical Trial NCT IDs/Phases** — regex `NCT\d{8}` for NCT IDs; regex `[Pp]hase [I1-3IViv]{1,3}` for phase mentions. Returns `nct_id`, `trial_phase`.
5. **Clinical Biomarkers** — regex for "ABR" (annualised bleeding rate), "Factor VIII", "Factor IX", "FVIII", "FIX", "IU/dL", expression percentage. Returns `biomarkers` list.

**Optional spaCy fallback (D-05):**
```python
try:
    import spacy
    nlp = spacy.load("en_core_sci_md")
    # Use spaCy NER to supplement regex matches
except (ImportError, OSError):
    pass  # graceful degradation — regex only
```

**Output per signal:** `{"signal_id": ..., "assets": [...], "companies": [...], "diseases": [...], "nct_ids": [...], "biomarkers": [...], "extraction_method": "regex|spacy"}`

**UAT:**
- Signal mentioning "emicizumab" → `assets` contains `{"asset_id": "emicizumab", "display_name": "Hemlibra", ...}`.
- Signal with `NCT04869267` → `nct_ids == ["NCT04869267"]`.
- Signal with "Factor IX expression" → `biomarkers` contains `"Factor IX"`.
- No imports crash when spaCy model is absent.

---

#### PLAN H — `backend/app/workflows/nodes/ontology.py` (node_ontology_enrich)

**New file.** Maps `extracted_entities` to canonical `DomainConfig` metadata.

**Logic:**
1. Load `DomainConfig` via `get_domain_config()`.
2. For each entity in `state['extracted_entities']`:
   - **Asset match**: look up by `asset_id` in `domain_config.assets` → attach `mechanism`, `modality`, `indication`, `approval_status`, `is_novo_nordisk`.
   - **Disease match**: look up by `disease_id` in `domain_config.diseases` → attach `icd10`, `deficiency`.
   - **Inhibitor classification**: map `inhibitor_status` to `domain_config.inhibitor_categories`.
   - **Signal type assignment**: if not already set, classify signal by keyword matching against `domain_config.signal_types`.
3. Unmapped entities (no match in domain config): tag with `is_known_ontology = False`, add to `state['unmapped_entities']` (D-07).
4. Emit `ontology_entities` — full enriched entity dicts.

**UAT:**
- `asset_id == "emicizumab"` → enriched entity has `mechanism: "FVIIIa-mimetic bispecific antibody"`, `is_novo_nordisk: False`.
- Unknown drug "drug-xyz-999" → added to `unmapped_entities` with `is_known_ontology: False`.
- No crash when `domain_config.yaml` has no `cross_source` key (backward compatible).

---

### Wave 4 — Confluence & Lifecycle Nodes (REQ-P2-4 + REQ-P2-5)

**Goal:** `node_confluence` clusters multi-source signal evidence into `ConfluenceStory` and `Development` records; `node_lifecycle` advances the 9-stage asset state machine.

---

#### PLAN I — `backend/app/workflows/nodes/confluence.py` (node_confluence)

**New file.** Implements 48h / ≥3 signal type multi-source convergence detection + development linking (D-09, D-10).

**Confluence detection logic:**
1. Group `state['ontology_entities']`-enriched signals by `asset_id` (primary) or `disease_id` (fallback).
2. For each group: collect `signal_type` values within 48-hour rolling window of `published_at` (read from `validated_signals`).
3. If distinct `signal_type` count ≥ `domain_config.confluence.minimum_independent_signals` (= 3): compute weighted severity `S = Σ(w_type × credibility)` using weights from `domain_config.baseline_routing_matrix` signal type priorities.
4. Emit `ConfluenceStory` dict: `{"asset_id": ..., "signal_ids": [...], "signal_types": [...], "severity_score": S, "created_at": ..., "confluence_type": "confirmed|emerging"}`.

**Development linking logic (D-10):**
1. For each signal, attempt development resolution:
   - **Tier 1 match:** find existing `Development` where `nct_id` matches signal's `nct_id` (if present).
   - **Tier 2 match:** find existing `Development` where `asset_id` + `indication` both match.
   - **No match:** create new `Development` record dict: `{"title": signal.title, "disease": signal.disease, "asset_id": ..., "company_id": ..., "current_stage": "announced"}`.
2. Link signal to resolved `development_id`.
3. Emit resolved `development_id` on each signal dict, append new `Development` dicts to `state['developments']`.

**UAT:**
- 3 signals same asset, 3 distinct signal types, within 48h → `confluent_stories` has 1 entry with `severity_score > 0`.
- 2 signals same asset, 2 distinct types → no confluence story emitted.
- Signal with `nct_id` matching existing development → linked by `development_id`, no new Development created.
- Signal with no matching development → new Development dict appended to `state['developments']`.

---

#### PLAN J — `backend/app/workflows/nodes/lifecycle.py` (node_lifecycle)

**New file.** Advances asset state machine and logs immutable `LifecycleEvent` records (D-11, D-12).

**FSM stages (from `haemophilia.yaml` `lifecycle_stages`):**
```
announced → in_trial → interim_result → final_result → congress_publication → regulatory_development → approved → post_market | discontinued
```

**Logic:**
1. For each signal + resolved `development_id` in `state`:
2. Infer new lifecycle stage from `signal_type`:
   - `CLINICAL_TRIAL` → `in_trial` (if current is `announced` or `in_trial`)
   - `CONGRESS` or `PUBLICATIONS` → `congress_publication` (if after `final_result`)
   - `REGULATORY` → `regulatory_development` (if after `final_result`)
   - etc. (map per Master Plan §4 lifecycle rules)
3. Validate monotonic progression: only advance, never regress. If signal implies a regressive stage, log a warning and do NOT change FSM state.
4. Emit immutable `LifecycleEvent` dict: `{"development_id": ..., "stage": new_stage, "event_date": signal.published_at, "signal_id": ..., "confidence": 0.85}`.
5. Append to `state['lifecycle_events']`.

**UAT:**
- `CLINICAL_TRIAL` signal for `announced` asset → lifecycle event with `stage == "in_trial"`.
- `CONGRESS` signal after `final_result` → `congress_publication` event.
- Signal implying regression (`announced` for `approved` asset) → no event emitted, warning logged.
- All lifecycle events include `development_id`, `stage`, `event_date`, `signal_id`.

---

### Wave 5 — Red-Team & Missing-Signal Nodes (REQ-P2-6 + REQ-P2-7)

**Goal:** `node_redteam` runs 19-rule pairwise contradiction evaluation; `node_missing_signal` computes inactivity lag alerts and 5-state watch rule evaluation.

---

#### PLAN K — `backend/app/workflows/nodes/redteam.py` (node_redteam)

**New file.** Invokes `RedTeamNLIService.evaluate_contradictions()` on claims derived from `validated_signals`.

**Logic:**
1. Build claim dicts from `state['validated_signals']`: `{"claim_id": signal_id, "asset": asset_id, "disease": disease, "signal_type": signal_type, "priority": priority, "source": source_id}`.
2. Call `await redteam_service.evaluate_contradictions(claims)`.
3. For each returned contradiction flag: emit `Contradiction` dict and append to `state['redteam_flags']`.
4. If `evaluate_contradictions` raises → error boundary: append to `state['errors']`, set `node_statuses['node_redteam'] = "DEGRADED"`, continue.

**UAT:**
- 2 signals same asset, different signal types → 1 contradiction flag in `redteam_flags`.
- Service exception → `errors` list populated, node status `DEGRADED`, downstream continues.
- Each contradiction flag has `rule_id`, `severity`, `confidence`, `description`.

---

#### PLAN L — `backend/app/workflows/nodes/missing_signal.py` (node_missing_signal)

**New file.** Inactivity lag alert computation + 5-state watch rule evaluation (D-13, D-14, D-15, D-16).

**Lag computation:**
1. For each development in `state['developments']`: compute `Δt = (now - last_event_date).days`.
2. Compare against domain lag threshold (read from `haemophilia.yaml` `lifecycle_stages` or a new `lag_thresholds` YAML block — add placeholder `lag_thresholds` to `haemophilia.yaml` if missing: e.g., `in_trial: 180`, `regulatory_development: 365`).
3. If `Δt > threshold`: compute confidence `C = min(0.40 + 0.002 * Δt, 0.95)`.
4. Emit `MissingSignalAlert` dict with strictly guardrailed text (D-15):
   ```json
   {
     "development_id": "...",
     "asset_id": "...",
     "current_stage": "in_trial",
     "days_since_last_signal": 210,
     "confidence": 0.62,
     "watch_text": "Watch for: Expected/possible next evidence for [asset] trial result. Not observed during the configured monitoring window (180 days).",
     "human_review_required": true
   }
   ```

**Watch rule evaluation:**
1. Check `state['redteam_flags']` (D-16): if a contradiction flag exists for the same `development_id` as a missing-signal alert, annotate the alert with `"redteam_cross_reference": true`.
2. Emit 5-state watch rule transitions:
   - `Δt == 0` → `watching`
   - new evidence in `validated_signals` for this development → `new_evidence_detected`
   - `Δt > threshold` → `no_new_evidence` (if monitoring window not expired) or `watch_expired`
   - Any contradiction flag on same asset → mark `human_review_required: True`

**UAT:**
- Development with 200-day silence, threshold 180 → alert emitted with `confidence ≈ 0.62`, guardrail text present, no certainty claims.
- Development with new signal this run → `watch_status == "new_evidence_detected"`.
- Contradiction flag on same asset → alert has `redteam_cross_reference: True`.
- Alert text must NOT contain: "cancelled", "failed", "abandoned", "will not", "confirmed absent".

---

### Wave 6 — Synthesis & Calibration Nodes (REQ-P2-8 + REQ-P2-9)

**Goal:** `node_synthesize` enforces evidence sufficiency gate and generates Q1–Q4 Four-Question briefs; `node_calibrate` applies weights and terminates at END.

---

#### PLAN M — `backend/app/workflows/nodes/synthesize.py` (node_synthesize)

**New file.** Evidence sufficiency gate, Four-Question brief generation via `ProviderFactory`, epistemic tagging (D-17, D-18, D-19).

**Evidence sufficiency gate (D-17):**
- Threshold: signal must have `content` length ≥ 200 chars AND at least 1 resolved `asset_id` or `nct_id` entity.
- Below threshold → output factual-only brief: `{"q1_what_changed": "[FACT] " + signal.title, "q2_why_matters": "Insufficient evidence to support an interpretation — human review requested.", "q3_impacted_functions": [], "q4_action": "Human review required.", "evidence_sufficient": False}`.

**Full synthesis (D-18, D-19) for sufficient evidence:**
1. Build `evidence: list[str]` = top 3 `content` excerpts (chunked via `chunk_text_for_embedding()`).
2. Build `task: str` = structured Four-Question prompt:
   ```
   Generate a structured Four-Question intelligence brief for: {signal.title}
   Q1: What changed? (facts only, cite source)
   Q2: Why does it matter to Novo Nordisk? (impact on portfolio vs competitors)
   Q3: Which of these functions is impacted? [Medical Affairs, Regulatory, Safety, Market Access, Communications, Leadership]
   Q4: What action is recommended? (specific, role-tailored)
   Label each statement: [FACT], [INTERPRETATION], or [SPECULATION].
   ```
3. Call `await provider_factory.execute_task(ProviderCapability.REASON, evidence, task, DataClassification.PUBLIC)`.
4. Parse response into structured `RoleBrief` dict:
   ```json
   {
     "signal_id": "...",
     "q1_what_changed": "[FACT] ...",
     "q2_why_matters": "[INTERPRETATION] ...",
     "q3_impacted_functions": ["MEDICAL_AFFAIRS", "REGULATORY"],
     "q4_action": "[INTERPRETATION] Recommended action: ...",
     "relevance_scores": {"MEDICAL_AFFAIRS": 0.85, "REGULATORY": 0.70, ...},
     "evidence_sufficient": true,
     "model_metadata": {...}
   }
   ```
5. Relevance scores seeded from `domain_config.baseline_routing_matrix` and modulated by `calibration_weights` (read from state).
6. Append to `state['role_briefs']` and `state['model_metadata']`.

**Error boundary:** if `ProviderFactory` raises → fall back to degraded factual brief (call `DegradedProvider` directly), set `model_metadata.fallback_used = True`, status `DEGRADED`.

**UAT:**
- Signal with 50-char content → `evidence_sufficient == False`, brief contains "Insufficient evidence" text, no `[INTERPRETATION]` claims.
- Signal with sufficient content → brief has Q1, Q2, Q3, Q4 structured keys, all with epistemic tags.
- `ProviderFactory` error → degraded brief returned, `fallback_used == True` in model_metadata.
- `[FACT]`, `[INTERPRETATION]`, `[SPECULATION]` tags present in output text.

---

#### PLAN N — `backend/app/workflows/nodes/calibrate.py` (node_calibrate)

**New file.** Applies calibration weights, updates routing scores on `role_briefs`, persists finalized records to state, terminates at `END` (D-20).

**Logic:**
1. Read `state['calibration_feedback']` — list of `CalibrationFeedback`-style dicts (submitted rating input).
2. If feedback present: compute weight deltas per stakeholder function using gradient update rule (from Master Plan §6): `w_new = w_old + α * (rating - 3.0)` (α = 0.05, ratings 1–5, center at 3.0).
3. Update `state['calibration_weights']` with new weights (clamped to [0.1, 2.0]).
4. Re-score all `role_briefs` using updated weights: `adjusted_score = base_score * calibration_weights[function]`.
5. Update `calibrated_primary_function` on each brief (function with highest adjusted score).
6. Emit `CalibrationHistory` dict: `{"version": "v1.0.0", "weights": calibration_weights, "applied_at": utc_now()}`.
7. Append final state summary to `node_statuses['node_calibrate'] = "SUCCESS"`.
8. Return updated state → graph routes to `END`.

**UAT:**
- No feedback input → weights unchanged, role_briefs re-scored with default weights, terminates at END.
- Feedback with `relevance_rating=5` for REGULATORY → REGULATORY weight increases, adjusted score updates accordingly.
- Weights clamped: if computed weight < 0.1 → clamped to 0.1.
- Calibration history dict emitted to state.

---

### Wave 7 — Pipeline Runner & FastAPI Integration (D-01)

**Goal:** Wrap graph execution in `PipelineRunner`; expose `/api/v1/pipeline/run` endpoint with `pipeline_runs` tracking.

---

#### PLAN O — `backend/app/workflows/runner.py` (PipelineRunner)

**New file.** Async execution wrapper that manages `pipeline_runs` lifecycle.

**Class: `PipelineRunner`**

```python
class PipelineRunner:
    def __init__(self, session: AsyncSession | None = None):
        self._session = session
        self._graph = build_graph()

    async def run(
        self,
        batch_size: int = 50,
        pipeline_run_id: str | None = None,
        calibration_weights: dict | None = None,
    ) -> dict:
        """
        Executes the 10-node LangGraph pipeline.
        Returns final IntelligenceState dict.
        Tracks PipelineRun lifecycle in DB if session available.
        """
```

**Logic:**
1. Create `PipelineRun` record with `status="running"`, `started_at=utc_now()`.
2. Build initial state via `create_initial_state(pipeline_run_id, batch_size, calibration_weights)`.
3. Execute: `final_state = await self._graph.ainvoke(initial_state)`.
4. On success: update `PipelineRun` → `status="completed"`, `completed_at`, `signals_fetched`, `signals_created`, `errors_count`.
5. On exception: update `PipelineRun` → `status="failed"`, `error_summary`.
6. Return `final_state`.

**UAT:**
- `await runner.run()` returns a dict containing `node_statuses`, `role_briefs`, `errors` keys.
- `pipeline_run_id` is propagated through entire state.
- Exception in graph invocation → caught, PipelineRun marked `failed`, exception re-raised with structured message.

---

#### PLAN P — `backend/app/api/v1/endpoints/pipeline.py` (NEW endpoint)

**New file.** FastAPI router exposing pipeline trigger endpoint.

```python
router = APIRouter()

@router.post("/pipeline/run", response_model=PipelineRunResponseSchema)
async def trigger_pipeline_run(
    batch_size: int = 50,
    session: AsyncSession = Depends(get_db)
) -> PipelineRunResponseSchema:
    """Triggers a synchronous LangGraph pipeline run and returns execution summary."""
    runner = PipelineRunner(session=session)
    final_state = await runner.run(batch_size=batch_size)
    return PipelineRunResponseSchema(
        pipeline_run_id=final_state["pipeline_run_id"],
        node_statuses=final_state["node_statuses"],
        signals_processed=final_state["signals_processed"],
        role_briefs_count=len(final_state["role_briefs"]),
        errors=final_state["errors"],
    )
```

**Register in `backend/app/main.py`:**
```python
from app.api.v1.endpoints import pipeline
app.include_router(pipeline.router, prefix=f"{settings.API_V1_STR}", tags=["Pipeline"])
```

**Add `PipelineRunResponseSchema` to `backend/app/schemas/__init__.py`.**

**UAT:**
- `POST /api/v1/pipeline/run` → 200 OK with `pipeline_run_id`, `node_statuses`, `signals_processed`.
- Schema exported to `contracts/openapi.json` by `scripts/export_openapi.py`.

---

### Wave 8 — Test Suite (REQ-P2-1 through REQ-P2-9, TESTING_STRATEGY.md)

**Goal:** Deterministic, DB-free unit tests for all 10 nodes + integration test for `PipelineRunner`.

---

#### PLAN Q — `tests/test_intelligence_nodes.py` (NEW test file)

**New file.** 20+ deterministic unit tests using in-memory mock data only (no DB, no network).

**Test categories:**

**State contract tests (Wave 1):**
```python
def test_create_initial_state_has_all_fields(): ...
def test_state_accumulator_reducer_appends(): ...
def test_state_replace_reducer_overwrites(): ...
```

**node_ingest tests:**
```python
async def test_node_ingest_synthetic_fallback_when_bronze_empty(): ...
async def test_node_ingest_returns_signals_processed_count(): ...
async def test_node_ingest_error_boundary_sets_failed_status(): ...
```

**node_validate tests:**
```python
async def test_node_validate_filters_short_content(): ...
async def test_node_validate_deduplicates_by_fingerprint(): ...
async def test_node_validate_scrubs_pii_content(): ...
```

**node_nlp_extract tests:**
```python
def test_nlp_extracts_emicizumab_asset(): ...
def test_nlp_extracts_nct_id_pattern(): ...
def test_nlp_extracts_factor_viii_biomarker(): ...
def test_nlp_graceful_when_spacy_unavailable(): ...
```

**node_ontology_enrich tests:**
```python
def test_ontology_enriches_known_asset(): ...
def test_ontology_marks_unknown_entity_as_unmapped(): ...
```

**node_confluence tests:**
```python
async def test_confluence_detected_with_3_signal_types(): ...
async def test_confluence_not_triggered_with_2_types(): ...
async def test_confluence_links_nct_id_to_existing_development(): ...
async def test_confluence_creates_new_development_when_no_match(): ...
```

**node_lifecycle tests:**
```python
def test_lifecycle_advances_announced_to_in_trial(): ...
def test_lifecycle_blocks_regressive_stage_transition(): ...
def test_lifecycle_event_has_required_fields(): ...
```

**node_redteam tests (extends existing test_redteam_behavior.py):**
```python
async def test_node_redteam_emits_contradiction_flag(): ...
async def test_node_redteam_error_boundary_degrades_gracefully(): ...
```

**node_missing_signal tests:**
```python
def test_missing_signal_confidence_formula(): ...
def test_missing_signal_guardrail_text_no_certainty(): ...
def test_missing_signal_cross_references_redteam_flag(): ...
def test_missing_signal_new_evidence_detected_state(): ...
```

**node_synthesize tests:**
```python
async def test_synthesize_insufficient_evidence_no_interpretation(): ...
async def test_synthesize_full_brief_has_q1_q2_q3_q4(): ...
async def test_synthesize_epistemic_tags_present_in_output(): ...
async def test_synthesize_provider_error_falls_back_to_degraded(): ...
```

**node_calibrate tests:**
```python
def test_calibrate_no_feedback_weights_unchanged(): ...
def test_calibrate_feedback_updates_weights(): ...
def test_calibrate_weights_clamped_to_bounds(): ...
def test_calibrate_emits_calibration_history(): ...
```

**Integration test:**
```python
async def test_pipeline_runner_full_run_returns_state(): ...
```

**Requirements:**
- All tests: `asyncio_mode = auto` (existing `pytest.ini`)
- No live DB calls — use `unittest.mock.AsyncMock` for `AsyncSession`
- No live LLM calls — mock `ProviderFactory.execute_task` to return structured dict
- All tests must pass without environment variables

---

### Wave 9 — Synthetic Data Asset & OpenAPI Export

**Goal:** Provide the 500-signal synthetic fallback dataset and update the OpenAPI contract.

---

#### PLAN R — `backend/app/data/synthetic_signals.json`

**New file.** 500-entry synthetic haemophilia intelligence signals covering all 7 signal types and core assets (emicizumab, mim8, concizumab, Hemgenix, Roctavian, fitusiran, marstacimab).

**Schema per signal:**
```json
{
  "id": "syn-001",
  "source_id": "pubmed",
  "external_id": "syn-001",
  "title": "...",
  "content": "...",
  "published_at": "2025-06-15T00:00:00Z",
  "signal_type": "CLINICAL_TRIAL",
  "disease": "haemophilia_a",
  "url": "https://example.com/syn-001"
}
```

Each signal must have content ≥ 200 chars (meets sufficiency gate) and credibly reference real Haemophilia domain terminology.

---

#### PLAN S — Update `scripts/export_openapi.py` + `contracts/openapi.json`

**Modify existing.** Re-run OpenAPI export after adding the `/pipeline/run` endpoint to ensure `PipelineRunResponseSchema` appears in `contracts/openapi.json` and `frontend/types/api.ts`.

**Command to run after implementation:**
```bash
cd backend && python ../scripts/export_openapi.py
```

---

### Wave 10 — Alembic Migration for `processed` Column (if needed)

**Agent discretion call:** `node_ingest` needs to identify unprocessed bronze records. Two approaches:

**Option A (preferred):** Query bronze records WHERE `pipeline_run_id IS NULL` as proxy for "not yet processed by workflow". No new migration needed — uses existing schema.

**Option B:** Add `processed: bool = False` column to `RawSignalBronze`. Requires new Alembic migration:
```bash
cd backend && alembic revision --autogenerate -m "add processed flag to raw_signals_bronze"
```

**Agent decides which approach is cleaner given the existing model.** If Option B chosen, document migration clearly and add to DoD checklist.

---

## Verification Checklist (Definition of Done — docs/rules/DEFINITION_OF_DONE.md)

- [ ] **Git branch:** `feature/phase-2-langgraph-engine` created and all commits made there
- [ ] **pytest:** `cd .. && pytest -v` passes with 0 failures (Phase 2 tests added to total count — target ≥ 38 tests)
- [ ] **TSC:** `cd frontend && npx tsc --noEmit` → 0 errors (Phase 2 only adds backend; frontend untouched unless schema changes)
- [ ] **ESLint:** `npx eslint .` → 0 errors
- [ ] **Next build:** `npx next build` → 0 build errors
- [ ] **OpenAPI sync:** `python scripts/export_openapi.py` → `contracts/openapi.json` updated, `frontend/types/api.ts` reflects new `PipelineRunResponseSchema`
- [ ] **LangGraph graph:** `build_graph()` compiles without error; 10 nodes, terminates at `END`
- [ ] **Pipeline runner:** `PipelineRunner().run()` returns a state dict with `node_statuses` and `role_briefs` keys
- [ ] **Security:** No PII in synthetic signals; PII scrubber invoked in `node_validate`; no secrets in any committed file
- [ ] **Guardrail text:** missing-signal alert text contains no certainty claims (`"cancelled"`, `"will not"`, etc.)
- [ ] **Docker:** `docker compose config` validates cleanly (no new services added in Phase 2)
- [ ] **No direct push to main:** all work on `feature/phase-2-langgraph-engine`

---

## File Inventory — New & Modified

| File | Status | Purpose |
|---|---|---|
| `backend/app/workflows/__init__.py` | **NEW** | Package exports |
| `backend/app/workflows/state.py` | **NEW** | `MetaRadarState`, reducers, `create_initial_state` |
| `backend/app/workflows/graph.py` | **NEW** | 10-node `StateGraph` assembly & compilation |
| `backend/app/workflows/runner.py` | **NEW** | `PipelineRunner` async wrapper |
| `backend/app/workflows/nodes/__init__.py` | **NEW** | Node re-exports |
| `backend/app/workflows/nodes/ingest.py` | **NEW** | `node_ingest` |
| `backend/app/workflows/nodes/validate.py` | **NEW** | `node_validate` |
| `backend/app/workflows/nodes/nlp_extract.py` | **NEW** | `node_nlp_extract` |
| `backend/app/workflows/nodes/ontology.py` | **NEW** | `node_ontology_enrich` |
| `backend/app/workflows/nodes/confluence.py` | **NEW** | `node_confluence` |
| `backend/app/workflows/nodes/lifecycle.py` | **NEW** | `node_lifecycle` |
| `backend/app/workflows/nodes/redteam.py` | **NEW** | `node_redteam` |
| `backend/app/workflows/nodes/missing_signal.py` | **NEW** | `node_missing_signal` |
| `backend/app/workflows/nodes/synthesize.py` | **NEW** | `node_synthesize` |
| `backend/app/workflows/nodes/calibrate.py` | **NEW** | `node_calibrate` |
| `backend/app/api/v1/endpoints/pipeline.py` | **NEW** | `POST /api/v1/pipeline/run` |
| `backend/app/data/synthetic_signals.json` | **NEW** | 500-entry synthetic fallback dataset |
| `backend/app/main.py` | **MODIFY** | Register pipeline router |
| `backend/app/schemas/__init__.py` | **MODIFY** | Add `PipelineRunResponseSchema` |
| `config/haemophilia.yaml` | **MODIFY** | Add `lag_thresholds` section (if missing) |
| `tests/test_intelligence_nodes.py` | **NEW** | 20+ node unit + integration tests |
| `contracts/openapi.json` | **MODIFY** | Re-export with pipeline endpoint |
| `frontend/types/api.ts` | **MODIFY** | Re-generate after OpenAPI export |

---

## Deferred to Later Phases

- Real 384-dim `sentence-transformers` embedding generation → Phase 3
- Real pgvector HNSW similarity search → Phase 3
- Real GPU-quantized Gemma 3 4B inference → Phase 3
- Live Grok API key validation → Phase 3
- Frontend Dashboard real-time rendering → Phase 4
- `StakeholderCalibrationService` UI → Phase 5
- Hackathon demo story (mim8 / emicizumab / Hemgenix) → Phase 5
