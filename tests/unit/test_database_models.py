"""Tests for database models."""

import pytest
from datetime import datetime
from uuid import uuid4

from models.database import (
    Database,
    Project,
    Conversation,
    Artifact,
    Deployment,
    ProjectStatus,
    MessageRole,
)


@pytest.fixture
def test_db():
    """Create test database."""
    db = Database("sqlite:///:memory:")
    db.create_all()
    session = db.get_session()
    yield session
    session.close()


class TestProject:
    """Test Project model."""

    def test_project_creation(self, test_db):
        """Test creating a project."""
        project = Project(
            name="Test Project",
            description="Test Description",
            status=ProjectStatus.PLANNING.value
        )
        test_db.add(project)
        test_db.commit()

        assert project.id is not None
        assert project.name == "Test Project"
        assert project.status == ProjectStatus.PLANNING.value
        assert project.created_at is not None

    def test_project_with_requirements(self, test_db):
        """Test project with JSON requirements."""
        project = Project(
            name="API Project",
            requirements={"features": ["auth", "crud"], "stack": "fastapi"}
        )
        test_db.add(project)
        test_db.commit()

        retrieved = test_db.query(Project).filter(Project.id == project.id).first()
        assert retrieved.requirements["features"] == ["auth", "crud"]
        assert retrieved.requirements["stack"] == "fastapi"


class TestConversation:
    """Test Conversation model."""

    def test_conversation_creation(self, test_db):
        """Test creating a conversation message."""
        project = Project(name="Test Project")
        test_db.add(project)
        test_db.commit()

        conversation = Conversation(
            project_id=project.id,
            role=MessageRole.USER.value,
            content="Build me an API",
            message_metadata={"intent": "create"}
        )
        test_db.add(conversation)
        test_db.commit()

        assert conversation.id is not None
        assert conversation.role == "user"
        assert conversation.content == "Build me an API"
        assert conversation.message_metadata["intent"] == "create"

    def test_conversation_relationship(self, test_db):
        """Test conversation-project relationship."""
        project = Project(name="Test Project")
        test_db.add(project)
        test_db.commit()

        conv1 = Conversation(
            project_id=project.id,
            role="user",
            content="Message 1"
        )
        conv2 = Conversation(
            project_id=project.id,
            role="assistant",
            content="Response 1"
        )
        test_db.add_all([conv1, conv2])
        test_db.commit()

        retrieved_project = test_db.query(Project).filter(Project.id == project.id).first()
        assert len(retrieved_project.conversations) == 2


class TestArtifact:
    """Test Artifact model."""

    def test_artifact_creation(self, test_db):
        """Test creating an artifact."""
        project = Project(name="Test Project")
        test_db.add(project)
        test_db.commit()

        artifact = Artifact(
            project_id=project.id,
            type="code",
            path="main.py",
            content="print('hello')",
            version=1
        )
        test_db.add(artifact)
        test_db.commit()

        assert artifact.id is not None
        assert artifact.type == "code"
        assert artifact.path == "main.py"
        assert artifact.version == 1

    def test_artifact_versioning(self, test_db):
        """Test artifact version increments."""
        project = Project(name="Test Project")
        test_db.add(project)
        test_db.commit()

        artifact = Artifact(
            project_id=project.id,
            type="code",
            path="main.py",
            content="v1",
            version=1
        )
        test_db.add(artifact)
        test_db.commit()

        # Simulate update
        artifact.content = "v2"
        artifact.version = 2
        test_db.commit()

        assert artifact.version == 2
        assert artifact.content == "v2"


class TestDeployment:
    """Test Deployment model."""

    def test_deployment_creation(self, test_db):
        """Test creating a deployment record."""
        project = Project(name="Test Project")
        test_db.add(project)
        test_db.commit()

        deployment = Deployment(
            project_id=project.id,
            environment="dev",
            status="deployed",
            deployment_url="http://example.com",
            cloud_provider="aws",
            resource_ids={"ecs_task": "task-123"}
        )
        test_db.add(deployment)
        test_db.commit()

        assert deployment.id is not None
        assert deployment.environment == "dev"
        assert deployment.cloud_provider == "aws"
        assert deployment.resource_ids["ecs_task"] == "task-123"

    def test_deployment_relationship(self, test_db):
        """Test deployment-project relationship."""
        project = Project(name="Test Project")
        test_db.add(project)
        test_db.commit()

        deployment = Deployment(
            project_id=project.id,
            environment="dev",
            status="deployed"
        )
        test_db.add(deployment)
        test_db.commit()

        retrieved_project = test_db.query(Project).filter(Project.id == project.id).first()
        assert len(retrieved_project.deployments) == 1
        assert retrieved_project.deployments[0].environment == "dev"


class TestDatabaseOperations:
    """Test database operations."""

    def test_cascade_delete(self, test_db):
        """Test that deleting project deletes related data."""
        project = Project(name="Test Project")
        test_db.add(project)
        test_db.commit()

        # Add related data
        conversation = Conversation(project_id=project.id, role="user", content="test")
        artifact = Artifact(project_id=project.id, type="code", path="test.py", content="test")
        deployment = Deployment(project_id=project.id, environment="dev", status="deployed")

        test_db.add_all([conversation, artifact, deployment])
        test_db.commit()

        # Delete project
        test_db.delete(project)
        test_db.commit()

        # Verify related data is also deleted
        assert test_db.query(Conversation).filter(Conversation.project_id == project.id).count() == 0
        assert test_db.query(Artifact).filter(Artifact.project_id == project.id).count() == 0
        assert test_db.query(Deployment).filter(Deployment.project_id == project.id).count() == 0

    def test_project_update(self, test_db):
        """Test updating project."""
        project = Project(name="Old Name", status=ProjectStatus.PLANNING.value)
        test_db.add(project)
        test_db.commit()

        original_updated_at = project.updated_at

        # Update project
        project.name = "New Name"
        project.status = ProjectStatus.DEPLOYED.value
        project.deployment_url = "http://deployed.com"
        test_db.commit()

        retrieved = test_db.query(Project).filter(Project.id == project.id).first()
        assert retrieved.name == "New Name"
        assert retrieved.status == ProjectStatus.DEPLOYED.value
        assert retrieved.deployment_url == "http://deployed.com"
