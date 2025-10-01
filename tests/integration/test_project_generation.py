"""Integration tests for end-to-end project generation."""

import shutil
import tempfile
from pathlib import Path

import pytest

from agents.architect import ArchitectAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.orchestrator import OrchestratorAgent
from agents.product_manager import ProductManagerAgent
from agents.qa_engineer import QAEngineerAgent
from utils.code_generator import CodeGenerator


@pytest.mark.integration
class TestProjectGeneration:
    """Test suite for complete project generation workflow."""

    @pytest.fixture
    def temp_projects_dir(self):
        """Create a temporary projects directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture
    def orchestrator(self, temp_projects_dir):
        """Create orchestrator with temp projects directory."""
        orch = OrchestratorAgent()
        # Override the code generator to use temp directory
        orch.code_generator = CodeGenerator(base_output_dir=temp_projects_dir)
        return orch

    def test_simple_api_generation(self, orchestrator, temp_projects_dir):
        """Test generating a simple API project structure."""
        # Don't actually execute agents (requires API key), just test the structure

        # Create a simple project
        requirements = "Build a simple REST API with a health check endpoint"
        project_id = orchestrator.create_project("Simple API", requirements)

        # Plan the project (creates tasks)
        tasks = orchestrator.plan_project(project_id)

        assert (
            len(tasks) == 6
        )  # Should create 6 tasks (PM, Arch, Backend, QA, DevOps, Docs)

        # Verify task structure
        project = orchestrator.project_states[project_id]
        assert project.project_id == project_id
        assert project.project_name == "Simple API"

        # Check that tasks have proper dependencies
        task_names = [t.name for t in tasks]
        assert "Analyze Requirements" in task_names
        assert "Design Architecture" in task_names
        assert "Implement Backend" in task_names

    def test_code_generator_integration(self, temp_projects_dir):
        """Test that CodeGenerator can handle agent outputs."""
        code_gen = CodeGenerator(base_output_dir=temp_projects_dir)

        # Simulate backend developer output
        agent_outputs = {
            "BackendDeveloper": {
                "generated_code": """
                **main.py**
                ```python
                from fastapi import FastAPI

                app = FastAPI()

                @app.get("/")
                def read_root():
                    return {"message": "Hello World"}

                @app.get("/health")
                def health():
                    return {"status": "healthy"}
                ```

                **requirements.txt**
                ```
                fastapi==0.104.1
                uvicorn[standard]==0.24.0
                ```
                """
            }
        }

        result = code_gen.generate_project_from_agent_output(
            "test-123", "API Project", agent_outputs
        )

        assert result["success"]
        assert result["files_generated"] >= 2

        # Verify files exist
        project_dir = Path(result["project_dir"])
        assert project_dir.exists()
        assert (project_dir / "main.py").exists()
        assert (project_dir / "requirements.txt").exists()

        # Verify file content
        main_content = (project_dir / "main.py").read_text()
        assert "FastAPI" in main_content
        assert "def read_root" in main_content

        requirements_content = (project_dir / "requirements.txt").read_text()
        assert "fastapi" in requirements_content

    def test_multiple_agent_outputs(self, temp_projects_dir):
        """Test handling outputs from multiple agents."""
        code_gen = CodeGenerator(base_output_dir=temp_projects_dir)

        agent_outputs = {
            "BackendDeveloper": {
                "response": """
                **main.py**
                ```python
                print("Backend code")
                ```
                """
            },
            "QAEngineer": {
                "response": """
                **tests/test_main.py**
                ```python
                def test_example():
                    assert True
                ```
                """
            },
        }

        result = code_gen.generate_project_from_agent_output(
            "test-456", "Multi Agent Project", agent_outputs
        )

        assert result["success"]
        assert result["files_generated"] >= 2

        project_dir = Path(result["project_dir"])
        assert (project_dir / "main.py").exists()
        assert (project_dir / "tests" / "test_main.py").exists()

    def test_project_state_persistence(self, orchestrator, temp_projects_dir):
        """Test that project state is saved and can be loaded."""
        # Create a project
        project_id = orchestrator.create_project("Test Project", "Build an API")

        # Add a task so there's something in the state
        from utils.project_state import Task

        task = Task(
            id="test-123",
            name="Test Task",
            description="Test",
            assigned_to="ProductManager",
        )
        project = orchestrator.project_states[project_id]
        project.add_task(task)

        # Save state manually
        orchestrator._save_project_state(project_id)

        # Verify state file exists (saved to temp_projects_dir)
        state_file = (
            Path(temp_projects_dir) / f"test_project_{project_id[:8]}/state.json"
        )
        assert state_file.exists()

        # Create new orchestrator and load state
        new_orchestrator = OrchestratorAgent()
        new_orchestrator.code_generator = CodeGenerator(
            base_output_dir=temp_projects_dir
        )
        loaded_project_id = new_orchestrator.load_project_state(str(state_file))

        assert loaded_project_id == project_id
        assert (
            new_orchestrator.project_states[project_id].project_name == "Test Project"
        )

    def test_generated_files_artifact(self, orchestrator, temp_projects_dir):
        """Test that generated files are stored as artifacts."""
        orchestrator.register_agent("ProductManager", ProductManagerAgent())
        orchestrator.register_agent("BackendDeveloper", BackendDeveloperAgent())

        # Create simple mock backend output
        project_id = orchestrator.create_project("Artifact Test", "Simple API")

        # Manually add a completed backend task with mock output
        from utils.project_state import Task, TaskStatus

        task = Task(
            id="test-task-123",
            name="Generate Backend",
            description="Generate code",
            assigned_to="BackendDeveloper",
            status=TaskStatus.COMPLETED,
            output={
                "generated_code": """
                **main.py**
                ```python
                print("test")
                ```
                """
            },
        )

        project = orchestrator.project_states[project_id]
        project.add_task(task)
        project.update_task_status(task.id, TaskStatus.COMPLETED, task.output)

        # Manually trigger code generation
        gen_result = orchestrator.code_generator.generate_project_from_agent_output(
            project_id, project.project_name, {"BackendDeveloper": task.output}
        )

        # Add artifact
        project.add_artifact("generated_files", gen_result)

        # Verify artifact exists
        assert "generated_files" in project.artifacts
        assert project.artifacts["generated_files"]["content"]["success"]
        assert project.artifacts["generated_files"]["content"]["files_generated"] >= 1


@pytest.mark.slow
@pytest.mark.integration
class TestRealAgentGeneration:
    """Tests that actually call Claude API (requires ANTHROPIC_API_KEY)."""

    @pytest.fixture
    def temp_projects_dir(self):
        """Create a temporary projects directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.mark.skip(
        reason="Requires Claude API key and makes real API calls - run manually"
    )
    @pytest.mark.asyncio
    async def test_full_backend_generation_with_claude(self, temp_projects_dir):
        """Test actual code generation with Claude (skipped by default)."""
        backend_agent = BackendDeveloperAgent()

        requirements = {
            "project_type": "REST API",
            "user_stories": [
                {"title": "Health Check", "description": "API has health endpoint"}
            ],
            "functional_requirements": ["Health check endpoint"],
        }

        architecture = {"architecture_analysis": "Simple FastAPI application"}

        result = await backend_agent.generate_backend_code(architecture, requirements)

        assert "generated_code" in result or "basic_files" in result

        # Try to extract and write code
        code_gen = CodeGenerator(base_output_dir=temp_projects_dir)
        gen_result = code_gen.generate_project_from_agent_output(
            "test-real", "Real Project", {"BackendDeveloper": result}
        )

        assert gen_result["files_generated"] > 0
