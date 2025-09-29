"""System Architect Agent for technical design."""

from typing import Dict, Any
import json

from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class ArchitectAgent(BaseAgent):
    """Handles system architecture and technical design."""

    def __init__(self):
        """Initialize the Architect Agent."""
        config = get_agent_config("architect")
        super().__init__(
            name="Architect",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"]
        )

    def create_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create system architecture based on requirements."""

        architecture = {
            "system_overview": {
                "type": "web_application",
                "pattern": "layered_architecture",
                "deployment": "cloud_native"
            },
            "technology_stack": {
                "backend": {
                    "framework": "FastAPI",
                    "language": "Python 3.11+",
                    "async": True,
                    "orm": "SQLAlchemy"
                },
                "database": {
                    "primary": "PostgreSQL",
                    "connection_pool": True,
                    "migrations": "Alembic"
                },
                "frontend": {
                    "framework": "HTML/CSS/JavaScript",
                    "ui_library": "Bootstrap",
                    "build_tool": "None (simple)"
                },
                "deployment": {
                    "containerization": "Docker",
                    "orchestration": "Docker Compose",
                    "cloud": "Any (GCP/AWS/Azure)"
                }
            },
            "components": {
                "api_gateway": {
                    "responsibility": "Request routing and authentication",
                    "technology": "FastAPI built-in"
                },
                "business_logic": {
                    "responsibility": "Core application logic",
                    "technology": "Python modules"
                },
                "data_access": {
                    "responsibility": "Database operations",
                    "technology": "SQLAlchemy ORM"
                },
                "authentication": {
                    "responsibility": "User authentication and authorization",
                    "technology": "JWT tokens"
                }
            },
            "api_design": {
                "style": "RESTful",
                "versioning": "URL path versioning (/api/v1/)",
                "documentation": "OpenAPI/Swagger",
                "endpoints": [
                    {"method": "POST", "path": "/api/v1/auth/register", "description": "User registration"},
                    {"method": "POST", "path": "/api/v1/auth/login", "description": "User login"},
                    {"method": "GET", "path": "/api/v1/items", "description": "List items"},
                    {"method": "POST", "path": "/api/v1/items", "description": "Create item"},
                    {"method": "GET", "path": "/api/v1/items/{id}", "description": "Get item"},
                    {"method": "PUT", "path": "/api/v1/items/{id}", "description": "Update item"},
                    {"method": "DELETE", "path": "/api/v1/items/{id}", "description": "Delete item"}
                ]
            },
            "data_model": {
                "user": {
                    "fields": ["id", "email", "password_hash", "created_at", "updated_at"],
                    "relationships": ["items"]
                },
                "item": {
                    "fields": ["id", "title", "description", "user_id", "created_at", "updated_at"],
                    "relationships": ["user"]
                }
            },
            "security": {
                "authentication": "JWT tokens",
                "authorization": "Role-based",
                "input_validation": "Pydantic models",
                "password_hashing": "bcrypt",
                "cors": "Configured for frontend"
            },
            "deployment_architecture": {
                "containers": {
                    "api": "FastAPI application",
                    "database": "PostgreSQL",
                    "nginx": "Reverse proxy (optional)"
                },
                "networking": "Docker network",
                "volumes": "Database persistence",
                "environment": "Environment variables for config"
            }
        }

        return architecture

    def process_request(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process architecture design request."""
        try:
            requirements = context.get("dependency_Analyze Requirements", {}).get("output", {}).get("structured_requirements", {})

            if not requirements:
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No structured requirements found in context"
                }

            architecture = self.create_architecture(requirements)

            return {
                "agent": self.name,
                "status": "success",
                "output": {
                    "architecture": architecture,
                    "technical_decisions": [
                        "FastAPI chosen for modern async Python development",
                        "PostgreSQL for reliable data persistence",
                        "JWT for stateless authentication",
                        "Docker for consistent deployment",
                        "RESTful API design for simplicity"
                    ],
                    "next_steps": [
                        "Setup project structure",
                        "Implement database models",
                        "Create API endpoints",
                        "Setup authentication"
                    ]
                }
            }

        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e)
            }