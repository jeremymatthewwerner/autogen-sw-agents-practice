"""Product Manager Agent for requirements analysis."""

from typing import Dict, Any
import json

from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class ProductManagerAgent(BaseAgent):
    """Handles requirements analysis and user story creation."""

    def __init__(self):
        """Initialize the Product Manager Agent."""
        config = get_agent_config("product_manager")
        super().__init__(
            name="ProductManager",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"]
        )

    def analyze_requirements(self, raw_requirements: str) -> Dict[str, Any]:
        """Convert natural language requirements to structured format."""
        # This is a simplified implementation
        # In production, this would use Claude to analyze and structure requirements

        structured_requirements = {
            "raw_input": raw_requirements,
            "project_type": "web_application",
            "functional_requirements": [
                "User authentication",
                "Data management",
                "API endpoints",
                "Web interface"
            ],
            "non_functional_requirements": {
                "performance": "Standard response times < 2s",
                "security": "Basic authentication and input validation",
                "scalability": "Single instance deployment"
            },
            "user_stories": [
                {
                    "id": "US001",
                    "title": "User Registration",
                    "description": "As a user, I want to register an account so that I can access the application",
                    "acceptance_criteria": [
                        "User can enter email and password",
                        "System validates input",
                        "User receives confirmation"
                    ]
                },
                {
                    "id": "US002",
                    "title": "Data Management",
                    "description": "As a user, I want to manage my data so that I can perform CRUD operations",
                    "acceptance_criteria": [
                        "User can create new records",
                        "User can view existing records",
                        "User can update records",
                        "User can delete records"
                    ]
                }
            ],
            "success_criteria": {
                "mvp_features": ["Authentication", "CRUD operations", "Basic UI"],
                "quality_gates": ["80% test coverage", "No security vulnerabilities"]
            }
        }

        return structured_requirements

    def process_request(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process requirements analysis request."""
        try:
            if "raw" in context.get("requirements", {}):
                requirements = self.analyze_requirements(context["requirements"]["raw"])

                return {
                    "agent": self.name,
                    "status": "success",
                    "output": {
                        "structured_requirements": requirements,
                        "recommendations": [
                            "Start with MVP features",
                            "Implement authentication first",
                            "Use FastAPI for rapid development",
                            "Focus on API-first design"
                        ]
                    }
                }
            else:
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No raw requirements found in context"
                }

        except Exception as e:
            return {
                "agent": self.name,
                "status": "error",
                "error": str(e)
            }