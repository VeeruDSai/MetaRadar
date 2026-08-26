"""Deterministic Explainable Routing & Leadership Escalation Engine.

Implements function routing and transparent leadership escalation policies:
- Clinical/scientific developments -> Medical Affairs
- Regulatory agency decisions/submissions -> Regulatory
- Safety signals/adverse events -> Safety / Pharmacovigilance
- Pricing/reimbursement/access -> Market Access
- External communication implications -> Communications
- Strategic cross-functional events or CRITICAL priority signals -> Leadership (Escalated: True)
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class StakeholderFunction(str, Enum):
    MEDICAL_AFFAIRS = "MEDICAL_AFFAIRS"
    REGULATORY = "REGULATORY"
    SAFETY = "SAFETY"
    MARKET_ACCESS = "MARKET_ACCESS"
    COMMUNICATIONS = "COMMUNICATIONS"
    LEADERSHIP = "LEADERSHIP"


FUNCTION_LABELS: Dict[StakeholderFunction, str] = {
    StakeholderFunction.MEDICAL_AFFAIRS: "Medical Affairs",
    StakeholderFunction.REGULATORY: "Regulatory Affairs",
    StakeholderFunction.SAFETY: "Safety / Pharmacovigilance",
    StakeholderFunction.MARKET_ACCESS: "Market Access",
    StakeholderFunction.COMMUNICATIONS: "Medical Communications",
    StakeholderFunction.LEADERSHIP: "Executive Leadership",
}


def resolve_signal_function(
    signal_type: Optional[str],
    title: str = "",
    content: str = "",
) -> StakeholderFunction:
    """
    Deterministically maps signal classification and semantic concepts to the primary stakeholder function.
    """
    st_upper = (signal_type or "").upper().strip()
    text = f"{title} {content}".lower()

    # Safety signals take precedence
    if st_upper == "SAFETY" or any(w in text for w in ["adverse event", "black box warning", "thrombotic microangiopathy", "liver enzyme elevation", "contraindication"]):
        return StakeholderFunction.SAFETY

    # Regulatory decisions and agency actions
    if st_upper == "REGULATORY" or any(w in text for w in ["fda approval", "ema chmp", "complete response letter", "crl", "pdufa", "bla submission", "marketing authorization"]):
        return StakeholderFunction.REGULATORY

    # Market access, reimbursement, and HTA
    if st_upper == "ACCESS" or any(w in text for w in ["reimbursement", "pricing", "hta", "icer", "cost-effectiveness", "formulary", "payer"]):
        return StakeholderFunction.MARKET_ACCESS

    # Commercial & patent activity
    if st_upper == "COMMERCIAL_PATENT" or any(w in text for w in ["patent cliff", "litigation", "acquisition", "licensing agreement"]):
        return StakeholderFunction.LEADERSHIP

    # External media communications
    if st_upper == "COMMUNICATIONS" or any(w in text for w in ["press briefing", "media controversy", "public announcement"]):
        return StakeholderFunction.COMMUNICATIONS

    # Default for Clinical trials, scientific publications, and congress abstracts
    return StakeholderFunction.MEDICAL_AFFAIRS


def resolve_signal_routing(
    signal_type: Optional[str],
    priority: str = "MEDIUM",
    priority_score: Optional[float] = None,
    title: str = "",
    content: str = "",
    is_competitor: bool = True,
) -> Dict[str, Any]:
    """
    Resolves complete deterministic routing and leadership escalation for a signal.
    Returns:
        {
            "relevant_function": StakeholderFunction,
            "route_destination": str,
            "route_role": "FUNCTION" | "LEADERSHIP",
            "is_escalated": bool,
            "routing_reason": str,
            "routing_timestamp": datetime,
            "suggested_action": str,
            "action_rationale": str,
        }
    """
    primary_fn = resolve_signal_function(signal_type, title, content)
    fn_label = FUNCTION_LABELS.get(primary_fn, "Functional Team")

    # Leadership Escalation Policy
    is_critical = (priority.upper() == "CRITICAL")
    is_major_event = any(w in f"{title} {content}".lower() for w in [
        "approved", "approval", "crl", "complete response letter",
        "black box", "trial halted", "suspended", "patent cliff", "litigation", "breakthrough therapy"
    ])
    is_strategic_domain = primary_fn in (StakeholderFunction.REGULATORY, StakeholderFunction.LEADERSHIP, StakeholderFunction.SAFETY)
    has_high_priority = priority.upper() in ("CRITICAL", "HIGH")
    has_strategic_score = (priority_score is not None and priority_score >= 80.0)

    if is_critical or (is_strategic_domain and is_major_event and (has_high_priority or has_strategic_score)):
        is_escalated = True
        route_destination = "LEADERSHIP"
        route_role = "LEADERSHIP"
        routing_reason = (
            f"Escalated to Executive Leadership due to high-impact strategic inflection event in {fn_label} "
            f"(Priority: {priority}, Score: {priority_score or 'N/A'}) requiring cross-functional alignment."
        )
    else:
        is_escalated = False
        route_destination = primary_fn.value
        route_role = "FUNCTION"
        routing_reason = f"Routed to {fn_label} queue based on {signal_type or 'intelligence'} domain classification."

    # Formulate Contextual Suggested Action
    suggested_action, action_rationale = formulate_suggested_action(primary_fn, is_escalated, signal_type, title)

    return {
        "relevant_function": primary_fn.value,
        "route_destination": route_destination,
        "route_role": route_role,
        "is_escalated": is_escalated,
        "routing_reason": routing_reason,
        "routing_timestamp": datetime.now(timezone.utc),
        "suggested_action": suggested_action,
        "action_rationale": action_rationale,
    }


def formulate_suggested_action(
    fn: StakeholderFunction,
    is_escalated: bool,
    signal_type: Optional[str] = None,
    title: str = "",
) -> Tuple[str, str]:
    """
    Formulates a structured recommendation and rationale based on the target function and escalation level.
    """
    title_lower = title.lower()

    if is_escalated:
        return (
            "Convene cross-functional executive steering committee to review strategic exposure, label implications, and commercial positioning against competitor milestone.",
            "High-impact inflection event requires coordinated alignment across Medical Affairs, Regulatory, and Market Access leadership.",
        )

    if fn == StakeholderFunction.REGULATORY:
        if "approval" in title_lower or "approved" in title_lower:
            return (
                "Review approved label and prescribing indications against Novo Nordisk asset dossier; assess filing timeline implications for competing submissions.",
                "Regulatory approval alters competitive baseline standards and potential label differentiation.",
            )
        else:
            return (
                "Evaluate regulatory filing pathway, endpoint precedents, and CHMP/FDA review timelines for potential benchmark impact.",
                "Regulatory interactions establish precedent requirements for ongoing rare disease programs.",
            )

    if fn == StakeholderFunction.SAFETY:
        return (
            "Initiate pharmacovigilance literature surveillance and evaluate signal causality compared to class-wide safety profiles in the global safety database.",
            "Potential safety signal requires prompt verification to safeguard patient safety and monitor adverse event rates.",
        )

    if fn == StakeholderFunction.MARKET_ACCESS:
        return (
            "Update comparative economic models, ICER cost-effectiveness projections, and national reimbursement dossier strategies.",
            "Pricing and reimbursement developments influence payer adoption thresholds and access hurdles.",
        )

    if fn == StakeholderFunction.COMMUNICATIONS:
        return (
            "Prepare internal Q&A briefing and align medical science liaison (MSL) reactive messaging with validated trial evidence.",
            "Ensures consistent, evidence-grounded scientific dialogue across external stakeholder interactions.",
        )

    # Default Medical Affairs
    return (
        "Incorporate trial readout data into haemophilia landscape clinical benchmark matrix; brief medical directors on efficacy/durability metrics.",
        "Clinical study results provide direct comparative evidence on patient annualized bleed rates (ABR) and Factor expression levels.",
    )
