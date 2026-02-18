"""
Integration Tests for Authentication Endpoints

TASK-371: Write integration tests for auth endpoints
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.models.user import User
from app.models.organization import Organization


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    """Create test database for each test"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    """Test client for API requests"""
    return TestClient(app)


class TestAuthEndpoints:
    """Integration tests for authentication endpoints"""

    def test_register_user_success(self, client, test_db):
        """Test successful user registration"""
        # Arrange
        payload = {
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["full_name"] == payload["full_name"]
        assert "id" in data
        assert "hashed_password" not in data  # Password should not be returned

    def test_register_user_duplicate_email(self, client, test_db):
        """Test registration with duplicate email"""
        # Arrange
        payload = {
            "email": "duplicate@example.com",
            "password": "SecurePassword123!",
            "full_name": "First User"
        }
        
        # Create first user
        client.post("/api/v1/auth/register", json=payload)

        # Act - Try to register again with same email
        response = client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()

    def test_register_user_weak_password(self, client, test_db):
        """Test registration with weak password"""
        # Arrange
        payload = {
            "email": "user@example.com",
            "password": "weak",
            "full_name": "Test User"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

    def test_register_user_invalid_email(self, client, test_db):
        """Test registration with invalid email"""
        # Arrange
        payload = {
            "email": "invalid-email",
            "password": "SecurePassword123!",
            "full_name": "Test User"
        }

        # Act
        response = client.post("/api/v1/auth/register", json=payload)

        # Assert
        assert response.status_code == 422  # Validation error

    def test_login_success(self, client, test_db):
        """Test successful login"""
        # Arrange - Register user first
        register_payload = {
            "email": "loginuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Login User"
        }
        client.post("/api/v1/auth/register", json=register_payload)

        # Act - Login
        login_payload = {
            "username": register_payload["email"],  # OAuth2 uses 'username'
            "password": register_payload["password"]
        }
        response = client.post("/api/v1/auth/login", data=login_payload)

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, test_db):
        """Test login with invalid credentials"""
        # Arrange
        payload = {
            "username": "nonexistent@example.com",
            "password": "WrongPassword123!"
        }

        # Act
        response = client.post("/api/v1/auth/login", data=payload)

        # Assert
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()

    def test_login_wrong_password(self, client, test_db):
        """Test login with wrong password"""
        # Arrange - Register user
        register_payload = {
            "email": "user@example.com",
            "password": "CorrectPassword123!",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=register_payload)

        # Act - Login with wrong password
        login_payload = {
            "username": register_payload["email"],
            "password": "WrongPassword123!"
        }
        response = client.post("/api/v1/auth/login", data=login_payload)

        # Assert
        assert response.status_code == 401

    def test_get_current_user(self, client, test_db):
        """Test getting current authenticated user"""
        # Arrange - Register and login
        register_payload = {
            "email": "currentuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Current User"
        }
        client.post("/api/v1/auth/register", json=register_payload)
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": register_payload["email"],
            "password": register_payload["password"]
        })
        token = login_response.json()["access_token"]

        # Act
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == register_payload["email"]
        assert data["full_name"] == register_payload["full_name"]

    def test_get_current_user_unauthorized(self, client, test_db):
        """Test getting current user without authentication"""
        # Act
        response = client.get("/api/v1/auth/me")

        # Assert
        assert response.status_code == 401

    def test_get_current_user_invalid_token(self, client, test_db):
        """Test getting current user with invalid token"""
        # Act
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )

        # Assert
        assert response.status_code == 401

    def test_refresh_token(self, client, test_db):
        """Test refreshing access token"""
        # Arrange - Register and login
        register_payload = {
            "email": "refreshuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Refresh User"
        }
        client.post("/api/v1/auth/register", json=register_payload)
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": register_payload["email"],
            "password": register_payload["password"]
        })
        refresh_token = login_response.json()["refresh_token"]

        # Act
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_refresh_token_invalid(self, client, test_db):
        """Test refreshing with invalid token"""
        # Act
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"}
        )

        # Assert
        assert response.status_code == 401

    def test_change_password(self, client, test_db):
        """Test changing user password"""
        # Arrange - Register and login
        register_payload = {
            "email": "changepass@example.com",
            "password": "OldPassword123!",
            "full_name": "Change Password User"
        }
        client.post("/api/v1/auth/register", json=register_payload)
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": register_payload["email"],
            "password": register_payload["password"]
        })
        token = login_response.json()["access_token"]

        # Act - Change password
        change_payload = {
            "old_password": "OldPassword123!",
            "new_password": "NewPassword456!"
        }
        response = client.post(
            "/api/v1/auth/change-password",
            json=change_payload,
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200

        # Verify can login with new password
        new_login_response = client.post("/api/v1/auth/login", data={
            "username": register_payload["email"],
            "password": "NewPassword456!"
        })
        assert new_login_response.status_code == 200

    def test_change_password_wrong_old_password(self, client, test_db):
        """Test changing password with wrong old password"""
        # Arrange - Register and login
        register_payload = {
            "email": "user@example.com",
            "password": "OldPassword123!",
            "full_name": "Test User"
        }
        client.post("/api/v1/auth/register", json=register_payload)
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": register_payload["email"],
            "password": register_payload["password"]
        })
        token = login_response.json()["access_token"]

        # Act
        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "old_password": "WrongOldPassword!",
                "new_password": "NewPassword456!"
            },
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 400

    def test_logout(self, client, test_db):
        """Test user logout"""
        # Arrange - Register and login
        register_payload = {
            "email": "logoutuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Logout User"
        }
        client.post("/api/v1/auth/register", json=register_payload)
        
        login_response = client.post("/api/v1/auth/login", data={
            "username": register_payload["email"],
            "password": register_payload["password"]
        })
        token = login_response.json()["access_token"]

        # Act
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Assert
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
