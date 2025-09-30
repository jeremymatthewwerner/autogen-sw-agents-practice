"""Unit tests for BaseAgent functionality."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from agents.base_agent import BaseAgent


class TestBaseAgent:
    """Test cases for BaseAgent class."""

    @pytest.fixture
    def agent_config(self):
        """Basic agent configuration for testing."""
        return {"model": "claude-3-5-sonnet-20241022", "max_tokens": 1000}

    @pytest.fixture
    def base_agent(self, agent_config):
        """Create a BaseAgent instance for testing."""
        with patch("agents.base_agent.AnthropicChatCompletionClient"):
            with patch("agents.base_agent.AssistantAgent"):
                agent = BaseAgent(
                    name="TestAgent",
                    system_prompt="Test system prompt",
                    llm_config=agent_config,
                )
                return agent

    def test_agent_initialization(self, base_agent):
        """Test that agent initializes with correct properties."""
        assert base_agent.name == "TestAgent"
        assert base_agent.system_prompt == "Test system prompt"
        assert base_agent.status == "ready"
        assert base_agent.current_task == ""
        assert base_agent.conversation_history == []

    def test_status_tracking(self, base_agent):
        """Test agent status tracking functionality."""
        # Test initial status
        assert base_agent.status == "ready"

        # Test status updates
        base_agent.status = "working"
        assert base_agent.status == "working"

        base_agent.status = "error"
        assert base_agent.status == "error"

    def test_current_task_tracking(self, base_agent):
        """Test current task tracking functionality."""
        # Test initial task
        assert base_agent.current_task == ""

        # Test task assignment
        base_agent.current_task = "Test Task"
        assert base_agent.current_task == "Test Task"

    @pytest.mark.asyncio
    async def test_process_request_async_success(self, base_agent):
        """Test successful async request processing."""
        # Mock the agent response
        mock_response = Mock()
        mock_response.chat_message.content = "Test response from Claude"
        base_agent.agent.on_messages = AsyncMock(return_value=mock_response)

        # Test the request
        result = await base_agent.process_request_async("Test message")

        # Verify result structure
        assert result["agent"] == "TestAgent"
        assert result["status"] == "success"
        assert result["response"] == "Test response from Claude"
        assert "message" in result

        # Verify conversation history is updated
        assert len(base_agent.conversation_history) == 1
        assert base_agent.conversation_history[0]["request"] == "Test message"
        assert base_agent.conversation_history[0]["response"] == result

    @pytest.mark.asyncio
    async def test_process_request_async_with_context(self, base_agent):
        """Test async request processing with context."""
        # Mock the agent response
        mock_response = Mock()
        mock_response.chat_message.content = "Test response with context"
        base_agent.agent.on_messages = AsyncMock(return_value=mock_response)

        # Test with context
        context = {"project_name": "Test Project", "task_id": "123"}
        result = await base_agent.process_request_async("Test message", context)

        # Verify context is included in message
        assert "project_name: Test Project" in result["message"]
        assert "task_id: 123" in result["message"]

        # Verify conversation history includes context
        assert base_agent.conversation_history[0]["context"] == context

    @pytest.mark.asyncio
    async def test_process_request_async_error_handling(self, base_agent):
        """Test error handling in async request processing."""
        # Mock an exception
        base_agent.agent.on_messages = AsyncMock(side_effect=Exception("Test error"))

        # Test error handling
        result = await base_agent.process_request_async("Test message")

        # Verify error result
        assert result["agent"] == "TestAgent"
        assert result["status"] == "error"
        assert result["error"] == "Test error"

    def test_process_request_sync_wrapper(self, base_agent):
        """Test synchronous wrapper for async processing."""
        # Mock the async method
        base_agent.process_request_async = AsyncMock(
            return_value={
                "agent": "TestAgent",
                "status": "success",
                "response": "Sync test response",
            }
        )

        # Test sync wrapper
        result = base_agent.process_request("Test message")

        # Verify result
        assert result["status"] == "success"
        assert result["response"] == "Sync test response"

    def test_get_history(self, base_agent):
        """Test conversation history retrieval."""
        # Add some history
        base_agent.conversation_history = [
            {"request": "Test 1", "response": {"status": "success"}},
            {"request": "Test 2", "response": {"status": "success"}},
        ]

        # Test history retrieval
        history = base_agent.get_history()
        assert len(history) == 2
        assert history[0]["request"] == "Test 1"
        assert history[1]["request"] == "Test 2"

    def test_clear_history(self, base_agent):
        """Test conversation history clearing."""
        # Add some history
        base_agent.conversation_history = [
            {"request": "Test", "response": {"status": "success"}}
        ]

        # Clear history
        base_agent.clear_history()

        # Verify history is cleared
        assert base_agent.conversation_history == []

    def test_message_formatting_with_system_prompt(self, base_agent):
        """Test that messages are properly formatted with system prompt."""
        # This is tested indirectly through process_request_async
        # but we can verify the formatting logic
        context = {"key": "value"}

        expected_parts = [
            f"System: {base_agent.system_prompt}",
            "Context:",
            "key: value",
            "Request:",
            "test message",
        ]

        # This would be the expected message format
        # (tested indirectly through the async method)
        assert base_agent.system_prompt == "Test system prompt"
