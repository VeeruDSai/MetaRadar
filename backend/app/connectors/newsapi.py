import hashlib
import json
import logging
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import settings, configuration_error_for
from app.connectors.base import (
    ConnectorFetchError,
    ProfileRunResult,
    RawSignalPayload,
    SourceConnector,
)
from app.services.deduplication import generate_fingerprint
from app.services.pii import PIIPHIScrubber

logger = logging.getLogger(__name__)


class NewsAPIConnector(SourceConnector):
    """NewsAPI async adapter (REQ-P1-3) — quota-aware.

    ~100 req/day dev cap (D-20): checks remaining quota before any fetch,
    halts with DEGRADED on exhaustion until the next window date rollover,
    and tracks ``quota_remaining`` from the X-RateLimit-Remaining response
    header — persisted to ConnectorState.cursor as JSON:
    {"quota_remaining": N, "quota_window_date": "YYYY-MM-DD"}.
    """

    source_id = "newsapi"
    source_type = "news"
    freshness_class = "delayed"
    BASE_URL = "https://newsapi.org/v2/everything"

    def __init__(self):
        super().__init__()
        self.config = self._connector_config()
        if self.config is not None and self.config.quota_per_day is not None:
            self.quota_remaining = self.config.quota_per_day

    # ------------------------------------------------------------------ #

    async def run_profile(
        self,
        session: Any,
        profile_id: str,
        force_backfill: bool = False,
    ) -> ProfileRunResult:
        started = datetime.now(timezone.utc)
        config_err = configuration_error_for("newsapi")
        if config_err:
            self.status = "configuration_error"
            self.last_error = config_err
            return ProfileRunResult(
                profile_id=profile_id,
                status="CONFIGURATION_ERROR",
                fetched=0,
                error_detail=self.last_error,
                duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
            )

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

        # --- quota gate: read state BEFORE any network call (D-20) ---
        quota_remaining, quota_window_date = await self._read_quota(session, profile_id)
        today = date.today().isoformat()

        if quota_remaining is not None and quota_remaining <= 0 and quota_window_date == today:
            self.status = "degraded"
            self.last_error = "NewsAPI daily quota exhausted"
            return ProfileRunResult(
                profile_id=profile_id,
                status="DEGRADED",
                fetched=0,
                error_detail="NewsAPI daily quota exhausted",
                duration_s=(datetime.now(timezone.utc) - started).total_seconds(),
            )

        try:
            from_date = await self._window_start(session, profile_id, force_backfill, today)
            params = {
                "q": profile.query,
                "language": profile.language or "en",
                "from": from_date,
                "to": today,
                "sortBy": "publishedAt",
                "pageSize": 100,
            }
            headers = {"X-Api-Key": settings.NEWSAPI_KEY}

            resp = await self._fetch_with_retry(self.BASE_URL, params=params, headers=headers)
            data = resp.json()

            # --- quota tracking from response header ---
            remaining_header = resp.headers.get("X-RateLimit-Remaining")
            if remaining_header is not None:
                try:
                    quota_remaining = int(remaining_header)
                except ValueError:
                    logger.warning("Unparseable X-RateLimit-Remaining header: %r", remaining_header)
            else:
                quota_remaining = max(0, (quota_remaining or 100) - 1)

            articles = data.get("articles") or []
            payloads: List[RawSignalPayload] = []
            for article in articles:
                payload = self._parse_article(article, started)
                if payload is not None:
                    payloads.append(payload)

            fetched = len(payloads)
            new_rows, duplicates = 0, 0
            if payloads:
                new_rows, duplicates = await self._persist_bronze(session, payloads)

            self.quota_remaining = quota_remaining
            self.last_success = datetime.now(timezone.utc)
            self.status = "active"
            self.last_error = None
            cursor = json.dumps({"quota_remaining": quota_remaining, "quota_window_date": today})
            await self._write_connector_state(
                session,
                profile_id,
                last_success=self.last_success,
                cursor=cursor,
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
            logger.exception("NewsAPIConnector profile %s failed", profile_id)
            return self._fail(profile_id, started, str(e))

    # ------------------------------------------------------------------ #

    async def _read_quota(self, session: Any, profile_id: str) -> Tuple[Optional[int], str]:
        default_quota = (self.config.quota_per_day if self.config else 100) or 100
        today = date.today().isoformat()
        state = await self._read_connector_state(session, profile_id)
        if state is None or not state.cursor:
            return default_quota, today
        try:
            cursor = json.loads(state.cursor)
            if isinstance(cursor, dict):
                return int(cursor.get("quota_remaining", default_quota)), cursor.get(
                    "quota_window_date", today
                )
        except (ValueError, TypeError):
            pass
        return default_quota, today

    async def _window_start(self, session: Any, profile_id: str, force_backfill: bool, today: str) -> str:
        cfg = self.config
        if cfg is None:
            return (date.today() - timedelta(days=7)).isoformat()
        if force_backfill:
            return (date.today() - timedelta(days=cfg.backfill_days)).isoformat()
        state = await self._read_connector_state(session, profile_id)
        if state is None or not state.first_run_completed:
            return (date.today() - timedelta(days=cfg.backfill_days)).isoformat()
        rolling_start = date.today() - timedelta(days=cfg.rolling_window_days)
        if state.last_success is not None and state.last_success.date() > rolling_start:
            return state.last_success.date().isoformat()
        return rolling_start.isoformat()

    def _parse_article(self, article: Dict[str, Any], retrieved_at: datetime) -> Optional[RawSignalPayload]:
        url = (article.get("url") or "").strip()
        title = (article.get("title") or "").strip()
        if not title and not url:
            return None
        published_raw = article.get("publishedAt") or ""
        published_at = self._parse_date(published_raw, retrieved_at)
        publisher = (article.get("source") or {}).get("name") or ""

        description = (article.get("description") or "").strip()
        body = (article.get("content") or "").strip()
        # PII scrub before bronze persistence (REQ-P1-14)
        scrubbed, _, _ = PIIPHIScrubber.scrub(f"{title}\n{description}\n{body}")
        content = scrubbed or title

        fingerprint = generate_fingerprint(
            title=title,
            published_at=published_at,
            publisher=publisher,
        )
        external_id = url or hashlib.sha256(fingerprint.encode("utf-8")).hexdigest()
        content_hash = hashlib.sha256(f"{external_id}:{content}".encode("utf-8")).hexdigest()
        entities = self._detect_entities(f"{title} {description}")

        raw_payload = {
            "external_id": external_id,
            "fingerprint": fingerprint,
            "title": title,
            "description": scrubbed,
            "source_name": publisher or "NewsAPI",
            "signal_type": "NEWS",
            "url": url or None,
            "evidence_text": scrubbed or description or title,
            "entity_terms": entities,
            "pii_scrubbed": True,
            "retrieved_at": retrieved_at.isoformat(),
            "connector_version": self.connector_version,
            "article": article,  # verbatim NewsAPI article object (D-23)
        }

        return RawSignalPayload(
            source_id=self.source_id,
            source_type=self.source_type,
            external_id=external_id,
            title=title,
            content=content,
            url=url or None,
            published_at=published_at,
            publisher=publisher or None,
            raw_hash=content_hash,
            raw_payload=raw_payload,
        )

    def _detect_entities(self, text: str) -> List[str]:
        """Detects domain asset entities in text (asset synonyms from config)."""
        from app.core.domain_config import get_domain_config

        hit = []
        try:
            cfg = get_domain_config()
            lowered = text.lower()
            for asset in cfg.assets:
                for term in (asset.generic_name, asset.brand_name):
                    if term and term.lower() in lowered:
                        hit.append(term)
        except Exception as e:  # noqa: BLE001 — entity detection is best effort
            logger.debug("Entity detection skipped: %s", e)
        return sorted(set(hit))

    @staticmethod
    def _parse_date(value: str, fallback: datetime) -> datetime:
        if not value:
            return fallback
        for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d"):
            try:
                parsed = datetime.strptime(value, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed
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