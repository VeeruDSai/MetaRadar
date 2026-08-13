---
phase: 02
slug: langgraph-10-node-intelligence-engine
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-08-14
---

# Phase 02 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x (asyncio_mode = auto) |
| **Config file** | `tests/pytest.ini` |
| **Quick run command** | `python -m pytest tests/test_intelligence_nodes.py -q` |
| **Full suite command** | `python -m pytest tests/ -q` |
| **Estimated runtime** | ~18 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_intelligence_nodes.py -q`
- **After every plan wave:** Run `python -m pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-A | 02 | 1 | REQ-P2-1 | T-02-01 / - | MetaRadarState TypedDict + accumulated reducers exported from package | unit | `pytest tests/test_intelligence_nodes.py::test_create_initial_state_structure` | yes | green |
| 02-01-B | 02 | 1 | REQ-P2-1 | T-02-01 / - | State contract with list-accumulate and dict-merge reducers; initial state factory | unit | `pytest tests/test_intelligence_nodes.py::test_create_initial_state_structure` | yes | green |
| 02-01-C | 02 | 1 | REQ-P2-1 | T-02-01 / - | 10-node StateGraph compiles, terminates at END | integration | `pytest tests/test_intelligence_nodes.py::test_build_graph_compilation` | yes | green |
| 02-02-D | 02 | 2 | REQ-P2-2 | T-02-02 / - | nodes package exports all 10 node modules | unit | `pytest tests/test_intelligence_nodes.py` | yes | green |
| 02-02-E | 02 | 2 | REQ-P2-2 | T-02-02 / - | node_ingest reads bronze/promoted rows; synthetic fallback; PII/PHI scrub | integration | `pytest tests/test_intelligence_nodes.py::test_node_ingest_synthetic_fallback` | yes | green |
| 02-02-F | 02 | 2 | REQ-P2-2 | T-02-02 / - | node_validate filters short/non-English signals; dedup; scrubs via PIIPHIScrubber | integration | `pytest tests/test_intelligence_nodes.py::test_node_validate_filtering_and_pii` | yes | green |
| 02-03-G | 02 | 3 | REQ-P2-3 | T-02-03 / - | node_nlp_extract produces 5-dimension biomedical extraction | integration | `pytest tests/test_intelligence_nodes.py::test_node_nlp_extract_5_dimensions` | yes | green |
| 02-03-H | 02 | 3 | REQ-P2-3 | T-02-03 / - | node_ontology_enrich maps haemophilia.yaml; preserves unmapped entities | integration | `pytest tests/test_intelligence_nodes.py::test_node_ontology_enrich_maps_haemophilia_yaml` | yes | green |
| 02-04-I | 02 | 4 | REQ-P2-4 | T-02-04 / - | node_confluence detects 48h/>=3 distinct signal type convergence; not on 2 types | integration | `pytest tests/test_intelligence_nodes.py::test_node_confluence_detection_with_3_distinct_signal_types` | yes | green |
| 02-04-J | 02 | 4 | REQ-P2-5 | T-02-05 / - | node_lifecycle advances 9-stage state machine; blocks regression | integration | `pytest tests/test_intelligence_nodes.py::test_node_lifecycle_advances_stage_and_blocks_regression` | yes | green |
| 02-05-K | 02 | 5 | REQ-P2-6 | T-02-06 / - | node_redteam runs 19-rule pairwise contradiction checks | integration | `pytest tests/test_intelligence_nodes.py::test_node_redteam_contradiction_detection` | yes | green |
| 02-05-L | 02 | 5 | REQ-P2-7 | T-02-07 / - | node_missing_signal lag computation + WATCH guardrails | integration | `pytest tests/test_intelligence_nodes.py::test_node_missing_signal_lag_calculation_and_guardrails` | yes | green |
| 02-06-M | 02 | 6 | REQ-P2-8 | T-02-08 / - | node_synthesize evidence-sufficiency gate + Q1-Q4 epistemic briefs | integration | `pytest tests/test_intelligence_nodes.py::test_node_synthesize_generates_four_questions_with_epistemic_tags` | yes | green |
| 02-06-N | 02 | 6 | REQ-P2-9 | T-02-09 / - | node_calibrate online gradient updates; routes to END | integration | `pytest tests/test_intelligence_nodes.py::test_node_calibrate_applies_feedback_gradient_updates` | yes | green |
| 02-07-O | 02 | 7 | D-01 | - / - | PipelineRunner async execution tracking pipeline_runs records | integration | `pytest tests/test_intelligence_nodes.py::test_pipeline_runner_end_to_end_execution` | yes | green |
| 02-07-P | 02 | 7 | D-01 | - / - | POST /api/v1/pipeline/run and GET /status/{id} endpoints | integration | `pytest tests/test_api_endpoints.py::test_pipeline_endpoints` | yes | green |
| 02-08-Q | 02 | 8 | REQ-P2-1..9 | all | 17-test Node/runner suite covering all 10 nodes | unit | `pytest tests/test_intelligence_nodes.py` | yes | green |

*Status: green all requirements verified (51/51 full suite passing).*

---

## Wave 0 Requirements

Existing infrastructure covers all phase requirements — pytest 9.x configured at `tests/pytest.ini` with `asyncio_mode = auto`, `testpaths = tests`, `pythonpath = backend .`. No additional stubs, fixtures, or framework installs required.

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Live LLM inference via ProviderFactory (Gemma 3 4B / Grok) | REQ-P2-8 | Requires live model weights (NVIDIA RTX 3050) and live Grok API credentials — deferred to Phase 3 per 02-VERIFICATION.md | Execute real GPU inference and hosted Grok fallback; confirm Four-Question briefs generated with epistemic tags |

---

## Validation Sign-Off

- [x] All tasks have automated verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 20s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-08-14