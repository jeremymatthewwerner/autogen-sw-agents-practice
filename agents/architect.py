"""System Architect Agent for technical design."""

import json
from typing import Any, Dict

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
            llm_config=config["llm_config"],
        )

    async def create_architecture(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Create system architecture based on requirements using Claude."""

        architecture_prompt = f"""
        As a System Architect, design a comprehensive technical architecture for this project.

        Requirements Analysis:
        - Project Type: {requirements.get('project_type', 'web_application')}
        - Complexity: {requirements.get('estimated_complexity', 'Medium')}
        - Functional Requirements: {requirements.get('functional_requirements', [])}
        - Non-functional Requirements: {requirements.get('non_functional_requirements', {})}
        - Recommended Tech Stack: {requirements.get('recommended_tech_stack', [])}
        - User Stories: {len(requirements.get('user_stories', []))} stories defined

        Design a production-ready architecture with:

        1. **System Overview** - architecture pattern, deployment model
        2. **Technology Stack** - backend framework, database, frontend (if needed), deployment tools
        3. **Component Architecture** - major system components and their responsibilities
        4. **API Design** - RESTful endpoints based on the user stories (list specific endpoints with HTTP methods)
        5. **Data Model** - database schema with specific tables, fields, and relationships
        6. **Security Architecture** - authentication strategy, authorization, data protection
        7. **Deployment Architecture** - containerization, orchestration, cloud services
        8. **Project File Structure** - Specify the exact directory structure and key files needed:
           ```
           project_root/
           ├── main.py
           ├── models.py
           ├── database.py
           ├── requirements.txt
           ├── Dockerfile
           ├── tests/
           │   └── test_api.py
           └── README.md
           ```
        9. **Technical Decisions** - rationale for major technology choices

        Focus on Python-based solutions (FastAPI, Django, Flask) but adapt based on requirements.
        Provide specific, implementable recommendations with clear justifications.
        Be concrete and detailed so backend developers can implement exactly what you specify.
        """

        try:
            response = await self.process_request_async(architecture_prompt)

            if response["status"] == "success":
                return {
                    "architecture_analysis": response["response"],
                    "design_method": "claude_powered",
                    "based_on_requirements": True,
                    "requirements_summary": {
                        "project_type": requirements.get("project_type"),
                        "complexity": requirements.get("estimated_complexity"),
                        "feature_count": len(requirements.get("user_stories", [])),
                    },
                }
            else:
                raise Exception(f"Architecture design failed: {response.get('error')}")

        except Exception as e:
            # Fallback architecture
            return {
                "error": str(e),
                "fallback_architecture": True,
                "basic_stack": {
                    "backend": "FastAPI",
                    "database": "PostgreSQL",
                    "deployment": "Docker",
                },
            }

    def process_request(
        self, message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process architecture design request."""
        try:
            requirements = (
                context.get("dependency_Analyze Requirements", {})
                .get("output", {})
                .get("structured_requirements", {})
            )

            if not requirements:
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No structured requirements found in context",
                }

            # Use Claude-powered architecture design
            import asyncio

            architecture = asyncio.run(self.create_architecture(requirements))

            return {
                "agent": self.name,
                "status": "success",
                "output": {
                    "architecture": architecture,
                    "design_method": architecture.get(
                        "design_method", "claude_powered"
                    ),
                    "based_on_requirements": architecture.get(
                        "based_on_requirements", True
                    ),
                    "requirements_used": architecture.get("requirements_summary", {}),
                },
            }

        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}
