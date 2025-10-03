"""Unit tests for cloud_api AWS deployment functions."""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from cloud_api import (
    _generate_lambda_handler,
    _get_default_dockerfile,
    deploy_to_beanstalk,
    deploy_to_ecs,
    deploy_to_lambda,
)
from utils.project_state import ProjectState


@pytest.fixture
def mock_project_state():
    """Create a mock project state for testing."""
    state = ProjectState(
        project_id="test-project-123",
        project_name="Test Application",
    )
    state.artifacts = {
        "deployment_config": {
            "dockerfile": "FROM python:3.11\nCMD ['python', 'app.py']"
        },
        "backend_code": {"framework": "fastapi", "version": "0.1.0"},
    }
    return state


@pytest.fixture
def mock_deployment_config():
    """Mock deployment configuration."""
    return {
        "dockerfile": "FROM python:3.11\nCMD ['python', 'app.py']",
        "docker-compose.yml": "version: '3.8'\nservices:\n  api:\n    build: .",
    }


@pytest.fixture
def mock_backend_code():
    """Mock backend code configuration."""
    return {
        "framework": "fastapi",
        "version": "0.1.0",
        "language": "python",
        "python_version": "3.11",
    }


class TestDockerfileGeneration:
    """Test Dockerfile generation."""

    def test_get_default_dockerfile_fastapi(self, mock_backend_code):
        """Test default Dockerfile generation for FastAPI."""
        dockerfile = _get_default_dockerfile(mock_backend_code)

        assert "FROM python:3.11-slim" in dockerfile
        assert "WORKDIR /app" in dockerfile
        assert "COPY requirements.txt ." in dockerfile
        assert "pip install" in dockerfile
        assert "EXPOSE 8000" in dockerfile
        assert "HEALTHCHECK" in dockerfile
        assert "uvicorn" in dockerfile

    def test_get_default_dockerfile_no_framework(self):
        """Test default Dockerfile generation with no framework specified."""
        dockerfile = _get_default_dockerfile({})

        assert "FROM python:3.11-slim" in dockerfile
        assert "uvicorn" in dockerfile  # defaults to fastapi


class TestLambdaHandlerGeneration:
    """Test Lambda handler generation."""

    def test_generate_lambda_handler(self, mock_backend_code):
        """Test Lambda handler generation."""
        handler_code = _generate_lambda_handler(mock_backend_code)

        assert "def handler(event, context):" in handler_code
        assert "import json" in handler_code
        assert "import logging" in handler_code
        assert "/health" in handler_code
        assert "statusCode" in handler_code
        assert "httpMethod" in handler_code

    def test_generate_lambda_handler_empty_config(self):
        """Test Lambda handler generation with empty config."""
        handler_code = _generate_lambda_handler({})

        assert "def handler(event, context):" in handler_code
        assert "statusCode" in handler_code


@pytest.mark.unit
@pytest.mark.asyncio
class TestECSDeployment:
    """Test ECS deployment functionality."""

    @patch("cloud_api.boto3.client")
    @patch("cloud_api.s3_client")
    @patch("cloud_api.S3_BUCKET_NAME", "test-bucket")
    @patch("cloud_api.ENVIRONMENT", "dev")
    @patch("cloud_api.AWS_REGION", "us-east-1")
    async def test_deploy_to_ecs_creates_repository(
        self,
        mock_s3_client,
        mock_boto_client,
        mock_project_state,
        mock_deployment_config,
        mock_backend_code,
    ):
        """Test ECS deployment creates ECR repository."""
        # Setup mocks
        mock_ecr = MagicMock()
        mock_ecs = MagicMock()
        mock_boto_client.side_effect = lambda service, **kwargs: (
            mock_ecr if service == "ecr" else mock_ecs
        )

        mock_ecr.create_repository.return_value = {
            "repository": {
                "repositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/dev-test-application"
            }
        }
        mock_ecs.register_task_definition.return_value = {
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:us-east-1:123456789012:task-definition/dev-test-application:1"
            }
        }

        with patch("cloud_api._get_account_id", return_value="123456789012"):
            await deploy_to_ecs(
                "test-project-123",
                mock_project_state,
                mock_deployment_config,
                mock_backend_code,
            )

        # Verify ECR repository creation
        mock_ecr.create_repository.assert_called_once()
        call_args = mock_ecr.create_repository.call_args
        assert call_args[1]["repositoryName"] == "dev-test-application"
        assert call_args[1]["imageScanningConfiguration"]["scanOnPush"] is True

        # Verify task definition registration
        mock_ecs.register_task_definition.assert_called_once()
        task_def = mock_ecs.register_task_definition.call_args[1]
        assert task_def["family"] == "dev-test-application"
        assert task_def["requiresCompatibilities"] == ["FARGATE"]
        assert task_def["cpu"] == "256"
        assert task_def["memory"] == "512"

        # Verify deployment info stored in project state
        assert "aws_deployment" in mock_project_state.artifacts
        deployment_info = mock_project_state.artifacts["aws_deployment"]
        assert deployment_info["deployment_type"] == "ecs"
        assert "repository_uri" in deployment_info
        assert "task_definition_arn" in deployment_info

    @patch("cloud_api.boto3.client")
    @patch("cloud_api.s3_client")
    @patch("cloud_api.S3_BUCKET_NAME", "test-bucket")
    @patch("cloud_api.ENVIRONMENT", "dev")
    @patch("cloud_api.AWS_REGION", "us-east-1")
    async def test_deploy_to_ecs_uses_existing_repository(
        self,
        mock_s3_client,
        mock_boto_client,
        mock_project_state,
        mock_deployment_config,
        mock_backend_code,
    ):
        """Test ECS deployment uses existing ECR repository."""
        mock_ecr = MagicMock()
        mock_ecs = MagicMock()
        mock_boto_client.side_effect = lambda service, **kwargs: (
            mock_ecr if service == "ecr" else mock_ecs
        )

        # Create a proper exception class
        class RepositoryAlreadyExistsException(Exception):
            pass

        mock_ecr.exceptions.RepositoryAlreadyExistsException = (
            RepositoryAlreadyExistsException
        )

        # Simulate repository already exists
        mock_ecr.create_repository.side_effect = RepositoryAlreadyExistsException(
            "Repository already exists"
        )
        mock_ecr.describe_repositories.return_value = {
            "repositories": [
                {
                    "repositoryUri": "123456789012.dkr.ecr.us-east-1.amazonaws.com/dev-test-application"
                }
            ]
        }
        mock_ecs.register_task_definition.return_value = {
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:us-east-1:123456789012:task-definition/dev-test-application:1"
            }
        }

        with patch("cloud_api._get_account_id", return_value="123456789012"):
            await deploy_to_ecs(
                "test-project-123",
                mock_project_state,
                mock_deployment_config,
                mock_backend_code,
            )

        # Verify it tried to create and then described existing repo
        mock_ecr.create_repository.assert_called_once()
        mock_ecr.describe_repositories.assert_called_once_with(
            repositoryNames=["dev-test-application"]
        )


@pytest.mark.unit
@pytest.mark.asyncio
class TestLambdaDeployment:
    """Test Lambda deployment functionality."""

    @patch("cloud_api.boto3.client")
    @patch("cloud_api.s3_client")
    @patch("cloud_api.S3_BUCKET_NAME", "test-bucket")
    @patch("cloud_api.ENVIRONMENT", "dev")
    @patch("cloud_api.AWS_REGION", "us-east-1")
    async def test_deploy_to_lambda_creates_function(
        self,
        mock_s3_client,
        mock_boto_client,
        mock_project_state,
        mock_deployment_config,
        mock_backend_code,
    ):
        """Test Lambda deployment creates function."""
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda

        mock_lambda.create_function.return_value = {
            "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:dev-test-application"
        }

        with patch("cloud_api._get_account_id", return_value="123456789012"):
            await deploy_to_lambda(
                "test-project-123",
                mock_project_state,
                mock_deployment_config,
                mock_backend_code,
            )

        # Verify Lambda function creation
        mock_lambda.create_function.assert_called_once()
        call_args = mock_lambda.create_function.call_args[1]
        assert call_args["FunctionName"] == "dev-test-application"
        assert call_args["Runtime"] == "python3.11"
        assert call_args["Handler"] == "lambda_function.handler"
        assert call_args["Timeout"] == 30
        assert call_args["MemorySize"] == 512

        # Verify deployment info stored
        assert "aws_deployment" in mock_project_state.artifacts
        deployment_info = mock_project_state.artifacts["aws_deployment"]
        assert deployment_info["deployment_type"] == "lambda"
        assert "function_arn" in deployment_info

    @patch("cloud_api.boto3.client")
    @patch("cloud_api.s3_client")
    @patch("cloud_api.S3_BUCKET_NAME", "test-bucket")
    @patch("cloud_api.ENVIRONMENT", "dev")
    @patch("cloud_api.AWS_REGION", "us-east-1")
    async def test_deploy_to_lambda_updates_existing_function(
        self,
        mock_s3_client,
        mock_boto_client,
        mock_project_state,
        mock_deployment_config,
        mock_backend_code,
    ):
        """Test Lambda deployment updates existing function."""
        mock_lambda = MagicMock()
        mock_boto_client.return_value = mock_lambda

        # Create a proper exception class
        class ResourceConflictException(Exception):
            pass

        mock_lambda.exceptions.ResourceConflictException = ResourceConflictException

        # Simulate function already exists
        mock_lambda.create_function.side_effect = ResourceConflictException(
            "Function already exists"
        )
        mock_lambda.update_function_configuration.return_value = {
            "FunctionArn": "arn:aws:lambda:us-east-1:123456789012:function:dev-test-application"
        }

        with patch("cloud_api._get_account_id", return_value="123456789012"):
            await deploy_to_lambda(
                "test-project-123",
                mock_project_state,
                mock_deployment_config,
                mock_backend_code,
            )

        # Verify update was called
        mock_lambda.update_function_configuration.assert_called_once()
        call_args = mock_lambda.update_function_configuration.call_args[1]
        assert call_args["FunctionName"] == "dev-test-application"


@pytest.mark.unit
@pytest.mark.asyncio
class TestBeanstalkDeployment:
    """Test Elastic Beanstalk deployment functionality."""

    @patch("cloud_api.boto3.client")
    @patch("cloud_api.s3_client")
    @patch("cloud_api.S3_BUCKET_NAME", "test-bucket")
    @patch("cloud_api.ENVIRONMENT", "dev")
    @patch("cloud_api.AWS_REGION", "us-east-1")
    async def test_deploy_to_beanstalk_creates_application(
        self,
        mock_s3_client,
        mock_boto_client,
        mock_project_state,
        mock_deployment_config,
        mock_backend_code,
    ):
        """Test Beanstalk deployment creates application."""
        mock_eb = MagicMock()
        mock_boto_client.return_value = mock_eb

        mock_eb.create_environment.return_value = {
            "CNAME": "dev-test-application-env.us-east-1.elasticbeanstalk.com"
        }

        await deploy_to_beanstalk(
            "test-project-123",
            mock_project_state,
            mock_deployment_config,
            mock_backend_code,
        )

        # Verify application creation
        mock_eb.create_application.assert_called_once()
        call_args = mock_eb.create_application.call_args[1]
        assert call_args["ApplicationName"] == "dev-test-application"

        # Verify application version creation
        mock_eb.create_application_version.assert_called_once()

        # Verify environment creation
        mock_eb.create_environment.assert_called_once()
        env_args = mock_eb.create_environment.call_args[1]
        assert env_args["ApplicationName"] == "dev-test-application"
        assert env_args["EnvironmentName"] == "dev-test-application-env"

        # Verify deployment info stored
        assert "aws_deployment" in mock_project_state.artifacts
        deployment_info = mock_project_state.artifacts["aws_deployment"]
        assert deployment_info["deployment_type"] == "beanstalk"
        assert "environment_url" in deployment_info
        assert deployment_info["environment_url"].startswith("http://")

    @patch("cloud_api.boto3.client")
    @patch("cloud_api.s3_client")
    @patch("cloud_api.S3_BUCKET_NAME", "test-bucket")
    @patch("cloud_api.ENVIRONMENT", "prod")
    @patch("cloud_api.AWS_REGION", "us-east-1")
    async def test_deploy_to_beanstalk_prod_uses_load_balanced(
        self,
        mock_s3_client,
        mock_boto_client,
        mock_project_state,
        mock_deployment_config,
        mock_backend_code,
    ):
        """Test Beanstalk deployment uses LoadBalanced for production."""
        mock_eb = MagicMock()
        mock_boto_client.return_value = mock_eb

        mock_eb.create_environment.return_value = {
            "CNAME": "test-app.elasticbeanstalk.com"
        }

        await deploy_to_beanstalk(
            "test-project-123",
            mock_project_state,
            mock_deployment_config,
            mock_backend_code,
        )

        # Check that LoadBalanced is used for prod
        env_args = mock_eb.create_environment.call_args[1]
        option_settings = env_args["OptionSettings"]
        env_type_setting = next(
            (s for s in option_settings if s["OptionName"] == "EnvironmentType"), None
        )
        assert env_type_setting is not None
        assert env_type_setting["Value"] == "LoadBalanced"
