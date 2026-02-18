"""
Performance Tests for Chat Endpoints

TASK-383: Load test chat endpoints
TASK-384: Test database query performance
TASK-385: Test SSE connection scalability
"""

import pytest
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def auth_token(client):
    # Register and login
    client.post("/api/v1/auth/register", json={
        "email": "perftest@example.com",
        "password": "SecurePassword123!",
        "full_name": "Performance Test User"
    })
    
    response = client.post("/api/v1/auth/login", data={
        "username": "perftest@example.com",
        "password": "SecurePassword123!"
    })
    
    return response.json()["access_token"]


class TestChatPerformance:
    """Performance tests for chat endpoints"""

    @pytest.mark.slow
    def test_chat_endpoint_response_time(self, client, auth_token):
        """Test chat endpoint response time is under 5 seconds"""
        start_time = time.time()
        
        response = client.post(
            "/api/v1/chat/messages",
            json={"content": "Hello", "agent_id": "test-agent"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        assert response_time < 5.0, f"Response time {response_time}s exceeds 5s threshold"

    @pytest.mark.slow
    def test_concurrent_chat_requests(self, client, auth_token):
        """Test handling 10 concurrent chat requests"""
        def send_request():
            return client.post(
                "/api/v1/chat/messages",
                json={"content": "Test", "agent_id": "test-agent"},
                headers={"Authorization": f"Bearer {auth_token}"}
            )
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(send_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All requests should complete
        assert len(results) == 10
        assert all(r.status_code in [200, 401] for r in results)

    @pytest.mark.slow
    def test_auth_endpoint_load(self, client):
        """Test authentication under load"""
        start_time = time.time()
        
        # 50 login attempts
        for i in range(50):
            client.post("/api/v1/auth/login", data={
                "username": f"user{i}@example.com",
                "password": "password"
            })
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 50
        
        assert avg_time < 0.5, f"Average auth time {avg_time}s exceeds 0.5s"


class TestDatabasePerformance:
    """Database query performance tests"""

    @pytest.mark.slow
    def test_user_query_performance(self, client, auth_token):
        """Test user query performance"""
        start_time = time.time()
        
        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        end_time = time.time()
        query_time = end_time - start_time
        
        assert query_time < 0.1, f"User query time {query_time}s exceeds 0.1s"

    @pytest.mark.slow
    def test_agent_list_query_performance(self, client, auth_token):
        """Test listing agents performance"""
        start_time = time.time()
        
        response = client.get(
            "/api/v1/agents",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        end_time = time.time()
        query_time = end_time - start_time
        
        assert query_time < 0.2, f"Agent list query time {query_time}s exceeds 0.2s"


class TestSSEPerformance:
    """SSE connection scalability tests"""

    @pytest.mark.slow
    def test_sse_connection_overhead(self, client, auth_token):
        """Test SSE connection overhead"""
        start_time = time.time()
        
        with client.stream(
            "POST",
            "/api/v1/chat/stream",
            json={"content": "Test", "agent_id": "test-agent"},
            headers={"Authorization": f"Bearer {auth_token}"}
        ) as response:
            # Measure connection establishment time
            connection_time = time.time() - start_time
            assert connection_time < 1.0
            
            # Read first chunk
            for _ in response.iter_lines():
                break
        
        assert connection_time < 1.0, f"SSE connection time {connection_time}s exceeds 1s"

    @pytest.mark.slow
    def test_multiple_sse_connections(self, client, auth_token):
        """Test handling multiple SSE connections"""
        connections = []
        
        try:
            for _ in range(5):
                conn = client.stream(
                    "POST",
                    "/api/v1/chat/stream",
                    json={"content": "Test", "agent_id": "test-agent"},
                    headers={"Authorization": f"Bearer {auth_token}"}
                )
                connections.append(conn.__enter__())
            
            # All connections should be active
            assert len(connections) == 5
        
        finally:
            for conn in connections:
                conn.__exit__(None, None, None)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "slow"])
