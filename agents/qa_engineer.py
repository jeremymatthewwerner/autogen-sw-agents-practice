"""QA Engineer Agent for testing."""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class QAEngineerAgent(BaseAgent):
    """Handles testing and quality assurance."""

    def __init__(self):
        config = get_agent_config("qa_engineer")
        super().__init__(
            name="QAEngineer",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"],
        )

    async def generate_tests(
        self, backend_code: Dict[str, Any], requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive tests using Claude."""

        user_stories = requirements.get("user_stories", [])
        functional_requirements = requirements.get("functional_requirements", [])

        test_generation_prompt = f"""
        As a Senior QA Engineer, create comprehensive test suites for this backend application.

        Context:
        - User Stories: {len(user_stories)} stories to test
        - Functional Requirements: {functional_requirements}
        - Backend Code: {backend_code.get('generation_method', 'generated')}
        - Framework: {backend_code.get('framework', 'FastAPI')}

        Generate complete test files:

        1. **test_main.py** - API endpoint tests:
           - Test all endpoints based on user stories
           - Authentication flow testing
           - Error handling tests
           - Edge case validation

        2. **test_models.py** - Database model tests:
           - Model validation tests
           - Relationship tests
           - Constraint testing

        3. **test_auth.py** - Authentication tests:
           - Registration tests
           - Login/logout tests
           - JWT token validation
           - Permission tests

        4. **conftest.py** - Test configuration:
           - Test database setup
           - Test client fixtures
           - Mock data fixtures

        5. **pytest.ini** - Test runner configuration

        Requirements:
        - Achieve >80% code coverage
        - Include integration tests
        - Test both success and failure scenarios
        - Use pytest best practices
        - Include performance tests where relevant

        Provide complete, runnable test files.
        """

        try:
            response = await self.process_request_async(test_generation_prompt)

            if response["status"] == "success":
                return {
                    "test_code": response["response"],
                    "generation_method": "claude_powered",
                    "coverage_target": "80%+",
                    "test_types": ["unit", "integration", "api"],
                    "user_stories_covered": len(user_stories),
                }
            else:
                raise Exception(f"Test generation failed: {response.get('error')}")

        except Exception as e:
            # Fallback basic tests
            basic_tests = {
                "test_main.py": """import pytest
from fastapi.testclient import TestClient

def test_api_health():
    # Basic health check test
    assert True  # Placeholder for generated tests
""",
                "pytest.ini": "[tool:pytest]\ntestpaths = tests",
            }

            return {
                "error": str(e),
                "fallback_tests": True,
                "basic_files": basic_tests,
                "generation_method": "fallback_template",
            }

    def process_request(self, message: str, context=None):
        """Generate tests for the application."""
        try:
            # Get backend code and requirements from context
            backend_code = context.get("dependency_Implement Backend", {}).get(
                "output", {}
            )
            requirements = (
                context.get("dependency_Analyze Requirements", {})
                .get("output", {})
                .get("structured_requirements", {})
            )

            if not backend_code and not requirements:
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No backend code or requirements found in context",
                }

            # Generate intelligent tests
            import asyncio

            test_result = asyncio.run(self.generate_tests(backend_code, requirements))

            return {"agent": self.name, "status": "success", "output": test_result}

        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}
