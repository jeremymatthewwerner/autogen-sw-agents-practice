"""Backend Developer Agent for server-side implementation."""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class BackendDeveloperAgent(BaseAgent):
    """Handles backend development and API implementation."""

    def __init__(self):
        config = get_agent_config("backend_developer")
        super().__init__(
            name="BackendDeveloper",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"]
        )

    async def generate_backend_code(self, architecture: Dict[str, Any], requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate backend code based on architecture and requirements using Claude."""

        # Extract key information for code generation
        project_type = requirements.get('project_type', 'web_application')
        user_stories = requirements.get('user_stories', [])
        functional_requirements = requirements.get('functional_requirements', [])

        code_generation_prompt = f"""
        As a Senior Backend Developer, generate production-ready Python code for this project.

        Project Context:
        - Type: {project_type}
        - Functional Requirements: {functional_requirements}
        - User Stories: {len(user_stories)} stories defined
        - Architecture: {architecture.get('architecture_analysis', 'FastAPI-based system')}

        Generate the following files:

        1. **main.py** - FastAPI application with:
           - Proper app configuration
           - CORS middleware
           - Authentication middleware
           - Error handling
           - API endpoints based on user stories
           - Health check endpoint

        2. **models.py** - Database models using SQLAlchemy:
           - User model with authentication fields
           - Business domain models based on requirements
           - Proper relationships and constraints

        3. **auth.py** - Authentication system:
           - JWT token handling
           - Password hashing
           - Login/register endpoints

        4. **database.py** - Database configuration:
           - SQLAlchemy setup
           - Database connection handling
           - Migration support

        5. **requirements.txt** - All necessary dependencies

        6. **Dockerfile** - Production-ready container setup

        Focus on:
        - Security best practices
        - Proper error handling
        - Input validation with Pydantic
        - Clean, maintainable code
        - Production readiness

        Provide complete, working code files that can be immediately deployed.
        """

        try:
            response = await self.process_request_async(code_generation_prompt)

            if response["status"] == "success":
                return {
                    "generated_code": response["response"],
                    "generation_method": "claude_powered",
                    "based_on_architecture": True,
                    "requirements_implemented": len(user_stories),
                    "code_language": "Python",
                    "framework": "FastAPI"
                }
            else:
                raise Exception(f"Code generation failed: {response.get('error')}")

        except Exception as e:
            # Fallback to basic template
            basic_code = {
                "main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Generated API")

app.add_middleware(CORSMiddleware, allow_origins=["*"])

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
""",
                "requirements.txt": "fastapi==0.104.1\nuvicorn[standard]==0.24.0"
            }

            return {
                "error": str(e),
                "fallback_code": True,
                "basic_files": basic_code,
                "generation_method": "fallback_template"
            }

    def process_request(self, message: str, context=None):
        """Generate backend code based on architecture."""
        try:
            # Get architecture and requirements from context
            architecture = context.get("dependency_Design Architecture", {}).get("output", {}).get("architecture", {})
            requirements = context.get("dependency_Analyze Requirements", {}).get("output", {}).get("structured_requirements", {})

            if not architecture and not requirements:
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No architecture or requirements found in context"
                }

            # Generate intelligent backend code
            import asyncio
            code_result = asyncio.run(self.generate_backend_code(architecture, requirements))

            return {
                "agent": self.name,
                "status": "success",
                "output": code_result
            }

        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}