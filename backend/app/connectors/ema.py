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


class EMARSSConnector(SourceConnector):
    """EMA RSS feed async adapter (REQ-P1-5).

    Adapter-ready status: parses the EMA medicines RSS feed with stdlib
    xml.etree. Items are filtered by configured profile keywords (title +
    description match); guid normalized -> ``reg:`` fingerprint. The verbatim
    XML fragment is stored JSON-encoded in raw_payload (D-23).
    """

    source_id = "ema"
    source_type = "regulatory"
    freshness_class = "adapter_ready"
    DEFAULT_RSS_URL = "https://www.ema.europa.eu/en/medicines/rss"

    def __init__(self):
        super().__init__()
        self.config = self._connector_config()
        if self.config is not None and self.config.rss_url:
            self.rss_url = self.config.rss_url
        else:
            self.rss_url = self.DEFAULT_RSS_URL

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
            target_url = getattr(profile, "rss_url", None) or self.rss_url
            resp = await self._fetch_with_retry(target_url)
            root = ET.fromstring(resp.text)

            keywords = [k.lower() for k in (profile.keywords or [])]
            payloads: List[RawSignalPayload] = []
            seen_external: set = set()

            for item in root.findall(".//item"):
                title = self._element_text(item, "title")
                description = self._element_text(item, "description")
                # keyword filter (title + description)
                if keywords:
                    haystack = f"{title} {description}".lower()
                    if not any(kw in haystack for kw in keywords):
                        continue

                guid = self._element_text(item, "guid") or self._element_text(item, "link")
                if not guid:
                    continue

                payload = self._parse_item(item, guid.strip(), title, description, started, profile_id)
                if payload is not None and payload.external_id not in seen_external:
                    seen_external.add(payload.external_id)
                    payloads.append(payload)

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
        except Exception as e:  # noqa: BLE001 — honest per-profile isolation
            logger.exception("EMARSSConnector profile %s failed", profile_id)
            return self._fail(profile_id, started, str(e))

    # ------------------------------------------------------------------ #

    def _parse_item(
        self,
        item: Any,
        guid: str,
        title: str,
        description: str,
        retrieved_at: datetime,
        profile_id: str = "ema_general",
    ) -> Optional[RawSignalPayload]:
        link = self._element_text(item, "link")
        pub_date_raw = self._element_text(item, "pubDate")
        published_at = self._parse_rfc2822(pub_date_raw, retrieved_at)

        scrubbed, _, _ = PIIPHIScrubber.scrub(description)
        content = scrubbed or title
        fingerprint = generate_fingerprint(regulatory_id=guid, title=title, published_at=published_at)
        external_id = self._normalize_guid(guid)
        content_hash = hashlib.sha256(
            f"{external_id}:{content}".encode("utf-8")
        ).hexdigest()

        if "orphan" in profile_id.lower():
            event_type = "ORPHAN_DESIGNATION"
        elif "epar" in profile_id.lower():
            event_type = "EPAR_UPDATE"
        else:
            event_type = "REGULATORY_DECISION"

        raw_payload = {
            "external_id": external_id,
            "fingerprint": fingerprint,
            "title": title,
            "description": scrubbed,
            "source_name": "EMA",
            "source_tier": 1,
            "signal_type": "REGULATORY",
            "event_type": event_type,
            "url": link or None,
            "evidence_text": scrubbed or description or title,
            "provenance_status": "available" if link else "missing_url",
            "link": link,
            "guid": guid,
            "pub_date": pub_date_raw,
            "published_at": published_at.isoformat(),
            "entities": [],
            "pii_scrubbed": True,
            "retrieved_at": retrieved_at.isoformat(),
            "connector_version": self.connector_version,
            "item_xml": ET.tostring(item, encoding="unicode"),  # verbatim XML fragment (D-23)
        }

        return RawSignalPayload(
            source_id=self.source_id,
            source_type=self.source_type,
            external_id=external_id,
            title=title,
            content=content,
            url=link or None,
            published_at=published_at,
            publisher="EMA",
            raw_hash=content_hash,
            raw_payload=raw_payload,
        )

    @staticmethod
    def _element_text(item: Any, tag: str) -> str:
        el = item.find(tag)
        if el is None or el.text is None:
            return ""
        return el.text.strip()

    @staticmethod
    def _normalize_guid(guid: str) -> str:
        """Normalizes a guid to a stable external id (lowercased, trimmed)."""
        return guid.strip().lower()

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