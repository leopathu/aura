from cryptography.fernet import Fernet
from app.core.config import settings
import base64

class EncryptionService:
    """Service for encrypting and decrypting sensitive data like API keys."""
    
    def __init__(self):
        # Ensure key is properly formatted
        key = settings.ENCRYPTION_KEY.encode()
        if len(key) != 32:
            # Derive a proper key if not exactly 32 bytes
            key = base64.urlsafe_b64encode(key.ljust(32)[:32])
        else:
            key = base64.urlsafe_b64encode(key)
        self.cipher = Fernet(key)
    
    def encrypt(self, data: str) -> str:
        """Encrypt a string."""
        return self.cipher.encrypt(data.encode()).decode()
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt an encrypted string."""
        return self.cipher.decrypt(encrypted_data.encode()).decode()

encryption_service = EncryptionService()
