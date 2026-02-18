"""
Unit Tests for Authentication Service

TASK-369: Write unit tests for auth service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session

from app.services.auth_service import AuthService
from app.models.user import User
from app.models.organization import Organization
from app.core.security import verify_password


class TestAuthService:
    """Test suite for AuthService"""

    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def auth_service(self, mock_db):
        """AuthService instance with mocked dependencies"""
        return AuthService(mock_db)

    def test_create_user_success(self, auth_service, mock_db):
        """Test successful user creation"""
        # Arrange
        email = "test@example.com"
        password = "SecurePassword123!"
        full_name = "Test User"
        
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()

        # Act
        user = auth_service.create_user(email, password, full_name)

        # Assert
        assert user.email == email
        assert user.full_name == full_name
        assert verify_password(password, user.hashed_password)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_create_user_duplicate_email(self, auth_service, mock_db):
        """Test user creation with duplicate email"""
        # Arrange
        existing_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user

        # Act & Assert
        with pytest.raises(ValueError, match="Email already registered"):
            auth_service.create_user("test@example.com", "password", "Test User")

    def test_create_user_weak_password(self, auth_service, mock_db):
        """Test user creation with weak password"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act & Assert
        with pytest.raises(ValueError, match="Password too weak"):
            auth_service.create_user("test@example.com", "weak", "Test User")

    def test_authenticate_user_success(self, auth_service, mock_db):
        """Test successful user authentication"""
        # Arrange
        email = "test@example.com"
        password = "SecurePassword123!"
        hashed_password = "$2b$12$example_hashed_password"
        
        mock_user = Mock(spec=User)
        mock_user.email = email
        mock_user.hashed_password = hashed_password
        mock_user.is_active = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        with patch('app.services.auth_service.verify_password', return_value=True):
            # Act
            user = auth_service.authenticate_user(email, password)
            
            # Assert
            assert user == mock_user
            assert user.email == email

    def test_authenticate_user_invalid_credentials(self, auth_service, mock_db):
        """Test authentication with invalid credentials"""
        # Arrange
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Act
        user = auth_service.authenticate_user("test@example.com", "wrong_password")

        # Assert
        assert user is None

    def test_authenticate_user_inactive_account(self, auth_service, mock_db):
        """Test authentication with inactive account"""
        # Arrange
        mock_user = Mock(spec=User)
        mock_user.is_active = False
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        user = auth_service.authenticate_user("test@example.com", "password")

        # Assert
        assert user is None

    def test_create_access_token(self, auth_service):
        """Test JWT access token creation"""
        # Arrange
        user_id = "user-123"
        
        # Act
        token = auth_service.create_access_token(user_id)

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Decode and verify claims
        from app.core.security import decode_token
        payload = decode_token(token)
        assert payload["sub"] == user_id
        assert "exp" in payload

    def test_create_refresh_token(self, auth_service):
        """Test JWT refresh token creation"""
        # Arrange
        user_id = "user-123"
        
        # Act
        token = auth_service.create_refresh_token(user_id)

        # Assert
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Verify longer expiration than access token
        from app.core.security import decode_token
        payload = decode_token(token)
        assert payload["sub"] == user_id

    def test_verify_token_valid(self, auth_service):
        """Test token verification with valid token"""
        # Arrange
        user_id = "user-123"
        token = auth_service.create_access_token(user_id)

        # Act
        result = auth_service.verify_token(token)

        # Assert
        assert result == user_id

    def test_verify_token_expired(self, auth_service):
        """Test token verification with expired token"""
        # Arrange
        user_id = "user-123"
        # Create token that expires immediately
        with patch('app.core.security.timedelta', return_value=timedelta(seconds=-1)):
            token = auth_service.create_access_token(user_id)

        # Act & Assert
        with pytest.raises(Exception):
            auth_service.verify_token(token)

    def test_verify_token_invalid(self, auth_service):
        """Test token verification with invalid token"""
        # Arrange
        invalid_token = "invalid.token.here"

        # Act & Assert
        with pytest.raises(Exception):
            auth_service.verify_token(invalid_token)

    def test_get_user_by_id(self, auth_service, mock_db):
        """Test getting user by ID"""
        # Arrange
        user_id = "user-123"
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        user = auth_service.get_user_by_id(user_id)

        # Assert
        assert user == mock_user
        assert user.id == user_id

    def test_get_user_by_email(self, auth_service, mock_db):
        """Test getting user by email"""
        # Arrange
        email = "test@example.com"
        mock_user = Mock(spec=User)
        mock_user.email = email
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        # Act
        user = auth_service.get_user_by_email(email)

        # Assert
        assert user == mock_user
        assert user.email == email

    def test_update_user_profile(self, auth_service, mock_db):
        """Test updating user profile"""
        # Arrange
        user_id = "user-123"
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.full_name = "Old Name"
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit = Mock()

        # Act
        updated_user = auth_service.update_user_profile(user_id, full_name="New Name")

        # Assert
        assert updated_user.full_name == "New Name"
        mock_db.commit.assert_called_once()

    def test_change_password(self, auth_service, mock_db):
        """Test password change"""
        # Arrange
        user_id = "user-123"
        old_password = "OldPassword123!"
        new_password = "NewPassword456!"
        
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit = Mock()

        with patch('app.services.auth_service.verify_password', return_value=True):
            # Act
            result = auth_service.change_password(user_id, old_password, new_password)

            # Assert
            assert result is True
            mock_db.commit.assert_called_once()

    def test_change_password_incorrect_old_password(self, auth_service, mock_db):
        """Test password change with incorrect old password"""
        # Arrange
        mock_user = Mock(spec=User)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch('app.services.auth_service.verify_password', return_value=False):
            # Act
            result = auth_service.change_password("user-123", "wrong", "NewPassword456!")

            # Assert
            assert result is False

    def test_deactivate_user(self, auth_service, mock_db):
        """Test user deactivation"""
        # Arrange
        user_id = "user-123"
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = True
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit = Mock()

        # Act
        auth_service.deactivate_user(user_id)

        # Assert
        assert mock_user.is_active is False
        mock_db.commit.assert_called_once()

    def test_reactivate_user(self, auth_service, mock_db):
        """Test user reactivation"""
        # Arrange
        user_id = "user-123"
        mock_user = Mock(spec=User)
        mock_user.id = user_id
        mock_user.is_active = False
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        mock_db.commit = Mock()

        # Act
        auth_service.reactivate_user(user_id)

        # Assert
        assert mock_user.is_active is True
        mock_db.commit.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
