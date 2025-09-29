"""Base agent class for the multi-agent system."""

from typing import Dict, Any, Optional, List
from autogen import AssistantAgent
import logging

logger = logging.getLogger(__name__)


class BaseAgent:
    """Base class for all specialized agents."""

    def __init__(self, name: str, system_prompt: str, llm_config: Dict[str, Any]):
        """Initialize the base agent."""
        self.name = name
        self.agent = AssistantAgent(
            name=name,
            system_message=system_prompt,
            llm_config=llm_config
        )
        self.conversation_history: List[Dict[str, Any]] = []
        logger.info(f"Initialized {name} agent")

    def process_request(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Process a request and return the response."""
        try:
            # Prepare the message with context if provided
            full_message = message
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                full_message = f"Context:\n{context_str}\n\nRequest:\n{message}"

            # This is a simplified response for now
            # In production, this would trigger actual AutoGen conversation
            response = {
                "agent": self.name,
                "status": "success",
                "message": full_message,
                "response": f"Processed by {self.name}"
            }

            self.conversation_history.append({
                "request": message,
                "response": response
            })

            return response

        except Exception as e:
            logger.error(f"Error in {self.name}: {str(e)}")
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