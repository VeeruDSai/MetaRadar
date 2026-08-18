import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.workflows.state import MetaRadarState
from app.services.calibration import StakeholderCalibrationService
from app.schemas import FeedbackSubmissionRequest

logger = logging.getLogger(__name__)


async def node_calibrate(
    state: MetaRadarState, session: Optional[AsyncSession] = None
) -> Dict[str, Any]:
    """
    Node 10: node_calibrate (D-20, D-01, D-02)
    Applies stakeholder calibration feedback, adjusts role-routing weights via online
    gradient update (in-memory or persistent StakeholderCalibrationService), recalculates role brief
    relevance scores, and explicitly routes to END.
    """
    node_name = "node_calibrate"
    calibration_feedback = state.get("calibration_feedback", [])
    current_weights = dict(state.get("calibration_weights", {}))
    role_briefs = list(state.get("role_briefs", []))
    errors: List[Dict[str, Any]] = []

    try:
        if session is not None:
            service = StakeholderCalibrationService(session)

            # Persist any feedback items from state
            for fb in calibration_feedback:
                if isinstance(fb, dict) and "signal_id" in fb and "stakeholder_function" in fb:
                    try:
                        sig_id_val = fb["signal_id"]
                        if isinstance(sig_id_val, str):
                            sig_id_val = uuid.UUID(sig_id_val)
                        req = FeedbackSubmissionRequest(
                            signal_id=sig_id_val,
                            stakeholder_function=fb["stakeholder_function"],
                            relevance_rating=fb.get("relevance_rating", 3),
                            urgency_rating=fb.get("urgency_rating", 3),
                            action_appropriate=fb.get("action_appropriate", True),
                            comments=fb.get("comments"),
                            user_id=fb.get("user_id", "pipeline_agent"),
                        )
                        await service.submit_feedback(req)
                    except Exception as fe:
                        logger.warning(f"Skipping invalid feedback entry during pipeline calibration: {fe}")

            # Trigger batch recalibration across all roles
            recal_resp = await service.recalibrate_role()
            for rw in recal_resp.updated_weights:
                current_weights[rw.stakeholder_function] = rw.impact_weight
        else:
            # In-Memory Fast Execution Path (Backwards Compatibility & Unit Tests)
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
                        logger.info(f"In-memory calibrated weight for {fn}: {old_weight} -> {new_weight}")

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

