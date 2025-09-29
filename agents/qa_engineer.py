"""QA Engineer Agent for testing."""

from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class QAEngineerAgent(BaseAgent):
    """Handles testing and quality assurance."""

    def __init__(self):
        config = get_agent_config("qa_engineer")
        super().__init__(
            name="QAEngineer",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"]
        )

    def process_request(self, message: str, context=None):
        """Generate tests for the application."""
        test_files = {
            "test_main.py": """import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "API is running"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
""",
            "pytest.ini": """[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
"""
        }

        return {
            "agent": self.name,
            "status": "success",
            "output": {"test_files": test_files}
        }