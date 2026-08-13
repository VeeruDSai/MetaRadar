import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.domain_config import get_domain_config
from app.providers.base import DataClassification, ProviderCapability
from app.providers.factory import provider_factory
from app.services.deduplication import chunk_text_for_embedding
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)

ALL_FUNCTIONS = [
    "MEDICAL_AFFAIRS",
    "REGULATORY",
    "SAFETY",
    "MARKET_ACCESS",
    "COMMUNICATIONS",
    "LEADERSHIP"
]


def _build_factual_only_brief(sig: Dict[str, Any], reason: str = "Insufficient evidence") -> Dict[str, Any]:
    """Constructs a strictly factual brief when evidence sufficiency gate fails (D-17)."""
    title = sig.get("title", "")
    content_excerpt = sig.get("content", "")[:200]
    return {
        "brief_id": str(uuid.uuid4()),
        "signal_id": str(sig.get("id") or sig.get("fingerprint")),
        "development_id": sig.get("development_id"),
        "q1_what_changed": f"[FACT] {title}. {content_excerpt}",
        "q2_why_matters": f"[INTERPRETATION] Insufficient evidence to support an interpretation — human review requested ({reason}).",
        "q3_impacted_functions": [],
        "q4_action": "[INTERPRETATION] Human review requested to establish clinical context before action formulation.",
        "relevance_scores": {fn: 0.20 for fn in ALL_FUNCTIONS},
        "primary_function": "MEDICAL_AFFAIRS",
        "evidence_sufficient": False,
        "epistemic_breakdown": {
            "facts": [f"{title}. {content_excerpt}"],
            "interpretation": "Insufficient evidence to support an interpretation — human review requested.",
            "speculation": None
        },
        "generated_at": datetime.now(timezone.utc).isoformat()
    }


async def node_synthesize(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 9: node_synthesize (D-17, D-18, D-19)
    Enforces the evidence sufficiency gate, invokes ProviderFactory to generate
    Four-Question briefs (Q1-Q4) with [FACT]/[INTERPRETATION]/[SPECULATION] tags,
    and calculates role-tailored routing scores across all 6 stakeholder functions.
    """
    node_name = "node_synthesize"
    scored_signals = state.get("scored_signals", state.get("validated_signals", []))
    ontology_entities = state.get("ontology_entities", [])
    calibration_weights = state.get("calibration_weights", {})

    role_briefs: List[Dict[str, Any]] = []
    model_metadata_list: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        domain_cfg = get_domain_config()
        routing_matrix = domain_cfg.baseline_routing_matrix if domain_cfg else {}

        ent_by_sig = {e.get("signal_id"): e for e in ontology_entities}

        for sig in scored_signals:
            sig_id = str(sig.get("id") or sig.get("fingerprint"))
            content = str(sig.get("content") or "").strip()
            title = str(sig.get("title") or "").strip()
            sig_type = sig.get("signal_type", "CLINICAL_TRIAL")
            asset_id = sig.get("asset_id", "Competitor Asset")
            company = sig.get("company", "Competitor")

            ent = ent_by_sig.get(sig_id, {})
            has_entities = bool(ent.get("assets") or ent.get("nct_ids") or ent.get("diseases"))

            # Evidence Sufficiency Check (D-17)
            if len(content) < 120 or not has_entities:
                brief = _build_factual_only_brief(sig, "content length below threshold or unmapped entity")
                role_briefs.append(brief)
                continue

            # Build evidence chunks
            evidence_chunk = chunk_text_for_embedding(f"{title}\n\n{content}")
            evidence_list = [evidence_chunk]

            # Formulate Four-Question synthesis prompt
            task_prompt = (
                f"Synthesize intelligence for haemophilia asset '{asset_id}' ({company}) "
                f"under signal type '{sig_type}'. Generate Four-Question breakdown:\n"
                f"Q1 (What changed?): Facts citing trial or regulatory event.\n"
                f"Q2 (Why it matters?): Strategic implications for Novo Nordisk portfolio.\n"
                f"Q3 (Impacted functions?): Relevant stakeholder functions.\n"
                f"Q4 (Recommended action?): Actionable strategic guidance.\n"
                f"Tag all sentences with [FACT], [INTERPRETATION], or [SPECULATION]."
            )

            # Compute Baseline Function Relevance Scores (D-19)
            base_routing = routing_matrix.get(sig_type, {})
            primary_fn = base_routing.get("primary", "MEDICAL_AFFAIRS")
            secondary_fns = base_routing.get("secondary", [])

            relevance_scores: Dict[str, float] = {}
            for fn in ALL_FUNCTIONS:
                if fn == primary_fn:
                    score = 0.90
                elif fn in secondary_fns:
                    score = 0.70
                else:
                    score = 0.35

                # Modulate by active calibration weights
                weight = calibration_weights.get(fn, 1.0)
                relevance_scores[fn] = round(min(1.0, score * weight), 2)

            # Invoke ProviderFactory Reasoning Layer
            try:
                intelligence = await provider_factory.execute_task(
                    required_capability=ProviderCapability.REASON,
                    evidence=evidence_list,
                    task=task_prompt,
                    classification=DataClassification.PUBLIC
                )

                meta = intelligence.get("model_metadata", {})
                model_metadata_list.append(meta)

                q1_text = intelligence.get("q1_what_changed") or f"[FACT] {title}. {content[:180]}..."
                q2_text = intelligence.get("q2_why_matters") or f"[INTERPRETATION] Demonstrates clinical development progression for {asset_id} ({company}), affecting competitive positioning."
                q3_functions = intelligence.get("q3_impacted_functions") or [primary_fn] + secondary_fns
                q4_action = intelligence.get("q4_action") or f"[INTERPRETATION] {primary_fn.replace('_', ' ').title()} should review clinical trial outcomes and cross-reference with internal pipeline milestones."

                # Ensure epistemic tags are present
                if not any(tag in q1_text for tag in ["[FACT]", "[INTERPRETATION]", "[SPECULATION]"]):
                    q1_text = f"[FACT] {q1_text}"
                if not any(tag in q2_text for tag in ["[FACT]", "[INTERPRETATION]", "[SPECULATION]"]):
                    q2_text = f"[INTERPRETATION] {q2_text}"
                if not any(tag in q4_action for tag in ["[FACT]", "[INTERPRETATION]", "[SPECULATION]"]):
                    q4_action = f"[INTERPRETATION] {q4_action}"

                brief = {
                    "brief_id": str(uuid.uuid4()),
                    "signal_id": sig_id,
                    "development_id": sig.get("development_id"),
                    "q1_what_changed": q1_text,
                    "q2_why_matters": q2_text,
                    "q3_impacted_functions": q3_functions,
                    "q4_action": q4_action,
                    "relevance_scores": relevance_scores,
                    "primary_function": primary_fn,
                    "evidence_sufficient": True,
                    "epistemic_breakdown": {
                        "facts": [q1_text],
                        "interpretation": q2_text,
                        "speculation": q4_action if "[SPECULATION]" in q4_action else None
                    },
                    "model_metadata": meta,
                    "generated_at": datetime.now(timezone.utc).isoformat()
                }
                role_briefs.append(brief)

            except Exception as pe:
                logger.warning(f"Provider execution degraded for signal {sig_id}: {pe}")
                fallback_brief = _build_factual_only_brief(sig, f"Provider degraded mode: {pe}")
                role_briefs.append(fallback_brief)

        return {
            "role_briefs": role_briefs,
            "model_metadata": model_metadata_list,
            "node_statuses": {node_name: "SUCCESS"}
        }

    except Exception as e:
        logger.error(f"Error in {node_name}: {e}", exc_info=True)
        errors.append({
            "node": node_name,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return {
            "role_briefs": [],
            "model_metadata": [],
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
