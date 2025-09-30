"""Unit tests for OrchestratorAgent functionality."""

import uuid
from unittest.mock import MagicMock, Mock, patch

import pytest

from agents.base_agent import BaseAgent
from agents.orchestrator import OrchestratorAgent
from utils.project_state import ProjectPhase, ProjectState, Task, TaskStatus


class TestOrchestratorAgent:
    """Test cases for OrchestratorAgent class."""

    @pytest.fixture
    def orchestrator(self):
        """Create an OrchestratorAgent instance for testing."""
        with patch("agents.orchestrator.get_agent_config") as mock_config:
            mock_config.return_value = {
                "system_prompt": "Test orchestrator prompt",
                "llm_config": {"model": "claude-3-5-sonnet-20241022"},
            }
            with patch("agents.base_agent.AnthropicChatCompletionClient"):
                with patch("agents.base_agent.AssistantAgent"):
                    return OrchestratorAgent()

    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing."""
        agent = Mock(spec=BaseAgent)
        agent.status = "ready"
        agent.current_task = ""
        agent.process_request.return_value = {
            "status": "success",
            "response": "Mock agent response",
        }
        return agent

    def test_orchestrator_initialization(self, orchestrator):
        """Test that orchestrator initializes correctly."""
        assert orchestrator.name == "Orchestrator"
        assert orchestrator.project_states == {}
        assert orchestrator.agent_registry == {}

    def test_register_agent(self, orchestrator, mock_agent):
        """Test agent registration functionality."""
        # Register an agent
        orchestrator.register_agent("TestAgent", mock_agent)

        # Verify agent is registered
        assert "TestAgent" in orchestrator.agent_registry
        assert orchestrator.agent_registry["TestAgent"] == mock_agent

    def test_create_project(self, orchestrator):
        """Test project creation functionality."""
        # Create a project
        project_id = orchestrator.create_project("Test Project", "Test requirements")

        # Verify project is created
        assert project_id in orchestrator.project_states
        project = orchestrator.project_states[project_id]
        assert project.project_name == "Test Project"
        assert project.requirements["raw"] == "Test requirements"

    def test_plan_project_creates_correct_tasks(self, orchestrator):
        """Test that project planning creates the correct task structure."""
        # Create a project first
        project_id = orchestrator.create_project("Test Project", "Test requirements")

        # Plan the project
        tasks = orchestrator.plan_project(project_id)

        # Verify correct number of tasks
        assert len(tasks) == 6

        # Verify task sequence and dependencies
        task_names = [task.name for task in tasks]
        expected_names = [
            "Analyze Requirements",
            "Design Architecture",
            "Implement Backend",
            "Write Tests",
            "Prepare Deployment",
            "Create User Documentation",
        ]
        assert task_names == expected_names

        # Verify agent assignments
        expected_agents = [
            "ProductManager",
            "Architect",
            "BackendDeveloper",
            "QAEngineer",
            "DevOpsEngineer",
            "DocumentationAgent",
        ]
        actual_agents = [task.assigned_to for task in tasks]
        assert actual_agents == expected_agents

        # Verify dependency chain
        assert tasks[0].dependencies == []  # First task has no dependencies
        assert tasks[1].dependencies == [
            tasks[0].id
        ]  # Architecture depends on requirements
        assert tasks[2].dependencies == [tasks[1].id]  # Backend depends on architecture
        assert tasks[3].dependencies == [tasks[2].id]  # Tests depend on backend
        assert tasks[4].dependencies == [tasks[3].id]  # Deployment depends on tests
        assert tasks[5].dependencies == [
            tasks[4].id
        ]  # Documentation depends on deployment

    def test_plan_project_invalid_project_id(self, orchestrator):
        """Test planning with invalid project ID raises error."""
        with pytest.raises(ValueError, match="Project .* not found"):
            orchestrator.plan_project("invalid-id")

    def test_execute_next_tasks_success(self, orchestrator, mock_agent):
        """Test successful task execution."""
        # Setup project with tasks
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.register_agent("ProductManager", mock_agent)
        orchestrator.plan_project(project_id)

        # Execute next tasks
        results = orchestrator.execute_next_tasks(project_id)

        # Verify task execution
        assert len(results) == 1  # Should execute the first ready task
        assert results[0]["status"] == "success"

        # Verify agent status was updated
        assert mock_agent.status == "ready"
        assert mock_agent.current_task == ""

    def test_execute_next_tasks_agent_not_found(self, orchestrator):
        """Test task execution when assigned agent is not registered."""
        # Setup project without registering the required agent
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.plan_project(project_id)

        # Execute next tasks (should fail because ProductManager is not registered)
        results = orchestrator.execute_next_tasks(project_id)

        # Verify no successful results
        assert len(results) == 0

        # Verify task was marked as failed
        project = orchestrator.project_states[project_id]
        first_task = next(iter(project.tasks.values()))
        assert first_task.status == TaskStatus.FAILED

    def test_execute_next_tasks_agent_error(self, orchestrator, mock_agent):
        """Test task execution when agent returns error."""
        # Setup agent to return error
        mock_agent.process_request.return_value = {
            "status": "error",
            "error": "Mock agent error",
        }

        # Setup project
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.register_agent("ProductManager", mock_agent)
        orchestrator.plan_project(project_id)

        # Execute next tasks
        results = orchestrator.execute_next_tasks(project_id)

        # Verify error handling
        assert len(results) == 1
        assert results[0]["status"] == "error"

        # Verify agent status
        assert mock_agent.status == "error"
        assert "Failed: Analyze Requirements" in mock_agent.current_task

    def test_execute_next_tasks_exception_handling(self, orchestrator, mock_agent):
        """Test task execution when agent throws exception."""
        # Setup agent to throw exception
        mock_agent.process_request.side_effect = Exception("Test exception")

        # Setup project
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.register_agent("ProductManager", mock_agent)
        orchestrator.plan_project(project_id)

        # Execute next tasks
        results = orchestrator.execute_next_tasks(project_id)

        # Verify exception handling
        assert len(results) == 1
        assert results[0]["status"] == "error"
        assert "Test exception" in results[0]["error"]

        # Verify agent status
        assert mock_agent.status == "error"
        assert "Error: Test exception" in mock_agent.current_task

    def test_get_project_status(self, orchestrator):
        """Test project status retrieval."""
        # Create and plan project
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.plan_project(project_id)

        # Get status
        status = orchestrator.get_project_status(project_id)

        # Verify status structure
        assert status["project_id"] == project_id
        assert status["project_name"] == "Test Project"
        assert status["phase"] == ProjectPhase.REQUIREMENTS.value
        assert status["total_tasks"] == 6
        assert status["task_summary"]["pending"] == 6
        assert status["task_summary"]["completed"] == 0
        assert status["progress_percentage"] == 0

    def test_get_project_status_invalid_id(self, orchestrator):
        """Test project status with invalid ID raises error."""
        with pytest.raises(ValueError, match="Project .* not found"):
            orchestrator.get_project_status("invalid-id")

    def test_coordinate_agents_success_flow(self, orchestrator, mock_agent):
        """Test complete agent coordination flow."""
        # Setup project and agent
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.register_agent("ProductManager", mock_agent)
        orchestrator.register_agent("Architect", mock_agent)
        orchestrator.register_agent("BackendDeveloper", mock_agent)
        orchestrator.register_agent("QAEngineer", mock_agent)
        orchestrator.register_agent("DevOpsEngineer", mock_agent)
        orchestrator.register_agent("DocumentationAgent", mock_agent)

        orchestrator.plan_project(project_id)

        # Mock successful completion for all tasks
        def mock_success(*args, **kwargs):
            return {"status": "success", "response": "Success"}

        mock_agent.process_request.side_effect = mock_success

        # Coordinate agents
        result = orchestrator.coordinate_agents(project_id)

        # Verify successful completion
        assert result is True

        # Verify project status
        project = orchestrator.project_states[project_id]
        assert project.phase == ProjectPhase.COMPLETED

    def test_coordinate_agents_with_blocked_tasks(self, orchestrator):
        """Test coordination when tasks are blocked."""
        # Create project without any agents registered
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.plan_project(project_id)

        # Coordinate should return False due to blocked tasks
        result = orchestrator.coordinate_agents(project_id)
        assert result is False

    def test_task_context_preparation(self, orchestrator, mock_agent):
        """Test that task context is properly prepared."""
        # Setup project
        project_id = orchestrator.create_project("Test Project", "Test requirements")
        orchestrator.register_agent("ProductManager", mock_agent)
        orchestrator.plan_project(project_id)

        # Execute task and capture the context passed to agent
        orchestrator.execute_next_tasks(project_id)

        # Verify agent was called with correct context
        mock_agent.process_request.assert_called_once()
        args, kwargs = mock_agent.process_request.call_args

        # The first argument should be the task description
        assert "Convert natural language requirements" in args[0]

        # The second argument should be the context
        context = args[1]
        assert context["project_name"] == "Test Project"
        assert context["task_name"] == "Analyze Requirements"
        assert "requirements" in context
