import logging
import uuid
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models import PipelineRun
from app.schemas import PipelineRunRequestSchema, PipelineRunResponseSchema
from app.workflows.runner import PipelineRunner

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/pipeline/run",
    response_model=PipelineRunResponseSchema,
    status_code=status.HTTP_200_OK,
    summary="Trigger LangGraph 10-Node Intelligence Engine Run",
    description="Executes the full 10-node stateful LangGraph pipeline (node_ingest -> node_calibrate -> END)."
)
async def trigger_pipeline_run(
    request: Optional[PipelineRunRequestSchema] = None,
    session: AsyncSession = Depends(get_db)
) -> PipelineRunResponseSchema:
    """Triggers execution of the LangGraph 10-node intelligence pipeline."""
    batch_size = request.batch_size if request else 50
    cal_weights = request.calibration_weights if request else None

    runner = PipelineRunner(session=session)
    final_state = await runner.run(
        batch_size=batch_size,
        calibration_weights=cal_weights
    )

    errors = final_state.get("errors", [])
    overall_status = "completed" if len(errors) == 0 else ("failed" if not final_state.get("role_briefs") else "partial")

    return PipelineRunResponseSchema(
        pipeline_run_id=final_state.get("pipeline_run_id", str(uuid.uuid4())),
        status=overall_status,
        signals_processed=final_state.get("signals_processed", 0),
        role_briefs_count=len(final_state.get("role_briefs", [])),
        developments_count=len(final_state.get("developments", [])),
        confluence_stories_count=len(final_state.get("confluent_stories", [])),
        contradictions_count=len(final_state.get("redteam_flags", [])),
        missing_signals_count=len(final_state.get("missing_signals", [])),
        node_statuses=final_state.get("node_statuses", {}),
        errors=errors
    )


@router.get(
    "/pipeline/status/{pipeline_run_id}",
    summary="Get Pipeline Run Status",
    description="Retrieves execution status and telemetry for a specific pipeline_run_id."
)
async def get_pipeline_run_status(
    pipeline_run_id: str,
    session: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """Queries the pipeline_runs table for run status and error summaries."""
    try:
        run_uuid = uuid.UUID(pipeline_run_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid pipeline_run_id UUID format")

    stmt = select(PipelineRun).where(PipelineRun.pipeline_run_id == run_uuid)
    result = await session.execute(stmt)
    run_record = result.scalar_one_or_none()

    if not run_record:
        raise HTTPException(status_code=404, detail=f"Pipeline run '{pipeline_run_id}' not found")

    return {
        "pipeline_run_id": str(run_record.pipeline_run_id),
        "status": run_record.status,
        "trigger": run_record.trigger,
        "started_at": run_record.started_at.isoformat() if run_record.started_at else None,
        "completed_at": run_record.completed_at.isoformat() if run_record.completed_at else None,
        "signals_fetched": run_record.signals_fetched,
        "signals_created": run_record.signals_created,
        "errors_count": run_record.errors_count,
        "error_summary": run_record.error_summary
    }
