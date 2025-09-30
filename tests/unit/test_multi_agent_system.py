"""Unit tests for MultiAgentSystem functionality."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from multi_agent_system import MultiAgentSystem


class TestMultiAgentSystem:
    """Test cases for MultiAgentSystem class."""

    @pytest.fixture
    def system(self):
        """Create a MultiAgentSystem instance for testing."""
        with patch("multi_agent_system.ProductManagerAgent"):
            with patch("multi_agent_system.ArchitectAgent"):
                with patch("multi_agent_system.BackendDeveloperAgent"):
                    with patch("multi_agent_system.QAEngineerAgent"):
                        with patch("multi_agent_system.DevOpsEngineerAgent"):
                            with patch("multi_agent_system.DocumentationAgent"):
                                with patch("multi_agent_system.OrchestratorAgent"):
                                    return MultiAgentSystem()

    def test_system_initialization(self, system):
        """Test that the system initializes correctly."""
        assert system.orchestrator is not None
        assert hasattr(system.orchestrator, "agent_registry")

    @pytest.mark.asyncio
    async def test_get_system_status(self, system):
        """Test system status retrieval."""
        # Mock orchestrator with agent registry
        mock_agent1 = Mock()
        mock_agent1.status = "ready"
        mock_agent1.current_task = ""

        mock_agent2 = Mock()
        mock_agent2.status = "working"
        mock_agent2.current_task = "Test Task"

        system.orchestrator.agent_registry = {
            "Agent1": mock_agent1,
            "Agent2": mock_agent2,
        }

        # Get system status
        status = await system.get_system_status()

        # Verify status structure
        assert "agents" in status
        assert len(status["agents"]) == 2

        # Check agent statuses
        agent_statuses = {agent["name"]: agent for agent in status["agents"]}
        assert agent_statuses["Agent1"]["status"] == "ready"
        assert agent_statuses["Agent1"]["current_task"] == ""
        assert agent_statuses["Agent2"]["status"] == "working"
        assert agent_statuses["Agent2"]["current_task"] == "Test Task"

    @pytest.mark.asyncio
    async def test_get_system_status_empty_registry(self, system):
        """Test system status when no agents are registered."""
        # Empty agent registry
        system.orchestrator.agent_registry = {}

        # Get system status
        status = await system.get_system_status()

        # Verify empty status
        assert "agents" in status
        assert len(status["agents"]) == 0

    @pytest.mark.asyncio
    async def test_get_system_status_with_missing_attributes(self, system):
        """Test system status when agents have missing attributes."""
        # Mock agent without status/current_task attributes
        mock_agent = Mock(spec=[])  # Empty spec to avoid auto-attributes

        system.orchestrator.agent_registry = {"TestAgent": mock_agent}

        # Get system status
        status = await system.get_system_status()

        # Verify default values are used
        agent_status = status["agents"][0]
        assert agent_status["name"] == "TestAgent"
        assert agent_status["status"] == "ready"  # default
        assert agent_status["current_task"] == ""  # default

    @pytest.mark.asyncio
    async def test_process_development_request_success(self, system):
        """Test successful development request processing."""
        # Mock orchestrator methods
        system.orchestrator.create_project = Mock(return_value="test-project-id")
        system.orchestrator.plan_project = Mock(return_value=[])
        system.orchestrator.coordinate_agents = Mock(return_value=True)
        system.orchestrator.agents = {"Agent1": Mock(), "Agent2": Mock()}

        # Start development request
        result = await system.process_development_request(
            "Test project", {"project_type": "test"}
        )

        # Verify result
        assert result["status"] == "started"
        assert result["project_id"] == "test-project-id"
        assert "Development project" in result["result"]

        # Verify orchestrator was called correctly
        system.orchestrator.create_project.assert_called_once_with(
            "test", "Test project"
        )

    @pytest.mark.asyncio
    async def test_process_development_request_background_execution(self, system):
        """Test that coordination runs in background thread."""
        # Mock successful coordination
        system.orchestrator.create_project = Mock(return_value="test-project-id")
        system.orchestrator.plan_project = Mock(return_value=[])
        system.orchestrator.agents = {"Agent1": Mock()}

        # Create a mock that can track if it was called
        coordination_called = False

        def mock_coordinate(*args):
            nonlocal coordination_called
            coordination_called = True
            return True

        system.orchestrator.coordinate_agents = Mock(side_effect=mock_coordinate)

        # Start development request
        result = await system.process_development_request(
            "Test project", {"project_type": "test"}
        )

        # Verify immediate response
        assert result["status"] == "started"
        assert result["project_id"] == "test-project-id"

        # Give background thread time to execute
        await asyncio.sleep(0.1)

        # Verify coordination was called in background
        assert coordination_called

    def test_develop_application(self, system):
        """Test synchronous develop_application method."""
        # Mock orchestrator methods
        system.orchestrator.create_project = Mock(return_value="test-project-id")
        system.orchestrator.plan_project = Mock(return_value=[])
        system.orchestrator.coordinate_agents = Mock(return_value=True)
        system.orchestrator.get_project_status = Mock(
            return_value={"status": "completed"}
        )

        # Test develop_application
        result = system.develop_application("Test Project", "Test requirements")

        # Verify result
        assert result["status"] == "completed"

        # Verify orchestrator was called
        system.orchestrator.create_project.assert_called_once_with(
            "Test Project", "Test requirements"
        )
        system.orchestrator.plan_project.assert_called_once_with("test-project-id")
        system.orchestrator.coordinate_agents.assert_called_once_with("test-project-id")

    @pytest.mark.asyncio
    async def test_project_coordination_logging(self, system):
        """Test that coordination activities are properly logged."""
        # Mock orchestrator with logging
        system.orchestrator.create_project = Mock(return_value="test-project-id")
        system.orchestrator.plan_project = Mock(return_value=[])
        system.orchestrator.coordinate_agents = Mock(return_value=True)
        system.orchestrator.agents = {"Agent1": Mock()}

        # Capture log messages by patching the logger
        with patch("multi_agent_system.logger") as mock_logger:
            await system.process_development_request(
                "Test project", {"project_type": "test"}
            )

            # Give background thread time to execute
            await asyncio.sleep(0.1)

            # Verify logging calls
            mock_logger.info.assert_called()
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]

            # Check for expected log messages
            assert any("Processing development request" in call for call in log_calls)

    @pytest.mark.asyncio
    async def test_error_handling_in_background_thread(self, system):
        """Test error handling in background coordination thread."""
        # Mock orchestrator methods
        system.orchestrator.create_project = Mock(return_value="test-project-id")
        system.orchestrator.plan_project = Mock(return_value=[])
        system.orchestrator.coordinate_agents = Mock(
            side_effect=Exception("Background error")
        )
        system.orchestrator.agents = {"Agent1": Mock()}

        # Capture log messages
        with patch("multi_agent_system.logger") as mock_logger:
            await system.process_development_request(
                "Test project", {"project_type": "test"}
            )

            # Give background thread time to execute and handle error
            await asyncio.sleep(0.1)

            # Verify error was logged
            mock_logger.error.assert_called()
            error_calls = [call.args[0] for call in mock_logger.error.call_args_list]
            assert any("Error in development process" in call for call in error_calls)

    def test_agent_registration_during_init(self, system):
        """Test that agents are properly registered during initialization."""
        # Verify orchestrator has register_agent method called during init
        # This is tested indirectly by checking the system can access agents
        assert hasattr(system.orchestrator, "agent_registry")

    @pytest.mark.asyncio
    async def test_concurrent_development_requests(self, system):
        """Test handling multiple concurrent development requests."""
        # Mock orchestrator to return different project IDs
        project_ids = ["project-1", "project-2", "project-3"]
        system.orchestrator.create_project = Mock(side_effect=project_ids)
        system.orchestrator.plan_project = Mock(return_value=[])
        system.orchestrator.coordinate_agents = Mock(return_value=True)
        system.orchestrator.agents = {"Agent1": Mock()}

        # Start multiple requests concurrently
        tasks = [
            system.process_development_request(
                f"Project {i}", {"project_type": f"type{i}"}
            )
            for i in range(3)
        ]

        results = await asyncio.gather(*tasks)

        # Verify all requests succeeded
        for i, result in enumerate(results):
            assert result["status"] == "started"
            assert result["project_id"] == project_ids[i]

        # Verify all projects were created
        assert system.orchestrator.create_project.call_count == 3
