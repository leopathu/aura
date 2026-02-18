"""
Unit Tests for Encryption Service

TASK-370: Write unit tests for encryption service
"""

import pytest
from cryptography.fernet import Fernet, InvalidToken

from app.services.encryption_service import EncryptionService


class TestEncryptionService:
    """Test suite for EncryptionService"""

    @pytest.fixture
    def encryption_service(self):
        """EncryptionService instance"""
        return EncryptionService()

    @pytest.fixture
    def sample_data(self):
        """Sample data for encryption"""
        return {
            "simple_string": "Hello, World!",
            "api_key": "sk_test_1234567890abcdefghijklmnop",
            "json_data": '{"key": "value", "nested": {"data": 123}}',
            "unicode": "こんにちは世界 🌍",
            "empty": "",
            "special_chars": "!@#$%^&*()_+-={}[]|:;<>?,./",
        }

    def test_encryption_service_initialization(self, encryption_service):
        """Test encryption service initializes with valid key"""
        assert encryption_service is not None
        assert hasattr(encryption_service, 'cipher_suite')
        assert isinstance(encryption_service.cipher_suite, Fernet)

    def test_encrypt_simple_string(self, encryption_service, sample_data):
        """Test encrypting a simple string"""
        # Arrange
        plaintext = sample_data["simple_string"]

        # Act
        encrypted = encryption_service.encrypt(plaintext)

        # Assert
        assert encrypted is not None
        assert isinstance(encrypted, str)
        assert encrypted != plaintext
        assert len(encrypted) > len(plaintext)

    def test_decrypt_simple_string(self, encryption_service, sample_data):
        """Test decrypting a simple string"""
        # Arrange
        plaintext = sample_data["simple_string"]
        encrypted = encryption_service.encrypt(plaintext)

        # Act
        decrypted = encryption_service.decrypt(encrypted)

        # Assert
        assert decrypted == plaintext

    def test_encrypt_decrypt_api_key(self, encryption_service, sample_data):
        """Test encrypting and decrypting API key"""
        # Arrange
        api_key = sample_data["api_key"]

        # Act
        encrypted = encryption_service.encrypt(api_key)
        decrypted = encryption_service.decrypt(encrypted)

        # Assert
        assert decrypted == api_key
        assert encrypted != api_key

    def test_encrypt_decrypt_json_data(self, encryption_service, sample_data):
        """Test encrypting and decrypting JSON data"""
        # Arrange
        json_data = sample_data["json_data"]

        # Act
        encrypted = encryption_service.encrypt(json_data)
        decrypted = encryption_service.decrypt(encrypted)

        # Assert
        assert decrypted == json_data

    def test_encrypt_decrypt_unicode(self, encryption_service, sample_data):
        """Test encrypting and decrypting unicode characters"""
        # Arrange
        unicode_text = sample_data["unicode"]

        # Act
        encrypted = encryption_service.encrypt(unicode_text)
        decrypted = encryption_service.decrypt(encrypted)

        # Assert
        assert decrypted == unicode_text

    def test_encrypt_empty_string(self, encryption_service, sample_data):
        """Test encrypting an empty string"""
        # Arrange
        empty = sample_data["empty"]

        # Act
        encrypted = encryption_service.encrypt(empty)
        decrypted = encryption_service.decrypt(encrypted)

        # Assert
        assert decrypted == empty

    def test_encrypt_special_characters(self, encryption_service, sample_data):
        """Test encrypting special characters"""
        # Arrange
        special = sample_data["special_chars"]

        # Act
        encrypted = encryption_service.encrypt(special)
        decrypted = encryption_service.decrypt(encrypted)

        # Assert
        assert decrypted == special

    def test_encryption_is_deterministic(self, encryption_service):
        """Test that same plaintext produces different ciphertext (with IV)"""
        # Arrange
        plaintext = "test data"

        # Act
        encrypted1 = encryption_service.encrypt(plaintext)
        encrypted2 = encryption_service.encrypt(plaintext)

        # Assert - Fernet includes timestamp, so encryptions differ
        assert encrypted1 != encrypted2
        # But both decrypt to same value
        assert encryption_service.decrypt(encrypted1) == plaintext
        assert encryption_service.decrypt(encrypted2) == plaintext

    def test_decrypt_invalid_token(self, encryption_service):
        """Test decrypting invalid token raises error"""
        # Arrange
        invalid_token = "invalid_encrypted_data"

        # Act & Assert
        with pytest.raises(Exception):  # Fernet raises InvalidToken
            encryption_service.decrypt(invalid_token)

    def test_decrypt_tampered_data(self, encryption_service):
        """Test decrypting tampered data raises error"""
        # Arrange
        plaintext = "test data"
        encrypted = encryption_service.encrypt(plaintext)
        
        # Tamper with encrypted data
        tampered = encrypted[:-10] + "tampered!!"

        # Act & Assert
        with pytest.raises(Exception):
            encryption_service.decrypt(tampered)

    def test_encrypt_none_raises_error(self, encryption_service):
        """Test encrypting None raises error"""
        # Act & Assert
        with pytest.raises((TypeError, AttributeError)):
            encryption_service.encrypt(None)

    def test_decrypt_none_raises_error(self, encryption_service):
        """Test decrypting None raises error"""
        # Act & Assert
        with pytest.raises((TypeError, AttributeError)):
            encryption_service.decrypt(None)

    def test_encrypt_large_data(self, encryption_service):
        """Test encrypting large data"""
        # Arrange
        large_data = "A" * 10000  # 10KB of data

        # Act
        encrypted = encryption_service.encrypt(large_data)
        decrypted = encryption_service.decrypt(encrypted)

        # Assert
        assert decrypted == large_data

    def test_multiple_encrypt_decrypt_cycles(self, encryption_service):
        """Test multiple encryption/decryption cycles"""
        # Arrange
        original = "test data"

        # Act - Encrypt and decrypt multiple times
        data = original
        for _ in range(5):
            encrypted = encryption_service.encrypt(data)
            data = encryption_service.decrypt(encrypted)

        # Assert
        assert data == original

    def test_encrypt_different_data_produces_different_output(self, encryption_service):
        """Test different plaintext produces different ciphertext"""
        # Arrange
        plaintext1 = "data one"
        plaintext2 = "data two"

        # Act
        encrypted1 = encryption_service.encrypt(plaintext1)
        encrypted2 = encryption_service.encrypt(plaintext2)

        # Assert
        assert encrypted1 != encrypted2

    def test_encryption_service_with_custom_key(self):
        """Test encryption service with custom key"""
        # Arrange
        custom_key = Fernet.generate_key()
        service = EncryptionService(key=custom_key)
        plaintext = "test with custom key"

        # Act
        encrypted = service.encrypt(plaintext)
        decrypted = service.decrypt(encrypted)

        # Assert
        assert decrypted == plaintext

    def test_encrypted_data_is_base64_encoded(self, encryption_service):
        """Test that encrypted data is base64 encoded"""
        # Arrange
        plaintext = "test data"

        # Act
        encrypted = encryption_service.encrypt(plaintext)

        # Assert - Fernet token is base64 URL-safe
        import base64
        try:
            base64.urlsafe_b64decode(encrypted)
            is_base64 = True
        except Exception:
            is_base64 = False
        
        assert is_base64

    def test_decrypt_with_wrong_key_fails(self):
        """Test decrypting with wrong key fails"""
        # Arrange
        service1 = EncryptionService()
        service2 = EncryptionService(key=Fernet.generate_key())
        
        plaintext = "test data"
        encrypted = service1.encrypt(plaintext)

        # Act & Assert
        with pytest.raises(Exception):
            service2.decrypt(encrypted)

    def test_encrypt_credentials_dict(self, encryption_service):
        """Test encrypting complex credential dictionary"""
        # Arrange
        import json
        credentials = {
            "api_key": "sk_test_12345",
            "api_secret": "secret_67890",
            "endpoint": "https://api.example.com",
            "metadata": {
                "created_at": "2024-01-01",
                "expires_at": "2025-01-01"
            }
        }
        plaintext = json.dumps(credentials)

        # Act
        encrypted = encryption_service.encrypt(plaintext)
        decrypted = encryption_service.decrypt(encrypted)
        decrypted_dict = json.loads(decrypted)

        # Assert
        assert decrypted_dict == credentials
        assert decrypted_dict["api_key"] == credentials["api_key"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
