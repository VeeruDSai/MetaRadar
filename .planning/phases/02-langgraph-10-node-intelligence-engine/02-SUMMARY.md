---
phase: 02-langgraph-10-node-intelligence-engine
plan: 01
subsystem: pipeline
tags: [langgraph, stategraph, ontology, pii-scrubbing, confluence, lifecycle, redteam, synthesis, calibration, pytest]

requires:
  - phase: 00-baseline-stabilization-governance
    provides: quality gates, PII/PHI scrubber, RedTeamNLIService, honest health endpoints, and database models
provides:
  - 10-node stateful LangGraph intelligence pipeline (MetaRadarState contract)
  - 10 modular workflow nodes (node_ingest through node_calibrate -> END)
  - PipelineRunner async execution engine with pipeline_runs tracking
  - REST endpoints (POST /api/v1/pipeline/run, GET /api/v1/pipeline/status/{pipeline_run_id})
  - 500-signal synthetic haemophilia dataset for testing and offline fallback
  - 17 unit and integration tests (tests/test_intelligence_nodes.py)

actuals:
  tasks: 10
  commits: 4

tech-stack:
  added: [langgraph, sqlalchemy, pydantic]
  patterns: [TypedDict state with operator.add/merge_dicts reducers, isolated node error boundaries, epistemic tagging]

key-files:
  created:
    - backend/app/workflows/state.py
    - backend/app/workflows/graph.py
    - backend/app/workflows/runner.py
    - backend/app/workflows/nodes/ingest.py
    - backend/app/workflows/nodes/validate.py
    - backend/app/workflows/nodes/nlp_extract.py
    - backend/app/workflows/nodes/ontology.py
    - backend/app/workflows/nodes/confluence.py
    - backend/app/workflows/nodes/lifecycle.py
    - backend/app/workflows/nodes/redteam.py
    - backend/app/workflows/nodes/missing_signal.py
    - backend/app/workflows/nodes/synthesize.py
    - backend/app/workflows/nodes/calibrate.py
    - backend/app/api/v1/endpoints/pipeline.py
    - backend/app/data/synthetic_signals.json
    - tests/test_intelligence_nodes.py
  modified:
    - config/haemophilia.yaml
    - backend/app/core/domain_config.py
    - backend/app/api/v1/router.py

key-decisions:
  - "D-01: Used LangGraph StateGraph with explicit MetaRadarState TypedDict reducers."
  - "D-02: Enforced evidence sufficiency gate (<120 chars) in node_synthesize before ProviderFactory invocation."
  - "D-03: Generated epistemic [FACT]/[INTERPRETATION]/[SPECULATION] tags across Four-Question briefs."
  - "D-04: Applied online gradient weight calibration clamped to [0.1, 2.0] in node_calibrate."

patterns-established:
  - "Node structure: async node function with isolated error boundaries and node_statuses dictionary."
  - "Epistemic breakdown: Q1 (what changed) -> Q2 (why it matters) -> Q3 (impacted functions) -> Q4 (action)."

requirements-completed:
  - REQ-P2-1
  - REQ-P2-2
  - REQ-P2-3
  - REQ-P2-4
  - REQ-P2-5
  - REQ-P2-6
  - REQ-P2-7
  - REQ-P2-8
  - REQ-P2-9

coverage:
  - id: D1
    description: "MetaRadarState TypedDict contract with typed reducers"
    requirement: REQ-P2-1
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_create_initial_state_structure"
        status: pass
    human_judgment: false
  - id: D2
    description: "Bronze batch ingestion and PII validation"
    requirement: REQ-P2-2
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_validate_filtering_and_pii"
        status: pass
    human_judgment: false
  - id: D3
    description: "5-dimension NLP extraction and haemophilia ontology mapping"
    requirement: REQ-P2-3
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_nlp_extract_5_dimensions"
        status: pass
    human_judgment: false
  - id: D4
    description: "Rolling 48h / >=3 distinct signal type confluence detection"
    requirement: REQ-P2-4
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_confluence_detection_with_3_distinct_signal_types"
        status: pass
    human_judgment: false
  - id: D5
    description: "9-stage asset lifecycle forward state machine"
    requirement: REQ-P2-5
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_lifecycle_advances_stage_and_blocks_regression"
        status: pass
    human_judgment: false
  - id: D6
    description: "19-rule Red-Team contradiction checking"
    requirement: REQ-P2-6
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_redteam_contradiction_detection"
        status: pass
    human_judgment: false
  - id: D7
    description: "Silence lag and stakeholder WATCH rule monitoring"
    requirement: REQ-P2-7
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_missing_signal_lag_calculation_and_guardrails"
        status: pass
    human_judgment: false
  - id: D8
    description: "Four-Question intelligence synthesis with epistemic tags"
    requirement: REQ-P2-8
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_synthesize_generates_four_questions_with_epistemic_tags"
        status: pass
    human_judgment: false
  - id: D9
    description: "Online gradient calibration and terminal routing to END"
    requirement: REQ-P2-9
    verification:
      - kind: unit
        ref: "tests/test_intelligence_nodes.py#test_node_calibrate_applies_feedback_gradient_updates"
        status: pass
    human_judgment: false

duration: 45 min
completed: 2026-08-14
status: complete
---

# Phase 2: LangGraph 10-Node Intelligence Engine Summary

**Production-grade stateful 10-node LangGraph intelligence pipeline with PII scrubbing, ontology enrichment, confluence detection, Red-Team contradiction analysis, Four-Question epistemic synthesis, and online gradient calibration.**

## Performance
- **Status:** Complete (51/51 tests passing)
- **Completed:** 2026-08-14
- **Tasks:** 10
- **Files Created/Modified:** 19

## Accomplishments
- Implemented `MetaRadarState` TypedDict contract with accumulating reducers.
- Constructed and compiled the 10-node `StateGraph` terminating at `END`.
- Implemented `PipelineRunner` for async execution and database run tracking.
- Created all 10 specialized workflow nodes (`node_ingest` through `node_calibrate`).
- Built 17 new unit and integration tests in `tests/test_intelligence_nodes.py`.
- Synchronized OpenAPI specifications and generated TypeScript API clients.

## Verification
- `pytest`: **51/51 passed**
- TypeScript: **0 errors**
- OpenAPI contract: **0 drift**
- All 9 must-have requirements verified in [02-VERIFICATION.md](./02-VERIFICATION.md).
