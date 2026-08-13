import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.services.redteam import RedTeamNLIService
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)


async def node_redteam(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 7: node_redteam (D-16, REQ-P2-6)
    Executes pairwise NLI contradiction analysis across 19-rule registry (Rules A-S)
    evaluating conflicting claims across clinical trials, safety, dosing, and regulatory stance.
    """
    node_name = "node_redteam"
    scored_signals = state.get("scored_signals", state.get("validated_signals", []))
    redteam_flags: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    if not scored_signals:
        return {
            "redteam_flags": [],
            "node_statuses": {node_name: "SUCCESS"}
        }

    try:
        service = RedTeamNLIService(candidate_cap=25)
        claims = []
        for i, sig in enumerate(scored_signals):
            claims.append({
                "claim_id": str(sig.get("id") or sig.get("fingerprint") or f"sig_{i}"),
                "signal_id": str(sig.get("id") or sig.get("fingerprint")),
                "asset": sig.get("asset_id") or sig.get("asset", ""),
                "disease": sig.get("disease", "haemophilia_a"),
                "signal_type": sig.get("signal_type", "CLINICAL_TRIAL"),
                "priority": sig.get("priority", "HIGH"),
                "source": sig.get("source_id", "external_source"),
                "content": sig.get("content", "")[:300],
                "published_at": sig.get("published_at"),
                "development_id": sig.get("development_id")
            })

        contradictions = await service.evaluate_contradictions(claims)

        for c in contradictions:
            flag = {
                "claim_a_id": c.get("claim_a_id"),
                "claim_b_id": c.get("claim_b_id"),
                "rule_id": c.get("rule_id"),
                "rule_name": c.get("rule_name"),
                "severity": c.get("severity", "HIGH"),
                "confidence": c.get("confidence", 0.88),
                "description": c.get("description", ""),
                "detected_at": datetime.now(timezone.utc).isoformat()
            }
            redteam_flags.append(flag)

        return {
            "redteam_flags": redteam_flags,
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
            "redteam_flags": [],
            "errors": errors,
            "node_statuses": {node_name: "DEGRADED"}
        }
