"""Main multi-agent system entry point."""

import logging
import asyncio
import threading
from typing import Dict, Any, Optional
from datetime import datetime
from agents.orchestrator import OrchestratorAgent
from agents.product_manager import ProductManagerAgent
from agents.architect import ArchitectAgent
from agents.backend_developer import BackendDeveloperAgent
from agents.qa_engineer import QAEngineerAgent
from agents.devops_engineer import DevOpsEngineerAgent
from agents.documentation_agent import DocumentationAgent
from utils.project_state import TaskStatus

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

        # Create project and start agent coordination in background
        project_name = requirements.get('project_type', 'web_app')
        project_id = self.orchestrator.create_project(project_name, task_description)

        # Start the development process in a background thread
        def run_development():
            try:
                # Plan tasks
                tasks = self.orchestrator.plan_project(project_id)
                logger.info(f"Created {len(tasks)} tasks for project {project_id}")

                # Execute project with real agent coordination
                success = self.orchestrator.coordinate_agents(project_id)

                if success:
                    logger.info(f"Project {project_id} completed successfully")
                else:
                    logger.error(f"Project {project_id} failed")

            except Exception as e:
                logger.error(f"Error in development process: {e}")

        # Start development in background thread
        development_thread = threading.Thread(target=run_development)
        development_thread.daemon = True
        development_thread.start()

        return {
            "status": "started",
            "project_id": project_id,
            "result": f"Development project '{project_name}' initiated. Agents are now coordinating to complete the request.",
            "agents_involved": list(self.orchestrator.agents.keys())
        }

    async def get_system_status(self):
        """Get the current status of all agents in the system."""
        logger.info("Getting system status")

        # Get real agent statuses from orchestrator
        agent_statuses = []
        for name, agent in self.orchestrator.agent_registry.items():
            status = getattr(agent, 'status', 'ready')
            current_task = getattr(agent, 'current_task', '')

            agent_statuses.append({
                "name": name,
                "status": status,
                "current_task": current_task
            })

        # Determine overall system status
        working_agents = [a for a in agent_statuses if a['status'] == 'working']
        overall_status = "active" if working_agents else "ready"
        current_task = f"{len(working_agents)} agents working" if working_agents else "System ready for development requests"

        return {
            "status": overall_status,
            "agents_active": len(agent_statuses),
            "current_task": current_task,
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