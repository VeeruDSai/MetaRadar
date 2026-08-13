import logging
import re
import uuid
from datetime import datetime, timedelta
from typing import Any, List, Optional, Set

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import RawSignalBronze

logger = logging.getLogger(__name__)


def _external_id_from_fingerprint(fingerprint: str) -> str:
    """Recovers the bronze external_id from a prefixed fingerprint.

    ``pmid:123`` -> ``123``, ``nct:...`` -> ``...``, ``reg:...`` -> ``...``.
    Hash-based fingerprints carry no recoverable source id and are returned
    unchanged (connectors set external_id to the same value for those).
    """
    for prefix in ("pmid:", "nct:", "reg:"):
        if fingerprint.startswith(prefix):
            return fingerprint[len(prefix):]
    return fingerprint


def _normalize_tokens(text: str) -> Set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _title_similarity(a: str, b: str) -> float:
    """Jaccard-style token overlap on normalized titles."""
    ta = _normalize_tokens(a)
    tb = _normalize_tokens(b)
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


class SourceIndependenceClassifier:
    """Cross-source identity classifier (REQ-P1-8 / D-17).

    Runs BEFORE Confluence (Phase 2). Assigns a ``cross_source_group_id`` to
    a bronze row by matching normalized title similarity + entity overlap
    within a date proximity window against already-grouped rows. Rules come
    from ``config/haemophilia.yaml`` -> ``cross_source.group_assignment``.
    """

    def __init__(self, config: Any) -> None:
        # config: CrossSourceConfig (already validated by domain_config)
        self.config = config

    async def classify(
        self,
        session: AsyncSession,
        fingerprint: str,
        title: str,
        published_at: datetime,
        entities: List[str],
    ) -> Optional[str]:
        """Returns the UUID group-id string for this fingerprint.

        - Row already grouped -> returns its existing group (idempotent).
        - High title similarity + entity overlap + within date window ->
          adopts the candidate's group.
        - Otherwise a fresh UUID group is created for the row.
        Returns None only when the bronze row cannot be located (i.e. the
        signal was never persisted).
        """
        group_cfg = self.config.group_assignment
        external_id = _external_id_from_fingerprint(fingerprint)

        # 1. Already grouped? (idempotency — no group churn on re-classify)
        current = (
            await session.execute(
                select(RawSignalBronze).where(RawSignalBronze.external_id == external_id)
            )
        ).scalar_one_or_none()
        if current is not None and current.cross_source_group_id is not None:
            return str(current.cross_source_group_id)

        # 2. Candidate rows within the date proximity window (exclude self)
        window = timedelta(hours=group_cfg.date_window_hours)
        candidates = list(
            (
                await session.execute(
                    select(RawSignalBronze).where(
                        RawSignalBronze.external_id != external_id,
                        RawSignalBronze.retrieved_at.between(
                            published_at - window, published_at + window
                        ),
                    )
                )
            ).scalars().all()
        )

        # 3. Match on title similarity + entity overlap
        entity_set = {str(e).lower() for e in entities}
        for cand in candidates:
            payload = cand.raw_payload or {}
            cand_title = str(payload.get("title") or "")
            cand_entities = {str(e).lower() for e in (payload.get("entities") or [])}
            if (
                cand.cross_source_group_id is not None
                and _title_similarity(title, cand_title) >= group_cfg.title_similarity_threshold
                and len(entity_set & cand_entities) >= group_cfg.entity_overlap_min
            ):
                await session.execute(
                    update(RawSignalBronze)
                    .where(RawSignalBronze.external_id == external_id)
                    .values(cross_source_group_id=cand.cross_source_group_id)
                )
                await session.commit()
                return str(cand.cross_source_group_id)

        # 4. New group
        group_id = uuid.uuid4()
        await session.execute(
            update(RawSignalBronze)
            .where(RawSignalBronze.external_id == external_id)
            .values(cross_source_group_id=group_id)
        )
        await session.commit()
        return str(group_id)