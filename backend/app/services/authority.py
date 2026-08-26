"""Source Authority Hierarchy & Discovery Validation Engine.

Implements machine-readable Source Authority classification and Discovery Source validation:
- AUTHORITATIVE: Primary sources (Regulatory agencies e.g. FDA/EMA, Clinical trial registries e.g. ClinicalTrials.gov, Peer-reviewed publications e.g. PubMed).
- SECONDARY: Official secondary sources (Company announcements, institutional press releases, congress abstracts).
- DISCOVERY: Trade media & news feeds (NewsAPI, Fierce Pharma, BioPharma Dive, Reuters).

Discovery sources discover signals but are never automatically upgraded to authoritative evidence.
Validation statuses: VALIDATED, PENDING_VALIDATION, NOT_VALIDATED, CONTRADICTED.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class SourceAuthorityTier(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    SECONDARY = "SECONDARY"
    DISCOVERY = "DISCOVERY"


class ValidationStatus(str, Enum):
    VALIDATED = "VALIDATED"
    PENDING_VALIDATION = "PENDING_VALIDATION"
    NOT_VALIDATED = "NOT_VALIDATED"
    CONTRADICTED = "CONTRADICTED"


# Registry mapping source identifiers to their authority tier and domain type
SOURCE_AUTHORITY_REGISTRY: Dict[str, Dict[str, Any]] = {
    "fda": {
        "tier": SourceAuthorityTier.AUTHORITATIVE,
        "category": "REGULATORY_AGENCY",
        "description": "U.S. Food and Drug Administration (Drugs@FDA & Regulatory Notices)",
        "trust_score": 1.0,
    },
    "ema": {
        "tier": SourceAuthorityTier.AUTHORITATIVE,
        "category": "REGULATORY_AGENCY",
        "description": "European Medicines Agency (EPAR & CHMP Safety Communications)",
        "trust_score": 1.0,
    },
    "who_ictrp": {
        "tier": SourceAuthorityTier.AUTHORITATIVE,
        "category": "REGULATORY_AGENCY",
        "description": "World Health Organization International Clinical Trials Registry",
        "trust_score": 0.98,
    },
    "clinical_trials": {
        "tier": SourceAuthorityTier.AUTHORITATIVE,
        "category": "CLINICAL_REGISTRY",
        "description": "ClinicalTrials.gov (National Library of Medicine Protocol & Results Database)",
        "trust_score": 0.98,
    },
    "pubmed": {
        "tier": SourceAuthorityTier.AUTHORITATIVE,
        "category": "PEER_REVIEWED_LITERATURE",
        "description": "NCBI PubMed / MEDLINE Peer-Reviewed Biomedical Literature",
        "trust_score": 0.95,
    },
    "ash": {
        "tier": SourceAuthorityTier.SECONDARY,
        "category": "CONGRESS_MATERIALS",
        "description": "American Society of Hematology Annual Meeting Abstracts",
        "trust_score": 0.88,
    },
    "isth": {
        "tier": SourceAuthorityTier.SECONDARY,
        "category": "CONGRESS_MATERIALS",
        "description": "International Society on Thrombosis and Haemostasis Congress",
        "trust_score": 0.88,
    },
    "eha": {
        "tier": SourceAuthorityTier.SECONDARY,
        "category": "CONGRESS_MATERIALS",
        "description": "European Hematology Association Congress Proceedings",
        "trust_score": 0.88,
    },
    "company_ir": {
        "tier": SourceAuthorityTier.SECONDARY,
        "category": "COMPANY_ANNOUNCEMENT",
        "description": "Corporate Investor Relations & SEC 8-K/Press Filings",
        "trust_score": 0.80,
    },
    "company_press": {
        "tier": SourceAuthorityTier.SECONDARY,
        "category": "COMPANY_ANNOUNCEMENT",
        "description": "Official Pharmaceutical Sponsor Press Communications",
        "trust_score": 0.80,
    },
    "newsapi": {
        "tier": SourceAuthorityTier.DISCOVERY,
        "category": "PHARMA_MEDIA",
        "description": "NewsAPI Aggregated Trade Media & Healthcare Journalism",
        "trust_score": 0.60,
    },
    "fierce_pharma": {
        "tier": SourceAuthorityTier.DISCOVERY,
        "category": "PHARMA_MEDIA",
        "description": "Fierce Pharma Industry News Feed",
        "trust_score": 0.65,
    },
    "biopharma_dive": {
        "tier": SourceAuthorityTier.DISCOVERY,
        "category": "PHARMA_MEDIA",
        "description": "BioPharma Dive Life Sciences Reporting",
        "trust_score": 0.65,
    },
    "reuters": {
        "tier": SourceAuthorityTier.DISCOVERY,
        "category": "FINANCIAL_MEDIA",
        "description": "Reuters Health & Pharmaceuticals Desk",
        "trust_score": 0.70,
    },
}


def get_source_authority_tier(source_id: Optional[str], numeric_tier: Optional[int] = None) -> SourceAuthorityTier:
    """Returns the explicit SourceAuthorityTier for a given source ID."""
    if not source_id:
        return SourceAuthorityTier.DISCOVERY

    norm_id = source_id.lower().strip()
    if norm_id in SOURCE_AUTHORITY_REGISTRY:
        return SOURCE_AUTHORITY_REGISTRY[norm_id]["tier"]

    # Fallback to numeric tier if configured (tier 1 -> AUTHORITATIVE, tier 2 -> SECONDARY, tier 3/4 -> DISCOVERY)
    if numeric_tier == 1:
        return SourceAuthorityTier.AUTHORITATIVE
    elif numeric_tier == 2:
        return SourceAuthorityTier.SECONDARY
    else:
        return SourceAuthorityTier.DISCOVERY


def resolve_validation_status(
    source_id: Optional[str],
    authority_tier: Optional[SourceAuthorityTier] = None,
    is_corroborated: bool = False,
    is_contradicted: bool = False,
) -> ValidationStatus:
    """
    Evaluates evidence validation state.
    - Contradicted by red-team -> CONTRADICTED
    - Authoritative primary sources -> VALIDATED
    - Secondary official sources -> VALIDATED
    - Discovery sources with authoritative corroboration -> VALIDATED
    - Discovery sources without corroboration -> PENDING_VALIDATION (or NOT_VALIDATED)
    """
    if is_contradicted:
        return ValidationStatus.CONTRADICTED

    if authority_tier is None:
        authority_tier = get_source_authority_tier(source_id)

    if authority_tier in (SourceAuthorityTier.AUTHORITATIVE, SourceAuthorityTier.SECONDARY):
        return ValidationStatus.VALIDATED

    # Discovery Source validation rules
    if is_corroborated:
        return ValidationStatus.VALIDATED
    else:
        return ValidationStatus.PENDING_VALIDATION


def get_source_credibility_breakdown(source_ids: List[str]) -> Dict[str, Any]:
    """
    Computes honest source diversity and credibility breakdown across multiple sources.
    Example: 3 sources -> 2 Authoritative, 1 Discovery.
    """
    authoritative_count = 0
    secondary_count = 0
    discovery_count = 0

    for sid in source_ids:
        tier = get_source_authority_tier(sid)
        if tier == SourceAuthorityTier.AUTHORITATIVE:
            authoritative_count += 1
        elif tier == SourceAuthorityTier.SECONDARY:
            secondary_count += 1
        else:
            discovery_count += 1

    total = len(source_ids)
    return {
        "total_sources": total,
        "authoritative_count": authoritative_count,
        "secondary_count": secondary_count,
        "discovery_count": discovery_count,
        "source_diversity_summary": f"{total} source(s): {authoritative_count} Authoritative, {secondary_count} Secondary, {discovery_count} Discovery",
        "has_authoritative_anchor": authoritative_count > 0,
    }
