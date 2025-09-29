"""Base agent class for the multi-agent system."""

from typing import Dict, Any, Optional, List
from autogen_ext.models.anthropic import AnthropicChatCompletionClient
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from dotenv import load_dotenv
import asyncio
import logging
import os

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all specialized agents using Claude integration."""

    def __init__(self, name: str, system_prompt: str, llm_config: Dict[str, Any]):
        """Initialize the base agent with Claude client."""
        self.name = name

        # Create Claude model client using existing pattern
        self.model_client = AnthropicChatCompletionClient(
            model=llm_config.get("model", "claude-3-5-sonnet-20241022"),
            api_key=os.getenv("ANTHROPIC_API_KEY")
        )

        # Create assistant agent with Claude client
        self.agent = AssistantAgent(
            name=name,
            model_client=self.model_client,
            description=system_prompt
        )

        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, Any]] = []
        logger.info(f"Initialized {name} agent with Claude integration")

    async def process_request_async(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a request asynchronously and return the response."""
        try:
            # Prepare the message with context if provided
            full_message = f"System: {self.system_prompt}\n\n"

            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                full_message += f"Context:\n{context_str}\n\n"

            full_message += f"Request:\n{message}"

            # Send message to Claude via AutoGen
            response = await self.agent.on_messages(
                [TextMessage(content=full_message, source="user")],
                CancellationToken()
            )

            result = {
                "agent": self.name,
                "status": "success",
                "message": full_message,
                "response": response.chat_message.content
            }

            self.conversation_history.append({
                "request": message,
                "context": context,
                "response": result
            })

            return result

        except Exception as e:
            logger.error(f"Error in {self.name}: {str(e)}")
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e)
            }

    def process_request(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Synchronous wrapper for process_request_async."""
        try:
            return asyncio.run(self.process_request_async(message, context))
        except Exception as e:
            logger.error(f"Error in sync wrapper for {self.name}: {str(e)}")
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e)
            }

    def get_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history."""
        return self.conversation_history

    def clear_history(self) -> None:
        """Clear the conversation history."""
        self.conversation_history = []