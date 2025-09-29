"""Orchestrator Agent for coordinating the multi-agent system."""

from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import logging

from agents.base_agent import BaseAgent
from utils.project_state import ProjectState, Task, TaskStatus, ProjectPhase
from config.agent_config import get_agent_config

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """Orchestrates and coordinates all other agents."""

    def __init__(self):
        """Initialize the Orchestrator Agent."""
        config = get_agent_config("orchestrator")
        super().__init__(
            name="Orchestrator",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"]
        )
        self.project_states: Dict[str, ProjectState] = {}
        self.agent_registry: Dict[str, BaseAgent] = {}

    def register_agent(self, agent_name: str, agent: BaseAgent) -> None:
        """Register an agent with the orchestrator."""
        self.agent_registry[agent_name] = agent
        logger.info(f"Registered agent: {agent_name}")

    def create_project(self, project_name: str, requirements: str) -> str:
        """Create a new project and return its ID."""
        project_id = str(uuid.uuid4())
        project_state = ProjectState(
            project_id=project_id,
            project_name=project_name,
            requirements={"raw": requirements}
        )
        self.project_states[project_id] = project_state
        logger.info(f"Created project: {project_name} (ID: {project_id})")
        return project_id

    def plan_project(self, project_id: str) -> List[Task]:
        """Create a task plan for the project."""
        if project_id not in self.project_states:
            raise ValueError(f"Project {project_id} not found")

        project = self.project_states[project_id]
        tasks = []

        # Phase 1: Requirements Analysis
        task_id = str(uuid.uuid4())
        tasks.append(Task(
            id=task_id,
            name="Analyze Requirements",
            description="Convert natural language requirements to structured specifications",
            assigned_to="ProductManager",
            dependencies=[]
        ))
        requirements_task_id = task_id

        # Phase 2: System Design
        task_id = str(uuid.uuid4())
        tasks.append(Task(
            id=task_id,
            name="Design Architecture",
            description="Create system architecture and technical design",
            assigned_to="Architect",
            dependencies=[requirements_task_id]
        ))
        architecture_task_id = task_id

        # Phase 3: Implementation
        task_id = str(uuid.uuid4())
        tasks.append(Task(
            id=task_id,
            name="Implement Backend",
            description="Develop backend APIs and business logic",
            assigned_to="BackendDeveloper",
            dependencies=[architecture_task_id]
        ))
        backend_task_id = task_id

        # Phase 4: Testing
        task_id = str(uuid.uuid4())
        tasks.append(Task(
            id=task_id,
            name="Write Tests",
            description="Create unit and integration tests",
            assigned_to="QAEngineer",
            dependencies=[backend_task_id]
        ))
        testing_task_id = task_id

        # Phase 5: Deployment Preparation
        task_id = str(uuid.uuid4())
        tasks.append(Task(
            id=task_id,
            name="Prepare Deployment",
            description="Setup CI/CD and deployment configuration",
            assigned_to="DevOpsEngineer",
            dependencies=[testing_task_id]
        ))

        # Add tasks to project state
        for task in tasks:
            project.add_task(task)

        logger.info(f"Created {len(tasks)} tasks for project {project_id}")
        return tasks

    def execute_next_tasks(self, project_id: str) -> List[Dict[str, Any]]:
        """Execute the next available tasks for a project."""
        if project_id not in self.project_states:
            raise ValueError(f"Project {project_id} not found")

        project = self.project_states[project_id]
        ready_tasks = project.get_ready_tasks()
        results = []

        for task in ready_tasks:
            # Update task status to in progress
            project.update_task_status(task.id, TaskStatus.IN_PROGRESS)

            # Get the assigned agent
            agent = self.agent_registry.get(task.assigned_to)
            if not agent:
                logger.error(f"Agent {task.assigned_to} not found")
                project.update_task_status(task.id, TaskStatus.FAILED)
                continue

            try:
                # Execute the task
                logger.info(f"Executing task: {task.name} with {task.assigned_to}")

                # Prepare context for the agent
                context = {
                    "project_name": project.project_name,
                    "task_name": task.name,
                    "requirements": project.requirements,
                    "architecture": project.architecture
                }

                # Get outputs from dependent tasks
                for dep_id in task.dependencies:
                    dep_task = project.tasks.get(dep_id)
                    if dep_task and dep_task.output:
                        context[f"dependency_{dep_task.name}"] = dep_task.output

                # Execute the task
                result = agent.process_request(task.description, context)

                if result["status"] == "success":
                    project.update_task_status(task.id, TaskStatus.COMPLETED, result)
                    logger.info(f"Task completed: {task.name}")
                else:
                    project.update_task_status(task.id, TaskStatus.FAILED)
                    logger.error(f"Task failed: {task.name}")

                results.append(result)

            except Exception as e:
                logger.error(f"Error executing task {task.name}: {str(e)}")
                project.update_task_status(task.id, TaskStatus.FAILED)
                results.append({
                    "agent": task.assigned_to,
                    "task": task.name,
                    "status": "error",
                    "error": str(e)
                })

        return results

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get the current status of a project."""
        if project_id not in self.project_states:
            raise ValueError(f"Project {project_id} not found")

        project = self.project_states[project_id]

        # Count task statuses
        status_counts = {
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "failed": 0
        }

        for task in project.tasks.values():
            status_counts[task.status.value] += 1

        return {
            "project_id": project.project_id,
            "project_name": project.project_name,
            "phase": project.phase.value,
            "task_summary": status_counts,
            "total_tasks": len(project.tasks),
            "progress_percentage": (status_counts["completed"] / len(project.tasks) * 100) if project.tasks else 0
        }

    def coordinate_agents(self, project_id: str) -> bool:
        """Main coordination loop for a project."""
        if project_id not in self.project_states:
            raise ValueError(f"Project {project_id} not found")

        project = self.project_states[project_id]

        # Continue executing tasks until all are complete or failed
        while True:
            ready_tasks = project.get_ready_tasks()

            if not ready_tasks:
                # Check if all tasks are complete
                all_complete = all(
                    task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED]
                    for task in project.tasks.values()
                )

                if all_complete:
                    logger.info(f"Project {project_id} completed")
                    project.phase = ProjectPhase.COMPLETED
                    return True
                else:
                    # Some tasks might be blocked
                    logger.warning(f"Project {project_id} has blocked tasks")
                    return False

            # Execute next batch of tasks
            results = self.execute_next_tasks(project_id)

            # Check for critical failures
            if any(r["status"] == "error" for r in results):
                logger.error(f"Critical error in project {project_id}")
                return False

        return True