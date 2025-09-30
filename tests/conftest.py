"""Global test configuration and fixtures."""

import asyncio
import os
from unittest.mock import AsyncMock, Mock

import pytest

from agents.architect import ArchitectAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.devops_engineer import DevOpsEngineerAgent
from agents.documentation_agent import DocumentationAgent
from agents.orchestrator import OrchestratorAgent
from agents.product_manager import ProductManagerAgent
from agents.qa_engineer import QAEngineerAgent
from multi_agent_system import MultiAgentSystem


@pytest.fixture
def mock_anthropic_api():
    """Mock Anthropic API calls for testing."""
    mock = AsyncMock()
    mock.return_value = {
        "agent": "test_agent",
        "status": "success",
        "response": "Test response from Claude",
    }
    return mock


@pytest.fixture
def product_manager_agent(mock_anthropic_api):
    """Create a ProductManager agent with mocked Claude API."""
    agent = ProductManagerAgent()
    agent.process_request_async = mock_anthropic_api
    return agent


@pytest.fixture
def architect_agent(mock_anthropic_api):
    """Create an Architect agent with mocked Claude API."""
    agent = ArchitectAgent()
    agent.process_request_async = mock_anthropic_api
    return agent


@pytest.fixture
def backend_developer_agent(mock_anthropic_api):
    """Create a BackendDeveloper agent with mocked Claude API."""
    agent = BackendDeveloperAgent()
    agent.process_request_async = mock_anthropic_api
    return agent


@pytest.fixture
def qa_engineer_agent(mock_anthropic_api):
    """Create a QAEngineer agent with mocked Claude API."""
    agent = QAEngineerAgent()
    agent.process_request_async = mock_anthropic_api
    return agent


@pytest.fixture
def devops_engineer_agent(mock_anthropic_api):
    """Create a DevOpsEngineer agent with mocked Claude API."""
    agent = DevOpsEngineerAgent()
    agent.process_request_async = mock_anthropic_api
    return agent


@pytest.fixture
def documentation_agent(mock_anthropic_api):
    """Create a DocumentationAgent with mocked Claude API."""
    agent = DocumentationAgent()
    agent.process_request_async = mock_anthropic_api
    return agent


@pytest.fixture
def orchestrator_agent():
    """Create an orchestrator agent for testing."""
    return OrchestratorAgent()


@pytest.fixture
def multi_agent_system(orchestrator_agent):
    """Create a complete multi-agent system for testing."""
    return MultiAgentSystem()


@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return {
        "raw": "Build a simple task management web application",
        "project_type": "web_application",
        "functional_requirements": [
            "User registration and authentication",
            "Create, read, update, delete tasks",
            "Mark tasks as complete/incomplete",
        ],
        "non_functional_requirements": {
            "performance": "Response time < 500ms",
            "security": "User authentication required",
            "scalability": "Support 1000+ concurrent users",
        },
    }


@pytest.fixture
def sample_project_id(orchestrator_agent, sample_requirements):
    """Create a sample project for testing."""
    return orchestrator_agent.create_project("Test Project", sample_requirements["raw"])


@pytest.fixture(autouse=True)
def set_test_environment():
    """Set environment variables for testing."""
    os.environ["ANTHROPIC_API_KEY"] = "test-api-key"
    os.environ["TESTING"] = "true"
    yield
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
