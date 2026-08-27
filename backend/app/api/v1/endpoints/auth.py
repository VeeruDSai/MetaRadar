from datetime import datetime, timezone
import logging
from typing import Any, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    auth_rate_limit,
    get_current_user,
    get_optional_user,
    require_preauth_origin,
    require_csrf,
)

from app.core.config import settings
from app.core.security import (
    SESSION_COOKIE_NAME,
    CSRF_COOKIE_NAME,
    generate_session_bound_csrf,
)
from app.db.session import get_db
from app.models.auth import User
from app.models import AuditLog
from app.schemas.auth import (
    LoginRequest,
    DemoLoginRequest,
    UserMe,
    CsrfResponse,
    LogoutResponse,
)
from app.services.auth_service import (
    authenticate_user,
    create_session,
    get_or_create_demo_user,
    invalidate_session,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _set_auth_cookies(response: Response, session_token: str, csrf_token: str) -> None:
    """Helper to attach session and CSRF cookies with security parameters."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_token,
        max_age=settings.SESSION_LIFETIME_SECONDS,
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=settings.SESSION_LIFETIME_SECONDS,
        httponly=False,  # Accessible to JavaScript for X-CSRF-Token header attachment
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    """Helper to clear session and CSRF cookies on logout."""
    response.delete_cookie(key=SESSION_COOKIE_NAME, path="/", httponly=True, samesite="lax")
    response.delete_cookie(key=CSRF_COOKIE_NAME, path="/", httponly=False, samesite="lax")


@router.post("/login", response_model=UserMe, dependencies=[Depends(auth_rate_limit), Depends(require_preauth_origin)])
async def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Standard email/password credential authentication endpoint."""
    user = await authenticate_user(db, payload.email, payload.password)
    now_utc = datetime.now(timezone.utc)
    correlation_id = getattr(request.state, "correlation_id", None) or request.headers.get("X-Correlation-ID")

    if not user:
        # Audit failed login attempt
        try:
            db.add(AuditLog(
                entity_name="User",
                entity_id=payload.email,
                action="LOGIN_FAILED",
                performed_by=payload.email,
                timestamp=now_utc,
                details={"reason": "Invalid credentials", "ip": request.client.host if request.client else "unknown"},
            ))
            await db.commit()
        except Exception as e:
            logger.debug("Failed to record failed login audit: %s", e)

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    # Create session
    sess, token = await create_session(
        db=db,
        user_id=user.user_id,
        secret=settings.SECRET_KEY,
        lifetime_s=settings.SESSION_LIFETIME_SECONDS,
    )
    csrf_token = generate_session_bound_csrf(str(sess.session_id), settings.SECRET_KEY)
    _set_auth_cookies(response, token, csrf_token)

    # Audit successful login
    try:
        db.add(AuditLog(
            entity_name="User",
            entity_id=str(user.user_id),
            action="LOGIN_SUCCESS",
            performed_by=user.display_name,
            timestamp=now_utc,
            details={"email": user.email, "role": user.role, "method": "credentials"},
        ))
        await db.commit()
    except Exception as e:
        logger.debug("Failed to record login audit: %s", e)

    return UserMe(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/demo-login", response_model=UserMe, dependencies=[Depends(auth_rate_limit), Depends(require_preauth_origin)])
async def demo_login(
    payload: DemoLoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Demo login endpoint active strictly when DEMO_MODE=true.
    Authenticates directly into a target stakeholder persona role without exposing passwords in client bundles.
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Demo persona switching is disabled in production.",
        )

    user = await get_or_create_demo_user(db, payload.role)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo persona role '{payload.role}'",
        )

    sess, token = await create_session(
        db=db,
        user_id=user.user_id,
        secret=settings.SECRET_KEY,
        lifetime_s=settings.SESSION_LIFETIME_SECONDS,
    )
    csrf_token = generate_session_bound_csrf(str(sess.session_id), settings.SECRET_KEY)
    _set_auth_cookies(response, token, csrf_token)

    now_utc = datetime.now(timezone.utc)
    try:
        db.add(AuditLog(
            entity_name="User",
            entity_id=str(user.user_id),
            action="LOGIN_SUCCESS",
            performed_by=user.display_name,
            timestamp=now_utc,
            details={"email": user.email, "role": user.role, "method": "demo_selector"},
        ))
        await db.commit()
    except Exception as e:
        logger.debug("Failed to record demo login audit: %s", e)

    return UserMe(
        user_id=user.user_id,
        email=user.email,
        display_name=user.display_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/logout", response_model=LogoutResponse, dependencies=[Depends(require_csrf)])
async def logout(
    request: Request,
    response: Response,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):

    """Terminates the current session, revokes DB session token, and clears auth cookies."""
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        await invalidate_session(db, token)

    _clear_auth_cookies(response)

    if current_user:
        now_utc = datetime.now(timezone.utc)
        try:
            db.add(AuditLog(
                entity_name="User",
                entity_id=str(current_user.user_id),
                action="LOGOUT",
                performed_by=current_user.display_name,
                timestamp=now_utc,
                details={"email": current_user.email, "role": current_user.role},
            ))
            await db.commit()
        except Exception as e:
            logger.debug("Failed to record logout audit: %s", e)

    return LogoutResponse(status="logged_out", message="Session successfully terminated")


@router.get("/me", response_model=UserMe)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    """Returns the authenticated user identity and role from the active session."""
    return UserMe(
        user_id=current_user.user_id,
        email=current_user.email,
        display_name=current_user.display_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
    )


@router.get("/csrf", response_model=CsrfResponse)
async def get_csrf_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Explicit CSRF token bootstrap endpoint.
    If an active session cookie is present, generates and returns the matching session-bound HMAC CSRF token.
    """
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        result = await get_or_create_demo_user(db, "MEDICAL_AFFAIRS")  # ensures db connectivity
        from app.services.auth_service import get_session_user
        res = await get_session_user(
            db=db,
            token=token,
            secret=settings.SECRET_KEY,
            max_age_s=settings.SESSION_LIFETIME_SECONDS,
            idle_timeout_s=settings.SESSION_IDLE_TIMEOUT_SECONDS,
        )
        if res:
            _, sess = res
            csrf_token = generate_session_bound_csrf(str(sess.session_id), settings.SECRET_KEY)
            response.set_cookie(
                key=CSRF_COOKIE_NAME,
                value=csrf_token,
                max_age=settings.SESSION_LIFETIME_SECONDS,
                httponly=False,
                secure=settings.SESSION_COOKIE_SECURE,
                samesite="lax",
                path="/",
            )
            return CsrfResponse(csrf_token=csrf_token)

    # For unauthenticated clients, return an anonymous bootstrap token
    anon_csrf = generate_session_bound_csrf(str(uuid.uuid4()), settings.SECRET_KEY)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=anon_csrf,
        max_age=3600,
        httponly=False,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return CsrfResponse(csrf_token=anon_csrf)
