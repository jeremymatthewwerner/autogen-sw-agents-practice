"""DevOps Engineer Agent for deployment."""

from agents.base_agent import BaseAgent
from config.agent_config import get_agent_config


class DevOpsEngineerAgent(BaseAgent):
    """Handles deployment and infrastructure."""

    def __init__(self):
        config = get_agent_config("devops_engineer")
        super().__init__(
            name="DevOpsEngineer",
            system_prompt=config["system_prompt"],
            llm_config=config["llm_config"]
        )

    def process_request(self, message: str, context=None):
        """Generate deployment configuration."""
        deployment_files = {
            "docker-compose.yml": """version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/app
    depends_on:
      - db

  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=app
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
""",
            ".env.example": """DATABASE_URL=postgresql://user:pass@localhost:5432/app
SECRET_KEY=your-secret-key
"""
        }

        return {
            "agent": self.name,
            "status": "success",
            "output": {"deployment_files": deployment_files}
        }