"""Project service for managing software development projects."""

import logging
from typing import Any, Dict, List, Optional
from uuid import UUID

from models.database import Artifact, Conversation, Deployment, MessageRole, Project, ProjectStatus
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


class ProjectService:
    """Manages software development projects."""

    def create_project(
        self,
        name: str,
        description: str,
        session: Session
    ) -> Project:
        """Create a new project.

        Args:
            name: Project name
            description: Project description
            session: Database session

        Returns:
            Created project
        """
        project = Project(
            name=name,
            description=description,
            status=ProjectStatus.PLANNING.value,
        )
        session.add(project)

        # Add initial system message
        system_msg = Conversation(
            project_id=project.id,
            role=MessageRole.SYSTEM.value,
            content=f"Project '{name}' created. Ready to start development.",
            metadata={"event": "project_created"}
        )
        session.add(system_msg)

        session.commit()
        session.refresh(project)

        logger.info(f"Created project: {project.name} (ID: {project.id})")
        return project

    def get_project(self, project_id: UUID, session: Session) -> Optional[Project]:
        """Get a project by ID.

        Args:
            project_id: Project ID
            session: Database session

        Returns:
            Project or None
        """
        return session.query(Project).filter(Project.id == project_id).first()

    def list_projects(
        self,
        session: Session,
        status: Optional[str] = None,
        limit: int = 50
    ) -> List[Project]:
        """List projects.

        Args:
            session: Database session
            status: Filter by status
            limit: Maximum projects to return

        Returns:
            List of projects
        """
        query = session.query(Project)

        if status:
            query = query.filter(Project.status == status)

        return query.order_by(Project.updated_at.desc()).limit(limit).all()

    def update_project_status(
        self,
        project_id: UUID,
        status: ProjectStatus,
        session: Session
    ) -> Project:
        """Update project status.

        Args:
            project_id: Project ID
            status: New status
            session: Database session

        Returns:
            Updated project
        """
        project = self.get_project(project_id, session)
        if not project:
            raise ValueError(f"Project {project_id} not found")

        project.status = status.value
        session.commit()
        session.refresh(project)

        logger.info(f"Updated project {project.name} status to {status.value}")
        return project

    def save_artifact(
        self,
        project_id: UUID,
        artifact_type: str,
        path: str,
        content: str,
        session: Session
    ) -> Artifact:
        """Save a project artifact.

        Args:
            project_id: Project ID
            artifact_type: Artifact type (code, test, config, etc.)
            path: File path
            content: File content
            session: Database session

        Returns:
            Created artifact
        """
        # Check if artifact already exists
        existing = (
            session.query(Artifact)
            .filter(Artifact.project_id == project_id, Artifact.path == path)
            .first()
        )

        if existing:
            # Update existing artifact with new version
            existing.content = content
            existing.version += 1
            session.commit()
            session.refresh(existing)
            logger.info(f"Updated artifact {path} to version {existing.version}")
            return existing
        else:
            # Create new artifact
            artifact = Artifact(
                project_id=project_id,
                type=artifact_type,
                path=path,
                content=content,
            )
            session.add(artifact)
            session.commit()
            session.refresh(artifact)
            logger.info(f"Created new artifact {path}")
            return artifact

    def get_artifacts(
        self,
        project_id: UUID,
        artifact_type: Optional[str] = None,
        session: Session = None
    ) -> List[Artifact]:
        """Get project artifacts.

        Args:
            project_id: Project ID
            artifact_type: Filter by type
            session: Database session

        Returns:
            List of artifacts
        """
        query = session.query(Artifact).filter(Artifact.project_id == project_id)

        if artifact_type:
            query = query.filter(Artifact.type == artifact_type)

        return query.order_by(Artifact.path).all()

    def record_deployment(
        self,
        project_id: UUID,
        environment: str,
        deployment_url: str,
        cloud_provider: str,
        resource_ids: Dict[str, Any],
        session: Session
    ) -> Deployment:
        """Record a deployment.

        Args:
            project_id: Project ID
            environment: Environment (dev, staging, prod)
            deployment_url: URL of deployed application
            cloud_provider: Cloud provider (aws, gcp, azure)
            resource_ids: Cloud resource IDs
            session: Database session

        Returns:
            Created deployment record
        """
        deployment = Deployment(
            project_id=project_id,
            environment=environment,
            status="deployed",
            deployment_url=deployment_url,
            cloud_provider=cloud_provider,
            resource_ids=resource_ids,
        )
        session.add(deployment)

        # Update project deployment URL
        project = self.get_project(project_id, session)
        if project:
            project.deployment_url = deployment_url
            project.status = ProjectStatus.DEPLOYED.value

        session.commit()
        session.refresh(deployment)

        logger.info(f"Recorded deployment for project {project_id} to {environment}")
        return deployment

    def delete_project(self, project_id: UUID, session: Session) -> bool:
        """Delete a project and all its data.

        Args:
            project_id: Project ID
            session: Database session

        Returns:
            True if deleted successfully
        """
        project = self.get_project(project_id, session)
        if not project:
            return False

        # Cascade delete will handle conversations, artifacts, deployments
        session.delete(project)
        session.commit()

        logger.info(f"Deleted project {project_id}")
        return True
