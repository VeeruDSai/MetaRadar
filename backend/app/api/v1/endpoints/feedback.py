import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas import (
    CalibrationWeightsResponse,
    ConfirmWatchItemRequest,
    ConfirmWatchItemResponse,
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
    FeedbackSummaryResponse,
    RecalibrateResponse,
)
from app.services.calibration import StakeholderCalibrationService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/feedback",
    response_model=FeedbackSubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit stakeholder rating and comment feedback on a signal",
)
async def submit_feedback(
    payload: FeedbackSubmissionRequest,
    db: AsyncSession = Depends(get_db),
) -> FeedbackSubmissionResponse:
    """
    Records stakeholder rating and review comments to the WORM calibration_feedback table (D-05, D-07).
    """
    try:
        service = StakeholderCalibrationService(db)
        return await service.submit_feedback(payload)
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record stakeholder feedback.",
        )


@router.get(
    "/feedback/summary",
    response_model=FeedbackSummaryResponse,
    summary="Retrieve aggregated feedback metrics and approval rates by stakeholder role",
)
async def get_feedback_summary(
    db: AsyncSession = Depends(get_db),
) -> FeedbackSummaryResponse:
    """
    Returns aggregated feedback metrics across all six canonical stakeholder functions (D-07).
    """
    try:
        service = StakeholderCalibrationService(db)
        return await service.get_summary()
    except Exception as e:
        logger.error(f"Error retrieving feedback summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve feedback summary.",
        )


@router.post(
    "/calibrate",
    response_model=RecalibrateResponse,
    summary="Trigger bounded batch weight recalibration and recompute calibrated routing",
)
async def trigger_recalibration(
    stakeholder_function: Optional[str] = Query(
        None,
        description="Optional stakeholder function to recalibrate. If omitted, recalibrates all roles.",
    ),
    db: AsyncSession = Depends(get_db),
) -> RecalibrateResponse:
    """
    Executes batch weight recalibration with bounded gradient updates (alpha=0.05, center=3.0, clamp [0.1, 2.0]),
    preserving baseline routing while generating side-by-side BEFORE/AFTER comparisons and watch-rule suggestions (D-01, D-02, D-03, D-08).
    """
    if stakeholder_function:
        fn_upper = stakeholder_function.strip().upper()
        if fn_upper not in [
            "MEDICAL_AFFAIRS",
            "REGULATORY",
            "SAFETY",
            "MARKET_ACCESS",
            "COMMUNICATIONS",
            "LEADERSHIP",
        ]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid stakeholder_function '{stakeholder_function}'. Allowed: MEDICAL_AFFAIRS, REGULATORY, SAFETY, MARKET_ACCESS, COMMUNICATIONS, LEADERSHIP",
            )
        stakeholder_function = fn_upper

    try:
        service = StakeholderCalibrationService(db)
        return await service.recalibrate_role(stakeholder_function)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing recalibration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute recalibration.",
        )


@router.get(
    "/calibration/weights",
    response_model=CalibrationWeightsResponse,
    summary="Get current calibrated scoring weights across all stakeholder functions",
)
async def get_calibration_weights(
    db: AsyncSession = Depends(get_db),
) -> CalibrationWeightsResponse:
    """
    Returns current impact, urgency, and novelty weights for all six stakeholder roles (D-04, D-07).
    """
    try:
        service = StakeholderCalibrationService(db)
        return await service.get_weights()
    except Exception as e:
        logger.error(f"Error retrieving calibration weights: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve calibration weights.",
        )


@router.post(
    "/watch-items/confirm",
    response_model=ConfirmWatchItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm a suggested watch-rule from stakeholder feedback",
)
async def confirm_watch_item(
    payload: ConfirmWatchItemRequest,
    db: AsyncSession = Depends(get_db),
) -> ConfirmWatchItemResponse:
    """
    Confirms a parsed watch rule suggestion and creates an active WatchItem attached to the development (D-09, D-10).
    """
    try:
        service = StakeholderCalibrationService(db)
        return await service.confirm_watch_item(payload)
    except Exception as e:
        logger.error(f"Error confirming watch item: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to confirm watch item.",
        )
