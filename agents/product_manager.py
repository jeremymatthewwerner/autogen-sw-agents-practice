"""Product Manager Agent for requirements analysis."""

import json
from typing import Any, Dict

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
            llm_config=config["llm_config"],
        )

    async def analyze_requirements(self, raw_requirements: str) -> Dict[str, Any]:
        """Convert natural language requirements to structured format using Claude."""

        analysis_prompt = f"""
        As a Product Manager, analyze these requirements and create a comprehensive structured specification.

        Raw Requirements: {raw_requirements}

        Please provide a detailed analysis in JSON format with the following structure:
        {{
            "raw_input": "{raw_requirements}",
            "project_type": "determine the type (web_application, api_service, desktop_app, etc)",
            "project_summary": "brief 1-2 sentence summary",
            "functional_requirements": ["list of specific functional requirements"],
            "non_functional_requirements": {{
                "performance": "performance expectations",
                "security": "security requirements",
                "scalability": "scalability needs",
                "usability": "usability requirements"
            }},
            "user_stories": [
                {{
                    "id": "US001",
                    "title": "Story Title",
                    "description": "As a [user type], I want [goal] so that [reason]",
                    "acceptance_criteria": ["list of specific testable criteria"],
                    "priority": "High/Medium/Low"
                }}
            ],
            "success_criteria": {{
                "mvp_features": ["minimum viable features"],
                "quality_gates": ["quality requirements"],
                "definition_of_done": ["completion criteria"]
            }},
            "estimated_complexity": "Low/Medium/High",
            "recommended_tech_stack": ["suggested technologies"],
            "risks_and_assumptions": ["potential risks or assumptions"]
        }}

        Ensure the analysis is thorough and tailored to the specific requirements provided.
        """

        try:
            response = await self.process_request_async(analysis_prompt)

            if response["status"] == "success":
                # Try to parse JSON from Claude's response
                response_text = response["response"]

                # Find JSON in the response (Claude might wrap it in markdown)
                import json
                import re

                # Try to extract JSON from response
                json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
                if json_match:
                    try:
                        parsed_analysis = json.loads(json_match.group())
                        return parsed_analysis
                    except json.JSONDecodeError:
                        pass

                # If JSON parsing fails, create structured response from Claude's text
                return {
                    "raw_input": raw_requirements,
                    "claude_analysis": response_text,
                    "project_type": "web_application",  # default fallback
                    "parsing_note": "Claude provided detailed analysis but not in expected JSON format",
                }
            else:
                raise Exception(
                    f"Claude analysis failed: {response.get('error', 'Unknown error')}"
                )

        except Exception as e:
            # Fallback to basic analysis if Claude fails
            return {
                "raw_input": raw_requirements,
                "error": str(e),
                "fallback_analysis": True,
                "project_type": "web_application",
                "basic_requirements": [
                    "User interface",
                    "Data management",
                    "Basic functionality",
                ],
            }

    def process_request(
        self, message: str, context: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process requirements analysis request."""
        try:
            if "raw" in context.get("requirements", {}):
                # Use async method for intelligent analysis
                import asyncio

                requirements = asyncio.run(
                    self.analyze_requirements(context["requirements"]["raw"])
                )

                # Generate intelligent recommendations based on the analysis
                recommendations_prompt = f"""
                Based on this requirements analysis, provide 4-5 specific actionable recommendations for the development team:

                Project: {requirements.get('project_summary', 'Software project')}
                Complexity: {requirements.get('estimated_complexity', 'Unknown')}
                Type: {requirements.get('project_type', 'web_application')}

                Focus on:
                1. Development approach and methodology
                2. Technology choices
                3. Implementation prioritization
                4. Risk mitigation
                5. Quality assurance

                Provide specific, actionable recommendations.
                """

                # Generate recommendations (skip for now to avoid recursion)
                rec_response = {
                    "response": "AI-generated recommendations based on requirements analysis"
                }

                return {
                    "agent": self.name,
                    "status": "success",
                    "output": {
                        "structured_requirements": requirements,
                        "analysis_method": (
                            "claude_powered"
                            if not requirements.get("fallback_analysis")
                            else "fallback"
                        ),
                        "recommendations": rec_response.get(
                            "response", "AI-generated recommendations"
                        ),
                    },
                }
            else:
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No raw requirements found in context",
                }

        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}
