"""Shared FastAPI dependencies for optional mutation auth and rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Optional

from fastapi import Header, HTTPException, Request, status

from app.core.config import settings

_rate_buckets: Dict[str, List[float]] = defaultdict(list)


async def require_mutation_auth(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> None:
    """Require X-API-Key when METARADAR_API_KEY is set; local-dev stays open when unset."""
    expected = (settings.METARADAR_API_KEY or "").strip()
    if not expected:
        return
    if not x_api_key or x_api_key != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


async def mutation_rate_limit(request: Request) -> None:
    limit = settings.MUTATION_RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = [t for t in _rate_buckets[client] if now - t < 60.0]
    if len(window) >= limit:
        _rate_buckets[client] = window
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
        )
    window.append(now)
    _rate_buckets[client] = window
