"""DevOps Engineer Agent for deployment."""

from typing import Any, Dict

from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class DevOpsEngineerAgent(BaseAgent):
    """Handles deployment and infrastructure."""

    def __init__(self):
        config = get_agent_config("devops_engineer")
        super().__init__(
            name="DevOpsEngineer",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"],
        )

    async def generate_deployment_config(
        self,
        backend_code: Dict[str, Any],
        architecture: Dict[str, Any],
        requirements: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate deployment configuration using Claude."""

        project_type = requirements.get("project_type", "web_application")
        complexity = requirements.get("estimated_complexity", "Medium")
        non_functional_reqs = requirements.get("non_functional_requirements", {})

        deployment_prompt = f"""
        As a Senior DevOps Engineer, create production-ready deployment configurations for this application.

        Project Context:
        - Type: {project_type}
        - Complexity: {complexity}
        - Performance Requirements: {non_functional_reqs.get('performance', 'Standard')}
        - Scalability Needs: {non_functional_reqs.get('scalability', 'Single instance')}
        - Security Requirements: {non_functional_reqs.get('security', 'Basic')}
        - Backend Framework: {backend_code.get('framework', 'FastAPI')}
        - Architecture: {architecture.get('design_method', 'claude_designed')}

        Generate complete deployment files:

        1. **Dockerfile** - Multi-stage production container:
           - Optimized for Python applications
           - Security best practices
           - Minimal image size
           - Health checks

        2. **docker-compose.yml** - Local development stack:
           - Application service
           - Database service
           - Environment configuration
           - Volume management
           - Networking setup

        3. **docker-compose.prod.yml** - Production configuration:
           - Production optimizations
           - Resource limits
           - Security hardening
           - Monitoring setup

        4. **.env.example** - Environment template:
           - All required environment variables
           - Security configurations
           - Database settings

        5. **kubernetes.yaml** - K8s deployment (if scalable):
           - Deployment, Service, Ingress
           - ConfigMaps and Secrets
           - Resource quotas
           - Health checks

        6. **nginx.conf** - Reverse proxy configuration:
           - Load balancing
           - SSL termination
           - Security headers

        Focus on:
        - Production readiness
        - Security best practices
        - Scalability considerations
        - Monitoring and logging
        - Easy deployment process

        Provide complete, working configuration files.
        """

        try:
            response = await self.process_request_async(deployment_prompt)

            if response["status"] == "success":
                return {
                    "deployment_config": response["response"],
                    "generation_method": "claude_powered",
                    "deployment_type": "containerized",
                    "scalability": complexity,
                    "security_level": non_functional_reqs.get("security", "basic"),
                    "ready_for_production": True,
                }
            else:
                raise Exception(
                    f"Deployment configuration failed: {response.get('error')}"
                )

        except Exception as e:
            # Fallback basic config
            basic_config = {
                "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
""",
                ".env.example": """DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-me-in-production
""",
            }

            return {
                "error": str(e),
                "fallback_config": True,
                "basic_files": basic_config,
                "generation_method": "fallback_template",
            }

    def process_request(self, message: str, context=None):
        """Generate deployment configuration."""
        try:
            # Get inputs from context
            backend_code = context.get("dependency_Implement Backend", {}).get(
                "output", {}
            )
            architecture = (
                context.get("dependency_Design Architecture", {})
                .get("output", {})
                .get("architecture", {})
            )
            requirements = (
                context.get("dependency_Analyze Requirements", {})
                .get("output", {})
                .get("structured_requirements", {})
            )

            if not any([backend_code, architecture, requirements]):
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No backend code, architecture, or requirements found in context",
                }

            # Generate intelligent deployment configuration
            import asyncio

            deployment_result = asyncio.run(
                self.generate_deployment_config(
                    backend_code, architecture, requirements
                )
            )

            return {
                "agent": self.name,
                "status": "success",
                "output": deployment_result,
            }

        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}
