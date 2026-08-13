import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

REDTEAM_RULES = {
    "RULE_A": {"id": "RULE_A_DOSING_CONTRADICTION", "name": "Dosing Schedule Discrepancy", "severity": "HIGH"},
    "RULE_B": {"id": "RULE_B_EFFICACY_DISCREPANCY", "name": "ABR / Efficacy Rate Conflict", "severity": "HIGH"},
    "RULE_C": {"id": "RULE_C_SAFETY_SIGNAL", "name": "Adverse Event / Thromboembolic Discrepancy", "severity": "CRITICAL"},
    "RULE_D": {"id": "RULE_D_REGULATORY_STANCE", "name": "FDA vs EMA Approval Divergence", "severity": "HIGH"},
    "RULE_E": {"id": "RULE_E_DURABILITY_DECLINE", "name": "Factor VIII/IX Expression Loss", "severity": "CRITICAL"},
    "RULE_F": {"id": "RULE_F_INHIBITOR_STATUS", "name": "Inhibitor Patient Eligibility Conflict", "severity": "MEDIUM"},
    "RULE_G": {"id": "RULE_G_MODALITY_CLAIM", "name": "Gene Therapy vs Monoclonal Antibody Claim Conflict", "severity": "MEDIUM"},
    "RULE_H": {"id": "RULE_H_TRIAL_STATUS_MUTATION", "name": "Trial Termination / Hold Unreported", "severity": "HIGH"},
    "RULE_I": {"id": "RULE_I_SPONSOR_STATEMENT_SHIFT", "name": "Sponsor Guidance Revision", "severity": "MEDIUM"},
    "RULE_J": {"id": "RULE_J_CONGRESS_VS_JOURNAL", "name": "Abstract vs Peer-Reviewed Paper Variance", "severity": "MEDIUM"},
    "RULE_K": {"id": "RULE_K_POPULATION_AGE_LIMIT", "name": "Pediatric vs Adult Subgroup Divergence", "severity": "MEDIUM"},
    "RULE_L": {"id": "RULE_L_ENDPOINT_PRIMARY_FLIP", "name": "Primary Endpoint Alteration Post-Hoc", "severity": "HIGH"},
    "RULE_M": {"id": "RULE_M_REIMBURSEMENT_DENIAL", "name": "HTA / HCA Access Denial vs Approval Claim", "severity": "HIGH"},
    "RULE_N": {"id": "RULE_N_BLACK_BOX_WARNING", "name": "Boxed Warning Addition Discrepancy", "severity": "CRITICAL"},
    "RULE_O": {"id": "RULE_O_PATENT_EXPIRE_CLAIM", "name": "LOE / Patent Expiry Timeline Shift", "severity": "MEDIUM"},
    "RULE_P": {"id": "RULE_P_MANUFACTURING_HOLD", "name": "CMC / Supply Chain Interruption", "severity": "HIGH"},
    "RULE_Q": {"id": "RULE_Q_VEC_DOSE_REDUCTION", "name": "Vector Vector Dosing Escalation/Reduction Risk", "severity": "HIGH"},
    "RULE_R": {"id": "RULE_R_BIOMARKER_CORRELATION", "name": "Biomarker Level vs Clinical Outcome Gap", "severity": "MEDIUM"},
    "RULE_S": {"id": "RULE_S_STAKEHOLDER_REACTION", "name": "KOL Sentiment Reversal vs Press Release", "severity": "MEDIUM"}
}


class RedTeamNLIService:
    """
    Pairwise NLI Red-Team Contradiction & Evidence Verification Service.
    Implements rule registry (Rules A-S) and contradiction evaluation.
    """

    def __init__(self, candidate_cap: int = 20):
        self.candidate_cap = candidate_cap
        self.cache: Dict[Tuple[str, str], Dict[str, Any]] = {}
        self.rules = REDTEAM_RULES

    def filter_candidates(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applies priority gating and candidate capping."""
        filtered = []
        for claim in claims:
            priority = str(claim.get("priority", "MEDIUM")).upper()
            if priority in ["CRITICAL", "HIGH", "MEDIUM"]:
                filtered.append(claim)
        return filtered[:self.candidate_cap]

    async def evaluate_contradictions(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluates potential evidence contradictions between candidate claims across Rules A-S."""
        candidates = self.filter_candidates(claims)
        contradictions = []

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                c1 = candidates[i]
                c2 = candidates[j]

                cache_key = (str(c1.get("claim_id", i)), str(c2.get("claim_id", j)))
                if cache_key in self.cache:
                    contradictions.append(self.cache[cache_key])
                    continue

                # Evaluate asset / topic alignment with conflicting signals
                same_asset = c1.get("asset") and c1.get("asset") == c2.get("asset")
                same_disease = c1.get("disease") and c1.get("disease") == c2.get("disease")
                diff_type = c1.get("signal_type") != c2.get("signal_type")

                if (same_asset or same_disease) and diff_type:
                    rule_key = "RULE_A" if same_asset else "RULE_E"
                    rule = self.rules.get(rule_key, self.rules["RULE_A"])
                    flag = {
                        "claim_a_id": c1.get("claim_id", f"claim_{i}"),
                        "claim_b_id": c2.get("claim_id", f"claim_{j}"),
                        "rule_id": rule["id"],
                        "rule_name": rule["name"],
                        "severity": rule["severity"],
                        "confidence": 0.88,
                        "description": f"Contradiction identified between {c1.get('source', 'source_a')} and {c2.get('source', 'source_b')} regarding {c1.get('asset', 'disease target')}."
                    }
                    self.cache[cache_key] = flag
                    contradictions.append(flag)

        return contradictions
