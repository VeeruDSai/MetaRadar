import hashlib
import logging
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


class OpenFDAConnector(SourceConnector):
    """OpenFDA Drug (drugsfda.json) async adapter (REQ-P1-4).

    Adapter-ready status (no free-form API key; public endpoint). One
    request per configured search term; application numbers carried as the
    canonical ``reg:`` fingerprint. Verbatim result JSON persisted to bronze.
    """

    source_id = "fda"
    source_type = "regulatory"
    freshness_class = "adapter_ready"
    BASE_URL = "https://api.fda.gov/drug/drugsfda.json"
    PAGE_LIMIT = 100

    def __init__(self):
        super().__init__()
        self.config = self._connector_config()
        if self.config is not None and self.config.base_url:
            self.base_url = self.config.base_url
        else:
            self.base_url = self.BASE_URL

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
            payloads: List[RawSignalPayload] = []
            seen_external: set = set()
            search_terms = profile.search_terms or []
            if not search_terms:
                return ProfileRunResult(
                    profile_id=profile_id,
                    status="PARTIAL",
                    fetched=0,
                    error_detail="Profile has no search_terms configured",
                )

            for term in search_terms:
                params = {
                    "search": f"openfda.substance_name:{term}",
                    "limit": 10,
                }
                resp = await self._fetch_with_retry(self.base_url, params=params)
                data = resp.json()
                for result_item in data.get("results") or []:
                    payload = self._parse_result(result_item, started)
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
            logger.exception("OpenFDAConnector profile %s failed", profile_id)
            return self._fail(profile_id, started, str(e))

    # ------------------------------------------------------------------ #

    def _parse_result(self, result_item: Dict[str, Any], retrieved_at: datetime) -> Optional[RawSignalPayload]:
        """Extracts application_number -> reg: fingerprint."""
        application_number = (result_item.get("application_number") or "").strip()
        if not application_number:
            return None

        openfda = result_item.get("openfda") or {}
        substances = [
            s for s in (openfda.get("substance_name") or []) if s
        ]
        brand_names = [b for b in (openfda.get("brand_name") or []) if b]
        sponsors = openfda.get("manufacturer_name") or [sponsor.get("name") for sponsor in (result_item.get("sponsor_name") or []) if sponsor.get("name")]
        sponsors = [s for s in sponsors if s]

        products = result_item.get("products") or []
        action_date = ""
        if products and isinstance(products[0], dict):
            action_date = products[0].get("marketing_start_date") or ""

        title = brand_names[0] if brand_names else application_number
        content = (
            f"{' '.join(brand_names)} — {' '.join(substances)} — "
            f"{' '.join(sponsors)}"
        ).strip(" —")
        scrubbed, _, _ = PIIPHIScrubber.scrub(content)

        published_at = self._parse_date(action_date, retrieved_at)
        url = None
        fingerprint = generate_fingerprint(regulatory_id=application_number, title=title, published_at=published_at)
        content_hash = hashlib.sha256(
            f"{application_number}:{scrubbed}".encode("utf-8")
        ).hexdigest()

        raw_payload = {
            "external_id": application_number,
            "fingerprint": fingerprint,
            "title": title,
            "brand_name": brand_names,
            "substance_name": substances,
            "sponsor_name": sponsors,
            "source_name": "openFDA",
            "signal_type": "REGULATORY",
            "url": None,
            "evidence_text": scrubbed or content or title,
            "provenance_status": "missing_url",
            "action_date": action_date,
            "published_at": published_at.isoformat(),
            "entities": list({*substances, *brand_names}),
            "pii_scrubbed": True,
            "retrieved_at": retrieved_at.isoformat(),
            "connector_version": self.connector_version,
            "result": result_item,  # verbatim drugsfda result object (D-23)
        }

        return RawSignalPayload(
            source_id=self.source_id,
            source_type=self.source_type,
            external_id=application_number,
            title=title,
            content=scrubbed or title,
            url=None,
            published_at=published_at,
            publisher=sponsors[0] if sponsors else None,
            raw_hash=content_hash,
            raw_payload=raw_payload,
        )

    @staticmethod
    def _parse_date(value: str, fallback: datetime) -> datetime:
        if not value:
            return fallback
        for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y%m%d", "%Y-%m"):
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
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