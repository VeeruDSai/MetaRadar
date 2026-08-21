import uuid
from datetime import datetime, timezone
import pytest
from app.services.confluence import ConfluenceEngine


def test_confluence_requires_distinct_source_providers():
    engine = ConfluenceEngine()
    dev_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    # 4 signals but all from PubMed -> NOT a confluence
    signals_same_source = [
        {"signal_id": "s1", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
        {"signal_id": "s2", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
        {"signal_id": "s3", "source_id": "pubmed", "signal_type": "CLINICAL_TRIAL", "published_at": now.isoformat()},
        {"signal_id": "s4", "source_id": "pubmed", "signal_type": "REGULATORY", "published_at": now.isoformat()},
    ]
    res_single = engine.detect_confluence_in_signals(signals_same_source, development_id=dev_id)
    assert res_single is None

    # 3 signals from 3 distinct sources (pubmed, clinical_trials, openfda) -> CONFIRMED/EMERGING confluence
    signals_multi_source = [
        {"signal_id": "s1", "source_id": "pubmed", "signal_type": "PUBLICATIONS", "published_at": now.isoformat()},
        {"signal_id": "s2", "source_id": "clinical_trials", "signal_type": "CLINICAL_TRIAL", "published_at": now.isoformat()},
        {"signal_id": "s3", "source_id": "openfda", "signal_type": "REGULATORY", "published_at": now.isoformat()},
    ]
    res_multi = engine.detect_confluence_in_signals(signals_multi_source, development_id=dev_id)
    assert res_multi is not None
    assert res_multi.independent_sources_count == 3
    assert res_multi.signal_count == 3
    assert res_multi.score > 0.0
    assert "REGULATORY" in res_multi.score_breakdown
    assert "CLINICAL_TRIAL" in res_multi.score_breakdown
    assert "PUBLICATIONS" in res_multi.score_breakdown


def test_confluence_score_calculation():
    engine = ConfluenceEngine()
    types = ["REGULATORY", "CLINICAL_TRIAL", "PUBLICATIONS"]
    score, breakdown = engine.calculate_confluence_score(types)
    assert score == 75.0  # 30 + 25 + 20
    assert breakdown["REGULATORY"] == 30.0
    assert breakdown["CLINICAL_TRIAL"] == 25.0
    assert breakdown["PUBLICATIONS"] == 20.0
