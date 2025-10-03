"""Database models for project persistence and conversation history."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

Base = declarative_base()


class ProjectStatus(str, Enum):
    """Project lifecycle status."""

    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    TESTING = "testing"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """Message role in conversation."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Project(Base):
    """Project model representing a software development project."""

    __tablename__ = "projects"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(String(50), default=ProjectStatus.PLANNING.value)

    # URLs and repositories
    deployment_url = Column(String(500))
    git_repo_url = Column(String(500))

    # Metadata
    requirements = Column(JSON)  # Structured requirements from ProductManager
    architecture = Column(JSON)  # System design from Architect
    tech_stack = Column(JSON)    # Technology choices

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deployed_at = Column(DateTime, nullable=True)

    # Relationships
    conversations = relationship("Conversation", back_populates="project", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="project", cascade="all, delete-orphan")
    deployments = relationship("Deployment", back_populates="project", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation message in a project thread."""

    __tablename__ = "conversations"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Message content
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)

    # Metadata
    message_metadata = Column(JSON)  # Agent responses, file changes, task results, etc.
    agent_name = Column(String(100))  # Which agent generated this (if assistant)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="conversations")


class Artifact(Base):
    """Project artifact (code, config, documentation, etc.)."""

    __tablename__ = "artifacts"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Artifact details
    type = Column(String(50), nullable=False)  # code, test, config, deployment, docs
    path = Column(String(500), nullable=False)  # Relative path in project
    content = Column(Text)  # File content

    # Versioning
    version = Column(Integer, default=1)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="artifacts")


class Deployment(Base):
    """Deployment record for tracking deployments."""

    __tablename__ = "deployments"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    project_id = Column(PGUUID(as_uuid=True), ForeignKey("projects.id"), nullable=False)

    # Deployment details
    environment = Column(String(50), default="dev")  # dev, staging, prod
    status = Column(String(50))  # pending, deploying, deployed, failed
    deployment_url = Column(String(500))

    # Cloud resources
    cloud_provider = Column(String(50))  # aws, gcp, azure
    resource_ids = Column(JSON)  # ECS task IDs, Lambda ARNs, etc.

    # Logs and metadata
    logs = Column(Text)
    error_message = Column(Text)
    deployment_metadata = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    deployed_at = Column(DateTime, nullable=True)
    failed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="deployments")


# Database connection utility
class Database:
    """Database connection manager."""

    def __init__(self, database_url: str):
        """Initialize database connection.

        Args:
            database_url: PostgreSQL connection string
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)

    def create_all(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self):
        """Get a new database session."""
        return self.SessionLocal()
