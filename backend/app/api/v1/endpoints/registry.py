from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models import Development, Asset, Company, Source, Signal
from app.schemas.registry import DevelopmentSummary, SourceRegistryItem

router = APIRouter()


@router.get("/developments", response_model=List[DevelopmentSummary])
async def get_developments_registry(
    disease: Optional[str] = Query(None),
    stage: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve indexed clinical/regulatory developments with asset and company details."""
    query = (
        select(
            Development,
            Asset.brand_name.label("asset_name"),
            Company.name.label("company_name"),
            func.count(Signal.signal_id).label("signal_count"),
        )
        .outerjoin(Asset, Development.asset_id == Asset.asset_id)
        .outerjoin(Company, Development.company_id == Company.company_id)
        .outerjoin(Signal, Development.development_id == Signal.development_id)
        .group_by(Development.development_id, Asset.brand_name, Company.name)
    )

    if disease:
        # Escape LIKE wildcards so user input matches literally (a search for
        # "100%" must not match everything); backslash is the escape character.
        escaped_disease = (
            disease.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        )
        query = query.where(Development.disease.ilike(f"%{escaped_disease}%", escape="\\"))
    if stage:
        query = query.where(Development.current_stage == stage)

    query = query.order_by(Development.updated_at.desc()).offset(offset).limit(limit)
    result = await db.execute(query)
    rows = result.all()

    items = []
    for dev, asset_name, company_name, sig_count in rows:
        items.append(
            DevelopmentSummary(
                development_id=dev.development_id,
                title=dev.title,
                disease=dev.disease,
                current_stage=dev.current_stage,
                asset_name=asset_name,
                company_name=company_name,
                signal_count=sig_count or 0,
                created_at=dev.created_at,
                updated_at=dev.updated_at,
            )
        )
    return items


@router.get("/sources", response_model=List[SourceRegistryItem])
async def get_sources_registry(
    db: AsyncSession = Depends(get_db),
):
    """Retrieve registered data sources with freshness classes and live status."""
    from app.core.config import configuration_error_for

    query = select(Source).order_by(Source.name.asc())
    result = await db.execute(query)
    sources = result.scalars().all()

    items = []
    for s in sources:
        config_err = configuration_error_for(s.source_id)
        if config_err:
            conn_status = "CONFIGURATION_ERROR"
            err_msg = config_err
        else:
            conn_status = s.connector_status or "NEVER_CONNECTED"
            err_msg = s.configuration_error_message

        items.append(
            SourceRegistryItem(
                source_id=s.source_id,
                name=s.name,
                freshness_class=s.freshness_class,
                syndication_group=s.syndication_group,
                status=s.status,
                quota_remaining=s.quota_remaining,
                last_success=s.last_success,
                connector_status=conn_status,
                last_attempted=s.last_attempted,
                latency_ms=s.latency_ms,
                records_fetched=s.records_fetched or 0,
                records_accepted=s.records_accepted or 0,
                records_rejected=s.records_rejected or 0,
                http_status=s.http_status,
                configuration_error_message=err_msg,
            )
        )
    return items
