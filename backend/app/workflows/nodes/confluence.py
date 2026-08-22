import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.core.domain_config import get_domain_config
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)

# Credibility weights by signal type
SIGNAL_TYPE_CREDIBILITY = {
    "REGULATORY": 1.0,
    "CLINICAL_TRIAL": 0.95,
    "PUBLICATIONS": 0.90,
    "CONGRESS": 0.85,
    "SAFETY": 0.95,
    "ACCESS": 0.80,
    "COMMERCIAL_PATENT": 0.75,
}


async def node_confluence(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 5: node_confluence (D-09, D-10)
    Detects multi-source convergence (≥3 distinct signal types within 48h)
    and executes two-tier development linking (NCT ID or Asset+Indication).
    """
    node_name = "node_confluence"
    validated_signals = state.get("validated_signals", [])
    ontology_entities = state.get("ontology_entities", [])
    existing_developments = list(state.get("developments", []))

    confluent_stories: List[Dict[str, Any]] = []
    scored_signals: List[Dict[str, Any]] = []
    new_developments: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        domain_cfg = get_domain_config()
        min_signals = domain_cfg.confluence.minimum_independent_signals if domain_cfg else 3
        window_hours = domain_cfg.confluence.time_window_hours if domain_cfg else 48

        # Create fast lookup by signal_id for enriched entities
        ent_by_sig = {e.get("signal_id"): e for e in ontology_entities}

        # 1. Two-tier Development Resolution
        dev_by_nct: Dict[str, Dict[str, Any]] = {}
        dev_by_asset: Dict[str, Dict[str, Any]] = {}

        for dev in existing_developments:
            if dev.get("nct_id"):
                dev_by_nct[dev["nct_id"].upper()] = dev
            if dev.get("asset_id"):
                dev_by_asset[dev["asset_id"]] = dev

        # Map each signal to a development_id
        signal_dev_map: Dict[str, str] = {}
        for sig in validated_signals:
            sig_id = str(sig.get("id") or sig.get("fingerprint"))
            ent = ent_by_sig.get(sig_id, {})
            nct_ids = ent.get("nct_ids", [])
            primary_asset = ent.get("primary_asset", {})
            asset_id = primary_asset.get("asset_id") if primary_asset else sig.get("asset_id")
            disease = sig.get("disease", "haemophilia_a")
            company = ent.get("primary_company", "Unknown")

            matched_dev_id: Optional[str] = None

            # Tier 1: Match on NCT ID
            for nct in nct_ids:
                if nct.upper() in dev_by_nct:
                    matched_dev_id = str(dev_by_nct[nct.upper()]["development_id"])
                    break

            # Tier 2: Match on Asset ID
            if not matched_dev_id and asset_id and asset_id in dev_by_asset:
                matched_dev_id = str(dev_by_asset[asset_id]["development_id"])

            # Tier 3: Create New Development if no match
            if not matched_dev_id:
                new_dev_id = str(uuid.uuid4())
                new_dev = {
                    "development_id": new_dev_id,
                    "title": sig.get("title", f"Development: {asset_id or 'Haemophilia'}"),
                    "disease": disease,
                    "asset_id": asset_id,
                    # company_id must reference companies.company_id (slug PKs like
                    # "novo-nordisk"). Extracted values here are display names
                    # ("Novo Nordisk") or "Unknown" — writing them into the FK
                    # either violates the constraint or creates junk rows. Leave
                    # None until a proper name→id resolution exists (WR-12).
                    "company_id": None,
                    "current_stage": "announced",
                    "nct_id": nct_ids[0] if nct_ids else None,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                new_developments.append(new_dev)
                existing_developments.append(new_dev)
                if nct_ids:
                    dev_by_nct[nct_ids[0].upper()] = new_dev
                if asset_id:
                    dev_by_asset[asset_id] = new_dev
                matched_dev_id = new_dev_id

            signal_dev_map[sig_id] = matched_dev_id

            # Attach development_id to signal
            scored_sig = dict(sig)
            scored_sig["development_id"] = matched_dev_id
            scored_sig["asset_id"] = asset_id
            scored_sig["company"] = company
            scored_signals.append(scored_sig)

        # 2. Confluence Detection: Group by Asset over rolling 48-hour window
        asset_groups: Dict[str, List[Dict[str, Any]]] = {}
        for sig in scored_signals:
            a_id = sig.get("asset_id") or sig.get("disease", "haemophilia")
            asset_groups.setdefault(a_id, []).append(sig)

        def parse_date(s):
            try:
                return datetime.fromisoformat(s.get("published_at", "").replace("Z", "+00:00"))
            except Exception:
                return datetime.now(timezone.utc)

        for a_id, group in asset_groups.items():
            if len(group) < min_signals:
                continue

            # Sort by published_at
            sorted_group = sorted(group, key=parse_date)

            for i in range(len(sorted_group)):
                window_signals = []
                start_dt = parse_date(sorted_group[i])
                window_limit = start_dt + timedelta(hours=window_hours)

                for j in range(i, len(sorted_group)):
                    curr_dt = parse_date(sorted_group[j])
                    if curr_dt <= window_limit:
                        window_signals.append(sorted_group[j])
                    else:
                        break

                distinct_sources = set(
                    (s.get("source_id") or s.get("source_name") or s.get("signal_type", "SOURCE")).lower()
                    for s in window_signals
                )
                if len(distinct_sources) >= min_signals:
                    distinct_types = set(s.get("signal_type", "CLINICAL_TRIAL") for s in window_signals)
                    # Calculate weighted severity
                    severity_score = sum(
                        SIGNAL_TYPE_CREDIBILITY.get(st, 0.7) for st in distinct_types
                    )
                    story = {
                        "confluence_id": str(uuid.uuid4()),
                        "asset_id": a_id,
                        "development_id": window_signals[0].get("development_id"),
                        "signal_count": len(window_signals),
                        "independent_sources_count": len(distinct_sources),
                        "signal_types": list(distinct_types),
                        "signal_ids": [s.get("id") or s.get("fingerprint") for s in window_signals],
                        "severity_score": round(severity_score, 2),
                        "confluence_type": "confirmed" if len(distinct_sources) >= 4 else "emerging",
                        "detected_at": datetime.now(timezone.utc).isoformat()
                    }
                    confluent_stories.append(story)
                    break  # Found confluence for this asset in this run

        return {
            "scored_signals": scored_signals,
            "developments": new_developments,
            "confluent_stories": confluent_stories,
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
            "scored_signals": validated_signals,
            "developments": [],
            "confluent_stories": [],
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
