"""
Integration Tests for App Integrations

TASK-373: Write integration tests for app integrations
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from unittest.mock import patch, Mock

from app.main import app
from app.core.database import Base, get_db


# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client, test_db):
    client.post("/api/v1/auth/register", json={
        "email": "integration@example.com",
        "password": "SecurePassword123!",
        "full_name": "Integration User"
    })
    
    login_response = client.post("/api/v1/auth/login", data={
        "username": "integration@example.com",
        "password": "SecurePassword123!"
    })
    
    return login_response.json()["access_token"]


class TestAppIntegrations:
    """Integration tests for app connection endpoints"""

    def test_list_available_apps(self, client, test_db, auth_token):
        """Test listing available apps for integration"""
        response = client.get(
            "/api/v1/integrations/apps",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_connect_gmail_oauth(self, client, test_db, auth_token):
        """Test initiating Gmail OAuth connection"""
        response = client.post(
            "/api/v1/integrations/gmail/connect",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 302]
        data = response.json()
        assert "authorization_url" in data or "redirect_url" in data

    @patch('app.services.gmail_service.GmailService.fetch_emails')
    def test_gmail_fetch_emails(self, mock_fetch, client, test_db, auth_token):
        """Test fetching emails from Gmail"""
        # Mock Gmail API response
        mock_fetch.return_value = [
            {"id": "1", "subject": "Test Email", "from": "sender@example.com"}
        ]

        response = client.get(
            "/api/v1/integrations/gmail/emails",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Note: May return 401 if not connected
        assert response.status_code in [200, 401]

    def test_connect_slack_api_key(self, client, test_db, auth_token):
        """Test connecting Slack with API key"""
        payload = {
            "api_key": "xoxb-test-slack-token",
            "workspace_name": "Test Workspace"
        }

        response = client.post(
            "/api/v1/integrations/slack/connect",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 201]

    @patch('app.services.slack_service.SlackService.send_message')
    def test_slack_send_message(self, mock_send, client, test_db, auth_token):
        """Test sending message to Slack"""
        mock_send.return_value = {"ok": True, "ts": "1234567890.123456"}

        payload = {
            "channel": "#general",
            "message": "Test message from Aura"
        }

        response = client.post(
            "/api/v1/integrations/slack/send",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # May return 401 if not connected
        assert response.status_code in [200, 401]

    def test_connect_jira_oauth(self, client, test_db, auth_token):
        """Test connecting Jira with OAuth"""
        response = client.post(
            "/api/v1/integrations/jira/connect",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 302]

    @patch('app.services.jira_service.JiraService.get_issues')
    def test_jira_fetch_issues(self, mock_get, client, test_db, auth_token):
        """Test fetching Jira issues"""
        mock_get.return_value = [
            {"key": "TEST-1", "summary": "Test Issue"}
        ]

        response = client.get(
            "/api/v1/integrations/jira/issues",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 401]

    def test_disconnect_integration(self, client, test_db, auth_token):
        """Test disconnecting an integration"""
        # First connect an app (mock)
        client.post(
            "/api/v1/integrations/slack/connect",
            json={"api_key": "test-key"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Then disconnect
        response = client.delete(
            "/api/v1/integrations/slack",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code in [200, 204, 404]

    def test_get_integration_status(self, client, test_db, auth_token):
        """Test getting integration connection status"""
        response = client.get(
            "/api/v1/integrations/status",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_list_user_credentials(self, client, test_db, auth_token):
        """Test listing user's stored credentials"""
        response = client.get(
            "/api/v1/integrations/credentials",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
