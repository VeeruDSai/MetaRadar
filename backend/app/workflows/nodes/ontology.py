import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.domain_config import get_domain_config
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)


async def node_ontology_enrich(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 4: node_ontology_enrich (D-06, D-07)
    Maps extracted entities against Haemophilia Domain Ontology (config/haemophilia.yaml).
    Attaches canonical IDs, mechanisms, modalities, indications, and competitors.
    Preserves novel/unmapped entities in state['unmapped_entities'] without rejecting signals.
    """
    node_name = "node_ontology_enrich"
    extracted_entities = state.get("extracted_entities", [])
    validated_signals = state.get("validated_signals", [])
    ontology_entities: List[Dict[str, Any]] = []
    unmapped_entities: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        domain_cfg = get_domain_config()
        asset_map = {a.id: a for a in domain_cfg.assets}
        disease_map = {d.id: d for d in domain_cfg.diseases}

        for ent in extracted_entities:
            sig_id = ent.get("signal_id")
            assets = ent.get("assets", [])
            diseases = ent.get("diseases", [])
            companies = ent.get("companies", [])

            enriched_assets = []
            for asset in assets:
                asset_id = asset.get("asset_id")
                if asset_id in asset_map:
                    cfg = asset_map[asset_id]
                    enriched_assets.append({
                        "asset_id": cfg.id,
                        "brand_name": cfg.brand_name,
                        "generic_name": cfg.generic_name,
                        "company": cfg.company,
                        "mechanism": cfg.mechanism,
                        "modality": cfg.modality,
                        "indication": cfg.indication,
                        "approval_status": cfg.approval_status,
                        "approval_date": cfg.approval_date,
                        "jurisdiction": cfg.jurisdiction,
                        "is_novo_nordisk": cfg.is_novo_nordisk,
                        "is_known_ontology": True
                    })
                else:
                    # Novel unmapped asset
                    unmapped = {
                        "entity_type": "asset",
                        "entity_id": asset_id,
                        "signal_id": sig_id,
                        "raw_name": asset.get("brand_name", asset_id),
                        "is_known_ontology": False
                    }
                    unmapped_entities.append(unmapped)
                    enriched_assets.append(unmapped)

            enriched_diseases = []
            for d_id in diseases:
                if d_id in disease_map:
                    d_cfg = disease_map[d_id]
                    enriched_diseases.append({
                        "disease_id": d_cfg.id,
                        "name": d_cfg.name,
                        "icd10": d_cfg.icd10,
                        "deficiency": d_cfg.deficiency,
                        "description": d_cfg.description,
                        "is_known_ontology": True
                    })
                else:
                    enriched_diseases.append({
                        "disease_id": d_id,
                        "name": d_id.replace("_", " ").title(),
                        "is_known_ontology": False
                    })

            enriched_record = {
                "signal_id": sig_id,
                "fingerprint": ent.get("fingerprint"),
                "assets": enriched_assets,
                "primary_asset": enriched_assets[0] if enriched_assets else None,
                "diseases": enriched_diseases,
                "primary_disease": enriched_diseases[0] if enriched_diseases else None,
                "companies": companies,
                "primary_company": companies[0] if companies else (enriched_assets[0]["company"] if enriched_assets and "company" in enriched_assets[0] else "Unknown"),
                "nct_ids": ent.get("nct_ids", []),
                "trial_phases": ent.get("trial_phases", []),
                "biomarkers": ent.get("biomarkers", []),
                "inhibitor_status": ent.get("inhibitor_status", "all_inhibitor_statuses"),
                "is_known_ontology": bool(enriched_assets and all(a.get("is_known_ontology", False) for a in enriched_assets))
            }
            ontology_entities.append(enriched_record)

        return {
            "ontology_entities": ontology_entities,
            "unmapped_entities": unmapped_entities,
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
            "ontology_entities": [],
            "unmapped_entities": [],
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
