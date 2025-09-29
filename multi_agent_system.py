"""Main multi-agent system entry point."""

import logging
from agents.orchestrator import OrchestratorAgent
from agents.product_manager import ProductManagerAgent
from agents.architect import ArchitectAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.qa_engineer import QAEngineerAgent
from agents.devops_engineer import DevOpsEngineerAgent

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
            "DevOpsEngineer": DevOpsEngineerAgent()
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