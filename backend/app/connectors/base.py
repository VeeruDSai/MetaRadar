import asyncio
import json
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ConnectorState
from app.services.deduplication import check_and_persist_bronze

logger = logging.getLogger(__name__)


class ConnectorFetchError(Exception):
    """Raised when a connector HTTP request fails after retries are exhausted."""


class RawSignalPayload(BaseModel):
    source_id: str
    source_type: str
    external_id: str
    title: str
    content: str
    url: Optional[str] = None
    published_at: datetime
    retrieved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    publisher: Optional[str] = None
    raw_hash: str
    # Verbatim source response (or faithful JSON-encoded XML fragment) —
    # persisted to raw_signals_bronze.raw_payload unchanged (D-23).
    raw_payload: Dict[str, Any] = Field(default_factory=dict)


class ConnectorStatus(BaseModel):
    source_id: str
    status: str  # active | degraded | error | idle
    quota_remaining: Optional[int] = None
    last_success: Optional[datetime] = None
    last_error: Optional[str] = None


RunStatus = Literal[
    "SUCCESS",
    "NO_NEW_DATA",
    "CONNECTED",
    "PARTIAL",
    "DEGRADED",
    "FAILED",
    "CONFIGURATION_ERROR",
    "RATE_LIMITED",
    "TIMEOUT",
    "STALE",
]


@dataclass
class ProfileRunResult:
    profile_id: str
    status: RunStatus
    fetched: int = 0
    new_rows: int = 0
    duplicates: int = 0
    records_updated: int = 0
    errors: int = 0
    duration_s: float = 0.0
    error_detail: Optional[str] = None
    upstream_data_timestamp: Optional[str] = None
    request_url: Optional[str] = None
    http_status: Optional[int] = None
    error_code: Optional[str] = None


class SourceConnector:
    """Abstract connector contract (D-01/D-06).

    Every connector is isolated, idempotent, source-specific, incrementally
    runnable, quota-aware, observable, and replayable. Connectors never
    generate intelligence and never bypass the canonical entity/evidence
    layer — Phase 1 persists bronze rows only (D-26).
    """

    source_id: str = "base"
    source_type: str = "publication"
    freshness_class: str = "batch"  # real_time | near_real_time | delayed | batch | adapter_ready | synthetic
    connector_version: str = "1.0.0"
    max_retries: int = 3
    retry_base_delay_s: float = 1.5
    timeout_s: float = 30.0

    def __init__(self):
        self.status = "idle"
        self.quota_remaining: Optional[int] = None
        self.last_success: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.config: Optional[Any] = None  # ConnectorConfig from domain config

    # ------------------------------------------------------------------ #
    # Config (per-source YAML query blocks — D-08/D-10)
    # ------------------------------------------------------------------ #

    def _connector_config(self) -> Optional[Any]:
        """Returns this source's ConnectorConfig from the domain config."""
        from app.core.domain_config import get_domain_config

        try:
            return get_domain_config().connectors.get(self.source_id)
        except Exception as e:
            logger.warning("Connector %s: failed to load domain config: %s", self.source_id, e)
            return None

    def _profiles(self) -> List[Any]:
        cfg = self._connector_config()
        return list(cfg.profiles) if cfg and cfg.profiles else []

    # ------------------------------------------------------------------ #
    # HTTP with bounded retry/backoff (D-19, no tenacity)
    # ------------------------------------------------------------------ #

    async def _fetch_with_retry(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """GET with bounded exponential backoff + jitter (max_retries)."""
        last_exc: Optional[Exception] = None
        for attempt in range(self.max_retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                    response = await client.get(url, params=params, headers=headers)
                if response.status_code >= 400:
                    last_exc = ConnectorFetchError(
                        f"HTTP {response.status_code} from {url} (params={params})"
                    )
                    if attempt < self.max_retries - 1:
                        await asyncio.sleep(self._backoff_delay(attempt))
                    continue
                return response
            except httpx.HTTPError as e:
                last_exc = e
                logger.warning(
                    "Connector %s fetch attempt %d/%d failed: %s",
                    self.source_id, attempt + 1, self.max_retries, e,
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self._backoff_delay(attempt))
        raise ConnectorFetchError(
            f"{self.source_id} fetch failed after {self.max_retries} attempts: {last_exc}"
        )

    def _backoff_delay(self, attempt: int) -> float:
        base = self.retry_base_delay_s * (2 ** attempt)
        return base + random.uniform(0, base * 0.2)

    # ------------------------------------------------------------------ #
    # Run orchestration
    # ------------------------------------------------------------------ #

    async def fetch_latest(self, limit: int = 50) -> List[RawSignalPayload]:
        raise NotImplementedError

    async def run_profile(
        self,
        session: AsyncSession,
        profile_id: str,
        force_backfill: bool = False,
    ) -> ProfileRunResult:
        raise NotImplementedError

    async def run_all_profiles(
        self,
        session: AsyncSession,
        force_backfill: bool = False,
    ) -> List[ProfileRunResult]:
        results: List[ProfileRunResult] = []
        for profile in self._profiles():
            results.append(
                await self.run_profile(session, profile.id, force_backfill=force_backfill)
            )
        return results

    def _resolve_run_status(self, results: List[ProfileRunResult]) -> RunStatus:
        """Determines aggregated connector run status from profile outcomes (D-21)."""
        if not results:
            return "FAILED"
        statuses = [r.status for r in results]
        if any(s == "CONFIGURATION_ERROR" for s in statuses):
            return "CONFIGURATION_ERROR"
        if all(s == "SUCCESS" for s in statuses):
            return "SUCCESS"
        if all(s == "NO_NEW_DATA" for s in statuses):
            return "NO_NEW_DATA"
        if all(s in ("SUCCESS", "NO_NEW_DATA") for s in statuses):
            return "SUCCESS"
        if all(s in ("FAILED", "UNHEALTHY") for s in statuses):
            return "FAILED"
        if all(s in ("DEGRADED", "RATE_LIMITED", "TIMEOUT") for s in statuses):
            return "DEGRADED"
        if any(s in ("FAILED", "DEGRADED", "PARTIAL", "RATE_LIMITED", "TIMEOUT") for s in statuses):
            return "PARTIAL"
        return "PARTIAL"

    # ------------------------------------------------------------------ #
    # Bronze persistence (D-02/D-16/D-23/D-24)
    # ------------------------------------------------------------------ #

    async def _persist_bronze(
        self,
        session: AsyncSession,
        payloads: List[RawSignalPayload],
        pipeline_run_id: Optional[Any] = None,
    ) -> Tuple[int, int]:
        """Persists payloads, returning (new_rows, duplicates). Never raises on collision."""
        new_rows = 0
        duplicates = 0
        for payload in payloads:
            result = await check_and_persist_bronze(session, payload, pipeline_run_id)
            if result == "new":
                new_rows += 1
            else:
                duplicates += 1
        return new_rows, duplicates

    # ------------------------------------------------------------------ #
    # Connector incremental state I/O (D-11/D-12)
    # ------------------------------------------------------------------ #

    async def _read_connector_state(
        self,
        session: Optional[AsyncSession],
        profile_id: str,
    ) -> Optional[ConnectorState]:
        if session is None:
            return None
        result = await session.execute(
            select(ConnectorState).where(
                ConnectorState.source_id == self.source_id,
                ConnectorState.profile_id == profile_id,
            )
        )
        return result.scalar_one_or_none()

    async def _write_connector_state(
        self,
        session: Optional[AsyncSession],
        profile_id: str,
        last_success: Optional[datetime] = None,
        cursor: Optional[str] = None,
        first_run_completed: bool = True,
        next_run_after: Optional[datetime] = None,
    ) -> None:
        if session is None:
            return
        values = {
            "source_id": self.source_id,
            "profile_id": profile_id,
            "last_success": last_success,
            "cursor": cursor,
            "next_run_after": next_run_after,
            "first_run_completed": first_run_completed,
            "updated_at": datetime.now(timezone.utc),
        }
        stmt = insert(ConnectorState).values(**values)
        stmt = stmt.on_conflict_do_update(
            index_elements=["source_id", "profile_id"],
            set_={
                "last_success": stmt.excluded.last_success,
                "cursor": stmt.excluded.cursor,
                "next_run_after": stmt.excluded.next_run_after,
                "first_run_completed": stmt.excluded.first_run_completed,
                "updated_at": stmt.excluded.updated_at,
            },
        )
        await session.execute(stmt)
        await session.commit()

    # ------------------------------------------------------------------ #
    # Observability (D-22 — honest health, no fabricated state)
    # ------------------------------------------------------------------ #

    async def get_status(
        self,
        session: Optional[AsyncSession] = None,
        state: Optional[ConnectorState] = None,
    ) -> ConnectorStatus:
        """Returns connector status; enriches last_success / quota_remaining
        from the live ConnectorState table. ``state`` may be pre-loaded by a
        batched caller (the health endpoint) to avoid one connection per
        connector. Degrades silently to in-memory state when the DB is
        unavailable — never fabricates values (D-22)."""
        last_success = self.last_success
        quota_remaining = self.quota_remaining
        last_error = self.last_error

        resolved = state
        if resolved is None and session is not None:
            try:
                result = await session.execute(
                    select(ConnectorState)
                    .where(ConnectorState.source_id == self.source_id)
                    .order_by(ConnectorState.updated_at.desc())
                    .limit(1)
                )
                resolved = result.scalar_one_or_none()
            except Exception as e:
                logger.warning(
                    "Connector %s state read failed (degrading to in-memory): %s",
                    self.source_id, e,
                )

        if resolved is not None:
            if resolved.last_success is not None:
                last_success = resolved.last_success
            if resolved.cursor:
                try:
                    cursor = json.loads(resolved.cursor)
                    if isinstance(cursor, dict) and cursor.get("quota_remaining") is not None:
                        quota_remaining = int(cursor["quota_remaining"])
                except (ValueError, TypeError):
                    pass

        return ConnectorStatus(
            source_id=self.source_id,
            status=self.status,
            quota_remaining=quota_remaining,
            last_success=last_success,
            last_error=last_error,
        )

    def _run_status_to_health_state(self, run_status: str) -> str:
        """Maps run outcome to canonical health enum."""
        mapping = {
            "SUCCESS": "HEALTHY",
            "HEALTHY": "HEALTHY",
            "NO_NEW_DATA": "NO_NEW_DATA",
            "CONNECTED": "CONNECTED",
            "STALE": "STALE",
            "PARTIAL": "DEGRADED",
            "DEGRADED": "DEGRADED",
            "RATE_LIMITED": "DEGRADED",
            "TIMEOUT": "DEGRADED",
            "FAILED": "UNHEALTHY",
            "UNHEALTHY": "UNHEALTHY",
            "CONFIGURATION_ERROR": "CONFIGURATION_ERROR",
            "NEVER_CONNECTED": "NEVER_CONNECTED",
        }
        return mapping.get(run_status, "UNHEALTHY")

    async def _persist_health_log(
        self,
        session: AsyncSession,
        result: ProfileRunResult,
        pipeline_run_id: Optional[Any] = None,
        http_status: Optional[int] = None,
    ) -> None:
        """Persists connector run telemetry to source_health_logs and updates live source state.

        Canonical ``records_rejected`` definition (shared with IngestionService):
        records fetched but NOT accepted into bronze — i.e. dedup/filter
        rejections (``result.duplicates``). Profile errors are never counted as
        rejected records; they surface via ``connector_status`` and ``last_error``.
        """
        try:
            from app.models import SourceHealthLog, Source
            from sqlalchemy import update

            health_state = self._run_status_to_health_state(result.status)
            checked_at = datetime.now(timezone.utc)
            latency_ms = int(result.duration_s * 1000)
            http_code = http_status or result.http_status

            log_entry = SourceHealthLog(
                source_id=self.source_id,
                profile_id=result.profile_id,
                pipeline_run_id=pipeline_run_id,
                checked_at=checked_at,
                connector_status=health_state,
                http_status=http_code,
                latency_ms=latency_ms,
                duration_ms=round(result.duration_s * 1000, 2),
                records_fetched=result.fetched,
                records_accepted=result.new_rows,
                records_rejected=result.duplicates,
                records_new=result.new_rows,
                records_updated=getattr(result, "records_updated", 0),
                records_duplicate=result.duplicates,
                upstream_data_timestamp=result.upstream_data_timestamp,
                last_error=result.error_detail,
                error_code=result.error_code or ("RATE_LIMITED" if http_code == 429 else None),
            )
            session.add(log_entry)

            # Update live Source record
            is_successful_sync = health_state in ("HEALTHY", "NO_NEW_DATA", "CONNECTED")
            await session.execute(
                update(Source)
                .where(Source.source_id == self.source_id)
                .values(
                    connector_status=health_state,
                    last_attempted=checked_at,
                    last_success=checked_at if is_successful_sync else Source.last_success,
                    latency_ms=latency_ms,
                    records_fetched=result.fetched,
                    records_accepted=result.new_rows,
                    records_rejected=result.duplicates,
                    records_new=result.new_rows,
                    records_updated=getattr(result, "records_updated", 0),
                    records_duplicate=result.duplicates,
                    upstream_data_timestamp=result.upstream_data_timestamp,
                    http_status=http_code,
                    last_error=result.error_detail,
                )
            )
            await session.commit()
        except Exception as e:
            logger.warning("Failed to persist source health log for %s: %s", self.source_id, e)
