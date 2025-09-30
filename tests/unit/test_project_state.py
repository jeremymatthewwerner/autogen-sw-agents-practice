"""Unit tests for project state management utilities."""

import pytest
from datetime import datetime
from utils.project_state import ProjectState, Task, TaskStatus, ProjectPhase


class TestTask:
    """Test cases for Task class."""

    def test_task_initialization(self):
        """Test task initialization with required fields."""
        task = Task(
            id="test-id",
            name="Test Task",
            description="Test description",
            assigned_to="TestAgent",
            dependencies=["dep1", "dep2"],
        )

        assert task.id == "test-id"
        assert task.name == "Test Task"
        assert task.description == "Test description"
        assert task.assigned_to == "TestAgent"
        assert task.dependencies == ["dep1", "dep2"]
        assert task.status == TaskStatus.PENDING
        assert task.output is None
        assert isinstance(task.created_at, datetime)
        assert task.completed_at is None

    def test_task_initialization_with_defaults(self):
        """Test task initialization with minimal required fields."""
        task = Task(
            id="test-id",
            name="Test Task",
            description="Test description",
            assigned_to="TestAgent",
        )

        assert task.dependencies == []
        assert task.status == TaskStatus.PENDING

    def test_task_status_enum_values(self):
        """Test that TaskStatus enum has correct values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.IN_PROGRESS.value == "in_progress"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestProjectState:
    """Test cases for ProjectState class."""

    @pytest.fixture
    def project_state(self):
        """Create a ProjectState instance for testing."""
        return ProjectState(
            project_id="test-project-id",
            project_name="Test Project",
            requirements={"raw": "Test requirements"},
        )

    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing."""
        return Task(
            id="task-1",
            name="Test Task",
            description="Test task description",
            assigned_to="TestAgent",
            dependencies=[],
        )

    def test_project_state_initialization(self, project_state):
        """Test project state initialization."""
        assert project_state.project_id == "test-project-id"
        assert project_state.project_name == "Test Project"
        assert project_state.requirements == {"raw": "Test requirements"}
        assert project_state.phase == ProjectPhase.REQUIREMENTS
        assert project_state.tasks == {}
        assert project_state.architecture == {}
        assert isinstance(project_state.created_at, datetime)

    def test_project_phase_enum_values(self):
        """Test that ProjectPhase enum has correct values."""
        assert ProjectPhase.REQUIREMENTS.value == "requirements"
        assert ProjectPhase.DESIGN.value == "design"
        assert ProjectPhase.IMPLEMENTATION.value == "implementation"
        assert ProjectPhase.TESTING.value == "testing"
        assert ProjectPhase.DEPLOYMENT.value == "deployment"
        assert ProjectPhase.COMPLETED.value == "completed"

    def test_add_task(self, project_state, sample_task):
        """Test adding a task to project state."""
        project_state.add_task(sample_task)

        assert sample_task.id in project_state.tasks
        assert project_state.tasks[sample_task.id] == sample_task

    def test_add_multiple_tasks(self, project_state):
        """Test adding multiple tasks to project state."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1")
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2")

        project_state.add_task(task1)
        project_state.add_task(task2)

        assert len(project_state.tasks) == 2
        assert "task-1" in project_state.tasks
        assert "task-2" in project_state.tasks

    def test_update_task_status_basic(self, project_state, sample_task):
        """Test basic task status update."""
        project_state.add_task(sample_task)

        # Update to in progress
        project_state.update_task_status(sample_task.id, TaskStatus.IN_PROGRESS)

        updated_task = project_state.tasks[sample_task.id]
        assert updated_task.status == TaskStatus.IN_PROGRESS

    def test_update_task_status_with_output(self, project_state, sample_task):
        """Test task status update with output."""
        project_state.add_task(sample_task)

        output = {"result": "success", "data": "test output"}
        project_state.update_task_status(sample_task.id, TaskStatus.COMPLETED, output)

        updated_task = project_state.tasks[sample_task.id]
        assert updated_task.status == TaskStatus.COMPLETED
        assert updated_task.output == output
        assert updated_task.completed_at is not None

    def test_update_task_status_invalid_id(self, project_state):
        """Test updating status of non-existent task."""
        # Should not raise an error, just do nothing
        project_state.update_task_status("invalid-id", TaskStatus.COMPLETED)
        assert "invalid-id" not in project_state.tasks

    def test_get_ready_tasks_no_dependencies(self, project_state):
        """Test getting ready tasks when tasks have no dependencies."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", [])

        project_state.add_task(task1)
        project_state.add_task(task2)

        ready_tasks = project_state.get_ready_tasks()

        assert len(ready_tasks) == 2
        assert task1 in ready_tasks
        assert task2 in ready_tasks

    def test_get_ready_tasks_with_dependencies(self, project_state):
        """Test getting ready tasks with dependency chain."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", ["task-1"])
        task3 = Task("task-3", "Task 3", "Description 3", "Agent3", ["task-2"])

        project_state.add_task(task1)
        project_state.add_task(task2)
        project_state.add_task(task3)

        # Initially, only task1 should be ready
        ready_tasks = project_state.get_ready_tasks()
        assert len(ready_tasks) == 1
        assert task1 in ready_tasks

        # Complete task1, now task2 should be ready
        project_state.update_task_status("task-1", TaskStatus.COMPLETED)
        ready_tasks = project_state.get_ready_tasks()
        assert len(ready_tasks) == 1
        assert task2 in ready_tasks

        # Complete task2, now task3 should be ready
        project_state.update_task_status("task-2", TaskStatus.COMPLETED)
        ready_tasks = project_state.get_ready_tasks()
        assert len(ready_tasks) == 1
        assert task3 in ready_tasks

    def test_get_ready_tasks_excludes_in_progress(self, project_state):
        """Test that ready tasks excludes tasks already in progress."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", [])

        project_state.add_task(task1)
        project_state.add_task(task2)

        # Mark task1 as in progress
        project_state.update_task_status("task-1", TaskStatus.IN_PROGRESS)

        ready_tasks = project_state.get_ready_tasks()

        # Only task2 should be ready
        assert len(ready_tasks) == 1
        assert task2 in ready_tasks

    def test_get_ready_tasks_excludes_completed(self, project_state):
        """Test that ready tasks excludes completed tasks."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", [])

        project_state.add_task(task1)
        project_state.add_task(task2)

        # Mark task1 as completed
        project_state.update_task_status("task-1", TaskStatus.COMPLETED)

        ready_tasks = project_state.get_ready_tasks()

        # Only task2 should be ready
        assert len(ready_tasks) == 1
        assert task2 in ready_tasks

    def test_get_ready_tasks_excludes_failed(self, project_state):
        """Test that ready tasks excludes failed tasks."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", [])

        project_state.add_task(task1)
        project_state.add_task(task2)

        # Mark task1 as failed
        project_state.update_task_status("task-1", TaskStatus.FAILED)

        ready_tasks = project_state.get_ready_tasks()

        # Only task2 should be ready
        assert len(ready_tasks) == 1
        assert task2 in ready_tasks

    def test_get_ready_tasks_blocked_by_incomplete_dependencies(self, project_state):
        """Test that tasks are blocked when dependencies are incomplete."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", ["task-1"])

        project_state.add_task(task1)
        project_state.add_task(task2)

        # Mark task1 as in progress (not completed)
        project_state.update_task_status("task-1", TaskStatus.IN_PROGRESS)

        ready_tasks = project_state.get_ready_tasks()

        # No tasks should be ready (task1 is in progress, task2 is blocked)
        assert len(ready_tasks) == 0

    def test_get_ready_tasks_blocked_by_failed_dependencies(self, project_state):
        """Test that tasks are blocked when dependencies failed."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", ["task-1"])

        project_state.add_task(task1)
        project_state.add_task(task2)

        # Mark task1 as failed
        project_state.update_task_status("task-1", TaskStatus.FAILED)

        ready_tasks = project_state.get_ready_tasks()

        # No tasks should be ready (task1 failed, task2 is blocked)
        assert len(ready_tasks) == 0

    def test_get_ready_tasks_multiple_dependencies(self, project_state):
        """Test ready tasks with multiple dependencies."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", [])
        task2 = Task("task-2", "Task 2", "Description 2", "Agent2", [])
        task3 = Task(
            "task-3", "Task 3", "Description 3", "Agent3", ["task-1", "task-2"]
        )

        project_state.add_task(task1)
        project_state.add_task(task2)
        project_state.add_task(task3)

        # Complete task1 but not task2
        project_state.update_task_status("task-1", TaskStatus.COMPLETED)

        ready_tasks = project_state.get_ready_tasks()

        # Only task2 should be ready (task3 still blocked)
        assert len(ready_tasks) == 1
        assert task2 in ready_tasks

        # Complete task2
        project_state.update_task_status("task-2", TaskStatus.COMPLETED)

        ready_tasks = project_state.get_ready_tasks()

        # Now task3 should be ready
        assert len(ready_tasks) == 1
        assert task3 in ready_tasks

    def test_get_ready_tasks_missing_dependency(self, project_state):
        """Test ready tasks when dependency doesn't exist."""
        task1 = Task("task-1", "Task 1", "Description 1", "Agent1", ["non-existent"])

        project_state.add_task(task1)

        ready_tasks = project_state.get_ready_tasks()

        # Task should not be ready due to missing dependency
        assert len(ready_tasks) == 0

    def test_task_timing_tracking(self, project_state, sample_task):
        """Test that task timing is properly tracked."""
        project_state.add_task(sample_task)

        # Initially no timing info
        assert sample_task.completed_at is None

        # Complete task
        project_state.update_task_status(sample_task.id, TaskStatus.COMPLETED)
        assert sample_task.completed_at is not None
