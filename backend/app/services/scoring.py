import math
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

SCORING_VERSION = "haemophilia_v2.0"

CLINICAL_KEYWORDS = [
    r"\bfactor\s+(?:viii|ix|8|9|vii|7)\b",
    r"\bprophylaxis\b",
    r"\bannualized\s+bleed(?:ing)?\s+rate\b|\babr\b",
    r"\binhibitor(?:s)?\b",
    r"\bnon-inferior(?:ity)?\b|\bsuperior(?:ity)?\b",
    r"\bphase\s+(?:i|ii|iii|1|2|3|iv|4)\b",
    r"\bpivotal\b|\binterim\s+readout\b|\bclinical\s+trial\b",
    r"\bdurability\b|\bexpression\s+level(?:s)?\b",
    r"\bhaemophilia\b|\bhemophilia\b",
    r"\bgene\s+therapy\b|\bmonoclonal\b|\bbispecific\b",
    r"\bprimary\s+endpoint\b|\bsecondary\s+endpoint\b",
    r"\badverse\s+event(?:s)?\b|\bthrombotic\b|\bliver\s+enzymes\b",
]

REGULATORY_KEYWORDS = [
    r"\bfda\b|\bema\b|\bchmp\b|\bmhra\b|\bpmda\b",
    r"\bpdufa\b|\btarget\s+action\s+date\b",
    r"\bbla\b|\bnda\b|\bmaa\b|\bsubmission\b|\bfiling\b",
    r"\borphan\s+drug\b|\bbreakthrough\s+therapy\b|\bfast\s+track\b",
    r"\bcomplete\s+response\s+letter\b|\bcrl\b",
    r"\bblack\s+box\s+warning\b|\bcontraindication\b|\blabel\s+(?:update|amendment)\b",
    r"\bapproval\b|\bapproved\b|\bauthorized\b|\bmarket\s+authorization\b",
    r"\bchmp\s+positive\s+opinion\b|\bchmp\s+negative\s+opinion\b",
    r"\badvisory\s+committee\b|\badcom\b",
]


@dataclass
class ScoreInput:
    novelty_distance: Optional[float]
    clinical_keywords_found: int
    regulatory_keywords_found: int
    hours_since_published: Optional[float]


@dataclass
class ScoreBreakdown:
    novelty: float
    clinical: float
    regulatory: float
    recency: float
    total: float
    priority_level: str
    version: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "novelty": round(self.novelty, 2),
            "clinical": round(self.clinical, 2),
            "regulatory": round(self.regulatory, 2),
            "recency": round(self.recency, 2),
            "total": round(self.total, 2),
            "priority_level": self.priority_level,
            "version": self.version,
        }


class PriorityScoringService:
    """
    Deterministic 4-factor Priority Scoring Engine.
    
    Formula:
      Total = Novelty (0-25) + Clinical (0-30) + Regulatory (0-25) + Recency (0-20)
    
    Returns None if any mandatory input is missing (allows honest 'not_computed' display).
    """

    VERSION = SCORING_VERSION
    HALF_LIFE_HOURS = 72.0

    @classmethod
    def extract_keywords_count(cls, text: str) -> tuple[int, int]:
        """Extract matched keyword counts for clinical and regulatory domains."""
        if not text:
            return 0, 0
        text_lower = text.lower()
        
        clin_count = sum(1 for pattern in CLINICAL_KEYWORDS if re.search(pattern, text_lower))
        reg_count = sum(1 for pattern in REGULATORY_KEYWORDS if re.search(pattern, text_lower))
        return clin_count, reg_count

    @classmethod
    def calculate_hours_since(cls, published_at: Optional[datetime]) -> Optional[float]:
        """Calculate elapsed hours since publication time."""
        if not published_at:
            return None
        now = datetime.now(timezone.utc)
        if published_at.tzinfo is None:
            published_at = published_at.replace(tzinfo=timezone.utc)
        delta_seconds = max(0.0, (now - published_at).total_seconds())
        return delta_seconds / 3600.0

    def score(self, inp: ScoreInput) -> Optional[ScoreBreakdown]:
        """
        Calculate multi-factor priority score. Returns None if inputs are insufficient.
        """
        if inp.hours_since_published is None or inp.novelty_distance is None:
            return None

        # 1. Novelty (0-25 points): Based on cosine distance to nearest neighbour
        # Cosine distance: 0 = identical, 1 = orthogonal, >1 = divergent
        clamped_distance = max(0.0, min(1.0, inp.novelty_distance))
        novelty_score = clamped_distance * 25.0

        # 2. Clinical Significance (0-30 points): 3.0 points per matched clinical concept
        clinical_score = min(30.0, inp.clinical_keywords_found * 3.0)

        # 3. Regulatory Relevance (0-25 points): 5.0 points per matched regulatory concept
        regulatory_score = min(25.0, inp.regulatory_keywords_found * 5.0)

        # 4. Recency (0-20 points): Exponential decay with 72-hour half-life
        recency_decay = math.exp(-0.693147 * (inp.hours_since_published / self.HALF_LIFE_HOURS))
        recency_score = max(0.0, min(20.0, recency_decay * 20.0))

        total_score = round(novelty_score + clinical_score + regulatory_score + recency_score, 2)

        # Map to canonical priority level
        if total_score >= 75.0:
            priority_level = "CRITICAL"
        elif total_score >= 50.0:
            priority_level = "HIGH"
        elif total_score >= 25.0:
            priority_level = "MEDIUM"
        else:
            priority_level = "LOW"

        return ScoreBreakdown(
            novelty=round(novelty_score, 2),
            clinical=round(clinical_score, 2),
            regulatory=round(regulatory_score, 2),
            recency=round(recency_score, 2),
            total=total_score,
            priority_level=priority_level,
            version=self.VERSION,
        )

    def score_text(
        self,
        text: str,
        published_at: Optional[datetime],
        novelty_distance: Optional[float] = 0.5,
    ) -> Optional[ScoreBreakdown]:
        """Convenience method to score from text, publication date, and embedding distance."""
        clin_count, reg_count = self.extract_keywords_count(text)
        hours = self.calculate_hours_since(published_at)
        return self.score(ScoreInput(
            novelty_distance=novelty_distance,
            clinical_keywords_found=clin_count,
            regulatory_keywords_found=reg_count,
            hours_since_published=hours,
        ))


priority_scorer = PriorityScoringService()
