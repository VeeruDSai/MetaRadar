import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)

# 9-Stage Asset Lifecycle Stage Hierarchy (0 to 8)
LIFECYCLE_STAGE_ORDER = {
    "announced": 0,
    "in_trial": 1,
    "interim_result": 2,
    "final_result": 3,
    "congress_publication": 4,
    "regulatory_development": 5,
    "approved": 6,
    "post_market": 7,
    "discontinued": 8
}

# Signal Type to Candidate Lifecycle Stage Mapping
SIGNAL_TO_STAGE_MAP = {
    "CLINICAL_TRIAL": "in_trial",
    "PUBLICATIONS": "congress_publication",
    "CONGRESS": "congress_publication",
    "REGULATORY": "regulatory_development",
    "COMMERCIAL_PATENT": "announced",
    "SAFETY": "post_market",
    "ACCESS": "post_market",
}


def infer_candidate_stage(signal_type: str, content: str = "") -> str:
    """Infers the most appropriate lifecycle stage from signal content and type."""
    content_lower = content.lower()
    if "fda approved" in content_lower or "ema approved" in content_lower or "marketing authorisation" in content_lower or "market approval" in content_lower:
        return "approved"
    if "supplemental application" in content_lower or "nda submitted" in content_lower or "bla filed" in content_lower or "chmp opinion" in content_lower or "pdufa" in content_lower:
        return "regulatory_development"
    if "interim analysis" in content_lower or "interim results" in content_lower or "preliminary results" in content_lower:
        return "interim_result"
    if "phase 3 completion" in content_lower or "primary endpoint met" in content_lower or "final results" in content_lower or "pivotal trial" in content_lower:
        return "final_result"
    if "oral presentation" in content_lower or "poster presentation" in content_lower or "congress abstract" in content_lower or "abstract #" in content_lower:
        return "congress_publication"
    if "phase 1" in content_lower or "phase 2" in content_lower or "phase 3" in content_lower or "enrolling" in content_lower or "trial evaluation" in content_lower:
        return "in_trial"
    if "discontinued" in content_lower or "terminated" in content_lower or "trial halt" in content_lower:
        return "discontinued"

    return SIGNAL_TO_STAGE_MAP.get(signal_type, "in_trial")


async def node_lifecycle(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 6: node_lifecycle (D-11, D-12)
    Executes 9-stage asset state machine with forward monotonic validation
    and emits immutable LifecycleEvent records preserving trial-to-approval chains.
    """
    node_name = "node_lifecycle"
    scored_signals = state.get("scored_signals", [])
    developments = list(state.get("developments", []))
    lifecycle_events: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        # Index developments by development_id
        dev_map = {str(d.get("development_id")): d for d in developments}

        for sig in scored_signals:
            dev_id = str(sig.get("development_id", ""))
            dev = dev_map.get(dev_id)
            if not dev:
                continue

            current_stage = str(dev.get("current_stage", "announced")).lower()
            current_order = LIFECYCLE_STAGE_ORDER.get(current_stage, 0)

            sig_type = sig.get("signal_type", "CLINICAL_TRIAL")
            content = sig.get("content", "")
            candidate_stage = infer_candidate_stage(sig_type, content)
            candidate_order = LIFECYCLE_STAGE_ORDER.get(candidate_stage, 1)

            # Monotonic Progression Check: Forward progression only
            if candidate_order > current_order and candidate_stage != "discontinued":
                # Advance stage
                dev["current_stage"] = candidate_stage
                dev["updated_at"] = datetime.now(timezone.utc).isoformat()

                event = {
                    "lifecycle_id": str(uuid.uuid4()),
                    "development_id": dev_id,
                    "source_id": sig.get("source_id"),
                    "signal_id": str(sig.get("id") or sig.get("fingerprint")),
                    "stage": candidate_stage,
                    "previous_stage": current_stage,
                    "event_date": sig.get("published_at", datetime.now(timezone.utc).isoformat()),
                    "notes": f"Advanced to {candidate_stage} via {sig_type} signal ({sig.get('title', '')[:80]}).",
                    "confidence": 0.90,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                lifecycle_events.append(event)
                logger.info(f"Development {dev_id} advanced: {current_stage} -> {candidate_stage}")

            elif candidate_order == current_order:
                # Same stage: still log event if novel signal
                event = {
                    "lifecycle_id": str(uuid.uuid4()),
                    "development_id": dev_id,
                    "source_id": sig.get("source_id"),
                    "signal_id": str(sig.get("id") or sig.get("fingerprint")),
                    "stage": current_stage,
                    "previous_stage": current_stage,
                    "event_date": sig.get("published_at", datetime.now(timezone.utc).isoformat()),
                    "notes": f"Evidence update at {current_stage} stage ({sig.get('title', '')[:80]}).",
                    "confidence": 0.85,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                lifecycle_events.append(event)

            else:
                # Regressive attempt: Block and warn
                logger.debug(
                    f"Blocked regressive lifecycle transition for {dev_id}: {current_stage} -> {candidate_stage}."
                )

        return {
            "lifecycle_events": lifecycle_events,
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
            "lifecycle_events": [],
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
