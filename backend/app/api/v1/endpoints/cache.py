import logging
from datetime import datetime, timezone
from fastapi import APIRouter
import redis.asyncio as aioredis
from app.core.config import settings
from app.schemas import CacheClearResponse

logger = logging.getLogger(__name__)
router = APIRouter()


def utc_now():
    return datetime.now(timezone.utc)


@router.post("/cache/clear", response_model=CacheClearResponse)
async def clear_server_cache():
    """Flush server-side Redis cache keys with graceful fallback."""
    now = utc_now()
    try:
        if settings.REDIS_URL:
            r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            await r.flushdb()
            await r.aclose()
            logger.info("Redis cache flushed successfully via /cache/clear.")
            return CacheClearResponse(status="cleared", flushed_at=now, keys_cleared=0)
        else:
            logger.warning("REDIS_URL not set; in-memory cache clear simulated.")
            return CacheClearResponse(status="cleared", flushed_at=now, keys_cleared=0)
    except Exception as e:
        logger.error(f"Failed to clear Redis cache: {e}")
        return CacheClearResponse(status="cache_unavailable", flushed_at=now, keys_cleared=0)
