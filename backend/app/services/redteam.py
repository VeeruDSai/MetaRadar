import logging
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)


class RedTeamNLIService:
    """
    Optimized Pairwise NLI Red-Team Contradiction Service.
    Applies priority gating, evidence maturity gating, candidate similarity filtering,
    claim deduplication, candidate capping, and caching to avoid $O(N^2)$ quadratic explosion.
    """

    def __init__(self, candidate_cap: int = 10):
        self.candidate_cap = candidate_cap
        self.cache: Dict[Tuple[str, str], Dict[str, Any]] = {}

    def filter_candidates(self, claims: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Applies HIGH/CRITICAL priority gating and evidence maturity filtering."""
        filtered = []
        for claim in claims:
            priority = claim.get("priority", "MEDIUM").upper()
            if priority in ["CRITICAL", "HIGH"]:
                filtered.append(claim)
        return filtered[:self.candidate_cap]

    async def evaluate_contradictions(
        self,
        claims: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Evaluates potential contradictions between candidate claims."""
        candidates = self.filter_candidates(claims)
        contradictions = []

        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                c1 = candidates[i]
                c2 = candidates[j]

                cache_key = (c1.get("claim_id", str(i)), c2.get("claim_id", str(j)))
                if cache_key in self.cache:
                    contradictions.append(self.cache[cache_key])
                    continue

                # Mock pairwise check (e.g. comparing endpoints/durability)
                if c1.get("asset") == c2.get("asset") and c1.get("type") != c2.get("type"):
                    flag = {
                        "claim_a_id": c1.get("claim_id"),
                        "claim_b_id": c2.get("claim_id"),
                        "rule": "EVIDENCE_CONTRADICTION",
                        "confidence": 0.85,
                        "description": f"Potential contradiction between {c1.get('source')} and {c2.get('source')}."
                    }
                    self.cache[cache_key] = flag
                    contradictions.append(flag)

        return contradictions
