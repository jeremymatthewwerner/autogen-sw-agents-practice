"""Backend Developer Agent for server-side implementation."""

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

    def process_request(self, message: str, context=None):
        """Generate backend code based on architecture."""
        try:
            # Simplified backend generation
            code_files = {
                "main.py": """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Generated API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "API is running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
""",
                "requirements.txt": """fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.7
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
""",
                "Dockerfile": """FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
            }

            return {
                "agent": self.name,
                "status": "success",
                "output": {"code_files": code_files}
            }
        except Exception as e:
            return {"agent": self.name, "status": "error", "error": str(e)}