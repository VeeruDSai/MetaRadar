import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors import ALL_CONNECTORS
from app.connectors.base import ProfileRunResult, SourceConnector
from app.models import SourceHealthLog, Source
from sqlalchemy import select
from app.core.logging import get_logger

logger = get_logger("ingestion_service")


class IngestionService:
    """
    Orchestrates live data ingestion across all registered source connectors.
    Executes connector profiles against real public biomedical endpoints (PubMed, ClinicalTrials, OpenFDA, EMA, NewsAPI),
    persists raw payloads to raw_signals_bronze, and writes source health telemetry.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def run_connectors(
        self,
        connector_ids: Optional[List[str]] = None,
        force_backfill: bool = False,
    ) -> Dict[str, Any]:
        """
        Executes configured profiles for the requested connectors (or all active connectors if None).
        Returns aggregated ingestion telemetry with per-connector status and counts.
        """
        started_at = datetime.now(timezone.utc)
        connectors_to_run: List[SourceConnector] = []

        for conn in ALL_CONNECTORS:
            if connector_ids is None or conn.source_id in connector_ids:
                connectors_to_run.append(conn)

        total_fetched = 0
        total_new = 0
        total_duplicates = 0
        per_source_results: Dict[str, Any] = {}

        from app.core.config import configuration_error_for

        logger.info(f"[INGESTION] Starting live ingestion run for {len(connectors_to_run)} connector(s): {[c.source_id for c in connectors_to_run]}")

        for conn in connectors_to_run:
            conn_start = time.perf_counter()
            conn_results: List[ProfileRunResult] = []
            conn_status = "HEALTHY"
            error_msg: Optional[str] = None
            config_err = configuration_error_for(conn.source_id)

            try:
                # Execute all profiles for this connector
                conn_results = await conn.run_all_profiles(self.session, force_backfill=force_backfill)
                resolved_status = conn._resolve_run_status(conn_results)

                conn_fetched = sum(r.fetched for r in conn_results)
                conn_new = sum(r.new_rows for r in conn_results)
                conn_dups = sum(r.duplicates for r in conn_results)

                # Precedence: CONFIGURATION_ERROR > UNHEALTHY > DEGRADED > HEALTHY
                if config_err:
                    conn_status = "CONFIGURATION_ERROR"
                    error_msg = config_err
                elif resolved_status == "CONFIGURATION_ERROR":
                    conn_status = "CONFIGURATION_ERROR"
                    error_msg = "; ".join(r.error_detail for r in conn_results if r.error_detail) or "Configuration error"
                elif resolved_status == "FAILED":
                    conn_status = "UNHEALTHY"
                    error_msg = "; ".join(r.error_detail for r in conn_results if r.error_detail) or "All profiles failed"
                elif conn_fetched == 0:
                    conn_status = "DEGRADED"
                    error_msg = "; ".join(r.error_detail for r in conn_results if r.error_detail) or "0 records fetched"
                elif conn_new == 0:
                    conn_status = "DEGRADED"
                    error_msg = "; ".join(r.error_detail for r in conn_results if r.error_detail) or "0 new records accepted (all duplicates or filtered)"
                elif resolved_status in ("DEGRADED", "PARTIAL"):
                    conn_status = "DEGRADED"
                    error_msg = "; ".join(r.error_detail for r in conn_results if r.error_detail)
                else:
                    conn_status = "HEALTHY"

                total_fetched += conn_fetched
                total_new += conn_new
                total_duplicates += conn_dups

                latency_ms = (time.perf_counter() - conn_start) * 1000.0
                now_utc = datetime.now(timezone.utc)

                logger.info(
                    f"[INGESTION] Connector '{conn.source_id}' -> status: {conn_status}, "
                    f"fetched: {conn_fetched}, new_bronze: {conn_new}, duplicates: {conn_dups}, latency: {latency_ms:.1f}ms"
                )

                # Record health log in database
                # records_rejected = fetched but not accepted (dedup rejections) —
                # same canonical definition as SourceConnector._persist_health_log.
                health_log = SourceHealthLog(
                    source_id=conn.source_id,
                    connector_status=conn_status,
                    latency_ms=round(latency_ms, 2),
                    records_fetched=conn_fetched,
                    records_accepted=conn_new,
                    records_rejected=conn_dups,
                    last_error=error_msg,
                    checked_at=now_utc,
                )
                self.session.add(health_log)

                # Update Source row if present
                src_res = await self.session.execute(select(Source).where(Source.source_id == conn.source_id))
                src_obj = src_res.scalar_one_or_none()
                if src_obj:
                    src_obj.connector_status = conn_status
                    src_obj.latency_ms = int(latency_ms)
                    src_obj.records_fetched = conn_fetched
                    src_obj.records_accepted = conn_new
                    src_obj.records_rejected = conn_dups
                    src_obj.last_attempted = now_utc
                    src_obj.last_error = error_msg
                    src_obj.configuration_error_message = config_err
                    if conn_status == "HEALTHY":
                        src_obj.last_success = now_utc

                await self.session.commit()

                per_source_results[conn.source_id] = {
                    "source_id": conn.source_id,
                    "status": conn_status,
                    "fetched": conn_fetched,
                    "new_rows": conn_new,
                    "duplicates": conn_dups,
                    "latency_ms": round(latency_ms, 2),
                    "error_detail": error_msg,
                    "profiles": [
                        {
                            "profile_id": r.profile_id,
                            "status": r.status,
                            "fetched": r.fetched,
                            "new_rows": r.new_rows,
                            "duplicates": r.duplicates,
                            "duration_s": round(r.duration_s, 2),
                            "error_detail": r.error_detail,
                        }
                        for r in conn_results
                    ]
                }

            except Exception as e:
                latency_ms = (time.perf_counter() - conn_start) * 1000.0
                error_str = str(e)
                logger.error(f"Connector '{conn.source_id}' execution failed: {error_str}", exc_info=True)

                # Rollback aborted transaction so session is clean for subsequent connectors
                try:
                    await self.session.rollback()
                except Exception:
                    pass

                try:
                    health_log = SourceHealthLog(
                        source_id=conn.source_id,
                        connector_status="UNHEALTHY",
                        latency_ms=round(latency_ms, 2),
                        records_fetched=0,
                        records_accepted=0,
                        records_rejected=0,
                        last_error=error_str,
                        checked_at=datetime.now(timezone.utc),
                    )
                    self.session.add(health_log)
                    await self.session.commit()
                except Exception:
                    try:
                        await self.session.rollback()
                    except Exception:
                        pass

                per_source_results[conn.source_id] = {
                    "source_id": conn.source_id,
                    "status": "UNHEALTHY",
                    "fetched": 0,
                    "new_rows": 0,
                    "duplicates": 0,
                    "latency_ms": round(latency_ms, 2),
                    "error_detail": error_str,
                    "profiles": []
                }

        duration_s = (datetime.now(timezone.utc) - started_at).total_seconds()
        logger.info(
            f"[INGESTION] Run completed in {duration_s:.2f}s -> "
            f"Total fetched: {total_fetched}, New Bronze records: {total_new}, Duplicates: {total_duplicates}"
        )

        return {
            "ingestion_run_id": str(uuid.uuid4()),
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "duration_s": round(duration_s, 2),
            "total_fetched": total_fetched,
            "total_new_bronze": total_new,
            "total_duplicates": total_duplicates,
            "sources_executed": list(per_source_results.keys()),
            "results": per_source_results,
        }
