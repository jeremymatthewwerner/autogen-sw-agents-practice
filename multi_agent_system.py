"""Main multi-agent system entry point."""

import logging
from agents.orchestrator import OrchestratorAgent
from agents.product_manager import ProductManagerAgent
from agents.architect import ArchitectAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.qa_engineer import QAEngineerAgent
from agents.devops_engineer import DevOpsEngineerAgent
from agents.documentation_agent import DocumentationAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiAgentSystem:
    """Main system coordinator."""

    def __init__(self):
        """Initialize the multi-agent system."""
        self.orchestrator = OrchestratorAgent()

        # Initialize and register agents
        agents = {
            "ProductManager": ProductManagerAgent(),
            "Architect": ArchitectAgent(),
            "BackendDeveloper": BackendDeveloperAgent(),
            "QAEngineer": QAEngineerAgent(),
            "DevOpsEngineer": DevOpsEngineerAgent(),
            "DocumentationAgent": DocumentationAgent()
        }

        for name, agent in agents.items():
            self.orchestrator.register_agent(name, agent)

        logger.info("Multi-agent system initialized")

    def develop_application(self, project_name: str, requirements: str):
        """Develop an application from requirements."""
        logger.info(f"Starting development of {project_name}")

        # Create project
        project_id = self.orchestrator.create_project(project_name, requirements)

        # Plan tasks
        tasks = self.orchestrator.plan_project(project_id)
        logger.info(f"Created {len(tasks)} tasks")

        # Execute project
        success = self.orchestrator.coordinate_agents(project_id)

        if success:
            logger.info("Project completed successfully")
            return self.orchestrator.get_project_status(project_id)
        else:
            logger.error("Project failed")
            return None

    async def process_development_request(self, task_description: str, requirements: dict):
        """Process a development request from the API."""
        logger.info(f"Processing development request: {task_description}")

        # Use the existing development method
        result = self.develop_application(
            project_name=requirements.get('project_type', 'web_app'),
            requirements=task_description
        )

        return {
            "status": "completed",
            "result": result or "Development process completed",
            "agents_involved": list(self.orchestrator.agents.keys()) if hasattr(self.orchestrator, 'agents') else []
        }

    async def get_system_status(self):
        """Get the current status of all agents in the system."""
        logger.info("Getting system status")

        # Mock agent statuses for now - in a real system these would be dynamic
        agent_statuses = [
            {"name": "Product Manager", "status": "ready", "current_task": "Planning features"},
            {"name": "Architect", "status": "idle", "current_task": ""},
            {"name": "Backend Developer", "status": "working", "current_task": "Building API"},
            {"name": "QA Engineer", "status": "ready", "current_task": "Test planning"},
            {"name": "DevOps Engineer", "status": "working", "current_task": "AWS deployment"},
            {"name": "Documentation Agent", "status": "ready", "current_task": "Writing docs"}
        ]

        return {
            "status": "active",
            "agents_active": len(agent_statuses),
            "current_task": "System ready for development requests",
            "agents": agent_statuses
        }


def main():
    """Demo of the multi-agent system."""
    system = MultiAgentSystem()

    requirements = """
    Build a simple task management web application where users can:
    - Register and login
    - Create, read, update, and delete tasks
    - Mark tasks as complete
    - View all their tasks in a list
    """

    result = system.develop_application("Task Manager", requirements)
    print(f"Result: {result}")


if __name__ == "__main__":
    main()