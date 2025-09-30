import os
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Dict, Any, List
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Multi-Agent Software Development System",
    description="AI-powered multi-agent system for software development",
    version="1.0.0",
)

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize the multi-agent system once at startup
from multi_agent_system import MultiAgentSystem

multi_agent_system = MultiAgentSystem()


class DevelopmentRequest(BaseModel):
    task_description: str
    requirements: Dict[str, Any] = {}


class AgentStatus(BaseModel):
    name: str
    status: str  # "ready", "working", "idle"
    current_task: str = ""


class StatusResponse(BaseModel):
    status: str
    agents_active: int
    current_task: str = None
    agents: List[AgentStatus] = []


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multi-agent-system"}


@app.post("/develop")
async def develop_software(request: DevelopmentRequest):
    try:
        result = await multi_agent_system.process_development_request(
            request.task_description, request.requirements
        )

        return {
            "status": "completed",
            "task": request.task_description,
            "result": result,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/status")
async def get_status():
    try:
        status = await multi_agent_system.get_system_status()
        return StatusResponse(**status)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api")
async def api_info():
    return {
        "message": "Multi-Agent Software Development System",
        "version": "1.0.0",
        "endpoints": {"health": "/health", "develop": "/develop", "status": "/status"},
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
