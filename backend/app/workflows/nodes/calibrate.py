import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)


async def node_calibrate(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 10: node_calibrate (D-20)
    Applies stakeholder calibration feedback, adjusts role-routing weights via online
    gradient update, recalculates role brief relevance scores, and explicitly routes to END.
    """
    node_name = "node_calibrate"
    calibration_feedback = state.get("calibration_feedback", [])
    current_weights = dict(state.get("calibration_weights", {}))
    role_briefs = list(state.get("role_briefs", []))
    errors: List[Dict[str, Any]] = []

    try:
        weights_modified = False

        # Apply Stakeholder Feedback Gradient Updates
        for fb in calibration_feedback:
            fn = fb.get("stakeholder_function")
            rating = fb.get("relevance_rating", 3)
            if fn in current_weights and isinstance(rating, (int, float)):
                # Learning rate alpha = 0.05, center baseline at 3.0
                delta = 0.05 * (rating - 3.0)
                old_weight = current_weights[fn]
                new_weight = round(max(0.1, min(2.0, old_weight + delta)), 3)
                if new_weight != old_weight:
                    current_weights[fn] = new_weight
                    weights_modified = True
                    logger.info(f"Calibrated weight for {fn}: {old_weight} -> {new_weight}")

        # Recalculate Adjusted Relevance Scores on Role Briefs
        for brief in role_briefs:
            scores = brief.get("relevance_scores", {})
            adjusted_scores: Dict[str, float] = {}
            for fn, base_score in scores.items():
                w = current_weights.get(fn, 1.0)
                adjusted_scores[fn] = round(min(1.0, base_score * w), 2)

            brief["calibrated_relevance_scores"] = adjusted_scores

            # Determine calibrated primary function
            if adjusted_scores:
                calibrated_primary = max(adjusted_scores.items(), key=lambda x: x[1])[0]
                brief["calibrated_primary_function"] = calibrated_primary

        calibration_history_records = []
        if weights_modified:
            calibration_history_records.append({
                "history_id": str(uuid.uuid4()),
                "version": f"v1.{int(datetime.now(timezone.utc).timestamp())}",
                "weights": current_weights,
                "applied_at": datetime.now(timezone.utc).isoformat()
            })

        return {
            "calibration_weights": current_weights,
            "role_briefs": role_briefs,
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
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
