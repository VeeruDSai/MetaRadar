# Phase 2: LangGraph 10-Node Intelligence Engine - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.  
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-08-14  
**Phase:** 2-LangGraph 10-Node Intelligence Engine  
**Areas discussed:** Pipeline Execution & Trigger Mode, NLP Extraction & Entity Resolution, Confluence Clustering & Development Linking, Missing-Signal Detection & Stakeholder Watch Rules, Four-Question Synthesis & Role-Specific Brief Routing

---

## 1. Pipeline Execution, State Reducers & Trigger Mode

| Option | Description | Selected |
|--------|-------------|----------|
| In-process async execution | In-process async execution triggered via FastAPI endpoint and APScheduler with status tracked in `pipeline_runs` (`queued -> running -> completed/failed`) | ✓ |
| Synchronous blocking endpoint | Synchronous blocking endpoint returning final IntelligenceState directly in HTTP response | |
| Worker queue consuming jobs | Worker queue consuming jobs from Redis with task polling endpoints | |
| TypedDict with typed reducers | Standard `TypedDict` with `Annotated[list, operator.add]` for accumulating entities/signals/alerts and replacement semantics for scalar metadata | ✓ |
| Pydantic BaseState model | Pydantic BaseState model with immutable copy-on-write state transitions | |
| Bounded bronze batch reading | Query unpromoted bronze records (`processed=false`) in bounded batches (50–100 records) with synthetic JSON fallback when bronze is empty | ✓ |
| Live connector fetch in ingest | Fetch live from connectors on-demand during `node_ingest` if bronze queue is empty | |
| Per-node try/except error boundary | Per-node try/except boundary appending structured errors to `state['errors']` with graceful degradation for downstream nodes | ✓ |
| Strict fail-fast | Strict fail-fast: any node error terminates graph execution immediately | |

**Decisions:** Captured as D-01 .. D-04.

---

## 2. NLP Extraction & Entity Resolution Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid regex + dictionary extractor | Fast regex + dictionary matching against `config/haemophilia.yaml` with graceful optional spaCy fallback, ensuring zero-crash execution | ✓ |
| Strict spaCy biomedical pipeline | Strict spaCy pipeline requiring pre-downloaded `en_core_sci_md` model with fail-fast | |
| Pure LLM-based NER | Pure LLM prompt sending each signal to Gemma/Grok to extract entities | |
| Domain YAML ontology enrichment | Dictionary-based enrichment using `config/haemophilia.yaml` to attach canonical IDs, mechanisms, modalities, inhibitor categories, and competitors | ✓ |
| SQL database lookup | Query SQL `assets` and `companies` tables during graph execution | |
| Preserve unmapped entities | Preserve signal, mark novel entity with `is_known_ontology=False`, and record in `state['unmapped_entities']` | ✓ |
| Discard unmapped signals | Discard signal if no primary haemophilia asset or disease is resolved | |
| 5-dimension entity extraction | Extract Assets/Synonyms, Companies/Sponsors, Disease/Inhibitors, Clinical Trial NCT IDs/Phases, and Clinical Biomarkers (ABR, Factor levels) | ✓ |

**Decisions:** Captured as D-05 .. D-08.

---

## 3. Confluence Clustering & Development Linking

| Option | Description | Selected |
|--------|-------------|----------|
| Rolling 48h / ≥3 signal types | Group by canonical asset/disease over rolling 48h window requiring ≥3 distinct signal types with weighted severity $S = \sum(w_{type} \times \text{credibility})$ | ✓ |
| Simple keyword frequency | Simple keyword frequency threshold over 7-day rolling window without source diversity constraint | |
| Two-tier development linking | Match by trial NCT ID or asset+indication to attach new Event to existing `development_id`; only create new Development if no match exists | ✓ |
| Always create new Development | Always create a new Development record for every new signal batch | |
| 9-stage FSM lifecycle | 9-stage FSM (`announced -> in_trial -> interim_result -> final_result -> congress_publication -> regulatory_development -> approved -> post_market/discontinued`) with forward progression rules | ✓ |
| Unrestricted state updates | Arbitrary lifecycle stage strings without validation | |
| Immutable Event records | Append immutable `Event` record (`event_type`, `event_date`, `development_id`, `signal_id`, `confidence`) preserving full chronological provenance | ✓ |

**Decisions:** Captured as D-09 .. D-12.

---

## 4. Missing-Signal Detection & Stakeholder Watch Rules

| Option | Description | Selected |
|--------|-------------|----------|
| Domain lag threshold evaluation | Evaluate elapsed days $\Delta t$ against domain lag thresholds in `config/haemophilia.yaml`, calculating confidence $C = \min(0.40 + 0.002 \times \Delta t_{\text{silence}}, 0.95)$ | ✓ |
| Fixed 30-day inactivity timer | Fixed 30-day inactivity timer across all assets and phases | |
| Formal 5-state watch rule lifecycle | `watching -> new_evidence_detected / no_new_evidence / watch_expired / human_review_required`, persisted in `watch_rules` and state | ✓ |
| Boolean active/inactive flag | Simple boolean flag without historical state transition tracking | |
| Strict non-deterministic framing | Guardrail framing: *"Watch for..."*, *"Expected/possible next evidence"*, *"Not observed yet"* — strictly prohibiting certainty claims | ✓ |
| Red-team contradiction cross-reference | Feed `node_redteam` contradiction outputs (Rules A–S) into `node_missing_signal` to cross-reference discrepancies | ✓ |

**Decisions:** Captured as D-13 .. D-16.

---

## 5. Four-Question Synthesis & Role-Specific Brief Routing

| Option | Description | Selected |
|--------|-------------|----------|
| Evidence-sufficiency gate | Verify minimum evidence threshold; if insufficient, restrict to verified facts with *"Insufficient evidence for interpretation"* label; if sufficient, run full synthesis | ✓ |
| Force full synthesis always | Generate speculative synthesis even when evidence is incomplete | |
| Structured Q1–Q4 with epistemic tags | Standardize Q1 (What changed?), Q2 (Why it matters), Q3 (Impacted functions), Q4 (Recommended actions) with `[FACT]`, `[INTERPRETATION]`, `[SPECULATION]` tags | ✓ |
| Free-form paragraph summaries | Unstructured text summary paragraphs | |
| 6-function calibrated routing | Calculate calibrated relevance scores (0.0–1.0) and role-tailored actions across all 6 stakeholder functions (Medical Affairs, Regulatory, Safety, Access, Comms, Leadership) | ✓ |
| Single-function routing | Assign each signal strictly to one department | |
| Calibrate updates & explicit END | `node_calibrate` applies calibration weights, adjusts routing scores, persists final RoleBriefs/Signals, and explicitly terminates at `END` (`node_calibrate -> END`) | ✓ |

**Decisions:** Captured as D-17 .. D-20.
