"""Phase 1 ingestion test suite — 15-point coverage (plan §4.15).

All tests use `unittest.mock` / `AsyncMock` against FakeSession and mocked
httpx responses — **no live API calls in CI** (REQ-P1-15 keeps the 18 Phase 0
tests green alongside these).
"""
import json
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from sqlalchemy import Insert, Select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from app.connectors.base import (  # noqa: E402
    ProfileRunResult,
    RawSignalPayload,
    SourceConnector,
)
from app.connectors.pubmed import PubMedConnector  # noqa: E402
from app.connectors.clinical_trials import ClinicalTrialsConnector  # noqa: E402
from app.connectors.newsapi import NewsAPIConnector  # noqa: E402
from app.connectors.fda import OpenFDAConnector  # noqa: E402
from app.connectors.ema import EMARSSConnector  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.domain_config import get_domain_config  # noqa: E402
from app.models import ConnectorState, RawSignalBronze  # noqa: E402
from app.services.deduplication import check_and_persist_bronze  # noqa: E402
from app.services.source_independence import SourceIndependenceClassifier  # noqa: E402


# --------------------------------------------------------------------------- #
# Test doubles
# --------------------------------------------------------------------------- #

class MockResponse:
    def __init__(self, json_data=None, text="", status_code=200, headers=None):
        self._json = json_data
        self.text = text
        self.status_code = status_code
        self.headers = headers or {}

    def json(self):
        return self._json


class FakeResult:
    def __init__(self, scalar_one=None, rows=None):
        self._scalar_one = scalar_one
        self._rows = rows if rows is not None else []

    def scalar_one_or_none(self):
        return self._rows[0] if self._rows else self._scalar_one

    def scalars(self):
        return self

    def all(self):
        return self._rows

    def first(self):
        return self._rows[0] if self._rows else None


class FakeSession:
    """In-memory AsyncSession stand-in.

    - Insert statements emulate the (source_id, external_id) unique
      constraint for bronze rows and capture compiled params.
    - Optional ``side_effects`` list is consumed per execute (used by the
      classifier tests to drive select/update behavior).
    - Optional ``select_result`` is returned for any Select when no
      side_effects are configured (used to preload ConnectorState rows).
    """

    def __init__(self, side_effects=None, select_result=None):
        self.side_effects = list(side_effects or [])
        self._select_result = select_result
        self.insert_params = []
        self.seen_external_ids = set()
        self.executed = []
        self.commit_count = 0

    async def execute(self, stmt, *args, **kwargs):
        self.executed.append(stmt)
        if self.side_effects:
            return self.side_effects.pop(0)
        if isinstance(stmt, Insert):
            params = self._compile_params(stmt)
            self.insert_params.append(params)
            key = (params.get("source_id"), params.get("external_id"))
            if key[1] is not None and key in self.seen_external_ids:
                return FakeResult()
            if key[1] is not None:
                self.seen_external_ids.add(key)
            return FakeResult(scalar_one=uuid.uuid4())
        if isinstance(stmt, Select):
            return self._select_result if self._select_result is not None else FakeResult()
        return FakeResult()

    @staticmethod
    def _compile_params(stmt):
        try:
            from sqlalchemy.dialects import postgresql

            return stmt.compile(dialect=postgresql.dialect()).params or {}
        except Exception:
            return {}

    async def commit(self):
        self.commit_count += 1

    async def close(self):
        pass


def mock_http_get(side_effect):
    """Patches httpx.AsyncClient.get so connector tests never touch the network."""
    return patch("httpx.AsyncClient.get", new_callable=AsyncMock, side_effect=side_effect)


def bronze_insert_params(session: FakeSession):
    """Returns the RawSignalBronze insert params captured by the fake session."""
    return [p for p in session.insert_params if "content_hash" in p]


def state_insert_params(session: FakeSession):
    """Returns the ConnectorState upsert params captured by the fake session."""
    return [p for p in session.insert_params if "first_run_completed" in p]


# --------------------------------------------------------------------------- #
# T-P1-01 / T-P1-02 — PubMed
# --------------------------------------------------------------------------- #

PUBMED_ESEARCH = {
    "esearchresult": {"idlist": ["11111111", "22222222"]}
}

PUBMED_EFETCH_XML = """<?xml version="1.0"?>
<!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2024//EN"
 "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_240101.dtd">
<PubmedArticleSet>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>11111111</PMID>
      <Article>
        <Journal><Title>Haemophilia</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
        <ArticleTitle>Emicizumab prophylaxis real-world outcomes in haemophilia A</ArticleTitle>
        <Abstract><AbstractText>Real-world study of emicizumab in 120 patients with haemophilia A.</AbstractText></Abstract>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
  <PubmedArticle>
    <MedlineCitation>
      <PMID>22222222</PMID>
      <Article>
        <Journal><Title>Blood</Title><JournalIssue><PubDate><Year>2025</Year></PubDate></JournalIssue></Journal>
        <ArticleTitle>Fitusiran long-term safety in haemophilia A and B</ArticleTitle>
        <Abstract><AbstractText>Contact doc@hospital.org for the full trial protocol.</AbstractText></Abstract>
      </Article>
    </MedlineCitation>
  </PubmedArticle>
</PubmedArticleSet>"""


@pytest.mark.asyncio
async def test_pubmed_connector():
    """T-P1-01: PubMed run_profile parses mocked esearch/efetch -> pmid: payloads."""
    connector = PubMedConnector()
    session = FakeSession()
    esearch_resp = MockResponse(json_data=PUBMED_ESEARCH)
    efetch_resp = MockResponse(text=PUBMED_EFETCH_XML)

    with mock_http_get([esearch_resp, esearch_resp, efetch_resp]):
        result = await connector.run_profile(session, "haemophilia_clinical")

    assert result.status == "SUCCESS"
    assert result.fetched == 2
    assert result.new_rows == 2
    assert result.duplicates == 0

    bronze = bronze_insert_params(session)
    assert len(bronze) == 2
    fingerprints = [p["raw_payload"]["fingerprint"] for p in bronze]
    assert "pmid:11111111" in fingerprints
    assert "pmid:22222222" in fingerprints
    # verbatim article XML persisted (D-23)
    assert all("xml_fragment" in p["raw_payload"] for p in bronze)


@pytest.mark.asyncio
async def test_pubmed_pii_scrub():
    """T-P1-02: PIIPHIScrubber scrubs the abstract before bronze persistence."""
    connector = PubMedConnector()
    session = FakeSession()
    esearch_resp = MockResponse(json_data=PUBMED_ESEARCH)
    efetch_resp = MockResponse(text=PUBMED_EFETCH_XML)

    with mock_http_get([esearch_resp, esearch_resp, efetch_resp]):
        result = await connector.run_profile(session, "haemophilia_clinical")

    assert result.status == "SUCCESS"
    bronze = bronze_insert_params(session)
    # Article 22222222 carried an email in its abstract -> must be redacted
    scrubbed_abstract = bronze[1]["raw_payload"]["abstract"]
    assert "[EMAIL_REDACTED]" in scrubbed_abstract
    assert "doc@hospital.org" not in scrubbed_abstract
    assert bronze[1]["raw_payload"]["pii_scrubbed"] is True


# --------------------------------------------------------------------------- #
# T-P1-03 — ClinicalTrials.gov
# --------------------------------------------------------------------------- #

def _ct_study(nct_id, title, conditions, interventions, sponsor="Novo Nordisk", date_str="2025-06-01"):
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": nct_id,
                "officialTitle": title,
                "organization": {"fullName": sponsor},
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "phase": ["Phase 3"],
                "studyFirstPostDateStruct": {"date": date_str},
            },
            "conditionsModule": {"conditions": conditions},
            "armsInterventionsModule": {"interventions": [{"name": i} for i in interventions]},
        }
    }


CT_PAGE_1 = {
    "studies": [
        _ct_study("NCT04476974", "Emicizumab prophylaxis study in haemophilia A",
                  ["Hemophilia A"], ["emicizumab"]),
        _ct_study("NCT03417102", "Fitusiran trial in haemophilia A and B",
                  ["Hemophilia A", "Hemophilia B"], ["fitusiran"]),
    ],
    "nextPageToken": "TOKEN-1",
}

CT_PAGE_2 = {
    "studies": [
        _ct_study("NCT03744793", "Mim8 bispecific antibody in haemophilia A",
                  ["Hemophilia A"], ["mim8"]),
    ],
    "nextPageToken": None,
}


@pytest.mark.asyncio
async def test_clinical_trials_connector():
    """T-P1-03: ClinicalTrials APIv2 pagination -> NCT-fingerprinted payloads."""
    connector = ClinicalTrialsConnector()
    session = FakeSession()

    with mock_http_get([MockResponse(json_data=CT_PAGE_1), MockResponse(json_data=CT_PAGE_2)]):
        result = await connector.run_profile(session, "haemophilia_trials")

    assert result.status == "SUCCESS"
    assert result.fetched == 3
    assert result.new_rows == 3

    bronze = bronze_insert_params(session)
    fingerprints = [p["raw_payload"]["fingerprint"] for p in bronze]
    assert "nct:NCT04476974" in fingerprints
    assert "nct:NCT03417102" in fingerprints
    assert "nct:NCT03744793" in fingerprints
    # verbatim study JSON persisted (D-23)
    assert bronze[0]["raw_payload"]["study"]["protocolSection"]["identificationModule"]["nctId"] == "NCT04476974"


# --------------------------------------------------------------------------- #
# T-P1-04 / T-P1-05 — NewsAPI
# --------------------------------------------------------------------------- #

NEWS_ARTICLE = {
    "url": "https://example.com/news/emicizumab-2025",
    "title": "Emicizumab real-world data presented at ISTH 2025",
    "description": "New real-world evidence for emicizumab in haemophilia A.",
    "content": "Full story content here.",
    "publishedAt": "2025-06-10T09:30:00Z",
    "source": {"name": "Hemophilia News Today"},
}


@pytest.mark.asyncio
async def test_newsapi_connector(monkeypatch):
    """T-P1-04: NewsAPI returns payloads; quota_remaining tracked from header."""
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "test-key")
    connector = NewsAPIConnector()
    session = FakeSession()
    resp = MockResponse(
        json_data={"articles": [NEWS_ARTICLE]},
        headers={"X-RateLimit-Remaining": "95"},
    )

    with mock_http_get([resp]):
        result = await connector.run_profile(session, "haemophilia_market")

    assert result.status == "SUCCESS"
    assert result.fetched == 1
    assert result.new_rows == 1
    assert connector.quota_remaining == 95

    state_params = state_insert_params(session)
    cursor = json.loads(state_params[0]["cursor"])
    assert cursor["quota_remaining"] == 95
    assert cursor["quota_window_date"] == date.today().isoformat()


@pytest.mark.asyncio
async def test_newsapi_quota_exhaustion(monkeypatch):
    """T-P1-05: quota_remaining=0 in today's window -> DEGRADED, no fetch, no raise."""
    monkeypatch.setattr(settings, "NEWSAPI_KEY", "test-key")
    connector = NewsAPIConnector()
    exhausted = ConnectorState(
        source_id="newsapi",
        profile_id="haemophilia_market",
        cursor=json.dumps(
            {"quota_remaining": 0, "quota_window_date": date.today().isoformat()}
        ),
        first_run_completed=True,
    )
    session = FakeSession(select_result=FakeResult(scalar_one=exhausted))

    with mock_http_get(AsyncMock(side_effect=AssertionError("must not fetch"))) as patched:
        result = await connector.run_profile(session, "haemophilia_market")

    assert result.status == "DEGRADED"
    assert result.fetched == 0
    assert result.error_detail == "NewsAPI daily quota exhausted"
    patched.assert_not_awaited()
    assert connector.status == "degraded"


# --------------------------------------------------------------------------- #
# T-P1-06 — OpenFDA
# --------------------------------------------------------------------------- #

FDA_RESULT = {
    "application_number": "NDA761234",
    "openfda": {
        "substance_name": ["emicizumab"],
        "brand_name": ["Hemlibra"],
        "manufacturer_name": ["Genentech, Inc."],
    },
    "products": [{"marketing_start_date": "2025-03-01"}],
    "sponsor_name": [{"name": "Genentech, Inc."}],
}


@pytest.mark.asyncio
async def test_fda_connector():
    """T-P1-06: OpenFDA parses mocked JSON -> reg: fingerprinted bronze rows."""
    connector = OpenFDAConnector()
    session = FakeSession()
    resp = MockResponse(json_data={"results": [FDA_RESULT]})
    # profile haemophilia_approvals has 5 search terms; same item per term is deduped
    with mock_http_get([resp] * 5):
        result = await connector.run_profile(session, "haemophilia_approvals")

    assert result.status == "SUCCESS"
    assert result.fetched == 1
    assert result.new_rows == 1

    bronze = bronze_insert_params(session)
    assert bronze[0]["raw_payload"]["fingerprint"] == "reg:nda761234"
    assert bronze[0]["raw_payload"]["title"] == "Hemlibra"
    assert "emicizumab" in bronze[0]["raw_payload"]["entities"]


# --------------------------------------------------------------------------- #
# T-P1-07 — EMA RSS
# --------------------------------------------------------------------------- #

EMA_RSS_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>EMA medicines</title>
    <item>
      <title>New haemophilia treatment receives EMA recommendation</title>
      <description>The CHMP adopted a positive opinion for the haemophilia medicine.</description>
      <link>https://www.ema.europa.eu/en/medicines/new-haemophilia-treatment</link>
      <guid>ema://medicines/HAEM-2025-001</guid>
      <pubDate>Tue, 10 Jun 2025 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>Diabetes drug label update</title>
      <description>Unrelated diabetes medicine update.</description>
      <link>https://www.ema.europa.eu/en/medicines/diabetes-update</link>
      <guid>ema://medicines/DIAB-2025-002</guid>
      <pubDate>Tue, 10 Jun 2025 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""


@pytest.mark.asyncio
async def test_ema_connector():
    """T-P1-07: EMA RSS parses mocked XML -> reg: fingerprinted rows, keyword filter."""
    connector = EMARSSConnector()
    session = FakeSession()

    with mock_http_get([MockResponse(text=EMA_RSS_XML)]):
        result = await connector.run_profile(session, "haemophilia_ema")

    assert result.status == "SUCCESS"
    assert result.fetched == 1  # diabetes item filtered out by keywords
    assert result.new_rows == 1

    bronze = bronze_insert_params(session)
    assert bronze[0]["raw_payload"]["fingerprint"] == "reg:ema://medicines/haem-2025-001"
    assert "item_xml" in bronze[0]["raw_payload"]  # verbatim XML fragment (D-23)


# --------------------------------------------------------------------------- #
# T-P1-08 / T-P1-09 — Bronze persistence & dedup
# --------------------------------------------------------------------------- #

def make_payload(external_id="NDA761234", title="Hemlibra label update", **overrides):
    now = datetime.now(timezone.utc)
    raw_payload = {
        "external_id": external_id,
        "fingerprint": f"reg:{external_id.lower()}",
        "title": title,
        "entities": ["emicizumab"],
        "verbatim": {"source": "openfda", "body": {"application_number": external_id}},
    }
    base = {
        "source_id": "fda",
        "source_type": "regulatory",
        "external_id": external_id,
        "title": title,
        "content": "Label content",
        "url": "https://example.com/item",
        "published_at": now,
        "retrieved_at": now,
        "publisher": "FDA",
        "raw_hash": "abc123",
        "raw_payload": raw_payload,
    }
    base.update(overrides)
    return RawSignalPayload(**base)


@pytest.mark.asyncio
async def test_bronze_persistence():
    """T-P1-08: check_and_persist_bronze writes content_hash + verbatim raw_payload."""
    session = FakeSession()
    payload = make_payload()

    result = await check_and_persist_bronze(session, payload)

    assert result == "new"
    bronze = bronze_insert_params(session)
    assert bronze[0]["source_id"] == "fda"
    assert bronze[0]["external_id"] == "NDA761234"
    assert bronze[0]["content_hash"] == payload.raw_hash
    assert bronze[0]["raw_payload"] == payload.raw_payload


@pytest.mark.asyncio
async def test_deduplication_skip():
    """T-P1-09: second call with same (source_id, external_id) -> 'duplicate', no raise."""
    session = FakeSession()
    payload = make_payload()

    first = await check_and_persist_bronze(session, payload)
    assert first == "new"

    # original row must be preserved unchanged — the insert is skipped
    second = await check_and_persist_bronze(session, make_payload(title="changed title"))
    assert second == "duplicate"
    assert len(bronze_insert_params(session)) == 2  # attempted again, but...
    assert session.seen_external_ids == {("fda", "NDA761234")}  # still one row tracked


# --------------------------------------------------------------------------- #
# T-P1-10 / T-P1-11 — Source independence
# --------------------------------------------------------------------------- #

def make_classifier():
    cfg = get_domain_config()
    return SourceIndependenceClassifier(cfg.cross_source)


@pytest.mark.asyncio
async def test_source_independence_new_group():
    """T-P1-10: first signal -> a fresh UUID cross_source_group_id is assigned."""
    classifier = make_classifier()
    session = FakeSession(
        side_effects=[
            FakeResult(),                       # current row lookup -> none
            FakeResult(rows=[]),                # no candidates in window
            FakeResult(),                       # update execute
        ]
    )

    group_id = await classifier.classify(
        session,
        fingerprint="pmid:11111111",
        title="Emicizumab real-world outcomes in haemophilia A",
        published_at=datetime.now(timezone.utc),
        entities=["emicizumab", "haemophilia"],
    )

    assert group_id is not None
    uuid.UUID(group_id)  # must parse as a UUID
    assert session.commit_count >= 1


@pytest.mark.asyncio
async def test_source_independence_existing_group():
    """T-P1-11: high title similarity + entity overlap -> existing group ID returned."""
    classifier = make_classifier()
    existing_group = uuid.uuid4()
    candidate = RawSignalBronze(
        external_id="nct:NCT04476974",
        raw_payload={
            "title": "Emicizumab real-world outcomes in haemophilia A",
            "entities": ["emicizumab", "haemophilia"],
        },
        cross_source_group_id=existing_group,
    )
    session = FakeSession(
        side_effects=[
            FakeResult(),                       # current row lookup -> none (ungrouped)
            FakeResult(rows=[candidate]),       # one candidate in window
            FakeResult(),                       # update execute
        ]
    )

    group_id = await classifier.classify(
        session,
        fingerprint="reg:hemlibra-2025",
        title="Emicizumab real-world outcomes in haemophilia A",
        published_at=datetime.now(timezone.utc),
        entities=["emicizumab", "haemophilia"],
    )

    assert group_id == str(existing_group)


# --------------------------------------------------------------------------- #
# T-P1-12 — Incremental connector state
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_connector_state_incremental():
    """T-P1-12: after first run last_success is persisted; second run uses the
    rolling window (not the backfill window)."""
    connector = PubMedConnector()
    today = date.today()

    # --- first run: no state -> backfill window (180 days) ---
    first_session = FakeSession()
    captured_first = {}

    async def fake_get_first(url, params=None, headers=None):
        if "efetch" in url:
            return MockResponse(text=PUBMED_EFETCH_XML)
        captured_first["esearch_params"] = params
        return MockResponse(json_data=PUBMED_ESEARCH)

    with mock_http_get(fake_get_first):
        first_result = await connector.run_profile(first_session, "haemophilia_clinical")

    assert first_result.status == "SUCCESS"
    state_params = state_insert_params(first_session)
    assert state_params[0]["first_run_completed"] is True
    assert state_params[0]["source_id"] == "pubmed"
    assert state_params[0]["profile_id"] == "haemophilia_clinical"
    mindate_first = datetime.strptime(captured_first["esearch_params"]["mindate"], "%Y/%m/%d").date()
    assert mindate_first <= today - timedelta(days=179)  # backfill, not rolling

    # --- second run: state present -> rolling window (30 days) ---
    recent_state = ConnectorState(
        source_id="pubmed",
        profile_id="haemophilia_clinical",
        first_run_completed=True,
        last_success=datetime.now(timezone.utc) - timedelta(days=5),
    )
    second_session = FakeSession(select_result=FakeResult(scalar_one=recent_state))
    captured_second = {}

    async def fake_get_second(url, params=None, headers=None):
        if "efetch" in url:
            return MockResponse(text=PUBMED_EFETCH_XML)
        captured_second["esearch_params"] = params
        return MockResponse(json_data=PUBMED_ESEARCH)

    with mock_http_get(fake_get_second):
        second_result = await connector.run_profile(second_session, "haemophilia_clinical")

    assert second_result.status == "SUCCESS"
    mindate_second = datetime.strptime(captured_second["esearch_params"]["mindate"], "%Y/%m/%d").date()
    assert mindate_second >= today - timedelta(days=30)   # rolling window
    assert mindate_second > today - timedelta(days=179)   # NOT backfill


# --------------------------------------------------------------------------- #
# T-P1-13 — Run status resolution
# --------------------------------------------------------------------------- #

def test_run_status_states():
    """T-P1-13: all-OK -> SUCCESS; one DEGRADED -> PARTIAL; all failed -> FAILED."""
    connector = SourceConnector()

    all_ok = [ProfileRunResult("a", "SUCCESS"), ProfileRunResult("b", "SUCCESS")]
    assert connector._resolve_run_status(all_ok) == "SUCCESS"

    one_degraded = [ProfileRunResult("a", "SUCCESS"), ProfileRunResult("b", "DEGRADED")]
    assert connector._resolve_run_status(one_degraded) == "PARTIAL"

    all_failed = [ProfileRunResult("a", "FAILED"), ProfileRunResult("b", "FAILED")]
    assert connector._resolve_run_status(all_failed) == "FAILED"

    all_degraded = [ProfileRunResult("a", "DEGRADED")]
    assert connector._resolve_run_status(all_degraded) == "DEGRADED"

    assert connector._resolve_run_status([]) == "FAILED"


# --------------------------------------------------------------------------- #
# T-P1-14 — Health endpoint
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_health_connectors_endpoint():
    """T-P1-14: GET /api/v1/health/connectors returns all 5 sources honestly."""
    from httpx import AsyncClient, ASGITransport
    from app.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/health/connectors")

    assert response.status_code == 200
    connectors = response.json()["connectors"]
    assert len(connectors) == 5

    by_source = {c["source_id"]: c for c in connectors}
    assert set(by_source) == {"pubmed", "clinical_trials", "newsapi", "fda", "ema"}
    for source_id, conn in by_source.items():
        assert conn["freshness_class"] in (
            "real_time", "near_real_time", "delayed", "batch", "adapter_ready", "synthetic"
        )
        assert "quota_remaining" in conn
        assert "last_success" in conn
        assert "last_error" in conn
        assert conn["status"] in ("active", "degraded", "error", "idle", "CONFIGURATION_ERROR", "HEALTHY", "UNHEALTHY", "DEGRADED")


# --------------------------------------------------------------------------- #
# T-P1-15 — Domain config query blocks
# --------------------------------------------------------------------------- #

def test_domain_config_query_blocks():
    """T-P1-15: extended haemophilia.yaml loads connectors + cross_source config."""
    cfg = get_domain_config()

    assert "pubmed" in cfg.connectors
    assert "clinical_trials" in cfg.connectors
    assert "newsapi" in cfg.connectors
    assert "fda" in cfg.connectors
    assert "ema" in cfg.connectors

    pubmed = cfg.connectors["pubmed"]
    assert pubmed.freshness_class == "batch"
    assert pubmed.backfill_days == 180
    assert pubmed.rolling_window_days == 30
    assert [p.id for p in pubmed.profiles] == [
        "haemophilia_clinical", "haemophilia_safety", "competitive_news",
    ]
    assert "emicizumab" in pubmed.profiles[0].queries[0]

    newsapi = cfg.connectors["newsapi"]
    assert newsapi.quota_per_day == 100
    assert newsapi.profiles[0].query.startswith("haemophilia")

    assert cfg.cross_source is not None
    assert cfg.cross_source.group_assignment.title_similarity_threshold == 0.85
    assert cfg.cross_source.group_assignment.date_window_hours == 48
    assert cfg.cross_source.group_assignment.entity_overlap_min == 2
