"""
Deployment Agent - Handles automatic deployment of generated applications to AWS.
This agent works as part of the multi-agent system to deploy applications created by other agents.
"""

import boto3
import json
import os
import tempfile
import zipfile
import time
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AWSDeploymentAgent:
    """Handles deployment of generated applications to various AWS services."""

    def __init__(self):
        """Initialize AWS clients and configuration."""
        self.ecs_client = boto3.client("ecs")
        self.ecr_client = boto3.client("ecr")
        self.lambda_client = boto3.client("lambda")
        self.iam_client = boto3.client("iam")
        self.logs_client = boto3.client("logs")
        self.s3_client = boto3.client("s3")

        # Configuration
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.account_id = boto3.client("sts").get_caller_identity()["Account"]

    async def deploy_application(
        self, project_id: str, deployment_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy an application based on the deployment configuration."""
        deployment_type = deployment_config.get("deployment_type", "ecs")

        try:
            if deployment_type == "ecs":
                return await self._deploy_to_ecs(project_id, deployment_config)
            elif deployment_type == "lambda":
                return await self._deploy_to_lambda(project_id, deployment_config)
            elif deployment_type == "beanstalk":
                return await self._deploy_to_beanstalk(project_id, deployment_config)
            else:
                raise ValueError(f"Unsupported deployment type: {deployment_type}")

        except Exception as e:
            logger.error(f"Deployment failed for project {project_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "deployment_type": deployment_type,
            }

    async def _deploy_to_ecs(
        self, project_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy application to ECS Fargate."""
        try:
            app_name = f"{project_id}-app"

            # 1. Create ECR repository if it doesn't exist
            ecr_repo = await self._ensure_ecr_repository(app_name)

            # 2. Build and push Docker image (simplified - in practice would use CodeBuild)
            # This would typically be handled by CI/CD pipeline

            # 3. Create ECS task definition
            task_definition = {
                "family": app_name,
                "networkMode": "awsvpc",
                "requiresCompatibilities": ["FARGATE"],
                "cpu": "512",
                "memory": "1024",
                "executionRoleArn": f"arn:aws:iam::{self.account_id}:role/ecsTaskExecutionRole",
                "containerDefinitions": [
                    {
                        "name": app_name,
                        "image": f"{ecr_repo['repositoryUri']}:latest",
                        "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
                        "essential": True,
                        "logConfiguration": {
                            "logDriver": "awslogs",
                            "options": {
                                "awslogs-group": f"/ecs/{app_name}",
                                "awslogs-region": self.region,
                                "awslogs-stream-prefix": "ecs",
                            },
                        },
                        "environment": config.get("environment_variables", []),
                    }
                ],
            }

            # Register task definition
            task_def_response = self.ecs_client.register_task_definition(
                **task_definition
            )

            # 4. Create ECS service
            service_config = {
                "serviceName": f"{app_name}-service",
                "cluster": "multi-agent-generated-apps",
                "taskDefinition": task_def_response["taskDefinition"][
                    "taskDefinitionArn"
                ],
                "desiredCount": 1,
                "launchType": "FARGATE",
                "networkConfiguration": {
                    "awsvpcConfiguration": {
                        "subnets": config.get("subnets", []),
                        "securityGroups": config.get("security_groups", []),
                        "assignPublicIp": "ENABLED",
                    }
                },
            }

            service_response = self.ecs_client.create_service(**service_config)

            return {
                "success": True,
                "deployment_type": "ecs",
                "service_arn": service_response["service"]["serviceArn"],
                "task_definition_arn": task_def_response["taskDefinition"][
                    "taskDefinitionArn"
                ],
                "endpoint": f"http://{app_name}-service.{self.region}.elb.amazonaws.com",
                "deployed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"ECS deployment failed: {str(e)}")
            raise

    async def _deploy_to_lambda(
        self, project_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy application as Lambda functions."""
        try:
            app_name = f"{project_id}-lambda"

            # 1. Create deployment package
            deployment_package = await self._create_lambda_package(
                config.get("code_files", {})
            )

            # 2. Create Lambda function
            function_config = {
                "FunctionName": app_name,
                "Runtime": "python3.11",
                "Role": config.get("lambda_role_arn"),
                "Handler": "main.lambda_handler",
                "Code": {"ZipFile": deployment_package},
                "Environment": {"Variables": config.get("environment_variables", {})},
                "Timeout": 30,
                "MemorySize": 512,
            }

            function_response = self.lambda_client.create_function(**function_config)

            # 3. Create API Gateway (if needed)
            api_gateway_url = None
            if config.get("create_api_gateway", True):
                # This would create API Gateway integration
                # Simplified for now
                api_gateway_url = f"https://api.gateway.url/{app_name}"

            return {
                "success": True,
                "deployment_type": "lambda",
                "function_arn": function_response["FunctionArn"],
                "function_name": app_name,
                "api_gateway_url": api_gateway_url,
                "deployed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Lambda deployment failed: {str(e)}")
            raise

    async def _deploy_to_beanstalk(
        self, project_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Deploy application to Elastic Beanstalk."""
        try:
            # This would implement Elastic Beanstalk deployment
            # Simplified for now
            return {
                "success": True,
                "deployment_type": "beanstalk",
                "application_name": f"{project_id}-beanstalk",
                "environment_url": f"http://{project_id}-env.{self.region}.elasticbeanstalk.com",
                "deployed_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Beanstalk deployment failed: {str(e)}")
            raise

    async def _ensure_ecr_repository(self, repository_name: str) -> Dict[str, Any]:
        """Ensure ECR repository exists, create if it doesn't."""
        try:
            response = self.ecr_client.describe_repositories(
                repositoryNames=[repository_name]
            )
            return response["repositories"][0]

        except self.ecr_client.exceptions.RepositoryNotFoundException:
            # Create repository
            response = self.ecr_client.create_repository(
                repositoryName=repository_name,
                imageTagMutability="MUTABLE",
                imageScanningConfiguration={"scanOnPush": True},
            )
            return response["repository"]

    async def _create_lambda_package(self, code_files: Dict[str, str]) -> bytes:
        """Create a ZIP package for Lambda deployment."""
        with tempfile.NamedTemporaryFile() as temp_file:
            with zipfile.ZipFile(temp_file.name, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for filename, content in code_files.items():
                    zip_file.writestr(filename, content)

            temp_file.seek(0)
            return temp_file.read()

    async def get_deployment_status(
        self, project_id: str, deployment_type: str
    ) -> Dict[str, Any]:
        """Get the current status of a deployment."""
        try:
            if deployment_type == "ecs":
                return await self._get_ecs_status(project_id)
            elif deployment_type == "lambda":
                return await self._get_lambda_status(project_id)
            elif deployment_type == "beanstalk":
                return await self._get_beanstalk_status(project_id)
            else:
                return {
                    "status": "unknown",
                    "error": f"Unknown deployment type: {deployment_type}",
                }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _get_ecs_status(self, project_id: str) -> Dict[str, Any]:
        """Get ECS service status."""
        service_name = f"{project_id}-app-service"
        cluster_name = "multi-agent-generated-apps"

        try:
            response = self.ecs_client.describe_services(
                cluster=cluster_name, services=[service_name]
            )

            if not response["services"]:
                return {"status": "not_found"}

            service = response["services"][0]
            return {
                "status": service["status"].lower(),
                "running_count": service["runningCount"],
                "desired_count": service["desiredCount"],
                "deployment_status": service.get("deploymentConfiguration", {}).get(
                    "deploymentStatus", "unknown"
                ),
            }

        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _get_lambda_status(self, project_id: str) -> Dict[str, Any]:
        """Get Lambda function status."""
        function_name = f"{project_id}-lambda"

        try:
            response = self.lambda_client.get_function(FunctionName=function_name)
            return {
                "status": response["Configuration"]["State"].lower(),
                "last_modified": response["Configuration"]["LastModified"],
            }

        except self.lambda_client.exceptions.ResourceNotFoundException:
            return {"status": "not_found"}
        except Exception as e:
            return {"status": "error", "error": str(e)}

    async def _get_beanstalk_status(self, project_id: str) -> Dict[str, Any]:
        """Get Elastic Beanstalk environment status."""
        # This would implement Beanstalk status checking
        return {"status": "implemented_placeholder"}

    async def cleanup_deployment(
        self, project_id: str, deployment_type: str
    ) -> Dict[str, Any]:
        """Clean up/delete a deployment."""
        try:
            if deployment_type == "ecs":
                return await self._cleanup_ecs_deployment(project_id)
            elif deployment_type == "lambda":
                return await self._cleanup_lambda_deployment(project_id)
            elif deployment_type == "beanstalk":
                return await self._cleanup_beanstalk_deployment(project_id)

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _cleanup_ecs_deployment(self, project_id: str) -> Dict[str, Any]:
        """Clean up ECS deployment."""
        try:
            service_name = f"{project_id}-app-service"
            cluster_name = "multi-agent-generated-apps"

            # Delete ECS service
            self.ecs_client.delete_service(
                cluster=cluster_name, service=service_name, force=True
            )

            return {"success": True, "message": f"ECS service {service_name} deleted"}

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _cleanup_lambda_deployment(self, project_id: str) -> Dict[str, Any]:
        """Clean up Lambda deployment."""
        try:
            function_name = f"{project_id}-lambda"

            # Delete Lambda function
            self.lambda_client.delete_function(FunctionName=function_name)

            return {
                "success": True,
                "message": f"Lambda function {function_name} deleted",
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    async def _cleanup_beanstalk_deployment(self, project_id: str) -> Dict[str, Any]:
        """Clean up Beanstalk deployment."""
        # This would implement Beanstalk cleanup
        return {"success": True, "message": "Beanstalk cleanup placeholder"}
