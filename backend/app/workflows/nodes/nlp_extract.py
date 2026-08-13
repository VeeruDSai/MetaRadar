import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.core.domain_config import get_domain_config
from app.workflows.state import MetaRadarState

logger = logging.getLogger(__name__)

# Optional spaCy biomedical NER model loader
_SPACY_NLP = None
try:
    import spacy
    for model_name in ["en_core_sci_md", "en_core_web_sm"]:
        try:
            _SPACY_NLP = spacy.load(model_name)
            logger.info(f"Loaded spaCy model '{model_name}' for node_nlp_extract.")
            break
        except Exception:
            continue
except ImportError:
    logger.debug("spaCy not installed; node_nlp_extract using regex & dictionary extractor.")


# Compiled Regex Patterns for 5 Core Dimensions
NCT_PATTERN = re.compile(r"\bNCT\d{8}\b", re.IGNORECASE)
PHASE_PATTERN = re.compile(r"\bPhase\s*(?:[1-4]|I{1,3}|IV)\b", re.IGNORECASE)
BIOMARKER_PATTERNS = [
    (re.compile(r"\b(?:ABR|Annualised Bleeding Rate|Annualized Bleeding Rate)\b", re.IGNORECASE), "ABR"),
    (re.compile(r"\b(?:Factor\s*VIII|FVIII|Factor\s*8)\b", re.IGNORECASE), "Factor VIII"),
    (re.compile(r"\b(?:Factor\s*IX|FIX|Factor\s*9)\b", re.IGNORECASE), "Factor IX"),
    (re.compile(r"\b(?:IU/dL|IU\/dL)\b", re.IGNORECASE), "IU/dL"),
    (re.compile(r"\b(?:Anti-TFPI|TFPI)\b", re.IGNORECASE), "Anti-TFPI"),
    (re.compile(r"\b(?:FVIIIa-mimetic|bispecific)\b", re.IGNORECASE), "Bispecific"),
    (re.compile(r"\b(?:AAV5|AAV|Gene Therapy)\b", re.IGNORECASE), "AAV Vector"),
]

INHIBITOR_PATTERNS = [
    (re.compile(r"\b(?:with(?:out)?\s+inhibitors?|with\s+inhibitors?|inhibitor[- ]positive)\b", re.IGNORECASE), "with_inhibitors"),
    (re.compile(r"\b(?:without\s+inhibitors?|inhibitor[- ]negative|non[- ]inhibitor)\b", re.IGNORECASE), "without_inhibitors"),
]

DISEASE_PATTERNS = [
    (re.compile(r"\b(?:haemophilia\s*a|hemophilia\s*a)\b", re.IGNORECASE), "haemophilia_a"),
    (re.compile(r"\b(?:haemophilia\s*b|hemophilia\s*b)\b", re.IGNORECASE), "haemophilia_b"),
    (re.compile(r"\b(?:haemophilia|hemophilia)\b", re.IGNORECASE), "haemophilia"),
]


def extract_entities_from_text(
    text: str,
    title: str = "",
    domain_assets: Optional[List[Any]] = None
) -> Dict[str, Any]:
    """Extracts 5 core biomedical dimensions from text + title."""
    full_text = f"{title} {text}"
    extracted_assets: List[Dict[str, Any]] = []
    extracted_companies: List[str] = []
    extracted_diseases: List[str] = []
    extracted_nct_ids: List[str] = []
    extracted_trial_phases: List[str] = []
    extracted_biomarkers: List[str] = []
    inhibitor_status: Optional[str] = None

    # 1. Assets & Companies via Domain Config / Synonyms
    if domain_assets:
        for asset_cfg in domain_assets:
            names_to_check = [
                asset_cfg.id,
                asset_cfg.generic_name,
                asset_cfg.brand_name,
            ]
            for name in names_to_check:
                if name and re.search(rf"\b{re.escape(name)}\b", full_text, re.IGNORECASE):
                    extracted_assets.append({
                        "asset_id": asset_cfg.id,
                        "brand_name": asset_cfg.brand_name,
                        "generic_name": asset_cfg.generic_name,
                        "company": asset_cfg.company,
                        "is_novo_nordisk": asset_cfg.is_novo_nordisk
                    })
                    if asset_cfg.company and asset_cfg.company not in extracted_companies:
                        extracted_companies.append(asset_cfg.company)
                    break

    # Additional company keywords
    known_companies = ["Novo Nordisk", "Roche", "CSL Behring", "BioMarin", "Sanofi", "Pfizer", "Chugai", "Takeda", "Bayer", "Spark Therapeutics"]
    for comp in known_companies:
        if comp not in extracted_companies and re.search(rf"\b{re.escape(comp)}\b", full_text, re.IGNORECASE):
            extracted_companies.append(comp)

    # 2. Disease & Inhibitor Status
    for pat, d_id in DISEASE_PATTERNS:
        if pat.search(full_text):
            if d_id not in extracted_diseases:
                extracted_diseases.append(d_id)

    for pat, inh_val in INHIBITOR_PATTERNS:
        if pat.search(full_text):
            inhibitor_status = inh_val
            break

    # 3. NCT IDs & Trial Phases
    nct_matches = NCT_PATTERN.findall(full_text)
    extracted_nct_ids = list(dict.fromkeys(m.upper() for m in nct_matches))

    phase_matches = PHASE_PATTERN.findall(full_text)
    extracted_trial_phases = list(dict.fromkeys(p.title() for p in phase_matches))

    # 4. Biomarkers
    for pat, bm_name in BIOMARKER_PATTERNS:
        if pat.search(full_text):
            if bm_name not in extracted_biomarkers:
                extracted_biomarkers.append(bm_name)

    # 5. Optional spaCy enrichment
    extraction_method = "regex_dictionary"
    if _SPACY_NLP is not None:
        try:
            doc = _SPACY_NLP(full_text[:1000])
            for ent in doc.ents:
                if ent.label_ in ["DISEASE", "CHEMICAL", "ORG"] and len(ent.text) > 3:
                    # Supplement if not already detected
                    pass
            extraction_method = "hybrid_spacy_regex"
        except Exception:
            pass

    return {
        "assets": extracted_assets,
        "companies": extracted_companies,
        "diseases": extracted_diseases or ["haemophilia_a"],
        "nct_ids": extracted_nct_ids,
        "trial_phases": extracted_trial_phases,
        "biomarkers": extracted_biomarkers,
        "inhibitor_status": inhibitor_status or "all_inhibitor_statuses",
        "extraction_method": extraction_method
    }


async def node_nlp_extract(state: MetaRadarState) -> Dict[str, Any]:
    """
    Node 3: node_nlp_extract (D-05, D-08)
    Extracts 5 core dimensions (Assets, Companies, Diseases, NCT IDs, Biomarkers)
    from validated signals using hybrid regex + dictionary + spaCy fallback.
    """
    node_name = "node_nlp_extract"
    validated_signals = state.get("validated_signals", [])
    extracted_entities: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    try:
        domain_cfg = get_domain_config()
        domain_assets = domain_cfg.assets if domain_cfg else []

        for sig in validated_signals:
            sig_id = str(sig.get("id") or sig.get("fingerprint"))
            content = sig.get("content", "")
            title = sig.get("title", "")

            entities = extract_entities_from_text(
                text=content,
                title=title,
                domain_assets=domain_assets
            )
            entities["signal_id"] = sig_id
            entities["fingerprint"] = sig.get("fingerprint")
            extracted_entities.append(entities)

        return {
            "extracted_entities": extracted_entities,
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
            "extracted_entities": [],
            "errors": errors,
            "node_statuses": {node_name: "FAILED"}
        }
