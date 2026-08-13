import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.domain_config import get_domain_config
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)

DEFAULT_LAG_THRESHOLDS = {
    "announced": 120,
    "in_trial": 180,
    "interim_result": 120,
    "final_result": 180,
    "congress_publication": 90,
    "regulatory_development": 270,
    "approved": 365,
    "post_market": 365,
    "discontinued": 730
}


def calculate_silence_confidence(delta_days: int) -> float:
    """Calculates silence confidence formula: C = min(0.40 + 0.002 * delta_days, 0.95)."""
    return round(min(0.40 + 0.002 * max(0, delta_days), 0.95), 2)


async def node_missing_signal(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 8: node_missing_signal (D-13, D-14, D-15, D-16)
    Calculates silence lag alerts and evaluates stakeholder WATCH rules with
    5-state transitions, strict non-deterministic guardrail language,
    and Red-Team contradiction cross-referencing.
    """
    node_name = "node_missing_signal"
    developments = state.get("developments", [])
    lifecycle_events = state.get("lifecycle_events", [])
    redteam_flags = state.get("redteam_flags", [])
    scored_signals = state.get("scored_signals", [])

    missing_signals: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        domain_cfg = get_domain_config()
        lag_thresholds = domain_cfg.lag_thresholds if (domain_cfg and domain_cfg.lag_thresholds) else DEFAULT_LAG_THRESHOLDS

        # Build index of last event date per development
        dev_last_event: Dict[str, datetime] = {}
        for ev in lifecycle_events:
            d_id = str(ev.get("development_id", ""))
            ev_dt_str = ev.get("event_date")
            if ev_dt_str and d_id:
                try:
                    dt = datetime.fromisoformat(str(ev_dt_str).replace("Z", "+00:00"))
                    if d_id not in dev_last_event or dt > dev_last_event[d_id]:
                        dev_last_event[d_id] = dt
                except Exception:
                    pass

        # Build index of redteam contradictions by asset / claim
        contradicted_assets = set()
        for rf in redteam_flags:
            desc = rf.get("description", "")
            for dev in developments:
                asset_name = dev.get("asset_id", "")
                if asset_name and asset_name.lower() in desc.lower():
                    contradicted_assets.add(str(dev.get("development_id")))

        now = datetime.now(timezone.utc)

        for dev in developments:
            dev_id = str(dev.get("development_id", ""))
            current_stage = str(dev.get("current_stage", "announced")).lower()
            asset_id = dev.get("asset_id", "Unknown Asset")
            threshold_days = lag_thresholds.get(current_stage, 180)

            # Determine last signal date
            last_dt = dev_last_event.get(dev_id)
            if not last_dt:
                created_at_str = dev.get("created_at")
                try:
                    last_dt = datetime.fromisoformat(str(created_at_str).replace("Z", "+00:00")) if created_at_str else now
                except Exception:
                    last_dt = now

            delta_days = (now - last_dt).days

            # Signals detected in current batch for this development
            signals_in_batch = [s for s in scored_signals if str(s.get("development_id")) == dev_id]

            # Determine 5-State Watch Rule Status (D-14)
            if signals_in_batch:
                watch_status = "new_evidence_detected"
            elif delta_days <= threshold_days:
                watch_status = "watching"
            elif delta_days > (threshold_days * 2):
                watch_status = "watch_expired"
            else:
                watch_status = "no_new_evidence"

            has_contradiction = dev_id in contradicted_assets
            if has_contradiction:
                watch_status = "human_review_required"

            # If silence exceeds threshold, generate alert (D-13, D-15)
            if delta_days > threshold_days:
                confidence = calculate_silence_confidence(delta_days)
                alert_text = (
                    f"Watch for: Expected/possible next evidence regarding {asset_id} at {current_stage} milestone. "
                    f"Not observed yet during the configured monitoring window ({threshold_days} days). "
                    f"Elapsed silence: {delta_days} days."
                )

                alert = {
                    "alert_id": str(uuid.uuid4()),
                    "development_id": dev_id,
                    "asset_id": asset_id,
                    "current_stage": current_stage,
                    "monitoring_window_days": threshold_days,
                    "elapsed_silence_days": delta_days,
                    "confidence": confidence,
                    "status": watch_status,
                    "watch_text": alert_text,
                    "redteam_cross_reference": has_contradiction,
                    "human_review_required": bool(has_contradiction or watch_status == "watch_expired"),
                    "detected_at": now.isoformat()
                }
                missing_signals.append(alert)

        return {
            "missing_signals": missing_signals,
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
            "missing_signals": [],
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
