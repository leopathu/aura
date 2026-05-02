"""Password hashing and JWT utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """Return a bcrypt hash of the given plaintext password."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if the plaintext password matches the hash."""
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def create_access_token(subject: str | Any, expires_delta: timedelta | None = None) -> str:
    """Create a signed JWT access token.

    Args:
        subject: Value to encode as the ``sub`` claim (typically user id).
        expires_delta: Custom expiry duration; defaults to settings value.

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Decode a JWT and return the ``sub`` claim.

    Raises:
        JWTError: If the token is invalid or expired.
    """
    payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    sub: str | None = payload.get("sub")
    if sub is None:
        raise JWTError("Token missing subject")
    return sub
