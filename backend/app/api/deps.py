"""Shared FastAPI dependencies for authentication, RBAC, CSRF, origin validation and rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Optional
from urllib.parse import urlparse

from fastapi import Header, HTTPException, Request, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    unsign_session_token,
    verify_session_bound_csrf,
)
from app.db.session import get_db
from app.models.auth import User
from app.services.auth_service import get_session_user

_rate_buckets: Dict[str, List[float]] = defaultdict(list)
_auth_rate_buckets: Dict[str, List[float]] = defaultdict(list)


def extract_origin(url: str) -> str:
    """Extracts exact scheme://netloc (including port if present) from a URL string."""
    if not url:
        return ""
    parsed = urlparse(url)
    if not parsed.scheme or not parsed.netloc:
        return ""
    return f"{parsed.scheme}://{parsed.netloc}"


def validate_exact_origin(origin: str, allowed_origins: List[str]) -> bool:
    """Performs exact scheme/host/port comparison against allowed CORS origins."""
    normalized = origin.rstrip("/")
    allowed_set = {extract_origin(o).rstrip("/") if "://" in o else o.rstrip("/") for o in allowed_origins}
    return normalized in allowed_set


async def require_preauth_origin(request: Request) -> None:
    """Enforces strict Origin/Referer header validation on pre-auth endpoints (OWASP Login CSRF defense)."""
    origin_header = request.headers.get("Origin")
    referer_header = request.headers.get("Referer")

    extracted = None
    if origin_header:
        extracted = extract_origin(origin_header)
    elif referer_header:
        extracted = extract_origin(referer_header)
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Missing Origin/Referer header on authentication request.",
        )

    if not extracted or not validate_exact_origin(extracted, settings.cors_origins_list):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Untrusted request origin.",
        )


async def auth_rate_limit(request: Request) -> None:
    """Rate limiter specifically protecting authentication endpoints against brute force."""
    limit = settings.AUTH_RATE_LIMIT_PER_MINUTE
    if limit <= 0:
        return
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window = [t for t in _auth_rate_buckets[client] if now - t < 60.0]
    if len(window) >= limit:
        _auth_rate_buckets[client] = window
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please wait before retrying.",
        )
    window.append(now)
    _auth_rate_buckets[client] = window


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Mandatory authentication dependency. Validates session cookie against DB,
    enforcing absolute (8h) and idle (1h) timeouts.
    Raises HTTP 401 Unauthorized if missing, invalid, or expired.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated: Missing active session token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await get_session_user(
        db=db,
        token=token,
        secret=settings.SECRET_KEY,
        max_age_s=settings.SESSION_LIFETIME_SECONDS,
        idle_timeout_s=settings.SESSION_IDLE_TIMEOUT_SECONDS,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user, sess = result
    return user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Optional authentication dependency that returns User if valid session exists, else None."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None

    result = await get_session_user(
        db=db,
        token=token,
        secret=settings.SECRET_KEY,
        max_age_s=settings.SESSION_LIFETIME_SECONDS,
        idle_timeout_s=settings.SESSION_IDLE_TIMEOUT_SECONDS,
    )
    if not result:
        return None
    user, _ = result
    return user


def require_role(*allowed_roles: str):
    """Role-Based Access Control (RBAC) dependency factory."""
    async def role_checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles and user.role != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: User role '{user.role}' is not authorized for this resource.",
            )
        return user
    return role_checker


async def require_csrf(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Session-bound HMAC CSRF validation dependency for all authenticated mutating requests.
    Validates that X-CSRF-Token matches the active session HMAC.
    """
    if request.method in {"GET", "HEAD", "OPTIONS"}:
        return

    cookie_token = request.cookies.get(CSRF_COOKIE_NAME, "")
    header_token = request.headers.get("X-CSRF-Token", "")
    if not cookie_token or not header_token or cookie_token != header_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: CSRF token missing or mismatch.",
        )

    session_cookie = request.cookies.get(SESSION_COOKIE_NAME, "")
    if not session_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden: Missing active session for CSRF verification.",
        )

    try:
        session_id_str = unsign_session_token(
            session_cookie,
            settings.SECRET_KEY,
            settings.SESSION_LIFETIME_SECONDS,
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Forbidden: Expired or invalid session token.",
        )

    if not verify_session_bound_csrf(header_token, session_id_str, settings.SECRET_KEY):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Invalid or forged session-bound CSRF token.",
        )


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
