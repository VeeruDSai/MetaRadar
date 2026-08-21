import pytest
import sys
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.models import Signal, RawSignalBronze, Source
from app.api.v1.endpoints.signals import _serialize_signal
from app.workflows.nodes.ingest import node_ingest, _load_synthetic_fallback
from app.workflows.runner import PipelineRunner
from app.connectors.pubmed import PubMedConnector
from app.connectors.clinical_trials import ClinicalTrialsConnector
from app.connectors.newsapi import NewsAPIConnector
from app.connectors.fda import OpenFDAConnector
from app.connectors.ema import EMARSSConnector


# ---------------------------------------------------------------------------
# Test 1: Serialization Truthfulness & Provenance Round-Trip
# ---------------------------------------------------------------------------
def test_serialize_signal_provenance_verbatim():
    now_dt = datetime.now(timezone.utc)
    sig_id = uuid.uuid4()
    stored_breakdown = {
        "novelty": 18.5,
        "clinical": 25.0,
        "regulatory": 20.0,
        "recency": 15.5,
        "total": 79.0,
        "version": "haemophilia_v2.0"
    }

    sig = Signal(
        signal_id=sig_id,
        source_id="pubmed",
        source_name="New England Journal of Medicine",
        pmid="38123456",
        external_id="38123456",
        fingerprint="sig:pubmed:38123456:test",
        canonical_url="https://pubmed.ncbi.nlm.nih.gov/38123456/",
        signal_type="PUBLICATIONS",
        disease="haemophilia_a",
        title="Novel bispecific antibody prophylaxis in severe haemophilia A",
        content="Subcutaneous administration achieved sustained zero-bleed rates.",
        evidence_text="Subcutaneous administration achieved sustained zero-bleed rates.",
        raw_record_reference="raw-bronze-12345",
        provenance_status="available",
        data_mode="live",
        is_synthetic=False,
        confidence_type="extraction",
        confidence_rationale="Extracted directly from peer-reviewed abstract",
        priority="HIGH",
        score_breakdown=stored_breakdown,
        scoring_model_version="haemophilia_v2.0",
        published_at=now_dt,
        retrieved_at=now_dt,
        ingested_at=now_dt,
        created_at=now_dt,
    )

    # Monkeypatch priority_scorer to raise if invoked during serialization
    with patch("app.api.v1.endpoints.signals.priority_scorer.score_text") as mock_scorer:
        mock_scorer.side_effect = AssertionError("priority_scorer.score_text must not be called during serialization!")
        serialized = _serialize_signal(sig)

    assert serialized.signal_id == sig_id
    assert serialized.source_name == "New England Journal of Medicine"
    assert serialized.external_id == "38123456"
    assert serialized.pmid == "38123456"
    assert serialized.canonical_url == "https://pubmed.ncbi.nlm.nih.gov/38123456/"
    assert serialized.evidence_text == "Subcutaneous administration achieved sustained zero-bleed rates."
    assert serialized.provenance_status == "available"
    assert serialized.raw_record_reference == "raw-bronze-12345"
    assert serialized.data_mode == "live"
    assert serialized.is_synthetic is False
    assert serialized.score_breakdown is not None
    assert serialized.score_breakdown.total == 79.0
    assert serialized.score_breakdown.clinical == 25.0
    assert serialized.scoring_status == "computed"
    # Confidence must not be fabricated
    assert serialized.confidence is None


def test_serialize_signal_not_computed_on_null_breakdown():
    now_dt = datetime.now(timezone.utc)
    sig = Signal(
        signal_id=uuid.uuid4(),
        source_id="clinical_trials",
        source_name="ClinicalTrials.gov",
        nct_id="NCT05551234",
        external_id="NCT05551234",
        fingerprint="sig:ct:NCT05551234:test",
        canonical_url="https://clinicaltrials.gov/study/NCT05551234",
        signal_type="CLINICAL_TRIAL",
        disease="haemophilia_b",
        title="Phase 3 Gene Therapy Durability Study",
        content="Long-term expression follow-up for Factor IX gene therapy.",
        evidence_text="Long-term expression follow-up for Factor IX gene therapy.",
        provenance_status="available",
        data_mode="live",
        is_synthetic=False,
        priority="MEDIUM",
        score_breakdown=None,
        published_at=now_dt,
        retrieved_at=now_dt,
        ingested_at=now_dt,
        created_at=now_dt,
    )

    with patch("app.api.v1.endpoints.signals.priority_scorer.score_text") as mock_scorer:
        mock_scorer.side_effect = AssertionError("priority_scorer.score_text must not be called during serialization!")
        serialized = _serialize_signal(sig)

    assert serialized.score_breakdown is None
    assert serialized.scoring_status == "not_computed"
    assert serialized.external_id == "NCT05551234"


def test_synthetic_fallback_tagging():
    """Synthetic fallback records must be explicitly tagged as test_fixture."""
    items = _load_synthetic_fallback(limit=10)
    for item in items:
        assert item.get("is_synthetic") is True
        assert item.get("data_mode") == "test_fixture"
        assert item.get("provenance_status") == "fixture"


# ---------------------------------------------------------------------------
# Test 2: Full Pipeline Integration Tests for all 5 Connectors
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_pubmed_pipeline_provenance_integration():
    """PubMed raw XML -> connector parse -> node_ingest -> runner persistence -> Signal"""
    xml_str = """
    <PubmedArticle>
        <MedlineCitation>
            <PMID>39999001</PMID>
            <Article>
                <Journal><Title>Blood Advances</Title></Journal>
                <ArticleTitle>Long-term prophylactic efficacy of mim8</ArticleTitle>
                <Abstract><AbstractText>Mim8 demonstrated sustained haemostatic protection in non-inhibitor patients.</AbstractText></Abstract>
                <JournalIssue><PubDate><Year>2026</Year></PubDate></JournalIssue>
            </Article>
        </MedlineCitation>
    </PubmedArticle>
    """
    article = ET.fromstring(xml_str.strip())
    retrieved_at = datetime.now(timezone.utc)
    connector = PubMedConnector()
    payload = connector._parse_article(article, retrieved_at)

    assert payload is not None
    assert payload.external_id == "39999001"
    assert payload.url == "https://pubmed.ncbi.nlm.nih.gov/39999001/"
    assert payload.raw_payload.get("url") == "https://pubmed.ncbi.nlm.nih.gov/39999001/"
    assert payload.raw_payload.get("signal_type") == "PUBLICATIONS"
    assert payload.raw_payload.get("source_name") == "Blood Advances"
    assert "Mim8 demonstrated" in payload.raw_payload.get("evidence_text", "")

    # Mock bronze row and pass through node_ingest
    mock_bronze = MagicMock(spec=RawSignalBronze)
    mock_bronze.id = uuid.uuid4()
    mock_bronze.source_id = "pubmed"
    mock_bronze.external_id = "39999001"
    mock_bronze.retrieved_at = retrieved_at
    mock_bronze.cross_source_group_id = None
    mock_bronze.raw_payload = payload.raw_payload

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [mock_bronze]
    mock_session.execute.return_value = mock_result

    state = {"batch_size": 10, "raw_signals": []}
    ingest_result = await node_ingest(state, session=mock_session)
    ingested_signals = ingest_result.get("raw_signals", [])
    assert len(ingested_signals) == 1

    sig_dict = ingested_signals[0]
    assert sig_dict.get("external_id") == "39999001"
    assert sig_dict.get("source_name") == "Blood Advances"
    assert sig_dict.get("signal_type") == "PUBLICATIONS"
    assert sig_dict.get("url") == "https://pubmed.ncbi.nlm.nih.gov/39999001/"
    assert "Mim8 demonstrated" in sig_dict.get("evidence_text", "")


@pytest.mark.asyncio
async def test_clinical_trials_provenance_integration():
    """ClinicalTrials.gov JSON -> connector parse -> raw_payload provenance"""
    study_json = {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT06667777",
                "briefTitle": "Phase 3 Safety and Efficacy of Emicizumab in Mild Haemophilia A",
                "organization": {"fullName": "F. Hoffmann-La Roche"}
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"startDate": "2026-01-15"}
            },
            "descriptionModule": {
                "briefSummary": "This study evaluates emicizumab prophylaxis in patients with mild haemophilia A."
            },
            "conditionsModule": {
                "conditions": ["Hemophilia A"]
            }
        }
    }
    connector = ClinicalTrialsConnector()
    retrieved_at = datetime.now(timezone.utc)
    payload = connector._parse_study(study_json, retrieved_at)

    assert payload is not None
    assert payload.external_id == "NCT06667777"
    assert payload.url == "https://clinicaltrials.gov/study/NCT06667777"
    assert payload.raw_payload.get("url") == "https://clinicaltrials.gov/study/NCT06667777"
    assert payload.raw_payload.get("signal_type") == "CLINICAL_TRIAL"
    assert payload.raw_payload.get("source_name") == "ClinicalTrials.gov"
    assert "emicizumab prophylaxis" in payload.raw_payload.get("evidence_text", "")


@pytest.mark.asyncio
async def test_openfda_provenance_integration():
    """openFDA JSON -> connector parse -> external_id preserved, canonical_url is None (missing_url)"""
    fda_doc = {
        "application_number": "BLA125890",
        "sponsor_name": [{"name": "BioMarin Pharmaceutical"}],
        "openfda": {
            "brand_name": ["ROCTAVIAN"],
            "substance_name": ["valoctocogene roxaparvovec-rvvx"],
            "manufacturer_name": ["BioMarin Pharmaceutical"]
        },
        "products": [
            {
                "brand_name": "ROCTAVIAN",
                "marketing_start_date": "20260210"
            }
        ]
    }
    connector = OpenFDAConnector()
    retrieved_at = datetime.now(timezone.utc)
    payload = connector._parse_result(fda_doc, retrieved_at)

    assert payload is not None
    assert payload.external_id == "BLA125890"
    # openFDA must NOT fabricate an API search URL as canonical URL
    assert payload.url is None
    assert payload.raw_payload.get("url") is None
    assert payload.raw_payload.get("signal_type") == "REGULATORY"
    assert payload.raw_payload.get("source_name") == "openFDA"
    assert payload.raw_payload.get("provenance_status") == "missing_url"


@pytest.mark.asyncio
async def test_newsapi_provenance_integration():
    """NewsAPI JSON -> connector parse -> raw_payload provenance"""
    article_doc = {
        "source": {"id": "reuters", "name": "Reuters Health"},
        "author": "Health Desk",
        "title": "FDA Approves Expanded Label for Haemophilia Prophylaxis",
        "description": "Regulatory expansion offers new maintenance treatment options.",
        "url": "https://www.reuters.com/business/healthcare-pharmaceuticals/fda-approves-expanded-label-2026",
        "publishedAt": "2026-02-15T14:30:00Z",
        "content": "Full article coverage of haemophilia therapeutics."
    }
    connector = NewsAPIConnector()
    retrieved_at = datetime.now(timezone.utc)
    payload = connector._parse_article(article_doc, retrieved_at)

    assert payload is not None
    assert payload.url == "https://www.reuters.com/business/healthcare-pharmaceuticals/fda-approves-expanded-label-2026"
    assert payload.raw_payload.get("source_name") == "Reuters Health"
    assert payload.raw_payload.get("signal_type") == "NEWS"
    assert payload.raw_payload.get("url") == "https://www.reuters.com/business/healthcare-pharmaceuticals/fda-approves-expanded-label-2026"


@pytest.mark.asyncio
async def test_ema_provenance_integration():
    """EMA RSS XML -> connector parse -> raw_payload provenance"""
    rss_xml = """
    <item>
        <title>CHMP recommends granting of marketing authorisation for Roctavian</title>
        <link>https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian</link>
        <description>The European Medicines Agency has recommended granting conditional marketing authorisation.</description>
        <guid>https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian</guid>
        <pubDate>Fri, 20 Feb 2026 10:00:00 GMT</pubDate>
    </item>
    """
    item = ET.fromstring(rss_xml.strip())
    connector = EMARSSConnector()
    retrieved_at = datetime.now(timezone.utc)
    guid = "https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian"
    title = "CHMP recommends granting of marketing authorisation for Roctavian"
    description = "The European Medicines Agency has recommended granting conditional marketing authorisation."
    payload = connector._parse_item(item, guid, title, description, retrieved_at)

    assert payload is not None
    assert payload.url == "https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian"
    assert payload.raw_payload.get("source_name") == "EMA"
    assert payload.raw_payload.get("signal_type") == "REGULATORY"
    assert payload.raw_payload.get("url") == "https://www.ema.europa.eu/en/medicines/human/EPAR/roctavian"
