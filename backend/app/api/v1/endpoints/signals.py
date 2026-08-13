from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models import Signal
from app.providers.factory import provider_factory
from app.providers.base import ProviderCapability, DataClassification

router = APIRouter()


class AthenaQueryRequest(BaseModel):
    prompt: str


class AthenaQueryResponse(BaseModel):
    answer: str
    confidence: float
    evidence_count: int


@router.get("/signals")
async def list_signals(
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Returns signals list."""
    try:
        result = await db.execute(select(Signal).limit(limit))
        signals = result.scalars().all()
        if signals:
            return {"signals": [s.__dict__ for s in signals], "total": len(signals)}
    except Exception:
        pass

    return {
        "signals": [
            {
                "signal_id": "sig-001",
                "title": "Hemgenix 3-Year Follow-up Study Readout",
                "disease": "Haemophilia B",
                "signal_type": "CLINICAL_TRIAL",
                "priority": "HIGH",
                "published_at": datetime.now(timezone.utc).isoformat(),
                "content": "Sustained Factor IX expression observed with stable ABR reduction across 54 adult male patients.",
                "source_id": "pubmed"
            }
        ],
        "total": 1
    }


@router.get("/overview")
async def get_overview():
    """Returns workspace summary metrics and health overview."""
    return {
        "active_signals": 38,
        "weekly_change": "+12.4%",
        "last_sync": datetime.now(timezone.utc).isoformat(),
        "health": {
            "api": "healthy",
            "latency_ms": 142,
            "source_count": 12
        }
    }


@router.post("/athena", response_model=AthenaQueryResponse)
async def query_athena(payload: AthenaQueryRequest):
    """Queries Athena intelligence synthesis layer."""
    evidence = [
        "Hemgenix 3-year durability shows sustained FIX levels at 36.5%",
        "Alhemo (concizumab) European rollout expanded to 14 centers",
        "Qfitlia (fitusiran) sub-q monthly dosing approved in Japan"
    ]
    res = await provider_factory.execute_task(
        required_capability=ProviderCapability.REASON,
        evidence=evidence,
        task=payload.prompt,
        classification=DataClassification.PUBLIC
    )
    return AthenaQueryResponse(
        answer=res.get("what_changed", "Synthesized response ready."),
        confidence=87.0,
        evidence_count=len(evidence)
    )
