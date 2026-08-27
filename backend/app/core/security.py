import hashlib
import hmac
import secrets
from typing import Optional
import bcrypt
from itsdangerous import TimestampSigner, SignatureExpired, BadSignature

SESSION_COOKIE_NAME = "metaradar_session"
CSRF_COOKIE_NAME = "metaradar_csrf"


def hash_password(plain: str) -> str:
    """Hashes a plaintext password using bcrypt with gensalt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(plain.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifies a plaintext password against a bcrypt hash."""
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def hash_token(token: str) -> str:
    """Computes a SHA-256 hex digest for persistent session indexing."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def sign_session_token(session_id: str, secret: str) -> str:
    """Signs a session UUID into a timestamped cookie token."""
    signer = TimestampSigner(secret)
    return signer.sign(session_id.encode("utf-8")).decode("utf-8")


def unsign_session_token(token: str, secret: str, max_age_s: int) -> str:
    """
    Unsigns a session token and returns the underlying session UUID string.
    Raises SignatureExpired or BadSignature if invalid or beyond absolute max_age_s.
    """
    signer = TimestampSigner(secret)
    return signer.unsign(token.encode("utf-8"), max_age=max_age_s).decode("utf-8")


def generate_session_bound_csrf(session_id: str, secret: str) -> str:
    """Generates an HMAC-SHA256 CSRF token cryptographically bound to the session ID."""
    nonce = secrets.token_hex(16)
    message = f"{session_id}:{nonce}".encode("utf-8")
    mac = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return f"{mac}:{nonce}"


def verify_session_bound_csrf(token: str, session_id: str, secret: str) -> bool:
    """Verifies that a CSRF token was signed with secret for the given session ID."""
    try:
        parts = token.split(":")
        if len(parts) != 2:
            return False
        mac, nonce = parts[0], parts[1]
        message = f"{session_id}:{nonce}".encode("utf-8")
        expected_mac = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return hmac.compare_digest(mac, expected_mac)
    except Exception:
        return False
