"""QA Engineer Agent for testing."""

import logging
import subprocess
from pathlib import Path
from typing import Any, Dict, Optional

from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config

logger = logging.getLogger(__name__)


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

        IMPORTANT: Format your response with each file clearly marked using this exact format:

        **filename.py**
        ```python
        code here
        ```

        Generate complete test files:

        1. **tests/test_main.py** - API endpoint tests:
           - Test all endpoints based on user stories
           - Authentication flow testing (if auth exists)
           - Error handling tests
           - Edge case validation

        2. **tests/test_models.py** - Database model tests (if models exist):
           - Model validation tests
           - Relationship tests
           - Constraint testing

        3. **tests/conftest.py** - Test configuration:
           - Test database setup
           - Test client fixtures
           - Mock data fixtures

        4. **pytest.ini** - Test runner configuration

        Requirements:
        - Achieve >80% code coverage
        - Include integration tests
        - Test both success and failure scenarios
        - Use pytest best practices
        - Make tests runnable with `pytest` command

        Remember to use the **filename** format before each code block!
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

    def run_tests(self, project_dir: Path) -> Dict[str, Any]:
        """Run pytest on generated test files.

        Args:
            project_dir: Path to the project directory

        Returns:
            Dictionary with test results
        """
        result = {
            "tests_run": False,
            "passed": 0,
            "failed": 0,
            "errors": [],
            "output": "",
        }

        try:
            # Check if tests directory exists
            tests_dir = project_dir / "tests"
            if not tests_dir.exists():
                logger.warning(f"Tests directory not found: {tests_dir}")
                result["errors"].append("No tests directory found")
                return result

            # Run pytest with coverage
            cmd = ["pytest", str(tests_dir), "-v", "--tb=short"]

            logger.info(f"Running tests in {tests_dir}")
            proc = subprocess.run(
                cmd,
                cwd=str(project_dir),
                capture_output=True,
                text=True,
                timeout=60,
            )

            result["tests_run"] = True
            result["output"] = proc.stdout + "\n" + proc.stderr
            result["exit_code"] = proc.returncode

            # Parse pytest output for pass/fail counts
            output_lines = result["output"].split("\n")
            for line in output_lines:
                if "passed" in line.lower() or "failed" in line.lower():
                    # Try to extract test counts
                    import re

                    passed_match = re.search(r"(\d+) passed", line)
                    failed_match = re.search(r"(\d+) failed", line)

                    if passed_match:
                        result["passed"] = int(passed_match.group(1))
                    if failed_match:
                        result["failed"] = int(failed_match.group(1))

            if proc.returncode != 0 and result["failed"] == 0:
                # Tests didn't run properly
                result["errors"].append(f"Test execution failed: {proc.stderr[:200]}")

            logger.info(
                f"Tests completed: {result['passed']} passed, {result['failed']} failed"
            )

        except subprocess.TimeoutExpired:
            result["errors"].append("Test execution timed out after 60 seconds")
            logger.error("Test execution timed out")
        except FileNotFoundError:
            result["errors"].append(
                "pytest not found - install with: pip install pytest"
            )
            logger.error("pytest not found")
        except Exception as e:
            result["errors"].append(f"Error running tests: {str(e)}")
            logger.error(f"Error running tests: {e}")

        return result

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

            # Try to run tests if project directory exists
            project_name = context.get("project_name", "")
            if project_name:
                # Look for generated project directory
                import re

                safe_name = re.sub(r"[^\w\s-]", "", project_name.lower())
                safe_name = re.sub(r"[-\s]+", "_", safe_name)

                # Try to find the project directory
                from pathlib import Path

                projects_dir = Path("projects")
                matching_dirs = list(projects_dir.glob(f"{safe_name}*"))

                if matching_dirs:
                    project_dir = matching_dirs[0]
                    logger.info(f"Running tests in {project_dir}")
                    test_run_result = self.run_tests(project_dir)
                    test_result["test_execution"] = test_run_result

            return {"agent": self.name, "status": "success", "output": test_result}

        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}
