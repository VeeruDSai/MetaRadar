import asyncio
import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.connectors.base import (
    ConnectorFetchError,
    ProfileRunResult,
    RawSignalPayload,
    SourceConnector,
)
from app.services.deduplication import generate_fingerprint
from app.services.pii import PIIPHIScrubber

logger = logging.getLogger(__name__)


class PubMedConnector(SourceConnector):
    """NCBI PubMed E-utilities async adapter (REQ-P1-1).

    Quota-free, incremental per profile via ConnectorState, multiple
    config-driven query profiles. Verbatim article XML fragments persisted
    to bronze; abstracts PII-scrubbed before persistence (REQ-P1-14).
    """

    source_id = "pubmed"
    source_type = "publication"
    freshness_class = "batch"
    BASE_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    BASE_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    BATCH_SIZE = 200
    BATCH_DELAY_S = 0.35

    def __init__(self):
        super().__init__()
        self.config = self._connector_config()

    # ------------------------------------------------------------------ #

    async def run_profile(
        self,
        session: Any,
        profile_id: str,
        force_backfill: bool = False,
    ) -> ProfileRunResult:
        started = datetime.now(timezone.utc)
        profile = next(
            (p for p in (self.config.profiles if self.config else []) if p.id == profile_id),
            None,
        )
        if profile is None:
            return ProfileRunResult(
                profile_id=profile_id,
                status="FAILED",
                fetched=0,
                error_detail=f"Profile '{profile_id}' not found in domain config",
            )

        try:
            today = started.date()
            start_date = await self._window_start(session, profile_id, force_backfill, today)

            # 2. esearch per query -> collect + dedupe PMIDs
            pmid_map: Dict[str, None] = {}
            for query in profile.queries or []:
                params = {
                    "db": "pubmed",
                    "term": query,
                    "datetype": "pdat",
                    "mindate": start_date.strftime("%Y/%m/%d"),
                    "maxdate": today.strftime("%Y/%m/%d"),
                    "retmax": (self.config.max_results_per_profile if self.config else 200) or 200,
                    "retmode": "json",
                }
                resp = await self._fetch_with_retry(self.BASE_ESEARCH, params=params)
                data = resp.json()
                for pmid in (data.get("esearchresult", {}).get("idlist") or []):
                    pmid_map[str(pmid)] = None

            pmids = list(pmid_map.keys())

            # 3. efetch in batches (XML abstracts) with polite delay between batches
            payloads: List[RawSignalPayload] = []
            for i in range(0, len(pmids), self.BATCH_SIZE):
                batch = pmids[i : i + self.BATCH_SIZE]
                if i > 0:
                    await asyncio.sleep(self.BATCH_DELAY_S)
                params = {
                    "db": "pubmed",
                    "id": ",".join(batch),
                    "retmode": "xml",
                    "rettype": "abstract",
                }
                resp = await self._fetch_with_retry(self.BASE_EFETCH, params=params)
                root = ET.fromstring(resp.text)
                for article in root.findall(".//PubmedArticle"):
                    payload = self._parse_article(article, started)
                    if payload is not None:
                        payloads.append(payload)

            fetched = len(payloads)
            new_rows, duplicates = 0, 0
            if payloads:
                new_rows, duplicates = await self._persist_bronze(session, payloads)

            # 4. update state — honest outcome (D-14: SUCCESS with 0 new is fine)
            self.last_success = datetime.now(timezone.utc)
            self.status = "active"
            self.last_error = None
            await self._write_connector_state(
                session,
                profile_id,
                last_success=self.last_success,
                first_run_completed=True,
            )

            return ProfileRunResult(
                profile_id=profile_id,
                status="SUCCESS",
                fetched=fetched,
                new_rows=new_rows,
                duplicates=duplicates,
                duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
            )
        except ConnectorFetchError as e:
            return self._fail(profile_id, started, str(e))
        except Exception as e:  # noqa: BLE001 — honest per-profile isolation
            logger.exception("PubMedConnector profile %s failed", profile_id)
            return self._fail(profile_id, started, str(e))

    # ------------------------------------------------------------------ #

    async def _window_start(self, session: Any, profile_id: str, force_backfill: bool, today) -> Any:
        """First run: backfill_days; later runs: max(last_success, rolling window);
        force_backfill: backfill_days replay (append-only, D-13)."""
        cfg = self.config
        if cfg is None:
            return today - timedelta(days=30)
        if force_backfill:
            return today - timedelta(days=cfg.backfill_days)
        state = await self._read_connector_state(session, profile_id)
        if state is None or not state.first_run_completed:
            return today - timedelta(days=cfg.backfill_days)
        rolling_start = today - timedelta(days=cfg.rolling_window_days)
        if state.last_success is not None:
            last_date = state.last_success.date()
            if last_date > rolling_start:
                return last_date
        return rolling_start

    def _parse_article(self, article: Any, retrieved_at: datetime) -> Optional[RawSignalPayload]:
        """Tolerates missing title/abstract/pubdate (plan §4.6)."""
        pmid_el = article.find(".//PMID")
        if pmid_el is None or not pmid_el.text or not pmid_el.text.strip():
            return None
        pmid = pmid_el.text.strip()

        title_el = article.find(".//ArticleTitle")
        title = "".join(title_el.itertext()).strip() if title_el is not None else ""

        abstract_el = article.find(".//AbstractText")
        abstract = "".join(abstract_el.itertext()).strip() if abstract_el is not None else ""

        journal_el = article.find(".//Journal/Title")
        journal = (journal_el.text or "").strip() if journal_el is not None else ""

        year_el = article.find(".//PubDate/Year")
        pub_year = (year_el.text or "").strip() if year_el is not None else ""

        mesh_terms: List[str] = []
        for mesh in article.findall(".//MeshHeading/DescriptorName"):
            if mesh.text and mesh.text.strip():
                mesh_terms.append(mesh.text.strip())

        # PII scrub before bronze persistence (REQ-P1-14)
        scrubbed, _, _ = PIIPHIScrubber.scrub(abstract)
        content = scrubbed or title
        published_at = self._parse_pub_date(pub_year, retrieved_at)
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"

        fingerprint = generate_fingerprint(pmid=pmid, title=title, published_at=published_at)
        content_hash = hashlib.sha256(f"{pmid}:{scrubbed}".encode("utf-8")).hexdigest()

        raw_payload = {
            "external_id": pmid,
            "fingerprint": fingerprint,
            "title": title,
            "abstract": scrubbed,
            "abstract_raw": abstract,
            "journal": journal,
            "pub_date": pub_year,
            "mesh_terms": mesh_terms,
            "entities": mesh_terms,
            "pii_scrubbed": True,
            "retrieved_at": retrieved_at.isoformat(),
            "connector_version": self.connector_version,
            "xml_fragment": ET.tostring(article, encoding="unicode"),
        }

        return RawSignalPayload(
            source_id=self.source_id,
            source_type=self.source_type,
            external_id=pmid,
            title=title,
            content=content,
            url=url,
            published_at=published_at,
            publisher=journal or None,
            raw_hash=content_hash,
            raw_payload=raw_payload,
        )

    @staticmethod
    def _parse_pub_date(pub_year: str, fallback: datetime) -> datetime:
        if pub_year:
            try:
                return datetime(int(pub_year), 1, 1, tzinfo=timezone.utc)
            except ValueError:
                pass
        return fallback

    def _fail(self, profile_id: str, started: datetime, detail: str) -> ProfileRunResult:
        self.status = "error"
        self.last_error = detail
        return ProfileRunResult(
            profile_id=profile_id,
            status="FAILED",
            fetched=0,
            duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
            error_detail=detail,
        )