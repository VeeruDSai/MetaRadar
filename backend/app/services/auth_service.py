import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import (
    hash_password,
    verify_password,
    hash_token,
    sign_session_token,
    unsign_session_token,
)
from app.models.auth import User, Session

logger = logging.getLogger(__name__)

DEMO_PERSONAS: Dict[str, Dict[str, str]] = {
    "MEDICAL_AFFAIRS": {
        "email": "medical.affairs@metaradar.internal",
        "display_name": "Dr. Elena Vance (Medical Affairs Lead)",
    },
    "REGULATORY": {
        "email": "regulatory@metaradar.internal",
        "display_name": "Marcus Chen (Regulatory Affairs Director)",
    },
    "SAFETY": {
        "email": "safety@metaradar.internal",
        "display_name": "Dr. Sarah Jenkins (Pharmacovigilance Lead)",
    },
    "MARKET_ACCESS": {
        "email": "market.access@metaradar.internal",
        "display_name": "Henrik Lindqvist (Value & Access Director)",
    },
    "COMMUNICATIONS": {
        "email": "comms@metaradar.internal",
        "display_name": "Claire Beaumont (Medical Communications Lead)",
    },
    "LEADERSHIP": {
        "email": "leadership@metaradar.internal",
        "display_name": "Dr. Alexander Wright (EVP Global Development)",
    },
    "ADMIN": {
        "email": "admin@metaradar.internal",
        "display_name": "System Administrator",
    },
}

_generated_demo_password: Optional[str] = None


def get_demo_password() -> str:
    """Returns configured or generated non-deterministic demo password."""
    global _generated_demo_password
    if settings.DEMO_USER_PASSWORD:
        return settings.DEMO_USER_PASSWORD
    if _generated_demo_password is None:
        _generated_demo_password = secrets.token_urlsafe(12)
        print(f"[MetaRadar Security] Demo password generated for local session: {_generated_demo_password}")
    return _generated_demo_password


async def seed_demo_users_if_needed(db: AsyncSession) -> None:
    """Seeds demo stakeholder personas if running in DEMO_MODE and table is missing them."""
    if not settings.DEMO_MODE or not settings.DEMO_AUTO_SEED_USERS:
        return

    demo_pw = get_demo_password()
    hashed_pw = hash_password(demo_pw)

    for role, info in DEMO_PERSONAS.items():
        stmt = select(User).where(User.email == info["email"])
        existing = (await db.execute(stmt)).scalars().first()
        if not existing:
            user = User(
                email=info["email"],
                display_name=info["display_name"],
                hashed_password=hashed_pw,
                role=role,
                is_active=True,
            )
            db.add(user)
    await db.commit()


async def authenticate_user(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """Authenticates a user via email and plaintext password."""
    await seed_demo_users_if_needed(db)
    stmt = select(User).where(User.email == email.strip().lower(), User.is_active.is_(True))
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


async def get_or_create_demo_user(db: AsyncSession, role: str) -> Optional[User]:
    """Retrieves or creates a demo user for the specified role when DEMO_MODE is true."""
    if not settings.DEMO_MODE:
        return None

    role_key = role.upper().strip()
    if role_key not in DEMO_PERSONAS:
        return None

    await seed_demo_users_if_needed(db)
    info = DEMO_PERSONAS[role_key]
    stmt = select(User).where(User.email == info["email"], User.is_active.is_(True))
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        demo_pw = get_demo_password()
        user = User(
            email=info["email"],
            display_name=info["display_name"],
            hashed_password=hash_password(demo_pw),
            role=role_key,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    return user


async def create_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    secret: str,
    lifetime_s: int
) -> Tuple[Session, str]:
    """
    Creates a new authenticated session record with a signed token and indexed SHA256 hash.
    Returns (Session, signed_token_string).
    """
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=lifetime_s)
    session_id = uuid.uuid4()

    signed_token = sign_session_token(str(session_id), secret)
    t_hash = hash_token(signed_token)

    sess = Session(
        session_id=session_id,
        user_id=user_id,
        token_hash=t_hash,
        created_at=now,
        last_activity_at=now,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(sess)
    await db.commit()
    await db.refresh(sess)
    return sess, signed_token


async def get_session_user(
    db: AsyncSession,
    token: str,
    secret: str,
    max_age_s: int,
    idle_timeout_s: int
) -> Optional[Tuple[User, Session]]:
    """
    Validates the session token, enforces dual timeout (absolute max_age_s & idle_timeout_s),
    updates last_activity_at, and returns (User, Session) if valid.
    """
    if not token:
        return None

    try:
        session_id_str = unsign_session_token(token, secret, max_age_s)
    except Exception:
        return None

    t_hash = hash_token(token)
    stmt = select(Session).where(Session.token_hash == t_hash, Session.is_revoked.is_(False))
    sess = (await db.execute(stmt)).scalars().first()
    if not sess:
        return None

    now = datetime.now(timezone.utc)
    # Check absolute expiration
    if sess.expires_at < now:
        return None

    # Check idle timeout
    if (now - sess.last_activity_at).total_seconds() > idle_timeout_s:
        return None

    # Update last activity
    sess.last_activity_at = now
    await db.commit()

    user_stmt = select(User).where(User.user_id == sess.user_id, User.is_active.is_(True))
    user = (await db.execute(user_stmt)).scalars().first()
    if not user:
        return None

    return user, sess


async def invalidate_session(db: AsyncSession, token: str) -> bool:
    """Revokes the given session token."""
    if not token:
        return False
    t_hash = hash_token(token)
    stmt = select(Session).where(Session.token_hash == t_hash)
    sess = (await db.execute(stmt)).scalars().first()
    if sess:
        sess.is_revoked = True
        await db.commit()
        return True
    return False
