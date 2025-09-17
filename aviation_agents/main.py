# main.py - Aviation Multi-Agent System with mas-a2a executor pattern
import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uuid
import time
import json
from datetime import datetime, date
import os
import logging

# Local imports
from config.settings import settings
from config.tenant_config import get_tenant_config, list_tenants
from executors import OrchestratorAgentExecutor, HRAgentExecutor, MeetingAgentExecutor, SupplyChainAgentExecutor
from executors.base_executor import RequestContext

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models for API
class ChatRequest(BaseModel):
    message: str
    tenant_id: Optional[str] = "default"
    user_id: Optional[str] = "system"
    agent_type: Optional[str] = "orchestrator"
    context: Optional[Dict[str, Any]] = {}

class ChatResponse(BaseModel):
    response: str
    agent_name: str
    task_id: str
    execution_time: float
    metadata: Dict[str, Any]

class AgentStatusResponse(BaseModel):
    available_agents: List[str]
    available_tenants: List[str]
    system_status: str

# Initialize FastAPI app
app = FastAPI(
    title="Aviation Multi-Agent System",
    description="Multi-tenant aviation agent system with mas-a2a executor pattern",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize agent executors
orchestrator = OrchestratorAgentExecutor()
hr_agent = HRAgentExecutor()
meeting_agent = MeetingAgentExecutor()
supply_chain_agent = SupplyChainAgentExecutor()

# Agent registry
AGENT_REGISTRY = {
    "orchestrator": orchestrator,
    "hr": hr_agent, 
    "meeting": meeting_agent,
    "supply_chain": supply_chain_agent
}

@app.get("/")
async def read_root():
    """Serve the web interface"""
    import os
    if os.path.exists("web/index.html"):
        return FileResponse("web/index.html")
    else:
        return JSONResponse(content={
            "message": "Aviation Multi-Agent System API",
            "version": "2.0.0",
            "endpoints": {
                "chat": "/chat",
                "agents": "/agents",
                "health": "/health"
            },
            "available_agents": list(AGENT_REGISTRY.keys())
        })

# Mount static files only if web directory exists
import os
if os.path.exists("web"):
    app.mount("/static", StaticFiles(directory="web"), name="static")

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """Main chat endpoint using executor pattern"""
    try:
        start_time = time.time()
        
        # Get the appropriate agent executor
        agent_executor = AGENT_REGISTRY.get(request.agent_type, orchestrator)
        
        # Create request context
        context = RequestContext(
            task_id=str(uuid.uuid4()),
            context_id=str(uuid.uuid4()),
            user_message=request.message,
            tenant_id=request.tenant_id,
            user_id=request.user_id
        )
        
        # Execute the agent
        result = await agent_executor.execute(context)
        
        execution_time = time.time() - start_time
        
        # Extract response content
        response_content = "I apologize, but I couldn't process your request."
        if result.get("status") == "completed" and result.get("artifacts"):
            response_content = result["artifacts"][0]["content"]
        elif result.get("status") == "failed":
            response_content = f"I encountered an error: {result.get('error', 'Unknown error')}"
        
        return ChatResponse(
            response=response_content,
            agent_name=result.get("agent_name", "Unknown Agent"),
            task_id=context.task_id,
            execution_time=execution_time,
            metadata={
                "tenant_id": request.tenant_id,
                "agent_type": request.agent_type,
                "status": result.get("status", "unknown"),
                "artifacts_count": len(result.get("artifacts", []))
            }
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/agents", response_model=AgentStatusResponse) 
async def get_agents_status():
    """Get available agents and system status"""
    try:
        return AgentStatusResponse(
            available_agents=list(AGENT_REGISTRY.keys()),
            available_tenants=list_tenants(),
            system_status="operational"
        )
    except Exception as e:
        logger.error(f"Agents status error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/agents/{agent_type}/status")
async def get_agent_status(agent_type: str):
    """Get specific agent status"""
    if agent_type not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
    
    agent = AGENT_REGISTRY[agent_type]
    return {
        "agent_name": agent.agent_name,
        "agent_type": agent.agent_type,
        "model": agent.model,
        "status": "ready"
    }

@app.post("/agents/{agent_type}/chat")
async def chat_with_specific_agent(agent_type: str, request: ChatRequest):
    """Chat with a specific agent directly"""
    if agent_type not in AGENT_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Agent {agent_type} not found")
    
    # Override the agent type in the request
    request.agent_type = agent_type
    return await chat_endpoint(request)

@app.get("/tenants")
async def get_tenants():
    """Get available tenants"""
    try:
        tenants = list_tenants()
        return {"tenants": tenants}
    except Exception as e:
        logger.error(f"Tenants endpoint error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/tenants/{tenant_id}/config")
async def get_tenant_config_endpoint(tenant_id: str):
    """Get tenant-specific configuration"""
    try:
        config = get_tenant_config(tenant_id)
        return {"tenant_id": tenant_id, "config": config}
    except Exception as e:
        logger.error(f"Tenant config error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agents": len(AGENT_REGISTRY),
        "model": settings.default_model
    }

if __name__ == "__main__":
    print("🛫 Starting Aviation Multi-Agent System with mas-a2a executors...")
    print(f"🔧 Using Ollama model: {settings.default_model}")
    print("🌐 Server will be available at: http://0.0.0.0:8000")
    print("📱 Web interface: http://localhost:8000")
    print("ℹ️  System will work with or without Ollama running")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        log_level="info"
    )