"""Documentation Agent for generating end-user documentation."""

from typing import Dict, Any
from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class DocumentationAgent(BaseAgent):
    """Handles creation of comprehensive user documentation for generated applications."""

    def __init__(self):
        """Initialize the Documentation Agent."""
        config = get_agent_config("documentation_agent")
        super().__init__(
            name="DocumentationAgent",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"]
        )

    async def generate_user_documentation(self, project_context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive user documentation using Claude."""

        # Extract context from other agents
        requirements = project_context.get('requirements', {})
        architecture = project_context.get('architecture', {})
        backend_code = project_context.get('backend_code', {})
        tests = project_context.get('tests', {})
        deployment = project_context.get('deployment', {})

        documentation_prompt = f"""
        As a Technical Documentation Writer, create comprehensive, user-friendly documentation for this software application.

        Project Context:
        - Application Type: {requirements.get('project_type', 'web_application')}
        - Project Summary: {requirements.get('project_summary', 'Software application')}
        - Complexity: {requirements.get('estimated_complexity', 'Medium')}
        - User Stories: {len(requirements.get('user_stories', []))} features implemented
        - Architecture: {architecture.get('design_method', 'System architecture defined')}
        - Deployment: {deployment.get('deployment_type', 'cloud deployment')}

        Generate the following documentation files:

        1. **README.md** - Main project overview with:
           - Project title and description
           - Key features and capabilities
           - Quick start guide
           - Prerequisites and requirements
           - Installation instructions
           - Basic usage examples

        2. **USER_GUIDE.md** - Comprehensive user guide with:
           - Detailed feature explanations
           - Step-by-step workflows
           - Screenshots placeholders [Screenshot: feature-name]
           - Common use cases and examples
           - Tips and best practices

        3. **API_DOCUMENTATION.md** - API reference (if applicable) with:
           - Authentication requirements
           - Available endpoints
           - Request/response examples
           - Error codes and handling
           - Rate limiting information

        4. **INSTALLATION.md** - Detailed setup instructions with:
           - System requirements
           - Environment setup
           - Database configuration
           - Environment variables
           - Troubleshooting guide

        5. **FAQ.md** - Frequently asked questions with:
           - Common issues and solutions
           - Performance tips
           - Security considerations
           - How-to guides for advanced features

        6. **CHANGELOG.md** - Version history template with:
           - Version 1.0.0 initial release
           - Future version structure
           - Feature tracking format

        Writing Guidelines:
        - Use clear, non-technical language for end users
        - Include practical examples and use cases
        - Add troubleshooting sections
        - Make it beginner-friendly
        - Include security and best practices
        - Add placeholders for screenshots/images
        - Provide multiple learning paths (quick start vs comprehensive)

        Focus on creating documentation that helps users:
        1. Understand what the application does
        2. Get started quickly
        3. Use all features effectively
        4. Troubleshoot common issues
        5. Follow best practices
        """

        try:
            response = await self.process_request_async(documentation_prompt)

            if response["status"] == "success":
                return {
                    "documentation": response["response"],
                    "generation_method": "claude_powered",
                    "documentation_types": [
                        "README", "User Guide", "API Docs",
                        "Installation Guide", "FAQ", "Changelog"
                    ],
                    "target_audience": "end_users",
                    "completeness": "comprehensive"
                }
            else:
                raise Exception(f"Documentation generation failed: {response.get('error')}")

        except Exception as e:
            # Fallback basic documentation
            basic_docs = {
                "README.md": f"""# {requirements.get('project_summary', 'Application')}

## Overview
This application was automatically generated using an AI multi-agent system.

## Quick Start
1. Follow the installation instructions
2. Configure your environment
3. Run the application
4. Access via web browser

## Features
- User authentication
- Data management
- Web interface
- API access

## Support
Check the user guide and FAQ for detailed information.
""",
                "USER_GUIDE.md": "# User Guide\n\nDetailed user documentation to be generated.",
            }

            return {
                "error": str(e),
                "fallback_documentation": True,
                "basic_files": basic_docs,
                "generation_method": "fallback_template"
            }

    def process_request(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process documentation generation request."""
        try:
            # Gather context from all previous agents
            project_context = {
                'requirements': context.get("dependency_Analyze Requirements", {}).get("output", {}).get("structured_requirements", {}),
                'architecture': context.get("dependency_Design Architecture", {}).get("output", {}).get("architecture", {}),
                'backend_code': context.get("dependency_Implement Backend", {}).get("output", {}),
                'tests': context.get("dependency_Write Tests", {}).get("output", {}),
                'deployment': context.get("dependency_Prepare Deployment", {}).get("output", {})
            }

            if not any(project_context.values()):
                return {
                    "agent": self.name,
                    "status": "error",
                    "error": "No project context found from previous agents"
                }

            # Generate intelligent user documentation
            import asyncio
            documentation_result = asyncio.run(self.generate_user_documentation(project_context))

            return {
                "agent": self.name,
                "status": "success",
                "output": documentation_result
            }

        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}