import hashlib
import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import insert
from app.models import Signal, RawSignalBronze
from app.core.config import settings


def generate_fingerprint(
    title: str,
    published_at: datetime,
    publisher: str = "",
    company: str = "",
    asset: str = "",
    pmid: Optional[str] = None,
    nct_id: Optional[str] = None,
    regulatory_id: Optional[str] = None
) -> str:
    """Generates a stable, deterministic fingerprint string for deduplication."""
    if pmid:
        return f"pmid:{pmid.strip().lower()}"
    if nct_id:
        return f"nct:{nct_id.strip().upper()}"
    if regulatory_id:
        return f"reg:{regulatory_id.strip().lower()}"

    # Fallback to normalized title + publisher + date + company + asset hash
    norm_title = re.sub(r"\W+", "", title.lower())
    norm_publisher = re.sub(r"\W+", "", publisher.lower())
    norm_date = published_at.strftime("%Y-%m-%d")
    norm_company = re.sub(r"\W+", "", company.lower())
    norm_asset = re.sub(r"\W+", "", asset.lower())

    raw_str = f"{norm_title}|{norm_publisher}|{norm_date}|{norm_company}|{norm_asset}"
    return f"hash:{hashlib.sha256(raw_str.encode('utf-8')).hexdigest()}"


def chunk_text_for_embedding(text: str, max_tokens: int = settings.EMBEDDING_MAX_SEQ_LENGTH) -> str:
    """
    Chunks or extracts evidence from text to fit within max_tokens (approx 4 chars per token).
    Prevents sequence truncation for sentence-transformers/all-MiniLM-L6-v2 (256-token max).
    """
    max_chars = max_tokens * 4
    cleaned = text.strip()
    if len(cleaned) > max_chars:
        return cleaned[:max_chars]
    return cleaned


async def upsert_signal(
    session: AsyncSession,
    signal_data: Dict[str, Any]
) -> Signal:
    """
    Database-safe transactional upsert using ON CONFLICT DO UPDATE handling.
    Safe under concurrent pipeline runs.
    """
    fingerprint = signal_data["fingerprint"]
    stmt = insert(Signal).values(**signal_data)

    # On Conflict DO UPDATE fields
    update_dict = {
        "title": stmt.excluded.title,
        "content": stmt.excluded.content,
        "retrieved_at": stmt.excluded.retrieved_at,
        "facts": stmt.excluded.facts,
        "interpretation": stmt.excluded.interpretation,
        "speculation": stmt.excluded.speculation,
        "priority": stmt.excluded.priority,
        "score_breakdown": stmt.excluded.score_breakdown,
        "pipeline_run_id": stmt.excluded.pipeline_run_id
    }

    stmt = stmt.on_conflict_do_update(
        index_elements=["fingerprint"],
        set_=update_dict
    ).returning(Signal)

    result = await session.execute(stmt)
    await session.commit()
    return result.scalar_one()
