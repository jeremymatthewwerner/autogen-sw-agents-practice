"""
Cloud API wrapper for the Multi-Agent Software Development System.
This provides a REST API interface for the multi-agent system to run in AWS.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import asyncio
import logging
import boto3
import json
from datetime import datetime
import uuid

from multi_agent_system import MultiAgentSystem
from utils.project_state import ProjectState, ProjectPhase
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="Multi-Agent Software Development System",
    description="Autonomous software development using specialized AI agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize multi-agent system
multi_agent_system = MultiAgentSystem()

# AWS clients
s3_client = boto3.client('s3')
secrets_client = boto3.client('secretsmanager')

# Configuration from environment
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
ENVIRONMENT = os.getenv('ENVIRONMENT', 'dev')

# Request/Response Models
class ProjectRequest(BaseModel):
    project_name: str
    requirements: str
    deployment_target: Optional[str] = "ecs"  # ecs, lambda, or beanstalk

class ProjectResponse(BaseModel):
    project_id: str
    project_name: str
    status: str
    message: str
    created_at: str

class ProjectStatus(BaseModel):
    project_id: str
    project_name: str
    phase: str
    progress_percentage: float
    task_summary: Dict[str, int]
    total_tasks: int
    aws_deployment_url: Optional[str] = None
    artifacts_s3_path: Optional[str] = None

class TaskDetail(BaseModel):
    id: str
    name: str
    assigned_to: str
    status: str
    created_at: str
    completed_at: Optional[str]
    output: Optional[Dict[str, Any]]

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer."""
    try:
        # Basic system health checks
        system_status = {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "environment": ENVIRONMENT,
            "region": AWS_REGION
        }

        # Check if multi-agent system is initialized
        if multi_agent_system:
            system_status["agents_registered"] = len(multi_agent_system.orchestrator.agent_registry)

        return system_status
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service unhealthy")

# Project management endpoints
@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(request: ProjectRequest, background_tasks: BackgroundTasks):
    """Create a new software development project."""
    try:
        # Create project with multi-agent system
        project_id = multi_agent_system.orchestrator.create_project(
            request.project_name,
            request.requirements
        )

        # Plan the project tasks
        multi_agent_system.orchestrator.plan_project(project_id)

        # Start development in background
        background_tasks.add_task(
            develop_project_async,
            project_id,
            request.deployment_target
        )

        logger.info(
            "Project created",
            project_id=project_id,
            project_name=request.project_name
        )

        return ProjectResponse(
            project_id=project_id,
            project_name=request.project_name,
            status="created",
            message="Project created and development started",
            created_at=datetime.utcnow().isoformat()
        )

    except Exception as e:
        logger.error("Failed to create project", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create project: {str(e)}"
        )

@app.get("/api/v1/projects/{project_id}/status", response_model=ProjectStatus)
async def get_project_status(project_id: str):
    """Get the current status of a project."""
    try:
        status = multi_agent_system.orchestrator.get_project_status(project_id)

        # Check if artifacts are stored in S3
        artifacts_path = None
        if S3_BUCKET_NAME:
            artifacts_path = f"s3://{S3_BUCKET_NAME}/projects/{project_id}/"

        return ProjectStatus(
            project_id=status["project_id"],
            project_name=status["project_name"],
            phase=status["phase"],
            progress_percentage=status["progress_percentage"],
            task_summary=status["task_summary"],
            total_tasks=status["total_tasks"],
            artifacts_s3_path=artifacts_path
        )

    except Exception as e:
        logger.error("Failed to get project status", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=404,
            detail=f"Project not found or error retrieving status: {str(e)}"
        )

@app.get("/api/v1/projects/{project_id}/tasks")
async def get_project_tasks(project_id: str) -> List[TaskDetail]:
    """Get detailed information about all tasks in a project."""
    try:
        project_state = multi_agent_system.orchestrator.project_states.get(project_id)
        if not project_state:
            raise HTTPException(status_code=404, detail="Project not found")

        tasks = []
        for task in project_state.tasks.values():
            tasks.append(TaskDetail(
                id=task.id,
                name=task.name,
                assigned_to=task.assigned_to,
                status=task.status.value,
                created_at=task.created_at.isoformat(),
                completed_at=task.completed_at.isoformat() if task.completed_at else None,
                output=task.output
            ))

        return tasks

    except Exception as e:
        logger.error("Failed to get project tasks", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve project tasks: {str(e)}"
        )

@app.get("/api/v1/projects")
async def list_projects():
    """List all projects in the system."""
    try:
        projects = []
        for project_id, project_state in multi_agent_system.orchestrator.project_states.items():
            status = multi_agent_system.orchestrator.get_project_status(project_id)
            projects.append({
                "project_id": project_id,
                "project_name": project_state.project_name,
                "phase": status["phase"],
                "progress_percentage": status["progress_percentage"],
                "created_at": project_state.created_at.isoformat()
            })

        return {"projects": projects}

    except Exception as e:
        logger.error("Failed to list projects", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list projects: {str(e)}"
        )

# Background task for project development
async def develop_project_async(project_id: str, deployment_target: str):
    """Develop a project using the multi-agent system."""
    try:
        logger.info("Starting project development", project_id=project_id)

        # Execute the multi-agent system
        success = multi_agent_system.orchestrator.coordinate_agents(project_id)

        if success:
            # Store artifacts in S3
            await store_project_artifacts(project_id)

            # If deployment target specified, deploy to AWS
            if deployment_target:
                await deploy_to_aws(project_id, deployment_target)

            logger.info("Project development completed successfully", project_id=project_id)
        else:
            logger.error("Project development failed", project_id=project_id)

    except Exception as e:
        logger.error("Error in project development", project_id=project_id, error=str(e))

async def store_project_artifacts(project_id: str):
    """Store project artifacts in S3."""
    if not S3_BUCKET_NAME:
        logger.warning("S3 bucket not configured, skipping artifact storage")
        return

    try:
        project_state = multi_agent_system.orchestrator.project_states.get(project_id)
        if not project_state:
            return

        # Store project state as JSON
        s3_key = f"projects/{project_id}/project_state.json"
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=json.dumps(project_state.to_dict(), indent=2),
            ContentType="application/json"
        )

        # Store individual artifacts
        for artifact_name, artifact_data in project_state.artifacts.items():
            s3_key = f"projects/{project_id}/artifacts/{artifact_name}"
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=json.dumps(artifact_data, indent=2),
                ContentType="application/json"
            )

        logger.info("Artifacts stored in S3", project_id=project_id, bucket=S3_BUCKET_NAME)

    except Exception as e:
        logger.error("Failed to store artifacts", project_id=project_id, error=str(e))

async def deploy_to_aws(project_id: str, deployment_target: str):
    """Deploy the generated application to AWS."""
    try:
        logger.info("Starting AWS deployment", project_id=project_id, target=deployment_target)

        # This would implement the actual deployment logic
        # For now, it's a placeholder that logs the deployment intent

        project_state = multi_agent_system.orchestrator.project_states.get(project_id)
        if not project_state:
            return

        # TODO: Implement actual deployment logic based on target
        # - ECS: Create task definition, service, and deploy
        # - Lambda: Package and deploy functions
        # - Elastic Beanstalk: Create application version and deploy

        logger.info("AWS deployment placeholder",
                   project_id=project_id,
                   target=deployment_target,
                   message="Deployment logic to be implemented")

    except Exception as e:
        logger.error("Failed to deploy to AWS", project_id=project_id, error=str(e))

# Metrics endpoint for monitoring
@app.get("/api/v1/metrics")
async def get_metrics():
    """Get system metrics for monitoring."""
    try:
        total_projects = len(multi_agent_system.orchestrator.project_states)
        completed_projects = sum(
            1 for state in multi_agent_system.orchestrator.project_states.values()
            if state.phase == ProjectPhase.COMPLETED
        )

        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "success_rate": completed_projects / total_projects if total_projects > 0 else 0,
            "registered_agents": len(multi_agent_system.orchestrator.agent_registry),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")

if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if ENVIRONMENT == "prod" else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Start the server
    uvicorn.run(
        "cloud_api:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "dev",
        workers=1 if ENVIRONMENT == "dev" else 4
    )