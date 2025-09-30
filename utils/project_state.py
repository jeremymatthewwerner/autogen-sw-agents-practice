"""Project state management for the multi-agent system."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import os


class TaskStatus(Enum):
    """Status of a development task."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectPhase(Enum):
    """Current phase of the project."""

    REQUIREMENTS = "requirements"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    COMPLETED = "completed"


@dataclass
class Task:
    """Represents a development task."""

    id: str
    name: str
    description: str
    assigned_to: str
    status: TaskStatus = TaskStatus.PENDING
    dependencies: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "assigned_to": self.assigned_to,
            "status": self.status.value,
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "output": self.output,
            "error": self.error,
        }


@dataclass
class ProjectState:
    """Manages the state of a software development project."""

    project_id: str
    project_name: str
    requirements: Dict[str, Any] = field(default_factory=dict)
    architecture: Dict[str, Any] = field(default_factory=dict)
    tasks: Dict[str, Task] = field(default_factory=dict)
    phase: ProjectPhase = ProjectPhase.REQUIREMENTS
    artifacts: Dict[str, Any] = field(default_factory=dict)
    quality_metrics: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def add_task(self, task: Task) -> None:
        """Add a task to the project."""
        self.tasks[task.id] = task

    def update_task_status(
        self, task_id: str, status: TaskStatus, output: Optional[Dict[str, Any]] = None
    ) -> None:
        """Update the status of a task."""
        if task_id in self.tasks:
            self.tasks[task_id].status = status
            if output:
                self.tasks[task_id].output = output
            if status == TaskStatus.COMPLETED:
                self.tasks[task_id].completed_at = datetime.now()

    def get_pending_tasks(self) -> List[Task]:
        """Get all pending tasks."""
        return [
            task for task in self.tasks.values() if task.status == TaskStatus.PENDING
        ]

    def get_ready_tasks(self) -> List[Task]:
        """Get tasks that are ready to execute (dependencies satisfied)."""
        ready_tasks = []
        for task in self.get_pending_tasks():
            dependencies_satisfied = all(
                self.tasks.get(dep_id, Task("", "", "", "")).status
                == TaskStatus.COMPLETED
                for dep_id in task.dependencies
            )
            if dependencies_satisfied:
                ready_tasks.append(task)
        return ready_tasks

    def add_artifact(self, name: str, content: Any) -> None:
        """Add an artifact to the project."""
        self.artifacts[name] = {
            "content": content,
            "created_at": datetime.now().isoformat(),
        }

    def update_quality_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update quality metrics."""
        self.quality_metrics.update(metrics)

    def to_dict(self) -> Dict[str, Any]:
        """Convert project state to dictionary."""
        return {
            "project_id": self.project_id,
            "project_name": self.project_name,
            "requirements": self.requirements,
            "architecture": self.architecture,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "phase": self.phase.value,
            "artifacts": self.artifacts,
            "quality_metrics": self.quality_metrics,
            "created_at": self.created_at.isoformat(),
        }

    def save_to_file(self, filepath: str) -> None:
        """Save project state to a JSON file."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, filepath: str) -> "ProjectState":
        """Load project state from a JSON file."""
        with open(filepath, "r") as f:
            data = json.load(f)

        # Reconstruct the project state
        state = cls(
            project_id=data["project_id"],
            project_name=data["project_name"],
            requirements=data["requirements"],
            architecture=data["architecture"],
            phase=ProjectPhase(data["phase"]),
            artifacts=data["artifacts"],
            quality_metrics=data["quality_metrics"],
        )

        # Reconstruct tasks
        for task_id, task_data in data["tasks"].items():
            task = Task(
                id=task_data["id"],
                name=task_data["name"],
                description=task_data["description"],
                assigned_to=task_data["assigned_to"],
                status=TaskStatus(task_data["status"]),
                dependencies=task_data["dependencies"],
                output=task_data.get("output"),
                error=task_data.get("error"),
            )
            state.tasks[task_id] = task

        return state
