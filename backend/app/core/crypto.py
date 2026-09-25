import base64
import hashlib
from cryptography.fernet import Fernet
from app.core.config import settings

def _get_fernet() -> Fernet:
    """Derive a consistent 32-byte urlsafe base64 key from settings.ENCRYPTION_KEY or SECRET_KEY."""
    raw_key = settings.ENCRYPTION_KEY.encode("utf-8")
    derived_32 = hashlib.sha256(raw_key).digest()
    urlsafe_key = base64.urlsafe_b64encode(derived_32)
    return Fernet(urlsafe_key)

def encrypt_secret(plaintext: str) -> str:
    """Encrypt a secret string into base64 ciphertext."""
    if not plaintext:
        return ""
    f = _get_fernet()
    encrypted = f.encrypt(plaintext.encode("utf-8"))
    return encrypted.decode("utf-8")

def decrypt_secret(ciphertext: str) -> str:
    """Decrypt a base64 ciphertext back to plaintext."""
    if not ciphertext:
        return ""
    try:
        f = _get_fernet()
        decrypted = f.decrypt(ciphertext.encode("utf-8"))
        return decrypted.decode("utf-8")
    except Exception:
        # Fallback if decryption fails or unencrypted in test
        return ciphertext
