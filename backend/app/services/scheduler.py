import asyncio
import hashlib
import logging
import random
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from app.connectors import ALL_CONNECTORS
from app.connectors.base import SourceConnector
from app.core.config import settings
from app.db.session import async_session_factory, try_advisory_lock, release_advisory_lock
from app.models import Source, SourceHealthLog
from app.services.ingestion import IngestionService
from app.workflows.runner import PipelineRunner

logger = logging.getLogger("metaradar.scheduler")


def _get_lock_id_for_source(source_id: str) -> int:
    """Generates a stable 31-bit positive integer for PostgreSQL advisory locks."""
    digest = hashlib.md5(f"metaradar_lock_{source_id}".encode("utf-8")).hexdigest()
    return int(digest[:7], 16) & 0x7FFFFFFF


class ScheduledJobState:
    def __init__(self, connector_id: str, base_interval_minutes: int):
        self.connector_id = connector_id
        self.base_interval_minutes = base_interval_minutes
        self.current_backoff_minutes: int = 0
        self.consecutive_failures: int = 0
        self.last_run_at: Optional[datetime] = None
        self.next_run_at: Optional[datetime] = None
        self.last_status: str = "IDLE"
        self.last_error: Optional[str] = None
        self.records_fetched_last_run: int = 0
        self.records_new_last_run: int = 0


class SourceScheduler:
    """
    Autonomous Persistent Background Ingestion Scheduler (Prompt §8, §9).
    Runs independent asyncio worker tasks per connector with source-specific intervals,
    jitter, exponential backoff, and distributed PostgreSQL advisory locks.
    Decouples ingestion from intelligence execution (only triggers LangGraph if new/changed records exist).
    """

    _instance: Optional["SourceScheduler"] = None

    def __init__(self):
        self.running: bool = False
        self.started_at: Optional[datetime] = None
        self._tasks: List[asyncio.Task] = []
        self._jobs: Dict[str, ScheduledJobState] = {}
        self._init_job_states()

    @classmethod
    def get_instance(cls) -> "SourceScheduler":
        if cls._instance is None:
            cls._instance = SourceScheduler()
        return cls._instance

    def _init_job_states(self):
        intervals = {
            "clinical_trials": settings.SCHEDULER_CT_INTERVAL_MINUTES,
            "pubmed": settings.SCHEDULER_PUBMED_INTERVAL_MINUTES,
            "ema": settings.SCHEDULER_EMA_INTERVAL_MINUTES,
            "fda": settings.SCHEDULER_FDA_INTERVAL_MINUTES,
            "newsapi": settings.SCHEDULER_NEWS_INTERVAL_MINUTES,
        }
        for conn in ALL_CONNECTORS:
            interval = intervals.get(conn.source_id, 30)
            self._jobs[conn.source_id] = ScheduledJobState(conn.source_id, interval)

    def start(self):
        if not settings.ENABLE_BACKGROUND_SCHEDULER:
            logger.info("SourceScheduler is disabled via ENABLE_BACKGROUND_SCHEDULER=False.")
            return

        if self.running:
            logger.warning("SourceScheduler is already running.")
            return

        self.running = True
        self.started_at = datetime.now(timezone.utc)
        self._tasks = []

        logger.info(f"Starting autonomous SourceScheduler with {len(ALL_CONNECTORS)} source worker(s)...")

        for conn in ALL_CONNECTORS:
            task = asyncio.create_task(
                self._connector_worker_loop(conn),
                name=f"metaradar-worker-{conn.source_id}"
            )
            self._tasks.append(task)

    async def stop(self):
        if not self.running:
            return

        logger.info("Stopping autonomous SourceScheduler workers...")
        self.running = False

        for task in self._tasks:
            if not task.done():
                task.cancel()

        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

        self._tasks = []
        logger.info("SourceScheduler stopped cleanly.")

    async def _connector_worker_loop(self, connector: SourceConnector):
        """Worker loop for an individual source connector."""
        job = self._jobs[connector.source_id]
        lock_id = _get_lock_id_for_source(connector.source_id)

        # Initial startup stagger with jitter so all connectors do not execute simultaneously
        startup_stagger = random.uniform(2.0, 15.0)
        job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=startup_stagger)
        await asyncio.sleep(startup_stagger)

        while self.running:
            start_time = datetime.now(timezone.utc)
            job.last_run_at = start_time
            job.last_status = "RUNNING"
            new_records_discovered = 0

            try:
                # 1. Acquire DB session & distributed PostgreSQL advisory lock
                async with async_session_factory() as session:
                    locked = await try_advisory_lock(session, lock_id)
                    if not locked:
                        logger.info(f"Connector '{connector.source_id}' lock is held by another instance. Skipping cycle.")
                        job.last_status = "SKIPPED_LOCKED"
                    else:
                        try:
                            # 2. Execute connector profiles via IngestionService
                            ingest_service = IngestionService(session)
                            result = await ingest_service.run_connectors(connector_ids=[connector.source_id])
                            
                            src_res = result.get("results", {}).get(connector.source_id, {})
                            conn_status = src_res.get("status", "HEALTHY")
                            job.last_status = conn_status
                            job.records_fetched_last_run = src_res.get("fetched", 0)
                            job.records_new_last_run = src_res.get("new_rows", 0)
                            new_records_discovered = job.records_new_last_run
                            job.last_error = src_res.get("error_detail")

                            # 3. Handle backoff / recovery
                            if conn_status in ("HEALTHY", "NO_NEW_DATA", "CONNECTED"):
                                job.consecutive_failures = 0
                                job.current_backoff_minutes = 0
                            elif conn_status in ("DEGRADED", "FAILED", "UNHEALTHY"):
                                job.consecutive_failures += 1
                                backoff_step = min(
                                    job.base_interval_minutes * (2 ** min(job.consecutive_failures, 4)),
                                    settings.SCHEDULER_MAX_BACKOFF_MINUTES
                                )
                                job.current_backoff_minutes = backoff_step

                        finally:
                            await release_advisory_lock(session, lock_id)

                # 4. Ingestion & Intelligence Separation:
                # Only trigger LangGraph intelligence pipeline if new/changed records were discovered!
                if new_records_discovered > 0:
                    logger.info(f"Connector '{connector.source_id}' discovered {new_records_discovered} new record(s). Triggering intelligence pipeline...")
                    try:
                        async with async_session_factory() as pipe_session:
                            runner = PipelineRunner(session=pipe_session)
                            await runner.run(batch_size=50)
                    except Exception as pe:
                        logger.error(f"Post-ingestion pipeline run failed for '{connector.source_id}': {pe}", exc_info=True)

            except asyncio.CancelledError:
                break
            except Exception as e:
                job.last_status = "ERROR"
                job.last_error = str(e)
                job.consecutive_failures += 1
                logger.error(f"Scheduler worker error in connector '{connector.source_id}': {e}", exc_info=True)

            # 5. Compute next run time with jitter and adaptive backoff
            delay_minutes = job.base_interval_minutes + job.current_backoff_minutes
            jitter_factor = 1.0 + random.uniform(
                -settings.SCHEDULER_JITTER_PERCENT / 100.0,
                settings.SCHEDULER_JITTER_PERCENT / 100.0
            )
            total_delay_seconds = max(10.0, (delay_minutes * 60.0) * jitter_factor)
            job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=total_delay_seconds)

            # Update next scheduled run in DB
            try:
                async with async_session_factory() as session:
                    src_obj = await session.get(Source, connector.source_id)
                    if src_obj:
                        src_obj.next_scheduled_run = job.next_run_at
                        src_obj.backoff_minutes = job.current_backoff_minutes
                        src_obj.consecutive_failures = job.consecutive_failures
                        await session.commit()
            except Exception:
                pass

            try:
                await asyncio.sleep(total_delay_seconds)
            except asyncio.CancelledError:
                break

    def get_status(self) -> Dict[str, Any]:
        """Returns observable telemetry on the background scheduler and all registered jobs."""
        active_jobs = []
        for src_id, job in self._jobs.items():
            active_jobs.append({
                "connector_id": src_id,
                "interval_minutes": job.base_interval_minutes,
                "next_run_at": job.next_run_at.isoformat() if job.next_run_at else None,
                "last_run_at": job.last_run_at.isoformat() if job.last_run_at else None,
                "last_status": job.last_status,
                "consecutive_failures": job.consecutive_failures,
                "current_backoff_minutes": job.current_backoff_minutes,
                "records_fetched_last_run": job.records_fetched_last_run,
                "records_new_last_run": job.records_new_last_run,
                "last_error": job.last_error,
            })

        return {
            "scheduler_enabled": settings.ENABLE_BACKGROUND_SCHEDULER,
            "scheduler_running": self.running,
            "scheduler_started_at": self.started_at.isoformat() if self.started_at else None,
            "total_jobs": len(self._jobs),
            "active_jobs": active_jobs,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
