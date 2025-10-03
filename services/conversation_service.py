"""Conversation service for managing project conversations and iterations."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from models.database import Conversation, MessageRole, Project, ProjectStatus
from services.project_service import ProjectService

logger = logging.getLogger(__name__)

# Will be set by cloud_api.py when initializing
_multi_agent_system = None


def set_multi_agent_system(system):
    """Set the multi-agent system instance."""
    global _multi_agent_system
    _multi_agent_system = system


class ConversationService:
    """Handles conversational interactions for project development."""

    def __init__(self, project_service: ProjectService):
        """Initialize conversation service.

        Args:
            project_service: Project service for project operations
        """
        self.project_service = project_service

    async def send_message(
        self, project_id: UUID, user_message: str, session
    ) -> Dict[str, Any]:
        """Send a message in a project conversation.

        This is the main entry point for conversational iteration.
        Analyzes the message, determines intent, and executes appropriate agents.

        Args:
            project_id: Project ID
            user_message: User's message
            session: Database session

        Returns:
            Response with agent output and any changes
        """
        # Load project
        project = session.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project {project_id} not found")

        # Save user message
        user_conv = Conversation(
            project_id=project_id,
            role=MessageRole.USER.value,
            content=user_message,
        )
        session.add(user_conv)
        session.commit()

        # Load conversation history for context
        history = self._get_conversation_history(project_id, session)

        # Determine intent and route to appropriate workflow
        intent = self._analyze_intent(user_message, project, history)

        try:
            if intent["type"] == "create":
                response = await self._handle_creation(project, user_message, session)
            elif intent["type"] == "refine":
                response = await self._handle_refinement(project, user_message, session)
            elif intent["type"] == "deploy":
                response = await self._handle_deployment(project, session)
            elif intent["type"] == "test":
                response = await self._handle_testing(project, session)
            elif intent["type"] == "question":
                response = await self._handle_question(project, user_message, history)
            else:
                response = {
                    "content": f"I understand you want to {intent['type']}, but I'm not sure how to help with that yet.",
                    "metadata": {"intent": intent},
                }

            # Save assistant response
            assistant_conv = Conversation(
                project_id=project_id,
                role=MessageRole.ASSISTANT.value,
                content=response["content"],
                message_metadata=response.get("metadata", {}),
                agent_name=response.get("agent_name"),
            )
            session.add(assistant_conv)
            session.commit()

            return response

        except Exception as e:
            logger.error(f"Error handling message: {e}")
            error_response = {
                "content": f"I encountered an error: {str(e)}",
                "metadata": {"error": str(e)},
            }

            assistant_conv = Conversation(
                project_id=project_id,
                role=MessageRole.ASSISTANT.value,
                content=error_response["content"],
                message_metadata=error_response["metadata"],
            )
            session.add(assistant_conv)
            session.commit()

            raise

    def _get_conversation_history(
        self, project_id: UUID, session, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a project.

        Args:
            project_id: Project ID
            session: Database session
            limit: Maximum messages to retrieve

        Returns:
            List of conversation messages
        """
        conversations = (
            session.query(Conversation)
            .filter(Conversation.project_id == project_id)
            .order_by(Conversation.created_at.desc())
            .limit(limit)
            .all()
        )

        return [
            {
                "role": conv.role,
                "content": conv.content,
                "metadata": conv.message_metadata or {},
                "agent_name": conv.agent_name,
                "created_at": conv.created_at.isoformat(),
            }
            for conv in reversed(conversations)
        ]

    def _analyze_intent(
        self, message: str, project: Project, history: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """Analyze user message to determine intent.

        Args:
            message: User message
            project: Project object
            history: Conversation history

        Returns:
            Intent classification
        """
        message_lower = message.lower()

        # Check for deployment intent
        if any(
            word in message_lower for word in ["deploy", "launch", "publish", "go live"]
        ):
            return {"type": "deploy", "confidence": "high"}

        # Check for testing intent
        if any(
            word in message_lower for word in ["test", "run tests", "check if it works"]
        ):
            return {"type": "test", "confidence": "high"}

        # Check for refinement intent (modification)
        if any(
            word in message_lower
            for word in ["add", "change", "update", "modify", "fix", "remove", "delete"]
        ):
            return {"type": "refine", "confidence": "high"}

        # Check for questions
        if any(
            word in message_lower
            for word in [
                "what",
                "how",
                "why",
                "when",
                "where",
                "?",
                "explain",
                "show me",
            ]
        ):
            return {"type": "question", "confidence": "medium"}

        # If project is new (planning status), treat as creation/refinement
        if project.status == ProjectStatus.PLANNING.value:
            return {"type": "create", "confidence": "medium"}

        # Default to refinement for existing projects
        if project.status in [
            ProjectStatus.IN_PROGRESS.value,
            ProjectStatus.DEPLOYED.value,
        ]:
            return {"type": "refine", "confidence": "low"}

        return {"type": "unknown", "confidence": "low"}

    async def _handle_creation(
        self, project: Project, message: str, session
    ) -> Dict[str, Any]:
        """Handle project creation/initial planning.

        Args:
            project: Project object
            message: User message
            session: Database session

        Returns:
            Response with requirements analysis
        """
        if not _multi_agent_system:
            return {
                "content": f"I'll help you build '{project.name}'. I'm analyzing your requirements:\n\n{message}\n\nLet me create a detailed specification and plan.",
                "metadata": {"phase": "requirements"},
                "agent_name": "ProductManager",
            }

        # Use ProductManager agent to analyze requirements
        try:
            pm_agent = _multi_agent_system.orchestrator.agent_registry.get(
                "ProductManager"
            )
            if pm_agent:
                context = {
                    "project_name": project.name,
                    "user_request": message,
                }
                result = pm_agent.process_request(
                    f"Analyze these requirements and create a structured specification: {message}",
                    context,
                )

                # Update project with requirements
                if result.get("status") == "success" and result.get("output"):
                    project.requirements = {
                        "raw": message,
                        "analyzed": result["output"],
                    }
                    session.commit()

                content = result.get(
                    "output", result.get("response", "Requirements analyzed")
                )
                return {
                    "content": f"I've analyzed your requirements for '{project.name}':\n\n{content}\n\nShall I proceed with creating the architecture design?",
                    "metadata": {"phase": "requirements", "analysis": result},
                    "agent_name": "ProductManager",
                }
            else:
                logger.warning("ProductManager agent not found")
                return {
                    "content": f"I'll help you build '{project.name}'. I'm analyzing your requirements.",
                    "metadata": {"phase": "requirements"},
                    "agent_name": "ProductManager",
                }

        except Exception as e:
            logger.error(f"Error in ProductManager agent: {e}")
            return {
                "content": f"I encountered an error analyzing requirements: {str(e)}",
                "metadata": {"error": str(e)},
                "agent_name": "ProductManager",
            }

    async def _handle_refinement(
        self, project: Project, message: str, session
    ) -> Dict[str, Any]:
        """Handle project refinement/modification.

        Args:
            project: Project object
            message: User message
            session: Database session

        Returns:
            Response with code changes
        """
        # Use BackendDeveloper to make changes
        # This is a placeholder - will integrate with actual agent
        return {
            "content": f"I'll update {project.name} with your requested changes:\n\n{message}\n\nLet me modify the code and run tests.",
            "metadata": {"phase": "implementation", "action": "modify"},
            "agent_name": "BackendDeveloper",
        }

    async def _handle_deployment(self, project: Project, session) -> Dict[str, Any]:
        """Handle project deployment.

        Args:
            project: Project object
            session: Database session

        Returns:
            Response with deployment status
        """
        # Use DevOpsEngineer to deploy
        # This is a placeholder - will integrate with actual agent
        return {
            "content": f"Deploying {project.name} to AWS...\n\nI'll create the necessary infrastructure and deploy your application.",
            "metadata": {"phase": "deployment", "status": "in_progress"},
            "agent_name": "DevOpsEngineer",
        }

    async def _handle_testing(self, project: Project, session) -> Dict[str, Any]:
        """Handle test execution.

        Args:
            project: Project object
            session: Database session

        Returns:
            Response with test results
        """
        # Use QAEngineer to run tests
        # This is a placeholder - will integrate with actual agent
        return {
            "content": f"Running tests for {project.name}...\n\nI'll execute all tests and report the results.",
            "metadata": {"phase": "testing", "status": "running"},
            "agent_name": "QAEngineer",
        }

    async def _handle_question(
        self, project: Project, message: str, history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle user questions about the project.

        Args:
            project: Project object
            message: User message
            history: Conversation history

        Returns:
            Response answering the question
        """
        # Use context from project and history to answer
        return {
            "content": f"Based on {project.name}, here's what I can tell you:\n\n{message}\n\n[Answer based on project context]",
            "metadata": {"type": "answer"},
            "agent_name": "Orchestrator",
        }
