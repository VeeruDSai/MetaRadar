import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PipelineRun
from app.workflows.graph import build_graph
from app.workflows.state import MetaRadarState, create_initial_state

logger = logging.getLogger(__name__)


class PipelineRunner:
    """
    Async Execution Orchestrator for the 10-node MetaRadar LangGraph Intelligence Pipeline (D-01).
    Manages PipelineRun DB lifecycle, error tracking, and state execution.
    """

    def __init__(self, session: Optional[AsyncSession] = None):
        self._session = session
        self._graph = build_graph()

    async def run(
        self,
        batch_size: int = 50,
        pipeline_run_id: Optional[str] = None,
        calibration_weights: Optional[Dict[str, float]] = None,
        raw_signals: Optional[List[Dict[str, Any]]] = None,
        calibration_feedback: Optional[List[Dict[str, Any]]] = None,
    ) -> MetaRadarState:
        """
        Executes the 10-node LangGraph pipeline.
        Tracks PipelineRun lifecycle in database if session is available.
        """
        run_uuid = uuid.UUID(pipeline_run_id) if pipeline_run_id else uuid.uuid4()
        run_id_str = str(run_uuid)

        db_run: Optional[PipelineRun] = None

        # 1. Initialize PipelineRun record in DB if session is active
        if self._session is not None:
            try:
                db_run = PipelineRun(
                    pipeline_run_id=run_uuid,
                    started_at=datetime.now(timezone.utc),
                    status="running",
                    trigger="scheduled" if not raw_signals else "manual",
                )
                self._session.add(db_run)
                await self._session.commit()
            except Exception as e:
                logger.warning(f"Could not persist initial PipelineRun record: {e}")
                db_run = None

        # 2. Build Initial State
        initial_state = create_initial_state(
            pipeline_run_id=run_id_str,
            batch_size=batch_size,
            calibration_weights=calibration_weights,
            raw_signals=raw_signals,
            calibration_feedback=calibration_feedback,
        )

        # 3. Execute LangGraph Pipeline
        try:
            logger.info(f"Starting LangGraph Pipeline execution for run {run_id_str}...")
            final_state = await self._graph.ainvoke(initial_state)

            signals_processed = final_state.get("signals_processed", 0)
            role_briefs_count = len(final_state.get("role_briefs", []))
            errors_count = len(final_state.get("errors", []))

            # 4. Update PipelineRun record on Success
            if self._session is not None and db_run is not None:
                try:
                    db_run.status = "completed" if errors_count == 0 else "partial"
                    db_run.completed_at = datetime.now(timezone.utc)
                    db_run.signals_fetched = signals_processed
                    db_run.signals_created = role_briefs_count
                    db_run.errors_count = errors_count
                    if errors_count > 0:
                        db_run.error_summary = final_state.get("errors")
                    await self._session.commit()
                except Exception as db_e:
                    logger.warning(f"Could not update final PipelineRun record: {db_e}")

            logger.info(
                f"Completed LangGraph Pipeline run {run_id_str}: "
                f"{signals_processed} signals processed, {role_briefs_count} briefs generated, "
                f"{errors_count} errors recorded."
            )
            return final_state

        except Exception as e:
            logger.error(f"Fatal error during LangGraph Pipeline execution: {e}", exc_info=True)
            if self._session is not None and db_run is not None:
                try:
                    db_run.status = "failed"
                    db_run.completed_at = datetime.now(timezone.utc)
                    db_run.errors_count = 1
                    db_run.error_summary = [{"error": str(e), "timestamp": datetime.now(timezone.utc).isoformat()}]
                    await self._session.commit()
                except Exception:
                    pass

            initial_state["errors"].append({
                "node": "graph_runner",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            initial_state["node_statuses"]["graph_runner"] = "FAILED"
            return initial_state
