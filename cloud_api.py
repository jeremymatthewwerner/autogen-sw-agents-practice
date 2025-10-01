"""
Cloud API wrapper for the Multi-Agent Software Development System.
This provides a REST API interface for the multi-agent system to run in AWS.
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import boto3
import structlog
from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from multi_agent_system import MultiAgentSystem
from utils.project_state import ProjectPhase, ProjectState

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
        structlog.processors.JSONRenderer(),
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
    redoc_url="/redoc",
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
s3_client = boto3.client("s3")
secrets_client = boto3.client("secretsmanager")

# Configuration from environment
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
ENVIRONMENT = os.getenv("ENVIRONMENT", "dev")


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
            "region": AWS_REGION,
        }

        # Check if multi-agent system is initialized
        if multi_agent_system:
            system_status["agents_registered"] = len(
                multi_agent_system.orchestrator.agent_registry
            )

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
            request.project_name, request.requirements
        )

        # Plan the project tasks
        multi_agent_system.orchestrator.plan_project(project_id)

        # Start development in background
        background_tasks.add_task(
            develop_project_async, project_id, request.deployment_target
        )

        logger.info(
            "Project created", project_id=project_id, project_name=request.project_name
        )

        return ProjectResponse(
            project_id=project_id,
            project_name=request.project_name,
            status="created",
            message="Project created and development started",
            created_at=datetime.utcnow().isoformat(),
        )

    except Exception as e:
        logger.error("Failed to create project", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to create project: {str(e)}"
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
            artifacts_s3_path=artifacts_path,
        )

    except Exception as e:
        logger.error(
            "Failed to get project status", project_id=project_id, error=str(e)
        )
        raise HTTPException(
            status_code=404,
            detail=f"Project not found or error retrieving status: {str(e)}",
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
            tasks.append(
                TaskDetail(
                    id=task.id,
                    name=task.name,
                    assigned_to=task.assigned_to,
                    status=task.status.value,
                    created_at=task.created_at.isoformat(),
                    completed_at=(
                        task.completed_at.isoformat() if task.completed_at else None
                    ),
                    output=task.output,
                )
            )

        return tasks

    except Exception as e:
        logger.error("Failed to get project tasks", project_id=project_id, error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve project tasks: {str(e)}"
        )


@app.get("/api/v1/projects")
async def list_projects():
    """List all projects in the system."""
    try:
        projects = []
        for (
            project_id,
            project_state,
        ) in multi_agent_system.orchestrator.project_states.items():
            status = multi_agent_system.orchestrator.get_project_status(project_id)
            projects.append(
                {
                    "project_id": project_id,
                    "project_name": project_state.project_name,
                    "phase": status["phase"],
                    "progress_percentage": status["progress_percentage"],
                    "created_at": project_state.created_at.isoformat(),
                }
            )

        return {"projects": projects}

    except Exception as e:
        logger.error("Failed to list projects", error=str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to list projects: {str(e)}"
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

            logger.info(
                "Project development completed successfully", project_id=project_id
            )
        else:
            logger.error("Project development failed", project_id=project_id)

    except Exception as e:
        logger.error(
            "Error in project development", project_id=project_id, error=str(e)
        )


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
            ContentType="application/json",
        )

        # Store individual artifacts
        for artifact_name, artifact_data in project_state.artifacts.items():
            s3_key = f"projects/{project_id}/artifacts/{artifact_name}"
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=s3_key,
                Body=json.dumps(artifact_data, indent=2),
                ContentType="application/json",
            )

        logger.info(
            "Artifacts stored in S3", project_id=project_id, bucket=S3_BUCKET_NAME
        )

    except Exception as e:
        logger.error("Failed to store artifacts", project_id=project_id, error=str(e))


async def deploy_to_aws(project_id: str, deployment_target: str):
    """Deploy the generated application to AWS."""
    try:
        logger.info(
            "Starting AWS deployment", project_id=project_id, target=deployment_target
        )

        project_state = multi_agent_system.orchestrator.project_states.get(project_id)
        if not project_state:
            logger.error("Project state not found", project_id=project_id)
            return

        # Get deployment artifacts from project state
        deployment_config = project_state.artifacts.get("deployment_config", {})
        backend_code = project_state.artifacts.get("backend_code", {})

        if deployment_target == "ecs":
            await deploy_to_ecs(project_id, project_state, deployment_config, backend_code)
        elif deployment_target == "lambda":
            await deploy_to_lambda(project_id, project_state, deployment_config, backend_code)
        elif deployment_target == "beanstalk":
            await deploy_to_beanstalk(project_id, project_state, deployment_config, backend_code)
        else:
            logger.warning(
                "Unknown deployment target",
                project_id=project_id,
                target=deployment_target,
            )

    except Exception as e:
        logger.error("Failed to deploy to AWS", project_id=project_id, error=str(e))


async def deploy_to_ecs(
    project_id: str,
    project_state: ProjectState,
    deployment_config: Dict[str, Any],
    backend_code: Dict[str, Any],
):
    """Deploy application to AWS ECS with Fargate."""
    try:
        ecs_client = boto3.client("ecs", region_name=AWS_REGION)
        ecr_client = boto3.client("ecr", region_name=AWS_REGION)

        # Create ECR repository for the project
        repo_name = f"{ENVIRONMENT}-{project_state.project_name.lower().replace(' ', '-')}"
        try:
            ecr_response = ecr_client.create_repository(
                repositoryName=repo_name,
                imageScanningConfiguration={"scanOnPush": True},
                encryptionConfiguration={"encryptionType": "AES256"},
            )
            repository_uri = ecr_response["repository"]["repositoryUri"]
            logger.info("ECR repository created", repository_uri=repository_uri)
        except ecr_client.exceptions.RepositoryAlreadyExistsException:
            describe_response = ecr_client.describe_repositories(repositoryNames=[repo_name])
            repository_uri = describe_response["repositories"][0]["repositoryUri"]
            logger.info("Using existing ECR repository", repository_uri=repository_uri)

        # Store Docker build instructions in S3
        if S3_BUCKET_NAME:
            dockerfile_content = deployment_config.get("dockerfile", _get_default_dockerfile(backend_code))
            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=f"projects/{project_id}/deployment/Dockerfile",
                Body=dockerfile_content,
                ContentType="text/plain",
            )

        # Create ECS task definition
        task_family = f"{ENVIRONMENT}-{project_state.project_name.lower().replace(' ', '-')}"
        task_definition = {
            "family": task_family,
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "256",
            "memory": "512",
            "containerDefinitions": [
                {
                    "name": f"{project_state.project_name.lower().replace(' ', '-')}-container",
                    "image": f"{repository_uri}:latest",
                    "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
                    "environment": [
                        {"name": "ENVIRONMENT", "value": ENVIRONMENT},
                        {"name": "AWS_REGION", "value": AWS_REGION},
                    ],
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": f"/ecs/{task_family}",
                            "awslogs-region": AWS_REGION,
                            "awslogs-stream-prefix": "ecs",
                        },
                    },
                    "healthCheck": {
                        "command": ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"],
                        "interval": 30,
                        "timeout": 5,
                        "retries": 3,
                        "startPeriod": 60,
                    },
                }
            ],
            "executionRoleArn": f"arn:aws:iam::{_get_account_id()}:role/ecsTaskExecutionRole",
        }

        # Register task definition
        register_response = ecs_client.register_task_definition(**task_definition)
        task_definition_arn = register_response["taskDefinition"]["taskDefinitionArn"]
        logger.info("ECS task definition registered", task_definition_arn=task_definition_arn)

        # Store deployment info in project state
        project_state.artifacts["aws_deployment"] = {
            "deployment_type": "ecs",
            "repository_uri": repository_uri,
            "task_definition_arn": task_definition_arn,
            "deployed_at": datetime.utcnow().isoformat(),
            "region": AWS_REGION,
            "build_instructions": f"s3://{S3_BUCKET_NAME}/projects/{project_id}/deployment/Dockerfile" if S3_BUCKET_NAME else None,
        }

        logger.info(
            "ECS deployment completed",
            project_id=project_id,
            repository_uri=repository_uri,
            task_definition=task_definition_arn,
        )

    except Exception as e:
        logger.error("ECS deployment failed", project_id=project_id, error=str(e))
        raise


async def deploy_to_lambda(
    project_id: str,
    project_state: ProjectState,
    deployment_config: Dict[str, Any],
    backend_code: Dict[str, Any],
):
    """Deploy application to AWS Lambda."""
    try:
        lambda_client = boto3.client("lambda", region_name=AWS_REGION)

        function_name = f"{ENVIRONMENT}-{project_state.project_name.lower().replace(' ', '-')}"

        # Store Lambda deployment package location in S3
        if S3_BUCKET_NAME:
            lambda_handler_content = _generate_lambda_handler(backend_code)
            deployment_package_key = f"projects/{project_id}/deployment/lambda-package.zip"

            s3_client.put_object(
                Bucket=S3_BUCKET_NAME,
                Key=f"projects/{project_id}/deployment/lambda_function.py",
                Body=lambda_handler_content,
                ContentType="text/x-python",
            )

        # Create or update Lambda function
        lambda_config = {
            "FunctionName": function_name,
            "Runtime": "python3.11",
            "Role": f"arn:aws:iam::{_get_account_id()}:role/lambda-execution-role",
            "Handler": "lambda_function.handler",
            "Code": {
                "S3Bucket": S3_BUCKET_NAME if S3_BUCKET_NAME else "deployment-bucket",
                "S3Key": f"projects/{project_id}/deployment/lambda-package.zip",
            },
            "Environment": {
                "Variables": {
                    "ENVIRONMENT": ENVIRONMENT,
                    "PROJECT_ID": project_id,
                }
            },
            "Timeout": 30,
            "MemorySize": 512,
        }

        try:
            create_response = lambda_client.create_function(**lambda_config)
            function_arn = create_response["FunctionArn"]
            logger.info("Lambda function created", function_arn=function_arn)
        except lambda_client.exceptions.ResourceConflictException:
            update_response = lambda_client.update_function_configuration(
                FunctionName=function_name,
                Runtime=lambda_config["Runtime"],
                Role=lambda_config["Role"],
                Handler=lambda_config["Handler"],
                Environment=lambda_config["Environment"],
                Timeout=lambda_config["Timeout"],
                MemorySize=lambda_config["MemorySize"],
            )
            function_arn = update_response["FunctionArn"]
            logger.info("Lambda function updated", function_arn=function_arn)

        # Store deployment info
        project_state.artifacts["aws_deployment"] = {
            "deployment_type": "lambda",
            "function_name": function_name,
            "function_arn": function_arn,
            "deployed_at": datetime.utcnow().isoformat(),
            "region": AWS_REGION,
        }

        logger.info(
            "Lambda deployment completed",
            project_id=project_id,
            function_name=function_name,
            function_arn=function_arn,
        )

    except Exception as e:
        logger.error("Lambda deployment failed", project_id=project_id, error=str(e))
        raise


async def deploy_to_beanstalk(
    project_id: str,
    project_state: ProjectState,
    deployment_config: Dict[str, Any],
    backend_code: Dict[str, Any],
):
    """Deploy application to AWS Elastic Beanstalk."""
    try:
        eb_client = boto3.client("elasticbeanstalk", region_name=AWS_REGION)

        app_name = f"{ENVIRONMENT}-{project_state.project_name.lower().replace(' ', '-')}"
        env_name = f"{app_name}-env"

        # Create application if it doesn't exist
        try:
            eb_client.create_application(
                ApplicationName=app_name,
                Description=f"Generated by multi-agent system - {project_state.project_name}",
            )
            logger.info("Elastic Beanstalk application created", application_name=app_name)
        except eb_client.exceptions.TooManyApplicationsException:
            logger.info("Using existing Elastic Beanstalk application", application_name=app_name)

        # Store deployment bundle in S3
        if S3_BUCKET_NAME:
            version_label = f"v-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            bundle_key = f"projects/{project_id}/deployment/application-bundle.zip"

            # Create application version
            eb_client.create_application_version(
                ApplicationName=app_name,
                VersionLabel=version_label,
                SourceBundle={"S3Bucket": S3_BUCKET_NAME, "S3Key": bundle_key},
                AutoCreateApplication=False,
            )

            # Create or update environment
            try:
                env_response = eb_client.create_environment(
                    ApplicationName=app_name,
                    EnvironmentName=env_name,
                    VersionLabel=version_label,
                    SolutionStackName="64bit Amazon Linux 2023 v4.0.0 running Python 3.11",
                    OptionSettings=[
                        {
                            "Namespace": "aws:elasticbeanstalk:environment",
                            "OptionName": "EnvironmentType",
                            "Value": "SingleInstance" if ENVIRONMENT == "dev" else "LoadBalanced",
                        },
                        {
                            "Namespace": "aws:elasticbeanstalk:application:environment",
                            "OptionName": "ENVIRONMENT",
                            "Value": ENVIRONMENT,
                        },
                    ],
                )
                environment_url = env_response.get("CNAME", "")
                logger.info("Elastic Beanstalk environment created", environment_name=env_name)
            except eb_client.exceptions.TooManyEnvironmentsException:
                eb_client.update_environment(
                    EnvironmentName=env_name, VersionLabel=version_label
                )
                environments = eb_client.describe_environments(
                    ApplicationName=app_name, EnvironmentNames=[env_name]
                )
                environment_url = environments["Environments"][0].get("CNAME", "")
                logger.info("Elastic Beanstalk environment updated", environment_name=env_name)

            # Store deployment info
            project_state.artifacts["aws_deployment"] = {
                "deployment_type": "beanstalk",
                "application_name": app_name,
                "environment_name": env_name,
                "environment_url": f"http://{environment_url}" if environment_url else None,
                "version_label": version_label,
                "deployed_at": datetime.utcnow().isoformat(),
                "region": AWS_REGION,
            }

            logger.info(
                "Elastic Beanstalk deployment completed",
                project_id=project_id,
                application_name=app_name,
                environment_url=environment_url,
            )

    except Exception as e:
        logger.error("Elastic Beanstalk deployment failed", project_id=project_id, error=str(e))
        raise


def _get_account_id() -> str:
    """Get AWS account ID."""
    sts_client = boto3.client("sts")
    return sts_client.get_caller_identity()["Account"]


def _get_default_dockerfile(backend_code: Dict[str, Any]) -> str:
    """Generate a default Dockerfile based on backend code."""
    framework = backend_code.get("framework", "fastapi").lower()

    return f"""FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""


def _generate_lambda_handler(backend_code: Dict[str, Any]) -> str:
    """Generate a Lambda handler based on backend code."""
    return """import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    \"\"\"AWS Lambda handler function.\"\"\"
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        # Extract request information
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        body = event.get('body', '{}')

        # Process request
        if path == '/health':
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'status': 'healthy'})
            }

        # Default response
        return {
            'statusCode': 200,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({
                'message': 'Application deployed successfully',
                'method': http_method,
                'path': path
            })
        }

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }
"""


# Metrics endpoint for monitoring
@app.get("/api/v1/metrics")
async def get_metrics():
    """Get system metrics for monitoring."""
    try:
        total_projects = len(multi_agent_system.orchestrator.project_states)
        completed_projects = sum(
            1
            for state in multi_agent_system.orchestrator.project_states.values()
            if state.phase == ProjectPhase.COMPLETED
        )

        return {
            "total_projects": total_projects,
            "completed_projects": completed_projects,
            "success_rate": (
                completed_projects / total_projects if total_projects > 0 else 0
            ),
            "registered_agents": len(multi_agent_system.orchestrator.agent_registry),
            "environment": ENVIRONMENT,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error("Failed to get metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


if __name__ == "__main__":
    import uvicorn

    # Configure logging
    logging.basicConfig(
        level=logging.INFO if ENVIRONMENT == "prod" else logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Start the server
    uvicorn.run(
        "cloud_api:app",
        host="0.0.0.0",
        port=8000,
        reload=ENVIRONMENT == "dev",
        workers=1 if ENVIRONMENT == "dev" else 4,
    )
