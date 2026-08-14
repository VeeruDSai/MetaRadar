"""node_embed — LangGraph pipeline embedding step (D-04).

Node 2.5: runs after ``node_validate`` and before ``node_nlp_extract``.
Embeds every validated signal synchronously via the fastembed CPU
``EmbeddingService`` and attaches ``embedding`` + ``embedding_model_version``
to each signal dict. Signals that fail embedding are kept with
``embedding=None`` (never silently dropped) and passed through to
``node_nlp_extract``.
"""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.core.config import settings
from app.services.embeddings import EmbeddingError, embedding_service
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)

NODE_NAME = "node_embed"


async def node_embed(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 2.5: node_embed (D-04)

    Embeds every validated_signal synchronously (fastembed CPU).
    Runs after node_validate, before node_nlp_extract.
    Adds 'embedding' key (list[float], 384 dims) and 'embedding_model_version'
    (settings.EMBEDDING_MODEL_REVISION) to each validated signal dict.
    Signals that fail embedding are kept with embedding=None and an error logged
    (never silently dropped -- pass through to nlp_extract).
    Returns validated_signals with embeddings, node_statuses.
    """
    validated_signals = state.get("validated_signals", [])
    errors: List[Dict[str, Any]] = []

    if not validated_signals:
        logger.debug("node_embed: no validated signals to embed, returning early.")
        return {
            "validated_signals": [],
            "node_statuses": {NODE_NAME: "SUCCESS"}
        }

    enriched_signals: List[Dict[str, Any]] = []
    embed_failures = 0

    try:
        for sig in validated_signals:
            try:
                vector = await embedding_service.embed_signal(sig)
                sig["embedding"] = vector
                sig["embedding_model_version"] = settings.EMBEDDING_MODEL_REVISION
            except EmbeddingError as e:
                embed_failures += 1
                logger.warning(
                    f"node_embed: embedding failed for signal "
                    f"{sig.get('id') or sig.get('fingerprint')}: {e}"
                )
                sig["embedding"] = None
                sig["embedding_model_version"] = None
                errors.append({
                    "node": NODE_NAME,
                    "signal_id": str(sig.get("id") or sig.get("fingerprint") or "unknown"),
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            enriched_signals.append(sig)

        if embed_failures == 0:
            status = "SUCCESS"
        elif embed_failures < len(validated_signals):
            status = "DEGRADED"
        else:
            status = "FAILED"

        return {
            "validated_signals": enriched_signals,
            "node_statuses": {NODE_NAME: status},
            "errors": errors
        }

    except Exception as e:
        logger.error(f"Error in {NODE_NAME}: {e}", exc_info=True)
        errors.append({
            "node": NODE_NAME,
            "error": str(e),
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        return {
            "validated_signals": [],
            "errors": errors,
            "node_statuses": {NODE_NAME: "FAILED"}
        }