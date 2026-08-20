import pytest
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, patch

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.workflows.state import create_initial_state, DEFAULT_CALIBRATION_WEIGHTS
from app.workflows.graph import build_graph
from app.workflows.runner import PipelineRunner
from app.workflows.nodes import (
    node_ingest,
    node_validate,
    node_nlp_extract,
    node_ontology_enrich,
    node_confluence,
    node_lifecycle,
    node_redteam,
    node_missing_signal,
    node_synthesize,
    node_calibrate,
)


# ============================================================================
# Wave 1: State Contract & Graph Assembly Tests
# ============================================================================

def test_create_initial_state_structure():
    state = create_initial_state(pipeline_run_id="test-run-1", batch_size=25)
    assert state["pipeline_run_id"] == "test-run-1"
    assert state["batch_size"] == 25
    assert state["signals_processed"] == 0
    assert isinstance(state["raw_signals"], list)
    assert isinstance(state["validated_signals"], list)
    assert isinstance(state["extracted_entities"], list)
    assert isinstance(state["ontology_entities"], list)
    assert isinstance(state["developments"], list)
    assert isinstance(state["scored_signals"], list)
    assert isinstance(state["confluent_stories"], list)
    assert isinstance(state["lifecycle_events"], list)
    assert isinstance(state["redteam_flags"], list)
    assert isinstance(state["missing_signals"], list)
    assert isinstance(state["unmapped_entities"], list)
    assert isinstance(state["role_briefs"], list)
    assert isinstance(state["errors"], list)
    assert state["calibration_weights"]["MEDICAL_AFFAIRS"] == 1.0


def test_build_graph_compilation():
    graph = build_graph()
    assert graph is not None
    # Verify graph node names exist
    node_keys = graph.nodes.keys()
    assert "node_ingest" in node_keys
    assert "node_validate" in node_keys
    assert "node_nlp_extract" in node_keys
    assert "node_ontology_enrich" in node_keys
    assert "node_confluence" in node_keys
    assert "node_lifecycle" in node_keys
    assert "node_redteam" in node_keys
    assert "node_missing_signal" in node_keys
    assert "node_synthesize" in node_keys
    assert "node_calibrate" in node_keys


# ============================================================================
# Wave 2: Ingest & Validate Node Tests
# ============================================================================

@pytest.mark.asyncio
async def test_node_ingest_synthetic_fallback():
    state = create_initial_state(batch_size=5)
    result = await node_ingest(state, session=None)
    assert result["node_statuses"]["node_ingest"] == "SUCCESS"
    assert len(result["raw_signals"]) == 5
    assert result["signals_processed"] == 5


@pytest.mark.asyncio
async def test_node_ingest_prioritizes_existing_raw_signals():
    existing = [{"id": "s1", "title": "Test Signal", "content": "Content here"}]
    state = create_initial_state(raw_signals=existing)
    result = await node_ingest(state, session=None)
    assert result["raw_signals"] == existing
    assert result["signals_processed"] == 1


@pytest.mark.asyncio
async def test_node_validate_filtering_and_pii():
    raw_signals = [
        # Short content -> filtered
        {"id": "s1", "title": "Short", "content": "Too short"},
        # Valid content with PII -> scrubbed
        {
            "id": "s2",
            "title": "Clinical Update for Patient John Smith",
            "content": "Phase 3 trial evaluating emicizumab with patient contact john.smith@hospital.com and SSN 000-11-2222 in haemophilia.",
            "published_at": "2025-06-01T00:00:00Z",
            "source_id": "pubmed",
            "external_id": "pmid:99901"
        },
        # Duplicate of s2 -> filtered
        {
            "id": "s3",
            "title": "Clinical Update for Patient John Smith",
            "content": "Phase 3 trial evaluating emicizumab with patient contact john.smith@hospital.com and SSN 000-11-2222 in haemophilia.",
            "published_at": "2025-06-01T00:00:00Z",
            "source_id": "pubmed",
            "external_id": "pmid:99901"
        }
    ]
    state = create_initial_state(raw_signals=raw_signals)
    state["raw_signals"] = raw_signals

    result = await node_validate(state)
    val = result["validated_signals"]
    assert len(val) == 1
    assert "john.smith@hospital.com" not in val[0]["content"]
    assert "[EMAIL_REDACTED]" in val[0]["content"] or "[REDACTED]" in val[0]["content"]
    assert val[0]["fingerprint"].startswith("pmid:99901")


# ============================================================================
# Wave 3: NLP Extract & Ontology Enrichment Tests
# ============================================================================

@pytest.mark.asyncio
async def test_node_nlp_extract_5_dimensions():
    validated_signals = [{
        "id": "s_nlp_1",
        "title": "Phase 3 Trial of mim8 in Haemophilia A with Inhibitors",
        "content": "Novo Nordisk reported updated Phase 3 clinical data (NCT04869267) for mim8. "
                   "The primary endpoint ABR demonstrated significant reduction, with sustained Factor VIII activity in patients with inhibitors.",
        "published_at": "2025-06-01T00:00:00Z"
    }]
    state = create_initial_state()
    state["validated_signals"] = validated_signals

    result = await node_nlp_extract(state)
    assert result["node_statuses"]["node_nlp_extract"] == "SUCCESS"
    entities = result["extracted_entities"][0]
    assert any(a["asset_id"] == "mim8" for a in entities["assets"])
    assert "Novo Nordisk" in entities["companies"]
    assert "NCT04869267" in entities["nct_ids"]
    assert "ABR" in entities["biomarkers"]
    assert "Factor VIII" in entities["biomarkers"]
    assert entities["inhibitor_status"] == "with_inhibitors"


@pytest.mark.asyncio
async def test_node_ontology_enrich_maps_haemophilia_yaml():
    extracted = [{
        "signal_id": "sig_ont_1",
        "assets": [{"asset_id": "emicizumab"}],
        "diseases": ["haemophilia_a"],
        "companies": ["Roche"],
        "nct_ids": ["NCT03000000"],
        "biomarkers": ["ABR"],
        "inhibitor_status": "all_inhibitor_statuses"
    }]
    state = create_initial_state()
    state["extracted_entities"] = extracted

    result = await node_ontology_enrich(state)
    assert result["node_statuses"]["node_ontology_enrich"] == "SUCCESS"
    enriched = result["ontology_entities"][0]
    assert enriched["primary_asset"]["brand_name"] == "Hemlibra"
    assert enriched["primary_asset"]["mechanism"] == "FVIIIa-mimetic bispecific antibody"
    assert enriched["primary_asset"]["is_novo_nordisk"] is False
    assert enriched["is_known_ontology"] is True


@pytest.mark.asyncio
async def test_node_ontology_enrich_preserves_unmapped_entities():
    extracted = [{
        "signal_id": "sig_novel",
        "assets": [{"asset_id": "novel_drug_x99", "brand_name": "X-99"}],
        "diseases": ["haemophilia_a"],
        "companies": ["StartupBio"],
        "nct_ids": [],
        "biomarkers": [],
        "inhibitor_status": "without_inhibitors"
    }]
    state = create_initial_state()
    state["extracted_entities"] = extracted

    result = await node_ontology_enrich(state)
    assert len(result["unmapped_entities"]) == 1
    assert result["unmapped_entities"][0]["entity_id"] == "novel_drug_x99"
    assert result["unmapped_entities"][0]["is_known_ontology"] is False


# ============================================================================
# Wave 4: Confluence & Lifecycle Tests
# ============================================================================

@pytest.mark.asyncio
async def test_node_confluence_detection_with_3_distinct_signal_types():
    base_time = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    signals = [
        {
            "id": "c_sig_1",
            "title": "Clinical Trial mim8",
            "content": "Phase 3 results for mim8 in haemophilia.",
            "published_at": base_time.isoformat(),
            "signal_type": "CLINICAL_TRIAL",
            "asset_id": "mim8",
            "disease": "haemophilia_a"
        },
        {
            "id": "c_sig_2",
            "title": "Regulatory Filing mim8",
            "content": "Regulatory dossier submission for mim8.",
            "published_at": (base_time + timedelta(hours=6)).isoformat(),
            "signal_type": "REGULATORY",
            "asset_id": "mim8",
            "disease": "haemophilia_a"
        },
        {
            "id": "c_sig_3",
            "title": "Congress Abstract mim8",
            "content": "Congress presentation of mim8 real-world data.",
            "published_at": (base_time + timedelta(hours=18)).isoformat(),
            "signal_type": "CONGRESS",
            "asset_id": "mim8",
            "disease": "haemophilia_a"
        }
    ]
    state = create_initial_state()
    state["validated_signals"] = signals
    state["ontology_entities"] = [{"signal_id": s["id"], "primary_asset": {"asset_id": "mim8"}} for s in signals]

    result = await node_confluence(state)
    assert result["node_statuses"]["node_confluence"] == "SUCCESS"
    assert len(result["confluent_stories"]) >= 1
    story = result["confluent_stories"][0]
    assert story["asset_id"] == "mim8"
    assert story["signal_count"] == 3
    assert story["severity_score"] > 0
    assert len(result["developments"]) >= 1


@pytest.mark.asyncio
async def test_node_confluence_does_not_trigger_with_only_2_types():
    base_time = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    signals = [
        {"id": "c1", "title": "T1", "content": "T1", "published_at": base_time.isoformat(), "signal_type": "CLINICAL_TRIAL", "asset_id": "concizumab"},
        {"id": "c2", "title": "T2", "content": "T2", "published_at": (base_time + timedelta(hours=2)).isoformat(), "signal_type": "CLINICAL_TRIAL", "asset_id": "concizumab"}
    ]
    state = create_initial_state()
    state["validated_signals"] = signals
    state["ontology_entities"] = [{"signal_id": s["id"], "primary_asset": {"asset_id": "concizumab"}} for s in signals]

    result = await node_confluence(state)
    assert len(result["confluent_stories"]) == 0


@pytest.mark.asyncio
async def test_node_lifecycle_advances_stage_and_blocks_regression():
    dev = {
        "development_id": "dev_fsm_1",
        "title": "mim8 Development",
        "current_stage": "announced",
        "asset_id": "mim8"
    }
    scored_signals = [
        {
            "id": "sig_trial",
            "development_id": "dev_fsm_1",
            "signal_type": "CLINICAL_TRIAL",
            "title": "Phase 3 Trial Evaluation",
            "content": "Phase 3 clinical evaluation enrolling patients.",
            "published_at": "2025-06-01T00:00:00Z"
        }
    ]
    state = create_initial_state()
    state["developments"] = [dev]
    state["scored_signals"] = scored_signals

    result = await node_lifecycle(state)
    assert result["node_statuses"]["node_lifecycle"] == "SUCCESS"
    assert dev["current_stage"] == "in_trial"
    assert len(result["lifecycle_events"]) == 1
    assert result["lifecycle_events"][0]["stage"] == "in_trial"

    # Now attempt a regressive signal (Commercial Patent implying announced)
    regressive_signal = [{
        "id": "sig_regressive",
        "development_id": "dev_fsm_1",
        "signal_type": "COMMERCIAL_PATENT",
        "title": "Patent filing",
        "content": "Commercial patent filing.",
        "published_at": "2025-06-02T00:00:00Z"
    }]
    state["scored_signals"] = regressive_signal
    await node_lifecycle(state)
    # Stage should NOT regress to announced
    assert dev["current_stage"] == "in_trial"


# ============================================================================
# Wave 5: Red-Team & Missing Signal Tests
# ============================================================================

@pytest.mark.asyncio
async def test_node_redteam_contradiction_detection():
    scored_signals = [
        {
            "id": "rt_1",
            "asset_id": "Hemgenix",
            "signal_type": "CLINICAL_TRIAL",
            "priority": "HIGH",
            "source_id": "PubMed",
            "content": "Study claims once-weekly dosing regimen."
        },
        {
            "id": "rt_2",
            "asset_id": "Hemgenix",
            "signal_type": "REGULATORY",
            "priority": "HIGH",
            "source_id": "FDA",
            "content": "FDA label specifies single-dose vector administration."
        }
    ]
    state = create_initial_state()
    state["scored_signals"] = scored_signals

    result = await node_redteam(state)
    assert result["node_statuses"]["node_redteam"] == "SUCCESS"
    assert len(result["redteam_flags"]) >= 1
    flag = result["redteam_flags"][0]
    assert flag["rule_id"] == "RULE_A_DOSING_CONTRADICTION"
    assert flag["severity"] == "HIGH"


@pytest.mark.asyncio
async def test_node_missing_signal_lag_calculation_and_guardrails():
    silent_date = datetime.now(timezone.utc) - timedelta(days=210)
    dev = {
        "development_id": "dev_silent_1",
        "asset_id": "mim8",
        "current_stage": "in_trial",
        "created_at": silent_date.isoformat()
    }
    lifecycle_events = [{
        "development_id": "dev_silent_1",
        "event_date": silent_date.isoformat()
    }]
    state = create_initial_state()
    state["developments"] = [dev]
    state["lifecycle_events"] = lifecycle_events
    state["scored_signals"] = []

    result = await node_missing_signal(state)
    assert result["node_statuses"]["node_missing_signal"] == "SUCCESS"
    assert len(result["missing_signals"]) == 1
    alert = result["missing_signals"][0]
    assert alert["elapsed_silence_days"] >= 209
    assert alert["confidence"] >= 0.80
    assert "Watch for:" in alert["watch_text"]
    assert "Not observed yet" in alert["watch_text"]
    # Check that forbidden certainty claims do NOT appear
    for forbidden in ["cancelled", "failed", "abandoned", "confirmed absent"]:
        assert forbidden not in alert["watch_text"].lower()


# ============================================================================
# Wave 6: Synthesis & Calibration Tests
# ============================================================================

@pytest.mark.asyncio
async def test_node_synthesize_evidence_sufficiency_gate():
    # Signal with short content (< 120 chars) -> should fail sufficiency gate
    insufficient_signal = {
        "id": "sig_insufficient",
        "title": "Brief headline",
        "content": "Short blurb.",
        "signal_type": "CLINICAL_TRIAL",
        "asset_id": "mim8"
    }
    state = create_initial_state()
    state["scored_signals"] = [insufficient_signal]
    state["ontology_entities"] = []

    result = await node_synthesize(state)
    brief = result["role_briefs"][0]
    assert brief["evidence_sufficient"] is False
    assert "Insufficient evidence" in brief["q2_why_matters"]
    assert brief["q1_what_changed"].startswith("[FACT]")


@pytest.mark.asyncio
async def test_node_synthesize_generates_four_questions_with_epistemic_tags():
    sufficient_signal = {
        "id": "sig_sufficient",
        "title": "Phase 3 Readout of mim8 Demonstrates Superior Bleed Control",
        "content": "Novo Nordisk announced comprehensive Phase 3 trial results (NCT04869267) for mim8. "
                   "Treatment resulted in zero treated bleeds in 86% of patients, presenting strong competitive differentiation vs emicizumab.",
        "signal_type": "CLINICAL_TRIAL",
        "asset_id": "mim8",
        "company": "Novo Nordisk"
    }
    state = create_initial_state()
    state["scored_signals"] = [sufficient_signal]
    state["ontology_entities"] = [{
        "signal_id": "sig_sufficient",
        "assets": [{"asset_id": "mim8"}],
        "nct_ids": ["NCT04869267"]
    }]

    result = await node_synthesize(state)
    assert len(result["role_briefs"]) == 1
    brief = result["role_briefs"][0]
    assert brief["evidence_sufficient"] is True
    assert "[FACT]" in brief["q1_what_changed"]
    assert "[INTERPRETATION]" in brief["q2_why_matters"] or "[FACT]" in brief["q2_why_matters"]
    assert len(brief["relevance_scores"]) == 6


@pytest.mark.asyncio
async def test_node_calibrate_applies_feedback_gradient_updates():
    brief = {
        "brief_id": "b1",
        "signal_id": "s1",
        "relevance_scores": {
            "REGULATORY": 0.70,
            "MEDICAL_AFFAIRS": 0.90,
            "SAFETY": 0.50
        }
    }
    feedback = [
        # Rating 5 for REGULATORY -> weight should increase (delta = +0.10)
        {"stakeholder_function": "REGULATORY", "relevance_rating": 5}
    ]
    state = create_initial_state(calibration_feedback=feedback)
    state["role_briefs"] = [brief]

    result = await node_calibrate(state)
    assert result["node_statuses"]["node_calibrate"] == "SUCCESS"
    new_reg_weight = result["calibration_weights"]["REGULATORY"]
    assert new_reg_weight > 1.0
    cal_scores = result["role_briefs"][0]["calibrated_relevance_scores"]
    assert cal_scores["REGULATORY"] > 0.70


# ============================================================================
# Wave 7: PipelineRunner End-to-End Test
# ============================================================================

@pytest.mark.asyncio
async def test_pipeline_runner_end_to_end_execution():
    sample_signals = [
        {
            "id": "e2e_sig_1",
            "title": "FDA Grants Priority Review for Gene Therapy in Haemophilia B",
            "source_id": "fda",
            "signal_type": "REGULATORY",
            "content": "Supplemental Biologics License Application (sBLA) for Hemgenix (etranacogene dezaparvovec) accepted under Priority Review for expanded indications in haemophilia B.",
            "disease": "haemophilia_b",
            "published_at": "2026-08-15T00:00:00Z"
        },
        {
            "id": "e2e_sig_2",
            "title": "Phase 3 Trial Demonstrates Long-Term Durability",
            "source_id": "clinical_trials",
            "signal_type": "CLINICAL_TRIAL",
            "content": "Phase 3 clinical trial results (NCT03569891) demonstrate sustained Factor IX expression and long-term hemostatic efficacy in severe haemophilia B patients over 36 months.",
            "disease": "haemophilia_b",
            "published_at": "2026-08-16T00:00:00Z"
        }
    ]
    runner = PipelineRunner(session=None)
    final_state = await runner.run(batch_size=2, raw_signals=sample_signals)

    assert final_state["pipeline_run_id"] is not None
    assert final_state["signals_processed"] >= 1
    assert len(final_state["role_briefs"]) >= 1
    assert "node_ingest" in final_state["node_statuses"]
    assert "node_synthesize" in final_state["node_statuses"]
    assert "node_calibrate" in final_state["node_statuses"]
    assert final_state["node_statuses"]["node_calibrate"] == "SUCCESS"
