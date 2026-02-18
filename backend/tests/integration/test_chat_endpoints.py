"""
Integration Tests for Chat Endpoints

TASK-372: Write integration tests for chat endpoints
"""

import pytest
import json
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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


@pytest.fixture
def auth_token(client, test_db):
    """Get authentication token for testing"""
    # Register user
    register_response = client.post("/api/v1/auth/register", json={
        "email": "chatuser@example.com",
        "password": "SecurePassword123!",
        "full_name": "Chat User"
    })
    
    # Login
    login_response = client.post("/api/v1/auth/login", data={
        "username": "chatuser@example.com",
        "password": "SecurePassword123!"
    })
    
    return login_response.json()["access_token"]


class TestChatEndpoints:
    """Integration tests for chat endpoints"""

    def test_create_agent_success(self, client, test_db, auth_token):
        """Test creating a new agent"""
        # Arrange
        payload = {
            "name": "Test Agent",
            "description": "A test agent for testing",
            "system_prompt": "You are a helpful assistant.",
            "model": "gpt-4"
        }

        # Act
        response = client.post(
            "/api/v1/agents",
            json=payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == payload["name"]
        assert data["description"] == payload["description"]
        assert "id" in data

    def test_create_agent_unauthorized(self, client, test_db):
        """Test creating agent without authentication"""
        # Arrange
        payload = {
            "name": "Test Agent",
            "system_prompt": "You are helpful."
        }

        # Act
        response = client.post("/api/v1/agents", json=payload)

        # Assert
        assert response.status_code == 401

    def test_list_agents(self, client, test_db, auth_token):
        """Test listing user's agents"""
        # Arrange - Create multiple agents
        for i in range(3):
            client.post(
                "/api/v1/agents",
                json={
                    "name": f"Agent {i}",
                    "system_prompt": f"Prompt {i}"
                },
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        # Act
        response = client.get(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3

    def test_get_agent_by_id(self, client, test_db, auth_token):
        """Test getting specific agent by ID"""
        # Arrange - Create agent
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Specific Agent", "system_prompt": "Helpful"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        # Act
        response = client.get(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
        assert data["name"] == "Specific Agent"

    def test_get_agent_not_found(self, client, test_db, auth_token):
        """Test getting non-existent agent"""
        # Act
        response = client.get(
            "/api/v1/agents/nonexistent-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 404

    def test_update_agent(self, client, test_db, auth_token):
        """Test updating agent"""
        # Arrange - Create agent
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Original Name", "system_prompt": "Original"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        # Act - Update agent
        update_payload = {
            "name": "Updated Name",
            "description": "Updated description"
        }
        response = client.patch(
            f"/api/v1/agents/{agent_id}",
            json=update_payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    def test_delete_agent(self, client, test_db, auth_token):
        """Test deleting agent"""
        # Arrange - Create agent
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Agent to Delete", "system_prompt": "Delete me"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        # Act
        response = client.delete(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 204

        # Verify agent is deleted
        get_response = client.get(
            f"/api/v1/agents/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert get_response.status_code == 404

    def test_send_message_to_agent(self, client, test_db, auth_token):
        """Test sending message to agent"""
        # Arrange - Create agent
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Chat Agent", "system_prompt": "You are helpful."},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        # Act
        message_payload = {
            "content": "Hello, agent!",
            "agent_id": agent_id
        }
        response = client.post(
            "/api/v1/chat/messages",
            json=message_payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "message" in data

    def test_get_chat_history(self, client, test_db, auth_token):
        """Test retrieving chat history"""
        # Arrange - Create agent and send messages
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "History Agent", "system_prompt": "Track history"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        # Send multiple messages
        for i in range(3):
            client.post(
                "/api/v1/chat/messages",
                json={"content": f"Message {i}", "agent_id": agent_id},
                headers={"Authorization": f"Bearer {auth_token}"}
            )

        # Act
        response = client.get(
            f"/api/v1/chat/history/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 3

    def test_stream_chat_response(self, client, test_db, auth_token):
        """Test streaming chat response"""
        # Arrange - Create agent
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Stream Agent", "system_prompt": "Stream responses"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        # Act
        message_payload = {
            "content": "Stream this response",
            "agent_id": agent_id,
            "stream": True
        }
        
        with client.stream(
            "POST",
            "/api/v1/chat/stream",
            json=message_payload,
            headers={"Authorization": f"Bearer {auth_token}"}
        ) as response:
            # Assert
            assert response.status_code == 200
            assert response.headers["content-type"] == "text/event-stream"
            
            # Read stream chunks
            chunks = []
            for line in response.iter_lines():
                if line:
                    chunks.append(line)
            
            assert len(chunks) > 0

    def test_chat_with_tools(self, client, test_db, auth_token):
        """Test chat with tool usage"""
        # Arrange - Create agent with tools
        create_response = client.post(
            "/api/v1/agents",
            json={
                "name": "Tool Agent",
                "system_prompt": "Use tools to help",
                "tools": ["calculator", "search"]
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        # Act
        response = client.post(
            "/api/v1/chat/messages",
            json={
                "content": "Calculate 2 + 2",
                "agent_id": agent_id
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "response" in data or "tool_calls" in data

    def test_delete_chat_history(self, client, test_db, auth_token):
        """Test deleting chat history"""
        # Arrange - Create agent and chat
        create_response = client.post(
            "/api/v1/agents",
            json={"name": "Delete Chat Agent", "system_prompt": "Chat"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        agent_id = create_response.json()["id"]

        client.post(
            "/api/v1/chat/messages",
            json={"content": "Test message", "agent_id": agent_id},
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Act
        response = client.delete(
            f"/api/v1/chat/history/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        # Assert
        assert response.status_code == 204

        # Verify history is empty
        history_response = client.get(
            f"/api/v1/chat/history/{agent_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert len(history_response.json()) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
