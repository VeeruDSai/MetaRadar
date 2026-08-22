import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel

logger = logging.getLogger(__name__)

CONFLUENCE_VERSION = "confluence_v2.0"

SIGNAL_TYPE_WEIGHTS = {
    "REGULATORY": 30.0,
    "CLINICAL_TRIAL": 25.0,
    "TRIAL": 25.0,
    "PUBLICATIONS": 20.0,
    "PUBLICATION": 20.0,
    "CONGRESS": 15.0,
    "SAFETY": 25.0,
    "ACCESS": 15.0,
    "COMMERCIAL_PATENT": 10.0,
    "PATENT": 10.0,
}


class ConfluenceResult(BaseModel):
    confluence_id: uuid.UUID
    development_id: uuid.UUID
    asset_id: Optional[str] = None
    signal_count: int
    independent_sources_count: int
    signal_types: List[str]
    signal_ids: List[str]
    score: float
    score_breakdown: Dict[str, float]
    confluence_type: str
    calculation_version: str = CONFLUENCE_VERSION
    detected_at: datetime


class ConfluenceEngine:
    """
    Deterministic multi-source confluence detection service.
    
    A valid confluence requires:
      - >= min_sources distinct source providers (default: 3) — counted via
        distinct source_id/source_name, NOT signal types
      - Signals published within a sliding time window (default: 48h)
      - Matched to the same canonical development / drug asset
    """

    VERSION = CONFLUENCE_VERSION

    def calculate_confluence_score(self, signal_types: List[str]) -> tuple[float, Dict[str, float]]:
        """Calculate weighted confluence score and return (total, breakdown)."""
        unique_types = set(signal_types)
        breakdown = {}
        total = 0.0

        for st in unique_types:
            weight = SIGNAL_TYPE_WEIGHTS.get(st.upper(), 10.0)
            breakdown[st] = weight
            total += weight

        # Cap total score at 100.0
        normalized_total = min(100.0, total)
        return round(normalized_total, 2), breakdown

    def detect_confluence_in_signals(
        self,
        signals: List[Dict[str, Any]],
        development_id: uuid.UUID,
        asset_id: Optional[str] = None,
        min_sources: int = 3,
        window_hours: int = 48,
    ) -> Optional[ConfluenceResult]:
        """Detect if signals within a 48-hour window meet the confluence threshold."""
        if len(signals) < min_sources:
            return None

        def parse_date(s: Dict[str, Any]) -> datetime:
            pub = s.get("published_at")
            if isinstance(pub, datetime):
                return pub if pub.tzinfo else pub.replace(tzinfo=timezone.utc)
            if isinstance(pub, str):
                try:
                    return datetime.fromisoformat(pub.replace("Z", "+00:00"))
                except Exception:
                    pass
            return datetime.now(timezone.utc)

        sorted_signals = sorted(signals, key=parse_date)

        for i in range(len(sorted_signals)):
            window_signals = []
            start_dt = parse_date(sorted_signals[i])
            window_limit = start_dt + timedelta(hours=window_hours)

            for j in range(i, len(sorted_signals)):
                curr_dt = parse_date(sorted_signals[j])
                if curr_dt <= window_limit:
                    window_signals.append(sorted_signals[j])
                else:
                    break

            # ``or`` chain (not .get defaults) so explicit None values from
            # upstream can never be stringified into a phantom "none" source.
            distinct_source_ids = set(
                (
                    s.get("source_id")
                    or s.get("source_name")
                    or s.get("signal_type")
                    or "SOURCE"
                ).lower()
                for s in window_signals
            )
            if len(distinct_source_ids) >= min_sources:
                distinct_types = set(s.get("signal_type", "CLINICAL_TRIAL").upper() for s in window_signals)
                score, breakdown = self.calculate_confluence_score(list(distinct_types))
                confluence_type = "confirmed" if len(distinct_source_ids) >= 4 else "emerging"

                return ConfluenceResult(
                    confluence_id=uuid.uuid4(),
                    development_id=development_id,
                    asset_id=asset_id,
                    signal_count=len(window_signals),
                    independent_sources_count=len(distinct_source_ids),
                    signal_types=list(distinct_types),
                    signal_ids=[str(s.get("signal_id") or s.get("id")) for s in window_signals],
                    score=score,
                    score_breakdown=breakdown,
                    confluence_type=confluence_type,
                    calculation_version=self.VERSION,
                    detected_at=datetime.now(timezone.utc),
                )

        return None


confluence_engine = ConfluenceEngine()
