from typing import Any, Dict, List, Optional, Tuple
from app.core.domain_config import get_domain_config


class RelevanceGate:
    """
    Deterministic first-stage relevance filter (D-12, Prompt §12).
    Evaluates raw incoming documents/records against haemophilia domain entities,
    assets, mechanisms, and inhibitor categories before triggering expensive AI nodes.
    Classifies records into DIRECTLY_RELEVANT, POTENTIALLY_RELEVANT, or IRRELEVANT.
    """

    @classmethod
    def evaluate(
        cls,
        title: str,
        content: str,
        entities: Optional[List[str]] = None,
        source_id: Optional[str] = None,
    ) -> Tuple[str, str, float]:
        """
        Evaluates relevance.
        Returns:
            (relevance_decision, relevance_reason, relevance_score)
            relevance_decision in ('DIRECTLY_RELEVANT', 'POTENTIALLY_RELEVANT', 'IRRELEVANT')
        """
        combined = f"{title} {content} {' '.join(entities or [])}".lower()
        cfg = get_domain_config()

        # 1. Check Primary Haemophilia Diseases & Core Coagulation Factors
        primary_disease_terms = [
            "haemophilia", "hemophilia", "factor viii", "factor ix", "fviii", "fix",
            "coagulation factor 8", "coagulation factor 9", "f8 deficiency", "f9 deficiency"
        ]
        matched_primary = [term for term in primary_disease_terms if term in combined]

        # 2. Check Monitored Assets & Competitors
        matched_assets = []
        for asset in cfg.assets:
            if asset.id.lower() in combined or asset.brand_name.lower() in combined or asset.generic_name.lower() in combined:
                matched_assets.append(asset.brand_name or asset.generic_name)

        # 3. Check Mechanisms & Modalities
        mechanism_terms = [
            "bispecific antibody", "fviiia-mimetic", "anti-tfpi", "aav5 gene therapy",
            "sirna antithrombin", "rebalancing therapy", "extended half-life",
            "non-factor therapy", "gene addition", "padua variant"
        ]
        matched_mechanisms = [term for term in mechanism_terms if term in combined]

        # 4. Check Inhibitor & Bleeding Categories
        category_terms = [
            "inhibitor", "alloantibody", "bethesda units", "annualized bleeding rate",
            "abr", "target joint", "prophylaxis", "on-demand"
        ]
        matched_categories = [term for term in category_terms if term in combined]

        # Decision Evaluation
        if matched_assets and (matched_primary or matched_mechanisms):
            matched_str = ", ".join(list(set(matched_assets + matched_primary))[:4])
            return (
                "DIRECTLY_RELEVANT",
                f"Matched monitored asset(s) and primary disease indications ({matched_str}).",
                1.0,
            )

        if matched_primary:
            matched_str = ", ".join(list(set(matched_primary + matched_categories))[:4])
            return (
                "DIRECTLY_RELEVANT",
                f"Directly addresses primary target bleeding indications ({matched_str}).",
                0.85,
            )

        if matched_assets:
            matched_str = ", ".join(matched_assets[:3])
            return (
                "DIRECTLY_RELEVANT",
                f"Mentions core monitored therapeutic asset ({matched_str}).",
                0.80,
            )

        if matched_mechanisms and matched_categories:
            matched_str = ", ".join((matched_mechanisms + matched_categories)[:3])
            return (
                "POTENTIALLY_RELEVANT",
                f"Matches coagulation mechanism and bleeding management concepts ({matched_str}).",
                0.55,
            )

        if matched_mechanisms:
            matched_str = ", ".join(matched_mechanisms[:3])
            return (
                "POTENTIALLY_RELEVANT",
                f"Mentions relevant rare disease gene or antibody mechanism ({matched_str}).",
                0.40,
            )

        # Irrelevant rejection
        return (
            "IRRELEVANT",
            "No haemophilia entity, monitored asset, clinical trial, mechanism, or relevant competitor detected.",
            0.0,
        )
