import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RawSignalBronze
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)


def _load_synthetic_fallback(limit: int = 50) -> List[Dict[str, Any]]:
    """Loads fallback pre-curated signals from synthetic dataset if bronze is empty."""
    # ingest.py lives at <repo>/backend/app/workflows/nodes/ → parents[4] is the repo root,
    # where data/synthetic_signals.json actually lives.
    data_path = Path(__file__).resolve().parents[4] / "data" / "synthetic_signals.json"
    if not data_path.exists():
        logger.error(f"Synthetic fallback dataset missing at {data_path}")
        return []

    try:
        with open(data_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tagged = []
        for item in data[:limit]:
            copied = dict(item)
            copied["is_synthetic"] = True
            copied["data_mode"] = "test_fixture"
            copied["provenance_status"] = "fixture"
            tagged.append(copied)
        return tagged
    except Exception as e:
        logger.warning(f"Failed to load synthetic dataset from {data_path}: {e}")
    return []


async def node_ingest(state: MetaRadarState, session: Optional[AsyncSession] = None) -> Dict[str, Any]:
    """
    Node 1: node_ingest (D-03, D-04)
    Queries unpromoted records from raw_signals_bronze up to batch_size,
    falling back to synthetic_signals.json if bronze queue is empty.
    """
    node_name = "node_ingest"
    batch_size = state.get("batch_size", 50)
    raw_signals: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    # If raw_signals already passed in state (e.g. testing or direct feed), prioritize them
    existing_raw = state.get("raw_signals", [])
    if existing_raw:
        return {
            "raw_signals": existing_raw,
            "signals_processed": len(existing_raw),
            "node_statuses": {node_name: "SUCCESS"}
        }

    try:
        if session is not None:
            stmt = select(RawSignalBronze).where(
                RawSignalBronze.pipeline_run_id.is_(None)
            ).limit(batch_size)
            result = await session.execute(stmt)
            bronze_rows = result.scalars().all()

            for row in bronze_rows:
                payload = row.raw_payload or {}
                url = payload.get("url")
                prov_status = payload.get("provenance_status", "available" if url else "missing_url")
                sig = {
                    "id": str(row.id),
                    "source_id": row.source_id,
                    "source_name": payload.get("source_name") or row.source_id.upper().replace("_", " "),
                    "external_id": row.external_id,
                    "title": payload.get("title", ""),
                    "content": payload.get("content", payload.get("abstract", "")),
                    "published_at": payload.get("published_at", row.retrieved_at.isoformat() if row.retrieved_at else datetime.now(timezone.utc).isoformat()),
                    "signal_type": payload.get("signal_type", "CLINICAL_TRIAL"),
                    "disease": payload.get("disease", "haemophilia_a"),
                    "url": url,
                    "evidence_text": payload.get("evidence_text") or payload.get("abstract") or payload.get("description") or payload.get("title", ""),
                    "provenance_status": prov_status,
                    "raw_record_reference": f"bronze:{row.id}",
                    "data_mode": payload.get("data_mode", "live"),
                    "is_synthetic": bool(payload.get("is_synthetic", False)),
                    "cross_source_group_id": str(row.cross_source_group_id) if row.cross_source_group_id else None
                }
                raw_signals.append(sig)

        # Fallback to synthetic dataset if bronze yielded nothing
        if not raw_signals:
            raw_signals = _load_synthetic_fallback(limit=batch_size)

        return {
            "raw_signals": raw_signals,
            "signals_processed": len(raw_signals),
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
            "raw_signals": [],
            "signals_processed": 0,
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
