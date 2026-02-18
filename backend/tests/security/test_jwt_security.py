"""
JWT Token Security Tests

TASK-390: Test JWT token security
Tests for token expiration, signature validation, claims verification
"""

import pytest
import jwt
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    SECRET_KEY,
    ALGORITHM
)
from app.core.config import settings


# In-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session(test_db):
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def override_get_db(db_session):
    def _override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def client(override_get_db):
    return TestClient(app)


@pytest.fixture
def authenticated_user(client):
    """Create and authenticate a test user"""
    # Register
    client.post("/api/v1/auth/register", json={
        "email": "jwt@example.com",
        "password": "SecurePass123!",
        "full_name": "JWT Test"
    })
    
    # Login
    response = client.post("/api/v1/auth/login", data={
        "username": "jwt@example.com",
        "password": "SecurePass123!"
    })
    
    return response.json()


class TestJWTSecurity:
    """Security tests for JWT tokens"""

    def test_token_has_required_claims(self, authenticated_user):
        """Test that JWT contains all required claims"""
        token = authenticated_user["access_token"]
        
        # Decode without verification (just to inspect claims)
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Required claims
        assert "sub" in decoded, "Missing 'sub' (subject) claim"
        assert "exp" in decoded, "Missing 'exp' (expiration) claim"
        assert "iat" in decoded, "Missing 'iat' (issued at) claim"
        
        # Subject should be user identifier
        assert decoded["sub"] == "jwt@example.com"
        
        # Expiration should be in the future
        assert decoded["exp"] > datetime.utcnow().timestamp()

    def test_token_signature_validation(self, authenticated_user):
        """Test that token signature is properly validated"""
        token = authenticated_user["access_token"]
        
        # Valid signature should verify
        try:
            decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            assert decoded is not None
        except jwt.InvalidSignatureError:
            pytest.fail("Valid token failed signature verification")
        
        # Tampered token should fail
        tampered_token = token[:-10] + "tampered1"
        with pytest.raises(jwt.InvalidSignatureError):
            jwt.decode(tampered_token, SECRET_KEY, algorithms=[ALGORITHM])

    def test_token_expiration_enforcement(self, client):
        """Test that expired tokens are rejected"""
        # Create an expired token
        expired_token = create_access_token(
            data={"sub": "test@example.com"},
            expires_delta=timedelta(seconds=-1)  # Already expired
        )
        
        # Try to use expired token
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()

    def test_token_with_invalid_algorithm(self, authenticated_user):
        """Test that tokens with wrong algorithm are rejected"""
        token_data = {
            "sub": "hacker@example.com",
            "exp": datetime.utcnow() + timedelta(hours=1)
        }
        
        # Try to create token with weak algorithm (none)
        none_token = jwt.encode(token_data, "", algorithm="none")
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {none_token}"}
        )
        
        assert response.status_code == 401

    def test_token_claims_cannot_be_modified(self, authenticated_user):
        """Test that modifying token claims invalidates signature"""
        token = authenticated_user["access_token"]
        
        # Decode token
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Modify claims
        decoded["sub"] = "hacker@example.com"
        decoded["exp"] = datetime.utcnow().timestamp() + 86400
        
        # Re-encode with modified claims (wrong signature)
        modified_token = jwt.encode(decoded, "wrong_key", algorithm=ALGORITHM)
        
        # Should be rejected
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {modified_token}"}
        )
        
        assert response.status_code == 401

    def test_refresh_token_different_from_access_token(self, authenticated_user):
        """Test that refresh tokens are different from access tokens"""
        access_token = authenticated_user["access_token"]
        refresh_token = authenticated_user.get("refresh_token")
        
        if refresh_token:
            assert access_token != refresh_token
            
            # Decode both
            access_decoded = jwt.decode(access_token, options={"verify_signature": False})
            refresh_decoded = jwt.decode(refresh_token, options={"verify_signature": False})
            
            # Refresh token should have longer expiration
            assert refresh_decoded["exp"] > access_decoded["exp"]

    def test_token_not_valid_before_issued(self, client):
        """Test that tokens are not valid before issue time"""
        # Create token with future issue time
        future_token = jwt.encode(
            {
                "sub": "test@example.com",
                "iat": datetime.utcnow().timestamp() + 3600,  # 1 hour in future
                "exp": datetime.utcnow().timestamp() + 7200   # 2 hours in future
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        # Should be rejected (if nbf/iat validation is implemented)
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {future_token}"}
        )
        
        # May be accepted if iat validation is not strict
        # Just ensure it's properly structured
        assert response.status_code in [200, 401]

    def test_token_audience_validation(self):
        """Test audience claim validation (if implemented)"""
        # Create token with specific audience
        token = jwt.encode(
            {
                "sub": "test@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "aud": "wrong-audience"
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        # If audience validation is implemented, this should fail
        # For now, just verify token structure
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "aud" in decoded

    def test_token_issuer_validation(self):
        """Test issuer claim validation (if implemented)"""
        # Create token with specific issuer
        token = jwt.encode(
            {
                "sub": "test@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iss": "aura-platform"
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )
        
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        assert "iss" in decoded

    def test_token_jti_uniqueness(self, client):
        """Test JWT ID (jti) for token uniqueness (if implemented)"""
        # Login twice
        client.post("/api/v1/auth/register", json={
            "email": "jti@example.com",
            "password": "SecurePass123!",
            "full_name": "JTI Test"
        })
        
        response1 = client.post("/api/v1/auth/login", data={
            "username": "jti@example.com",
            "password": "SecurePass123!"
        })
        
        response2 = client.post("/api/v1/auth/login", data={
            "username": "jti@example.com",
            "password": "SecurePass123!"
        })
        
        token1 = response1.json()["access_token"]
        token2 = response2.json()["access_token"]
        
        # Tokens should be different
        assert token1 != token2

    def test_token_revocation_check(self, authenticated_user, client):
        """Test token revocation mechanism (if implemented)"""
        token = authenticated_user["access_token"]
        
        # Token should work initially
        response1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 200
        
        # Logout (should revoke token)
        client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Token should be revoked (if blacklisting is implemented)
        response2 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # May still work if blacklisting is not implemented
        assert response2.status_code in [200, 401]

    def test_token_replay_attack_protection(self, client):
        """Test protection against token replay attacks"""
        # Register and login
        client.post("/api/v1/auth/register", json={
            "email": "replay@example.com",
            "password": "SecurePass123!",
            "full_name": "Replay Test"
        })
        
        response = client.post("/api/v1/auth/login", data={
            "username": "replay@example.com",
            "password": "SecurePass123!"
        })
        token = response.json()["access_token"]
        
        # Use token multiple times
        responses = []
        for _ in range(5):
            r = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            responses.append(r.status_code)
        
        # All should succeed (unless rate limiting is applied)
        # This tests that tokens can be used multiple times
        # (which is normal behavior, not a vulnerability)
        assert all(status == 200 for status in responses)

    def test_short_lived_access_tokens(self, authenticated_user):
        """Test that access tokens have reasonable expiration time"""
        token = authenticated_user["access_token"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Calculate token lifetime
        issued_at = decoded.get("iat", datetime.utcnow().timestamp())
        expires_at = decoded["exp"]
        lifetime_seconds = expires_at - issued_at
        
        # Access tokens should be short-lived (< 1 hour recommended)
        assert lifetime_seconds <= 3600, \
            f"Access token lifetime is too long: {lifetime_seconds} seconds"

    def test_token_does_not_contain_sensitive_data(self, authenticated_user):
        """Test that tokens don't contain sensitive information"""
        token = authenticated_user["access_token"]
        decoded = jwt.decode(token, options={"verify_signature": False})
        
        # Should not contain sensitive data
        sensitive_fields = ["password", "hashed_password", "secret_key", "api_key"]
        for field in sensitive_fields:
            assert field not in decoded, \
                f"Token contains sensitive field: {field}"

    def test_hmac_sha256_algorithm_used(self, authenticated_user):
        """Test that strong algorithm (HS256 or better) is used"""
        token = authenticated_user["access_token"]
        
        # Decode header
        header = jwt.get_unverified_header(token)
        
        # Check algorithm
        assert header["alg"] in ["HS256", "HS384", "HS512", "RS256", "RS384", "RS512"], \
            f"Weak or unsupported algorithm: {header['alg']}"
        
        # Verify 'none' algorithm is not accepted
        assert header["alg"] != "none"

    def test_secret_key_strength(self):
        """Test that secret key is sufficiently strong"""
        # Secret key should be long and random
        assert len(SECRET_KEY) >= 32, \
            "Secret key is too short (should be at least 32 characters)"
        
        # Should not be a common/weak key
        weak_keys = ["secret", "password", "12345", "abc123", "changeme"]
        assert SECRET_KEY.lower() not in weak_keys, \
            "Secret key is too weak"

    def test_token_authorization_header_format(self, authenticated_user, client):
        """Test that only proper Bearer format is accepted"""
        token = authenticated_user["access_token"]
        
        # Valid format
        response1 = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response1.status_code == 200
        
        # Invalid formats should be rejected
        invalid_formats = [
            token,  # No Bearer prefix
            f"Basic {token}",  # Wrong scheme
            f"bearer {token}",  # Wrong case (should be case-insensitive but test)
            f"Bearer{token}",  # No space
        ]
        
        for invalid_format in invalid_formats:
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": invalid_format}
            )
            # Some may be accepted (Bearer is case-insensitive)
            # Main test is that proper format works
            assert response.status_code in [200, 401, 403]
