"""CLI backfill for signals with NULL embeddings (D-05).

Usage:
    python -m app.services.embeddings_backfill [--batch-size 50] [--dry-run]

Embeds existing Signal rows in bounded batches, records
``embedding_model_version`` (Settings.EMBEDDING_MODEL_REVISION) for
auditability, and repeats until no NULL-embedding rows remain. Partial
failures are logged and skipped — a single bad row never aborts the batch.
"""

import argparse
import asyncio
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models import Signal
from app.services.embeddings import EmbeddingError, embedding_service

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _signal_as_dict(row: Signal) -> Dict[str, Any]:
    """Builds the embedding text source dict from a Signal row (D-02)."""
    return {
        "title": row.title or "",
        "content": row.content or "",
        "signal_type": row.signal_type or "",
    }


async def async_main(batch_size: int = 50, dry_run: bool = False) -> int:
    """Backfills NULL-embedding signals in bounded batches.

    Returns the number of rows actually updated (0 in dry-run mode).
    """
    session = AsyncSessionLocal()
    total_backfilled = 0

    try:
        while True:
            stmt = (
                select(Signal)
                .where(Signal.embedding.is_(None))
                .limit(batch_size)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()

            if not rows:
                logger.info("Backfill complete: no NULL-embedding signals remain.")
                break

            batch_backfilled = 0
            for row in rows:
                try:
                    vector = await embedding_service.embed_signal(_signal_as_dict(row))
                except EmbeddingError as e:
                    logger.warning(f"Backfill: embedding failed for signal {row.signal_id}, skipping: {e}")
                    continue

                if dry_run:
                    logger.info(
                        f"Dry-run: would embed signal {row.signal_id} "
                        f"(embedding_model_version={settings.EMBEDDING_MODEL_REVISION})"
                    )
                    continue

                row.embedding = vector
                row.embedding_model_version = settings.EMBEDDING_MODEL_REVISION
                batch_backfilled += 1

            if dry_run:
                # Never wrote anything — re-querying would return the same rows.
                logger.info(f"Dry-run: {len(rows)} signals would be backfilled (embedding_model_version={settings.EMBEDDING_MODEL_REVISION})")
                break

            await session.commit()
            total_backfilled += batch_backfilled
            logger.info(
                f"Backfilled {batch_backfilled} signals "
                f"(embedding_model_version={settings.EMBEDDING_MODEL_REVISION})"
            )

        return total_backfilled
    finally:
        await session.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m app.services.embeddings_backfill",
        description="Backfill NULL-embedding signals via fastembed (D-05).",
    )
    parser.add_argument("--batch-size", type=int, default=50, help="Signals to embed per batch (default: 50)")
    parser.add_argument("--dry-run", action="store_true", help="Log what would be embedded without writing to DB")
    args = parser.parse_args()

    asyncio.run(async_main(batch_size=args.batch_size, dry_run=args.dry_run))


if __name__ == "__main__":
    main()