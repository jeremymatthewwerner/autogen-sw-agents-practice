import os
import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(
    title="Multi-Agent Software Development System",
    description="AI-powered multi-agent system for software development",
    version="1.0.0"
)

class DevelopmentRequest(BaseModel):
    task_description: str
    requirements: Dict[str, Any] = {}

class StatusResponse(BaseModel):
    status: str
    agents_active: int
    current_task: str = None

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "multi-agent-system"}

@app.post("/develop")
async def develop_software(request: DevelopmentRequest):
    try:
        from multi_agent_system import MultiAgentSystem

        system = MultiAgentSystem()
        result = await system.process_development_request(
            request.task_description,
            request.requirements
        )

        return {
            "status": "completed",
            "task": request.task_description,
            "result": result
        }
    except ImportError:
        return {
            "status": "demo_mode",
            "task": request.task_description,
            "result": "Multi-agent system would process this request in production"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    try:
        from multi_agent_system import MultiAgentSystem

        system = MultiAgentSystem()
        status = await system.get_system_status()

        return StatusResponse(**status)
    except ImportError:
        return StatusResponse(
            status="demo_mode",
            agents_active=7,
            current_task="System ready for development requests"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {
        "message": "Multi-Agent Software Development System",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "develop": "/develop",
            "status": "/status"
        }
    }

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)