"""Password hashing, JWT utilities, and credential encryption."""

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


# ---------------------------------------------------------------------------
# Credential encryption (Fernet symmetric)
# ---------------------------------------------------------------------------

import json

from cryptography.fernet import Fernet, InvalidToken


def _get_fernet() -> Fernet:
    """Return a Fernet instance using the configured encryption key.

    Raises:
        ValueError: If ``credentials_encryption_key`` is not set in settings.
    """
    key = settings.credentials_encryption_key
    if not key:
        raise ValueError(
            "CREDENTIALS_ENCRYPTION_KEY is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_credentials(data: dict) -> str:
    """Serialize *data* to JSON, encrypt it, and return a URL-safe base64 string.

    Args:
        data: Dictionary of credentials (e.g. OAuth tokens).

    Returns:
        Encrypted string suitable for storing in the database.
    """
    raw = json.dumps(data).encode()
    return _get_fernet().encrypt(raw).decode()


def decrypt_credentials(token: str) -> dict:
    """Decrypt a string produced by :func:`encrypt_credentials`.

    Args:
        token: Encrypted credential string from the database.

    Returns:
        Original credentials dictionary.

    Raises:
        InvalidToken: If decryption fails (wrong key or tampered data).
    """
    raw = _get_fernet().decrypt(token.encode())
    return json.loads(raw)
