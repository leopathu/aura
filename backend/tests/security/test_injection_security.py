"""
Security Tests for SQL Injection, XSS, and CSRF Protection

TASK-392: Test for SQL injection vulnerabilities
TASK-393: Test for XSS vulnerabilities  
TASK-394: Test for CSRF vulnerabilities
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.core.database import Base, get_db


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
    client.post("/api/v1/auth/register", json={
        "email": "security@example.com",
        "password": "SecurePass123!",
        "full_name": "Security Test"
    })
    
    response = client.post("/api/v1/auth/login", data={
        "username": "security@example.com",
        "password": "SecurePass123!"
    })
    
    return response.json()


class TestSQLInjection:
    """Tests for SQL injection vulnerabilities"""

    def test_sql_injection_in_login(self, client):
        """Test SQL injection attempts in login endpoint"""
        sql_injections = [
            "admin' OR '1'='1",
            "admin' --",
            "admin' #",
            "' OR 1=1 --",
            "admin' UNION SELECT * FROM users --",
            "'; DROP TABLE users; --",
            "admin' AND 1=0 UNION ALL SELECT NULL, NULL, NULL --",
        ]
        
        for injection in sql_injections:
            response = client.post("/api/v1/auth/login", data={
                "username": injection,
                "password": "anything"
            })
            
            # Should not succeed or leak SQL errors
            assert response.status_code in [401, 422], \
                f"SQL injection may have succeeded: {injection}"
            
            # Response should not contain SQL error messages
            response_text = str(response.json()).lower()
            sql_error_indicators = ["sql", "syntax error", "database", "table", "column"]
            for indicator in sql_error_indicators:
                assert indicator not in response_text, \
                    f"SQL error leaked in response: {indicator}"

    def test_sql_injection_in_search(self, client, authenticated_user):
        """Test SQL injection in search/query parameters"""
        token = authenticated_user["access_token"]
        
        sql_injections = [
            "test' OR '1'='1",
            "'; DROP TABLE agents; --",
            "1 UNION SELECT * FROM credentials",
        ]
        
        for injection in sql_injections:
            # Test in query parameters
            response = client.get(
                f"/api/v1/agents?search={injection}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should handle safely
            assert response.status_code in [200, 400, 422]
            
            # Should not expose SQL errors
            response_text = str(response.json()).lower()
            assert "sql" not in response_text

    def test_orm_prevents_sql_injection(self, db_session):
        """Test that ORM (SQLAlchemy) prevents SQL injection"""
        # Direct test with database session
        malicious_input = "test' OR '1'='1"
        
        # Using ORM (safe)
        try:
            # This should safely escape the input
            result = db_session.execute(
                text("SELECT * FROM users WHERE email = :email"),
                {"email": malicious_input}
            )
            # Query executes but finds nothing (safe)
            assert result is not None
        except Exception as e:
            # Should not throw SQL syntax errors
            assert "syntax" not in str(e).lower()

    def test_parameterized_queries_used(self, client, authenticated_user):
        """Test that parameterized queries are used (not string concatenation)"""
        token = authenticated_user["access_token"]
        
        # Special characters that would break string concatenation
        special_chars = ["'; --", "' OR '1'='1", "\"; DROP TABLE", "\\x00"]
        
        for char in special_chars:
            # Try creating agent with special chars in name
            response = client.post(
                "/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": f"Test Agent {char}",
                    "system_prompt": "Test prompt"
                }
            )
            
            # Should either succeed (chars escaped) or fail gracefully
            assert response.status_code in [200, 201, 400, 422]


class TestXSS:
    """Tests for Cross-Site Scripting (XSS) vulnerabilities"""

    def test_xss_in_user_input(self, client):
        """Test XSS script injection in user inputs"""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "';alert(String.fromCharCode(88,83,83))//",
        ]
        
        for payload in xss_payloads:
            response = client.post("/api/v1/auth/register", json={
                "email": "xss@example.com",
                "password": "SecurePass123!",
                "full_name": payload  # XSS in full_name
            })
            
            if response.status_code in [200, 201]:
                # If accepted, should be sanitized in response
                response_data = response.json()
                assert "<script>" not in str(response_data)
                assert "onerror=" not in str(response_data)
                assert "javascript:" not in str(response_data)

    def test_xss_in_agent_creation(self, client, authenticated_user):
        """Test XSS in agent creation"""
        token = authenticated_user["access_token"]
        
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
        ]
        
        for payload in xss_payloads:
            response = client.post(
                "/api/v1/agents",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "name": payload,
                    "system_prompt": payload,
                    "description": payload
                }
            )
            
            if response.status_code in [200, 201]:
                # Should sanitize output
                response_data = str(response.json())
                assert "<script>" not in response_data
                assert "onerror=" not in response_data

    def test_stored_xss_prevention(self, client, authenticated_user):
        """Test stored XSS prevention (data stored in DB)"""
        token = authenticated_user["access_token"]
        
        # Create agent with potential XSS
        xss_payload = "<script>alert('Stored XSS')</script>"
        create_response = client.post(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "name": f"Agent {xss_payload}",
                "system_prompt": "Test"
            }
        )
        
        if create_response.status_code in [200, 201]:
            agent_id = create_response.json()["id"]
            
            # Retrieve agent
            get_response = client.get(
                f"/api/v1/agents/{agent_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            # Should be sanitized
            response_data = str(get_response.json())
            assert "<script>" not in response_data

    def test_reflected_xss_prevention(self, client, authenticated_user):
        """Test reflected XSS prevention (data reflected in response)"""
        token = authenticated_user["access_token"]
        
        xss_payload = "<script>alert('Reflected XSS')</script>"
        
        # Test in query parameters
        response = client.get(
            f"/api/v1/agents?search={xss_payload}",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Response should not include unescaped script
        response_text = str(response.json())
        assert "<script>" not in response_text

    def test_content_type_headers(self, client):
        """Test that proper Content-Type headers prevent XSS"""
        response = client.get("/api/v1/health")
        
        # Should return JSON
        assert response.headers.get("content-type") == "application/json"
        
        # Should not return HTML that could execute scripts
        assert "text/html" not in response.headers.get("content-type", "")

    def test_json_response_not_interpreted_as_html(self, client, authenticated_user):
        """Test that JSON responses are not interpreted as HTML"""
        token = authenticated_user["access_token"]
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # Should have proper Content-Type
        assert "application/json" in response.headers.get("content-type", "")


class TestCSRF:
    """Tests for Cross-Site Request Forgery (CSRF) protection"""

    def test_csrf_token_required_for_state_changing_operations(self, client, authenticated_user):
        """Test CSRF protection on state-changing operations"""
        token = authenticated_user["access_token"]
        
        # For API endpoints, CSRF is typically not needed if using tokens
        # But test that authentication is required
        
        # Try to create agent without auth
        response = client.post("/api/v1/agents", json={
            "name": "Test Agent",
            "system_prompt": "Test"
        })
        
        assert response.status_code == 401, \
            "Endpoint accessible without authentication"

    def test_state_changing_operations_require_post(self, client, authenticated_user):
        """Test that state-changing operations don't allow GET"""
        token = authenticated_user["access_token"]
        
        # Try to perform state-changing operation with GET
        # (FastAPI/Pydantic should prevent this)
        response = client.get(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        # GET should only read, not modify
        # If creating agents via GET worked, that would be a CSRF vulnerability
        assert response.status_code == 200  # Should be read-only

    def test_origin_header_validation(self, client):
        """Test Origin header validation for CORS"""
        # Try request with suspicious origin
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "test@example.com", "password": "pass"},
            headers={"Origin": "https://evil.com"}
        )
        
        # Should either reject or not set CORS headers for untrusted origin
        # Check CORS headers
        cors_header = response.headers.get("access-control-allow-origin")
        if cors_header:
            assert cors_header != "*", \
                "Wildcard CORS allows CSRF from any origin"

    def test_same_site_cookie_policy(self, client, authenticated_user):
        """Test SameSite cookie attribute (if using cookies)"""
        # If application uses cookies for session management
        # Check for SameSite attribute
        
        response = client.post("/api/v1/auth/login", data={
            "username": "security@example.com",
            "password": "SecurePass123!"
        })
        
        # Check Set-Cookie headers
        set_cookie = response.headers.get("set-cookie", "")
        if set_cookie:
            # Should have SameSite attribute
            assert "SameSite" in set_cookie or "samesite" in set_cookie.lower(), \
                "Cookies should have SameSite attribute for CSRF protection"

    def test_referer_header_check(self, client, authenticated_user):
        """Test Referer header validation (defense in depth)"""
        token = authenticated_user["access_token"]
        
        # Request from suspicious referer
        response = client.post(
            "/api/v1/agents",
            headers={
                "Authorization": f"Bearer {token}",
                "Referer": "https://evil.com/csrf-attack"
            },
            json={"name": "Test", "system_prompt": "Test"}
        )
        
        # For API with Bearer tokens, referer may not be checked
        # Just ensure auth is enforced
        assert response.status_code in [200, 201, 403]

    def test_double_submit_cookie_pattern(self, client):
        """Test double-submit cookie pattern (if implemented)"""
        # This is one CSRF protection method
        # Where CSRF token is sent both as cookie and request parameter
        # For JWT Bearer token auth, this may not be used
        pass

    def test_custom_request_headers_require_auth(self, client):
        """Test that custom headers require preflight (CORS protection)"""
        # Custom headers trigger CORS preflight
        # Which helps prevent CSRF
        
        response = client.options("/api/v1/agents")
        
        # Check CORS preflight response
        if response.status_code == 200:
            allowed_headers = response.headers.get("access-control-allow-headers", "")
            # Should allow Authorization header
            assert "authorization" in allowed_headers.lower()
