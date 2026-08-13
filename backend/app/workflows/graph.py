import logging
from langgraph.graph import StateGraph, END

from app.workflows.state import MetaRadarState
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

logger = logging.getLogger(__name__)


def build_graph():
    """
    Assembles and compiles the canonical 10-node MetaRadar LangGraph intelligence pipeline.
    Node execution order:
      node_ingest -> node_validate -> node_nlp_extract -> node_ontology_enrich ->
      node_confluence -> node_lifecycle -> node_redteam -> node_missing_signal ->
      node_synthesize -> node_calibrate -> END
    """
    graph = StateGraph(MetaRadarState)

    # 1. Add all 10 Intelligence Nodes
    graph.add_node("node_ingest", node_ingest)
    graph.add_node("node_validate", node_validate)
    graph.add_node("node_nlp_extract", node_nlp_extract)
    graph.add_node("node_ontology_enrich", node_ontology_enrich)
    graph.add_node("node_confluence", node_confluence)
    graph.add_node("node_lifecycle", node_lifecycle)
    graph.add_node("node_redteam", node_redteam)
    graph.add_node("node_missing_signal", node_missing_signal)
    graph.add_node("node_synthesize", node_synthesize)
    graph.add_node("node_calibrate", node_calibrate)

    # 2. Wire Explicit Linear Pipeline Edges
    graph.add_edge("node_ingest", "node_validate")
    graph.add_edge("node_validate", "node_nlp_extract")
    graph.add_edge("node_nlp_extract", "node_ontology_enrich")
    graph.add_edge("node_ontology_enrich", "node_confluence")
    graph.add_edge("node_confluence", "node_lifecycle")
    graph.add_edge("node_lifecycle", "node_redteam")
    graph.add_edge("node_redteam", "node_missing_signal")
    graph.add_edge("node_missing_signal", "node_synthesize")
    graph.add_edge("node_synthesize", "node_calibrate")
    graph.add_edge("node_calibrate", END)

    # 3. Set Entry Point
    graph.set_entry_point("node_ingest")

    compiled_graph = graph.compile()
    logger.info("Compiled MetaRadar 10-node LangGraph Intelligence Pipeline successfully.")
    return compiled_graph
