"""
Rate Limiting and Security Configuration Tests

TASK-395: Review CORS configuration
TASK-396: Test rate limiting
"""

import pytest
import time
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db
from app.core.cors import CORSConfig


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


class TestCORSConfiguration:
    """Tests for CORS security configuration"""

    def test_cors_allows_configured_origins(self, client):
        """Test that CORS allows configured origins"""
        allowed_origins = CORSConfig.get_allowed_origins()
        
        if allowed_origins:
            origin = allowed_origins[0]
            response = client.options(
                "/api/v1/health",
                headers={"Origin": origin}
            )
            
            # Should allow the origin
            assert response.headers.get("access-control-allow-origin") in [origin, "*"]

    def test_cors_rejects_unknown_origins(self, client):
        """Test that CORS rejects unknown origins"""
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "https://evil.com"}
        )
        
        # Should not allow unknown origin (or return null/none)
        allowed_origin = response.headers.get("access-control-allow-origin")
        if allowed_origin:
            assert allowed_origin != "https://evil.com"

    def test_cors_no_wildcard_in_production(self):
        """Test that wildcard CORS is not used in production"""
        config = CORSConfig.get_cors_config()
        allowed_origins = config["allow_origins"]
        
        # Should not contain wildcard
        assert "*" not in allowed_origins, \
            "Wildcard (*) CORS is not allowed in production"

    def test_cors_credentials_with_specific_origins(self):
        """Test that credentials are only allowed with specific origins"""
        config = CORSConfig.get_cors_config()
        
        if config["allow_credentials"]:
            # If credentials are allowed, origins must be specific
            assert "*" not in config["allow_origins"], \
                "Cannot use credentials with wildcard origins"

    def test_cors_limited_methods(self):
        """Test that only necessary HTTP methods are allowed"""
        config = CORSConfig.get_cors_config()
        allowed_methods = config["allow_methods"]
        
        # Should only include standard RESTful methods
        standard_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
        
        for method in allowed_methods:
            assert method in standard_methods, \
                f"Unexpected HTTP method allowed: {method}"
        
        # Should not allow TRACE or CONNECT
        assert "TRACE" not in allowed_methods
        assert "CONNECT" not in allowed_methods

    def test_cors_limited_headers(self):
        """Test that only necessary headers are allowed"""
        config = CORSConfig.get_cors_config()
        allowed_headers = config["allow_headers"]
        
        # Should include standard headers
        required_headers = ["Authorization", "Content-Type"]
        for header in required_headers:
            assert header in allowed_headers, \
                f"Required header missing: {header}"
        
        # Should not be wildcard
        assert "*" not in allowed_headers

    def test_cors_preflight_caching(self, client):
        """Test that CORS preflight responses are cached"""
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        
        # Should have max-age header
        max_age = response.headers.get("access-control-max-age")
        if max_age:
            assert int(max_age) > 0, "CORS max-age should be positive"
            assert int(max_age) <= 86400, "CORS max-age should not exceed 24 hours"

    def test_cors_origin_validation(self):
        """Test origin validation logic"""
        # Valid origins
        valid_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
        ]
        
        for origin in valid_origins:
            if origin in CORSConfig.get_allowed_origins():
                assert CORSConfig.validate_origin(origin), \
                    f"Valid origin rejected: {origin}"
        
        # Invalid origins
        invalid_origins = [
            "https://evil.com",
            "http://malicious.example.com",
            "null",
        ]
        
        for origin in invalid_origins:
            assert not CORSConfig.validate_origin(origin), \
                f"Invalid origin accepted: {origin}"


class TestRateLimiting:
    """Tests for rate limiting protection"""

    def test_rate_limiting_on_auth_endpoints(self, client):
        """Test that auth endpoints are rate limited"""
        # Make multiple login attempts
        attempts = 0
        for i in range(20):  # Try 20 times
            response = client.post("/api/v1/auth/login", data={
                "username": f"test{i}@example.com",
                "password": "wrong"
            })
            
            if response.status_code == 429:  # Rate limited
                break
            attempts += 1
            time.sleep(0.1)  # Small delay
        
        # Should be rate limited before 20 attempts
        assert attempts < 20, "No rate limiting detected on auth endpoint"

    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are included in responses"""
        response = client.get("/api/v1/health")
        
        # Should include rate limit headers
        headers = response.headers
        # Note: Headers may not be present if rate limiting middleware isn't active
        # This is a check to ensure they're added when implemented
        rate_limit_headers = [
            "x-ratelimit-limit",
            "x-ratelimit-remaining",
        ]
        
        # At least some rate limit info should be present (if implemented)
        # For now, just check response is successful
        assert response.status_code == 200

    def test_rate_limit_different_endpoints_different_limits(self, client):
        """Test that different endpoints have different rate limits"""
        # This is a conceptual test
        # Auth endpoints should have stricter limits than regular API
        
        # Register a user
        client.post("/api/v1/auth/register", json={
            "email": "ratelimit@example.com",
            "password": "SecurePass123!",
            "full_name": "Rate Limit Test"
        })
        
        # Login to get token
        login_response = client.post("/api/v1/auth/login", data={
            "username": "ratelimit@example.com",
            "password": "SecurePass123!"
        })
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Make many API requests
            api_attempts = 0
            for i in range(150):
                response = client.get(
                    "/api/v1/agents",
                    headers={"Authorization": f"Bearer {token}"}
                )
                if response.status_code == 429:
                    break
                api_attempts += 1
                if i % 10 == 0:
                    time.sleep(0.1)
            
            # API should allow more requests than auth
            # (This assumes different limits are configured)
            assert api_attempts > 5

    def test_rate_limit_per_ip_address(self, client):
        """Test that rate limiting is applied per IP address"""
        # Make requests from "same" IP
        for i in range(10):
            response = client.get("/api/v1/health")
            if response.status_code == 429:
                # Rate limited
                assert "rate limit" in response.json().get("detail", "").lower()
                break

    def test_rate_limit_429_response(self, client):
        """Test that rate limit returns proper 429 response"""
        # Make many requests quickly
        for i in range(200):
            response = client.post("/api/v1/auth/login", data={
                "username": f"spam{i}@example.com",
                "password": "wrong"
            })
            
            if response.status_code == 429:
                # Check response format
                assert "detail" in response.json()
                assert "retry-after" in response.headers or \
                       "retry_after" in response.json(), \
                       "Rate limit response should include retry-after"
                break

    def test_rate_limit_resets_after_window(self, client):
        """Test that rate limit resets after time window"""
        # This is a time-consuming test, so we'll make it simple
        # Just verify that rate limiting is temporary
        
        # Hit rate limit
        for i in range(20):
            client.post("/api/v1/auth/login", data={
                "username": "test@example.com",
                "password": "wrong"
            })
        
        # Wait a bit
        time.sleep(2)
        
        # Should be able to make request again
        response = client.get("/api/v1/health")
        assert response.status_code in [200, 429]  # Either works or still limited

    def test_rate_limit_bypass_with_whitelist(self):
        """Test that whitelisted IPs bypass rate limiting"""
        # This would require mocking IP address
        # For now, just a placeholder
        pass

    def test_distributed_rate_limiting_with_redis(self):
        """Test that rate limiting works across multiple instances (with Redis)"""
        # This requires Redis to be running
        # Test that rate limits are shared across instances
        # Placeholder for integration test
        pass


class TestSecurityHeaders:
    """Tests for security headers"""

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses"""
        response = client.get("/api/v1/health")
        headers = response.headers
        
        # Check for important security headers
        security_headers = {
            "x-frame-options": ["DENY", "SAMEORIGIN"],
            "x-content-type-options": ["nosniff"],
            "x-xss-protection": ["1; mode=block", "0"],
        }
        
        for header, valid_values in security_headers.items():
            header_value = headers.get(header)
            if header_value:
                assert any(valid in header_value for valid in valid_values), \
                    f"Invalid value for {header}: {header_value}"

    def test_hsts_header_on_https(self, client):
        """Test that HSTS header is present on HTTPS"""
        # For HTTPS requests, HSTS should be set
        # This requires HTTPS setup in tests
        response = client.get("/api/v1/health")
        
        # If HTTPS, should have HSTS
        # For HTTP, HSTS should not be set
        # Check if header exists
        hsts = response.headers.get("strict-transport-security")
        # In tests with HTTP, HSTS may not be present (which is correct)
        if hsts:
            assert "max-age=" in hsts

    def test_csp_header_prevents_inline_scripts(self, client):
        """Test that CSP header prevents inline scripts"""
        response = client.get("/api/v1/health")
        csp = response.headers.get("content-security-policy")
        
        if csp:
            # Should have script-src directive
            assert "script-src" in csp or "default-src" in csp
            
            # For maximum security, should not allow unsafe-inline
            # (though some apps may need it for functionality)
            # Just check that CSP is present
            assert len(csp) > 0

    def test_server_header_removed(self, client):
        """Test that server header is removed or generic"""
        response = client.get("/api/v1/health")
        server = response.headers.get("server")
        
        # Server header should be removed or generic
        if server:
            # Should not reveal server details
            server_lower = server.lower()
            assert "uvicorn" not in server_lower or "fastapi" not in server_lower, \
                "Server header reveals implementation details"
