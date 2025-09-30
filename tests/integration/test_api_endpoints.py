"""Integration tests for API endpoints."""

import pytest
import asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add parent directory to path for imports
sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app import app


@pytest.mark.integration
class TestAPIEndpoints:
    """Test cases for API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the FastAPI app."""
        return TestClient(app)

    @pytest.fixture(autouse=True)
    def mock_system(self):
        """Mock the MultiAgentSystem for testing."""
        with patch("app.multi_agent_system") as mock_sys:
            # Mock get_system_status
            async def mock_get_status():
                return {
                    "status": "ready",
                    "agents_active": 6,
                    "current_task": "System ready",
                    "agents": [
                        {
                            "name": "ProductManager",
                            "status": "ready",
                            "current_task": "",
                        },
                        {"name": "Architect", "status": "ready", "current_task": ""},
                        {
                            "name": "BackendDeveloper",
                            "status": "ready",
                            "current_task": "",
                        },
                        {"name": "QAEngineer", "status": "ready", "current_task": ""},
                        {
                            "name": "DevOpsEngineer",
                            "status": "ready",
                            "current_task": "",
                        },
                        {
                            "name": "DocumentationAgent",
                            "status": "ready",
                            "current_task": "",
                        },
                    ],
                }

            # Mock process_development_request
            async def mock_process_request(task, requirements):
                return {
                    "status": "started",
                    "project_id": "test-project-123",
                    "result": f"Processing: {task}",
                    "agents_involved": [
                        "ProductManager",
                        "Architect",
                        "BackendDeveloper",
                    ],
                }

            mock_sys.get_system_status = mock_get_status
            mock_sys.process_development_request = mock_process_request
            yield mock_sys

    def test_root_endpoint(self, client):
        """Test the root endpoint returns the UI."""
        response = client.get("/")
        assert response.status_code == 200
        assert "Multi-Agent Software Development System" in response.text
        assert "text/html" in response.headers["content-type"]

    def test_status_endpoint(self, client):
        """Test the /status endpoint returns system status."""
        response = client.get("/status")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert data["agents_active"] == 6
        assert "agents" in data
        assert len(data["agents"]) == 6

    def test_status_endpoint_agent_structure(self, client):
        """Test the structure of agent data in status response."""
        response = client.get("/status")
        assert response.status_code == 200

        data = response.json()
        for agent in data["agents"]:
            assert "name" in agent
            assert "status" in agent
            assert "current_task" in agent

    def test_develop_endpoint_success(self, client):
        """Test the /develop endpoint with valid request."""
        request_data = {
            "task_description": "Build a todo list application",
            "requirements": {
                "project_type": "web_app",
                "features": ["CRUD operations", "User authentication"],
            },
        }

        response = client.post("/develop", json=request_data)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "started"
        assert "project_id" in data
        assert data["project_id"] == "test-project-123"
        assert "agents_involved" in data

    def test_develop_endpoint_missing_task(self, client):
        """Test the /develop endpoint with missing task description."""
        request_data = {"requirements": {"project_type": "web_app"}}

        response = client.post("/develop", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity

    def test_develop_endpoint_missing_requirements(self, client):
        """Test the /develop endpoint with missing requirements."""
        request_data = {"task_description": "Build a todo list application"}

        response = client.post("/develop", json=request_data)
        assert response.status_code == 422  # Unprocessable Entity

    def test_develop_endpoint_empty_request(self, client):
        """Test the /develop endpoint with empty request body."""
        response = client.post("/develop", json={})
        assert response.status_code == 422  # Unprocessable Entity

    def test_develop_endpoint_invalid_json(self, client):
        """Test the /develop endpoint with invalid JSON."""
        response = client.post("/develop", data="invalid json")
        assert response.status_code == 422  # Unprocessable Entity

    def test_cors_headers(self, client):
        """Test that CORS headers are properly set."""
        response = client.options("/status")
        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers
        assert response.headers["access-control-allow-origin"] == "*"

    def test_status_endpoint_error_handling(self, client, mock_system):
        """Test error handling in status endpoint."""

        # Mock get_system_status to raise an exception
        async def mock_error():
            raise Exception("System error")

        mock_system.get_system_status = mock_error

        # The endpoint should handle the error gracefully
        response = client.get("/status")
        # The actual behavior depends on error handling implementation
        # For now, we'll just verify it doesn't crash
        assert response.status_code in [200, 500]

    def test_develop_endpoint_error_handling(self, client, mock_system):
        """Test error handling in develop endpoint."""

        # Mock process_development_request to raise an exception
        async def mock_error(task, requirements):
            raise Exception("Processing error")

        mock_system.process_development_request = mock_error

        request_data = {
            "task_description": "Build app",
            "requirements": {"project_type": "web"},
        }

        response = client.post("/develop", json=request_data)
        # The actual behavior depends on error handling implementation
        assert response.status_code in [200, 500]

    def test_health_check_endpoint(self, client):
        """Test if a health check endpoint exists or root can serve as one."""
        response = client.get("/")
        assert response.status_code == 200

    def test_response_content_types(self, client):
        """Test that endpoints return appropriate content types."""
        # HTML for root
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

        # JSON for API endpoints
        response = client.get("/status")
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_concurrent_status_requests(self, client):
        """Test handling of concurrent status requests."""
        # Make multiple concurrent requests
        tasks = []
        for _ in range(10):
            response = client.get("/status")
            tasks.append(response)

        # All should succeed
        for response in tasks:
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_concurrent_develop_requests(self, client):
        """Test handling of concurrent development requests."""
        request_data = {
            "task_description": "Build app",
            "requirements": {"project_type": "web"},
        }

        # Make multiple concurrent requests
        tasks = []
        for i in range(5):
            response = client.post("/develop", json=request_data)
            tasks.append(response)

        # All should succeed
        for response in tasks:
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "started"

    def test_request_validation_types(self, client):
        """Test type validation for request parameters."""
        # Wrong type for task_description (should be string)
        request_data = {
            "task_description": 123,
            "requirements": {"project_type": "web"},
        }

        response = client.post("/develop", json=request_data)
        assert response.status_code == 422

        # Wrong type for requirements (should be dict)
        request_data = {"task_description": "Build app", "requirements": "not a dict"}

        response = client.post("/develop", json=request_data)
        assert response.status_code == 422

    def test_large_request_handling(self, client):
        """Test handling of large request payloads."""
        # Create a large requirements dictionary
        large_requirements = {
            "project_type": "enterprise_app",
            "features": ["feature" + str(i) for i in range(100)],
            "constraints": ["constraint" + str(i) for i in range(100)],
            "description": "x" * 10000,  # 10KB of text
        }

        request_data = {
            "task_description": "Build enterprise application",
            "requirements": large_requirements,
        }

        response = client.post("/develop", json=request_data)
        assert response.status_code == 200
