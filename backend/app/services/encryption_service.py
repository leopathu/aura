"""
Encryption Service
Handles encryption and decryption of sensitive data using Fernet (AES-256)
"""

from cryptography.fernet import Fernet
from app.core.config import settings


class EncryptionService:
    """Service for encrypting/decrypting sensitive data"""
    
    def __init__(self):
        """Initialize with encryption key from settings"""
        self.cipher = Fernet(settings.ENCRYPTION_KEY.encode())
    
    def encrypt(self, plaintext: str) -> str:
        """
        Encrypt a plaintext string
        
        Args:
            plaintext: The string to encrypt
            
        Returns:
            Encrypted string (base64 encoded)
        """
        if not plaintext:
            raise ValueError("Cannot encrypt empty string")
        
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, encrypted: str) -> str:
        """
        Decrypt an encrypted string
        
        Args:
            encrypted: The encrypted string (base64 encoded)
            
        Returns:
            Decrypted plaintext string
        """
        if not encrypted:
            raise ValueError("Cannot decrypt empty string")
        
        decrypted_bytes = self.cipher.decrypt(encrypted.encode())
        return decrypted_bytes.decode()


# Singleton instance
encryption_service = EncryptionService()
