import hashlib
import logging
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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


class ETPharmaRSSConnector(SourceConnector):
    """Economic Times Pharma (ET Pharma) RSS feed async adapter (REQ-P9-08).

    Tier 3 Discovery source: parses the ET Pharma RSS feeds
    (top stories and drug approvals) with stdlib xml.etree. Items are
    filtered by configured profile keywords (title + description match);
    stores the article link as canonical URL for honest provenance.
    """

    source_id = "et_pharma"
    source_type = "news"
    freshness_class = "delayed"
    DEFAULT_RSS_URL = "https://pharma.economictimes.indiatimes.com/rss/topstories"

    def __init__(self):
        super().__init__()
        self.config = self._connector_config()
        if self.config is not None and getattr(self.config, "rss_url", None):
            self.rss_url = self.config.rss_url
        else:
            self.rss_url = self.DEFAULT_RSS_URL

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
            target_url = getattr(profile, "rss_url", None) or self.rss_url
            payloads: List[RawSignalPayload] = []
            seen_external: set = set()

            try:
                resp = await self._fetch_with_retry(target_url)
                root = ET.fromstring(resp.text)
                keywords = [k.lower() for k in (profile.keywords or [])]

                for item in root.findall(".//item"):
                    title = self._element_text(item, "title")
                    description = self._element_text(item, "description")

                    # Keyword filter (title + description)
                    if keywords:
                        haystack = f"{title} {description}".lower()
                        if not any(kw in haystack for kw in keywords):
                            continue

                    link = self._element_text(item, "link")
                    guid = self._element_text(item, "guid") or link
                    if not link and not guid:
                        continue

                    payload = self._parse_item(item, guid.strip(), title, description, started, profile_id)
                    if payload is not None and payload.external_id not in seen_external:
                        seen_external.add(payload.external_id)
                        payloads.append(payload)
            except (ET.ParseError, ConnectorFetchError) as parse_or_fetch_err:
                logger.warning("ET Pharma profile %s feed unavailable/invalid XML: %s", profile_id, parse_or_fetch_err)
            except Exception as inner_ex:
                logger.warning("ET Pharma profile %s unexpected error: %s", profile_id, inner_ex)

            fetched = len(payloads)
            new_rows, duplicates = 0, 0
            if payloads:
                new_rows, duplicates = await self._persist_bronze(session, payloads)

            self.last_success = datetime.now(timezone.utc)
            self.status = "active"
            self.last_error = None
            await self._write_connector_state(
                session,
                profile_id,
                last_success=self.last_success,
                first_run_completed=True,
            )

            status_result = "SUCCESS" if new_rows > 0 or fetched > 0 else "NO_NEW_DATA"
            return ProfileRunResult(
                profile_id=profile_id,
                status=status_result,
                fetched=fetched,
                new_rows=new_rows,
                duplicates=duplicates,
                duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
            )
        except ConnectorFetchError as e:
            return self._fail(profile_id, started, str(e))
        except ET.ParseError as e:
            return self._fail(profile_id, started, f"RSS XML parse error: {e}")
        except Exception as e:  # noqa: BLE001
            logger.exception("ETPharmaRSSConnector profile %s failed", profile_id)
            return self._fail(profile_id, started, str(e))

    def _parse_item(
        self,
        item: Any,
        guid: str,
        title: str,
        description: str,
        retrieved_at: datetime,
        profile_id: str = "haemophilia_pharma_news",
    ) -> Optional[RawSignalPayload]:
        link = self._element_text(item, "link")
        pub_date_raw = self._element_text(item, "pubDate")
        published_at = self._parse_rfc2822(pub_date_raw, retrieved_at)

        scrubbed, _, _ = PIIPHIScrubber.scrub(description)
        content = scrubbed or title
        fingerprint = generate_fingerprint(title=title, published_at=published_at, publisher="ET Pharma")
        external_id = link or guid or hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
        content_hash = hashlib.sha256(f"{external_id}:{content}".encode("utf-8")).hexdigest()
        entities = self._detect_entities(f"{title} {description}")

        raw_payload = {
            "external_id": external_id,
            "fingerprint": fingerprint,
            "title": title,
            "description": scrubbed,
            "source_name": "ET Pharma",
            "source_tier": 3,
            "signal_type": "NEWS",
            "event_type": "INDUSTRY_NEWS",
            "url": link or None,
            "evidence_text": scrubbed or description or title,
            "provenance_status": "available" if link else "missing_url",
            "link": link,
            "guid": guid,
            "pub_date": pub_date_raw,
            "published_at": published_at.isoformat(),
            "entity_terms": entities,
            "pii_scrubbed": True,
            "retrieved_at": retrieved_at.isoformat(),
            "connector_version": self.connector_version,
            "item_xml": ET.tostring(item, encoding="unicode"),
        }

        return RawSignalPayload(
            source_id=self.source_id,
            source_type=self.source_type,
            external_id=external_id,
            title=title,
            content=content,
            url=link or None,
            published_at=published_at,
            publisher="ET Pharma",
            raw_hash=content_hash,
            raw_payload=raw_payload,
        )

    def _detect_entities(self, text: str) -> List[str]:
        from app.core.domain_config import get_domain_config

        hit = []
        try:
            cfg = get_domain_config()
            lowered = text.lower()
            for asset in cfg.assets:
                for term in (asset.generic_name, asset.brand_name):
                    if term and term.lower() in lowered:
                        hit.append(term)
        except Exception as e:  # noqa: BLE001
            logger.debug("Entity detection skipped: %s", e)
        return sorted(set(hit))

    @staticmethod
    def _element_text(item: Any, tag: str) -> str:
        el = item.find(tag)
        if el is None or el.text is None:
            return ""
        return el.text.strip()

    @staticmethod
    def _parse_rfc2822(value: str, fallback: datetime) -> datetime:
        if not value:
            return fallback
        try:
            from email.utils import parsedate_to_datetime

            parsed = parsedate_to_datetime(value)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed
        except (ValueError, TypeError):
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
