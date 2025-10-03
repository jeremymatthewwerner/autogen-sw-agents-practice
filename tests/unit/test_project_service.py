"""Unit tests for project service."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.database import Base, Project, Conversation
from services.project_service import ProjectService


@pytest.fixture
def test_db():
    """Create test database."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def project_service():
    """Create project service instance."""
    return ProjectService()


class TestProjectService:
    """Test project service functionality."""

    def test_create_project(self, project_service, test_db):
        """Test creating a project with initial system message."""
        # Create project
        project = project_service.create_project(
            name="Test Project",
            description="A test project",
            session=test_db,
        )

        # Verify project was created
        assert project.id is not None
        assert project.name == "Test Project"
        assert project.description == "A test project"
        assert project.status == "planning"

        # Verify system message was created
        conversations = (
            test_db.query(Conversation)
            .filter(Conversation.project_id == project.id)
            .all()
        )
        assert len(conversations) == 1
        assert conversations[0].role == "system"
        assert "Test Project" in conversations[0].content
        assert conversations[0].message_metadata["event"] == "project_created"

    def test_create_project_generates_valid_id(self, project_service, test_db):
        """Test that project ID is generated before creating system message."""
        project = project_service.create_project(
            name="ID Test",
            description="Test ID generation",
            session=test_db,
        )

        # Project ID should be set
        assert project.id is not None

        # System message should reference the project ID
        conversation = (
            test_db.query(Conversation)
            .filter(Conversation.project_id == project.id)
            .first()
        )
        assert conversation is not None
        assert conversation.project_id == project.id

    def test_get_project(self, project_service, test_db):
        """Test retrieving a project by ID."""
        # Create project
        created = project_service.create_project(
            name="Get Test",
            description="Test get",
            session=test_db,
        )

        # Retrieve project
        retrieved = project_service.get_project(created.id, test_db)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == "Get Test"

    def test_list_projects(self, project_service, test_db):
        """Test listing projects."""
        # Create multiple projects
        project_service.create_project("Project 1", "Description 1", test_db)
        project_service.create_project("Project 2", "Description 2", test_db)
        project_service.create_project("Project 3", "Description 3", test_db)

        # List all projects
        projects = project_service.list_projects(test_db)

        assert len(projects) == 3
        assert all(p.name in ["Project 1", "Project 2", "Project 3"] for p in projects)
