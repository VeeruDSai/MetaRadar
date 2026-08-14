import operator
import uuid
from typing import Annotated, Any, Dict, List, Optional, TypedDict


def merge_dicts(a: Optional[Dict[str, Any]], b: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    res = dict(a or {})
    if b:
        res.update(b)
    return res


def replace_list(a: Optional[List[Any]], b: Optional[List[Any]]) -> List[Any]:
    """Replacement semantics for list channels that nodes re-emit whole.

    ``node_validate`` and ``node_embed`` both RETURN the full
    ``validated_signals`` list (validate produces it, embed enriches it in
    place). A reducer is mandatory because LangGraph always applies the
    channel reducer to the incoming value — with ``operator.add`` the enriched
    list would be APPENDED to the already-validated list, duplicating every
    signal. Replacement keeps exactly one copy of the canonical list.
    """
    return list(b) if b is not None else list(a or [])


class MetaRadarState(TypedDict, total=False):
    """
    Canonical 10-node LangGraph IntelligenceState contract (D-02).
    Uses typed reducers (Annotated[list, operator.add] and merge_dicts) for accumulating data
    and replacement semantics for scalar metadata.
    """
    pipeline_run_id: str
    raw_signals: Annotated[List[Dict[str, Any]], operator.add]
    validated_signals: Annotated[List[Dict[str, Any]], replace_list]
    extracted_entities: Annotated[List[Dict[str, Any]], operator.add]
    ontology_entities: Annotated[List[Dict[str, Any]], operator.add]
    developments: Annotated[List[Dict[str, Any]], operator.add]
    scored_signals: Annotated[List[Dict[str, Any]], operator.add]
    confluent_stories: Annotated[List[Dict[str, Any]], operator.add]
    lifecycle_events: Annotated[List[Dict[str, Any]], operator.add]
    redteam_flags: Annotated[List[Dict[str, Any]], operator.add]
    missing_signals: Annotated[List[Dict[str, Any]], operator.add]
    unmapped_entities: Annotated[List[Dict[str, Any]], operator.add]
    role_briefs: Annotated[List[Dict[str, Any]], operator.add]
    calibration_feedback: Annotated[List[Dict[str, Any]], operator.add]
    model_metadata: Annotated[List[Dict[str, Any]], operator.add]
    errors: Annotated[List[Dict[str, Any]], operator.add]
    calibration_weights: Annotated[Dict[str, float], merge_dicts]
    node_statuses: Annotated[Dict[str, str], merge_dicts]
    batch_size: int
    signals_processed: int


# Backward compatibility alias
IntelligenceState = MetaRadarState


DEFAULT_CALIBRATION_WEIGHTS: Dict[str, float] = {
    "MEDICAL_AFFAIRS": 1.0,
    "REGULATORY": 1.0,
    "SAFETY": 1.0,
    "MARKET_ACCESS": 1.0,
    "COMMUNICATIONS": 1.0,
    "LEADERSHIP": 1.0,
}


def create_initial_state(
    pipeline_run_id: Optional[str] = None,
    batch_size: int = 50,
    calibration_weights: Optional[Dict[str, float]] = None,
    raw_signals: Optional[List[Dict[str, Any]]] = None,
    calibration_feedback: Optional[List[Dict[str, Any]]] = None,
) -> MetaRadarState:
    """
    Factory creating a clean MetaRadarState dictionary initialized with empty
    accumulating collections and default execution metadata.
    """
    run_id = pipeline_run_id or str(uuid.uuid4())
    weights = dict(DEFAULT_CALIBRATION_WEIGHTS)
    if calibration_weights:
        weights.update(calibration_weights)

    return {
        "pipeline_run_id": run_id,
        "raw_signals": raw_signals or [],
        "validated_signals": [],
        "extracted_entities": [],
        "ontology_entities": [],
        "developments": [],
        "scored_signals": [],
        "confluent_stories": [],
        "lifecycle_events": [],
        "redteam_flags": [],
        "missing_signals": [],
        "unmapped_entities": [],
        "role_briefs": [],
        "calibration_feedback": calibration_feedback or [],
        "model_metadata": [],
        "errors": [],
        "calibration_weights": weights,
        "node_statuses": {},
        "batch_size": batch_size,
        "signals_processed": 0,
    }
