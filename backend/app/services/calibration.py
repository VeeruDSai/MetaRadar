import hashlib
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    CalibrationFeedback,
    CalibrationHistory,
    ScoringWeights,
    Signal,
    SignalRouting,
    WatchItem,
)
from app.schemas import (
    BeforeAfterComparisonSchema,
    CalibrationWeightsResponse,
    ConfirmWatchItemRequest,
    ConfirmWatchItemResponse,
    FeedbackRoleSummarySchema,
    FeedbackSubmissionRequest,
    FeedbackSubmissionResponse,
    FeedbackSummaryResponse,
    RecalibrateResponse,
    RoleWeightSchema,
    WatchRuleSuggestionSchema,
)

logger = logging.getLogger(__name__)

CANONICAL_FUNCTIONS = [
    "MEDICAL_AFFAIRS",
    "REGULATORY",
    "SAFETY",
    "MARKET_ACCESS",
    "COMMUNICATIONS",
    "LEADERSHIP",
]

KEYWORDS_MAP = [
    ("congress", "ASH/ISTH Congress presentation & clinical readout", 90),
    ("abstract", "ASH/ISTH Congress presentation & clinical readout", 90),
    ("durability", "Long-term durability follow-up & expression trajectory", 180),
    ("long-term", "Long-term durability follow-up & expression trajectory", 180),
    ("trial", "Clinical trial milestone readout & cohort analysis", 180),
    ("phase", "Clinical trial milestone readout & cohort analysis", 180),
    ("regulatory", "Regulatory filing submission or label amendment", 270),
    ("label", "Regulatory filing submission or label amendment", 270),
    ("filing", "Regulatory filing submission or label amendment", 270),
    ("safety", "Safety surveillance update & inhibitor monitoring", 90),
    ("inhibitor", "Safety surveillance update & inhibitor monitoring", 90),
    ("titer", "Safety surveillance update & inhibitor monitoring", 90),
    ("competitor", "Competitor commercial positioning & pricing update", 120),
    ("commercial", "Competitor commercial positioning & pricing update", 120),
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class HeuristicWatchParser:
    """
    Deterministic keyword/intent rules parsing feedback comments into
    structured WatchItem suggestions (Decision D-08). Zero external LLM dependency.
    """

    @staticmethod
    def parse(
        comment: str,
        signal_id: Optional[UUID] = None,
        development_id: Optional[UUID] = None,
        responsible_function: str = "REGULATORY",
    ) -> Optional[WatchRuleSuggestionSchema]:
        if not comment or len(comment.strip()) < 3:
            return None

        comment_lower = comment.lower()
        matched_event = None
        matched_window = 90

        for kw, event_desc, window_days in KEYWORDS_MAP:
            if re.search(rf"\b{re.escape(kw)}\b", comment_lower):
                matched_event = event_desc
                matched_window = window_days
                break

        if not matched_event:
            return None

        # Deterministic suggestion ID
        raw_key = f"{signal_id}_{responsible_function}_{matched_event}"
        suggestion_id = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()[:16]

        trigger = comment.strip()
        if len(trigger) > 120:
            trigger = trigger[:117] + "..."

        return WatchRuleSuggestionSchema(
            suggestion_id=f"sug-{suggestion_id}",
            development_id=development_id,
            trigger_event=trigger,
            expected_event=matched_event,
            monitoring_window_days=matched_window,
            responsible_function=responsible_function,
            rationale=f"Heuristic parser matched '{matched_event}' from stakeholder feedback comment.",
        )


class StakeholderCalibrationService:
    """
    Service managing persistent human-in-the-loop (HITL) calibration feedback,
    bounded batch weight recalibration (alpha=0.05, center=3.0, clamp [0.1, 2.0]),
    WORM baseline preservation, and watch-rule generation.
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def submit_feedback(
        self, req: FeedbackSubmissionRequest
    ) -> FeedbackSubmissionResponse:
        """Appends feedback to calibration_feedback WORM table (D-05, D-07)."""
        feedback_id = uuid.uuid4()
        feedback_row = CalibrationFeedback(
            feedback_id=feedback_id,
            signal_id=req.signal_id,
            stakeholder_function=req.stakeholder_function,
            relevance_rating=req.relevance_rating,
            urgency_rating=req.urgency_rating,
            action_appropriate=req.action_appropriate,
            comments=req.comments,
            submitted_at=utc_now(),
        )
        self.session.add(feedback_row)
        await self.session.commit()
        await self.session.refresh(feedback_row)

        # Count unapplied feedback for this role
        stmt = select(func.count(CalibrationFeedback.feedback_id)).where(
            CalibrationFeedback.stakeholder_function == req.stakeholder_function
        )
        result = await self.session.execute(stmt)
        unapplied_count = result.scalar_one() or 1

        recalibration_triggered = unapplied_count >= 3

        return FeedbackSubmissionResponse(
            feedback_id=feedback_row.feedback_id,
            signal_id=feedback_row.signal_id,
            stakeholder_function=feedback_row.stakeholder_function,
            status="recorded",
            unapplied_count=unapplied_count,
            recalibration_triggered=recalibration_triggered,
        )

    async def get_weights(self) -> CalibrationWeightsResponse:
        """Retrieves active scoring weights across canonical functions, seeding defaults if missing."""
        stmt = select(ScoringWeights)
        result = await self.session.execute(stmt)
        existing_rows = {row.stakeholder_function: row for row in result.scalars().all()}

        weights_list: List[RoleWeightSchema] = []
        now = utc_now()

        for fn in CANONICAL_FUNCTIONS:
            if fn in existing_rows:
                r = existing_rows[fn]
                weights_list.append(
                    RoleWeightSchema(
                        stakeholder_function=r.stakeholder_function,
                        impact_weight=r.impact_weight,
                        urgency_weight=r.urgency_weight,
                        novelty_weight=r.novelty_weight,
                        updated_at=r.updated_at or now,
                    )
                )
            else:
                # Seed default 1.0 (D-04)
                new_row = ScoringWeights(
                    stakeholder_function=fn,
                    impact_weight=1.0,
                    urgency_weight=1.0,
                    novelty_weight=1.0,
                    updated_at=now,
                )
                self.session.add(new_row)
                weights_list.append(
                    RoleWeightSchema(
                        stakeholder_function=fn,
                        impact_weight=1.0,
                        urgency_weight=1.0,
                        novelty_weight=1.0,
                        updated_at=now,
                    )
                )

        if len(existing_rows) < len(CANONICAL_FUNCTIONS):
            await self.session.commit()

        # Query latest version from history
        hist_stmt = (
            select(CalibrationHistory)
            .order_by(CalibrationHistory.applied_at.desc())
            .limit(1)
        )
        hist_res = await self.session.execute(hist_stmt)
        latest_hist = hist_res.scalar_one_or_none()
        version = latest_hist.version if latest_hist else "v1.0.0"

        return CalibrationWeightsResponse(version=version, weights=weights_list)

    async def recalibrate_role(
        self, stakeholder_function: Optional[str] = None
    ) -> RecalibrateResponse:
        """
        Executes bounded batch weight recalibration for a single role or all roles (D-01, D-02, D-03).
        Computes side-by-side BEFORE/AFTER comparisons without overwriting baseline routing.
        """
        # 1. Fetch active weights
        weights_resp = await self.get_weights()
        active_weights = {w.stakeholder_function: w for w in weights_resp.weights}

        # 2. Query feedback rows
        fb_query = select(CalibrationFeedback)
        if stakeholder_function:
            fb_query = fb_query.where(
                CalibrationFeedback.stakeholder_function == stakeholder_function
            )
        fb_res = await self.session.execute(fb_query)
        feedback_rows = fb_res.scalars().all()

        if not feedback_rows:
            return RecalibrateResponse(
                status="no_unapplied_feedback",
                calibration_version=weights_resp.version,
                stakeholder_function=stakeholder_function,
                applied_feedback_count=0,
                updated_weights=weights_resp.weights,
                comparisons=[],
                watch_rule_suggestions=[],
            )

        # 3. Aggregate feedback per function
        fn_feedback: Dict[str, List[CalibrationFeedback]] = {}
        for fb in feedback_rows:
            fn_feedback.setdefault(fb.stakeholder_function, []).append(fb)

        updated_weights_list: List[RoleWeightSchema] = []
        weights_modified = False
        watch_suggestions: List[WatchRuleSuggestionSchema] = []

        now = utc_now()

        for fn, fbs in fn_feedback.items():
            current_w = active_weights.get(fn)
            old_impact = current_w.impact_weight if current_w else 1.0
            old_urgency = current_w.urgency_weight if current_w else 1.0
            old_novelty = current_w.novelty_weight if current_w else 1.0

            # Batch mean calculation
            avg_rel = sum(f.relevance_rating for f in fbs) / len(fbs)
            avg_urg = sum(f.urgency_rating for f in fbs) / len(fbs)

            # Gradient update math: alpha = 0.05, center = 3.0, clamp [0.1, 2.0]
            delta_impact = 0.05 * (avg_rel - 3.0)
            delta_urgency = 0.05 * (avg_urg - 3.0)

            new_impact = round(max(0.1, min(2.0, old_impact + delta_impact)), 3)
            new_urgency = round(max(0.1, min(2.0, old_urgency + delta_urgency)), 3)
            new_novelty = old_novelty  # Preserved unless explicit novelty feedback

            if new_impact != old_impact or new_urgency != old_urgency:
                weights_modified = True

            # Update in DB
            db_w_stmt = select(ScoringWeights).where(
                ScoringWeights.stakeholder_function == fn
            )
            db_w_res = await self.session.execute(db_w_stmt)
            db_w_row = db_w_res.scalar_one_or_none()
            if db_w_row:
                db_w_row.impact_weight = new_impact
                db_w_row.urgency_weight = new_urgency
                db_w_row.novelty_weight = new_novelty
                db_w_row.updated_at = now
            else:
                db_w_row = ScoringWeights(
                    stakeholder_function=fn,
                    impact_weight=new_impact,
                    urgency_weight=new_urgency,
                    novelty_weight=new_novelty,
                    updated_at=now,
                )
                self.session.add(db_w_row)

            updated_weights_list.append(
                RoleWeightSchema(
                    stakeholder_function=fn,
                    impact_weight=new_impact,
                    urgency_weight=new_urgency,
                    novelty_weight=new_novelty,
                    updated_at=now,
                )
            )

            # Heuristic watch-rule extraction from comments
            for fb in fbs:
                if fb.comments:
                    sug = HeuristicWatchParser.parse(
                        comment=fb.comments,
                        signal_id=fb.signal_id,
                        responsible_function=fn,
                    )
                    if sug and not any(s.suggestion_id == sug.suggestion_id for s in watch_suggestions):
                        watch_suggestions.append(sug)

        # 4. Generate next semver calibration version
        curr_ver = weights_resp.version
        try:
            parts = curr_ver.lstrip("v").split(".")
            next_patch = int(parts[-1]) + 1
            new_version = f"v{parts[0]}.{parts[1]}.{next_patch}"
        except Exception:
            new_version = f"v1.1.{int(now.timestamp()) % 1000}"

        # 5. Insert history record
        hist_entry = CalibrationHistory(
            version=new_version,
            weights={
                w.stakeholder_function: {
                    "impact": w.impact_weight,
                    "urgency": w.urgency_weight,
                    "novelty": w.novelty_weight,
                }
                for w in updated_weights_list
            },
            applied_at=now,
        )
        self.session.add(hist_entry)

        # 6. Recompute Calibrated Routing & BEFORE/AFTER Comparisons
        comparisons: List[BeforeAfterComparisonSchema] = []
        routing_stmt = select(SignalRouting)
        routing_res = await self.session.execute(routing_stmt)
        routing_rows = routing_res.scalars().all()

        weight_map = {w.stakeholder_function: w for w in updated_weights_list}

        for routing in routing_rows:
            base_scores = routing.baseline_relevance_scores or {}
            calibrated_scores: Dict[str, float] = {}

            for f_name, base_s in base_scores.items():
                w_obj = weight_map.get(f_name) or active_weights.get(f_name)
                w_val = w_obj.impact_weight if w_obj else 1.0
                calibrated_scores[f_name] = round(min(1.0, float(base_s) * w_val), 2)

            calibrated_primary = routing.baseline_primary_function
            if calibrated_scores:
                calibrated_primary = max(calibrated_scores.items(), key=lambda x: x[1])[0]

            # Priority recompute
            target_fn = stakeholder_function or routing.baseline_primary_function
            w_target = weight_map.get(target_fn) or active_weights.get(target_fn)
            w_imp = w_target.impact_weight if w_target else 1.0
            w_urg = w_target.urgency_weight if w_target else 1.0

            base_val = float(base_scores.get(target_fn, 0.75))
            cal_val = float(calibrated_scores.get(target_fn, base_val))

            # Baseline priority score (unit weights)
            base_priority_score = round(0.6 * base_val + 0.4 * 0.8, 2)
            if base_priority_score >= 0.75:
                baseline_priority = "CRITICAL"
            elif base_priority_score >= 0.50:
                baseline_priority = "HIGH"
            elif base_priority_score >= 0.30:
                baseline_priority = "MEDIUM"
            else:
                baseline_priority = "LOW"

            # Calibrated priority score
            priority_score = round(0.6 * (base_val * w_imp) + 0.4 * (0.8 * w_urg), 2)
            if priority_score >= 0.75:
                calibrated_priority = "CRITICAL"
            elif priority_score >= 0.50:
                calibrated_priority = "HIGH"
            elif priority_score >= 0.30:
                calibrated_priority = "MEDIUM"
            else:
                calibrated_priority = "LOW"

            calibrated_action = (
                f"Calibrated Action: Immediate high-priority {target_fn} briefing and "
                f"cross-functional coordination triggered (Score: {int(cal_val*100)}%)."
            )

            # Persist calibrated columns without altering baseline (D-03)
            routing.calibrated_primary_function = calibrated_primary
            routing.calibrated_relevance_scores = calibrated_scores
            routing.calibrated_suggested_action = calibrated_action
            routing.calibration_version = new_version
            routing.updated_at = now

            uplift_pct = round(((cal_val - base_val) / max(0.01, base_val)) * 100.0, 1)

            comparisons.append(
                BeforeAfterComparisonSchema(
                    signal_id=routing.signal_id,
                    stakeholder_function=target_fn,
                    baseline_priority=baseline_priority,
                    calibrated_priority=calibrated_priority,
                    baseline_relevance_score=base_val,
                    calibrated_relevance_score=cal_val,
                    baseline_suggested_action=routing.baseline_suggested_action,
                    calibrated_suggested_action=calibrated_action,
                    confidence_uplift_pct=uplift_pct,
                )
            )

        await self.session.commit()

        return RecalibrateResponse(
            status="recalibrated",
            calibration_version=new_version,
            stakeholder_function=stakeholder_function,
            applied_feedback_count=len(feedback_rows),
            updated_weights=updated_weights_list,
            comparisons=comparisons,
            watch_rule_suggestions=watch_suggestions,
        )

    async def get_summary(self) -> FeedbackSummaryResponse:
        """Aggregates feedback metrics and accuracy by stakeholder function."""
        stmt = select(
            CalibrationFeedback.stakeholder_function,
            func.count(CalibrationFeedback.feedback_id).label("total"),
            func.avg(CalibrationFeedback.relevance_rating).label("avg_rel"),
            func.avg(CalibrationFeedback.urgency_rating).label("avg_urg"),
            func.sum(
                func.cast(CalibrationFeedback.action_appropriate, func.integer())
            ).label("approved_count"),
        ).group_by(CalibrationFeedback.stakeholder_function)

        result = await self.session.execute(stmt)
        rows = result.all()

        roles_summary: List[FeedbackRoleSummarySchema] = []
        total_feedback = 0

        for r in rows:
            fn = r.stakeholder_function
            cnt = int(r.total)
            avg_rel = round(float(r.avg_rel or 0.0), 2)
            avg_urg = round(float(r.avg_urg or 0.0), 2)
            app_rate = round((float(r.approved_count or 0) / max(1, cnt)) * 100.0, 1)
            total_feedback += cnt

            roles_summary.append(
                FeedbackRoleSummarySchema(
                    stakeholder_function=fn,
                    total_feedback_count=cnt,
                    average_relevance=avg_rel,
                    average_urgency=avg_urg,
                    action_approval_rate=app_rate,
                )
            )

        return FeedbackSummaryResponse(
            total_feedback=total_feedback,
            roles=roles_summary,
        )

    async def confirm_watch_item(
        self, req: ConfirmWatchItemRequest
    ) -> ConfirmWatchItemResponse:
        """Creates a confirmed active WatchItem attached to development (D-09, D-10)."""
        watch_id = uuid.uuid4()
        watch_row = WatchItem(
            watch_id=watch_id,
            development_id=req.development_id,
            trigger_event=req.trigger_event,
            expected_event=req.expected_event,
            monitoring_window_days=req.monitoring_window_days,
            responsible_function=req.responsible_function,
            status="watching",
            created_at=utc_now(),
        )
        self.session.add(watch_row)
        await self.session.commit()
        await self.session.refresh(watch_row)

        return ConfirmWatchItemResponse(
            watch_id=watch_row.watch_id,
            status=watch_row.status,
            responsible_function=watch_row.responsible_function,
            monitoring_window_days=watch_row.monitoring_window_days,
        )
