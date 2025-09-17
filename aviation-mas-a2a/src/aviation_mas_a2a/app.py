"""
Main FastAPI application for Aviation MAS-A2A System
"""
import asyncio
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from loguru import logger

from .shared.config import config
from .agents.agent_manager import AgentManager
from .mcp_servers.hr_tools import HRTools
from .mcp_servers.meeting_tools import MeetingTools
from .mcp_servers.supply_chain_tools import SupplyChainTools


# Pydantic models for API requests
class MessageRequest(BaseModel):
    message: str
    target_agent: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ConversationRequest(BaseModel):
    conversation_id: str
    participants: List[str]


class BroadcastRequest(BaseModel):
    message: str
    exclude_agents: Optional[List[str]] = None


# Initialize FastAPI app
app = FastAPI(
    title="Aviation MAS-A2A System",
    description="Multi-Agent System for Aviation Operations",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
agent_manager: Optional[AgentManager] = None
mcp_servers: Dict[str, Any] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    global agent_manager, mcp_servers
    
    try:
        logger.info("Starting Aviation MAS-A2A System...")
        
        # Initialize agent manager
        agent_manager = AgentManager()
        await agent_manager.initialize_agents()
        
        # Initialize MCP servers
        mcp_servers = {
            "hr": HRTools(),
            "meeting": MeetingTools(),
            "supply_chain": SupplyChainTools()
        }
        
        # Start MCP servers in background
        asyncio.create_task(start_mcp_servers())
        
        logger.info("Aviation MAS-A2A System started successfully")
        
    except Exception as e:
        logger.error(f"Failed to start system: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    global agent_manager
    
    try:
        logger.info("Shutting down Aviation MAS-A2A System...")
        
        if agent_manager:
            await agent_manager.shutdown()
        
        logger.info("System shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


async def start_mcp_servers():
    """Start all MCP servers"""
    try:
        tasks = []
        
        # Start HR tools server
        tasks.append(
            asyncio.create_task(
                mcp_servers["hr"].start_server(config.mcp_base_port + 1)
            )
        )
        
        # Start Meeting tools server
        tasks.append(
            asyncio.create_task(
                mcp_servers["meeting"].start_server(config.mcp_base_port + 2)
            )
        )
        
        # Start Supply Chain tools server
        tasks.append(
            asyncio.create_task(
                mcp_servers["supply_chain"].start_server(config.mcp_base_port + 3)
            )
        )
        
        # Wait for all servers to start
        await asyncio.gather(*tasks)
        
    except Exception as e:
        logger.error(f"Failed to start MCP servers: {e}")


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Aviation MAS-A2A System",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        status = await agent_manager.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/message")
async def send_message(request: MessageRequest):
    """Send a message to an agent"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        response = await agent_manager.route_message(
            message=request.message,
            target_agent=request.target_agent,
            context=request.context
        )
        return response
    except Exception as e:
        logger.error(f"Failed to send message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/conversation")
async def start_conversation(request: ConversationRequest):
    """Start a new conversation between agents"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        response = await agent_manager.start_conversation(
            conversation_id=request.conversation_id,
            participants=request.participants
        )
        return response
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/broadcast")
async def broadcast_message(request: BroadcastRequest):
    """Broadcast a message to all agents"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        response = await agent_manager.broadcast_message(
            message=request.message,
            exclude_agents=request.exclude_agents
        )
        return response
    except Exception as e:
        logger.error(f"Failed to broadcast message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents")
async def list_agents():
    """List all available agents"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        agents = list(agent_manager.agents.keys())
        return {
            "status": "success",
            "agents": agents,
            "total": len(agents)
        }
    except Exception as e:
        logger.error(f"Failed to list agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/agents/{agent_type}/status")
async def get_agent_status(agent_type: str):
    """Get status of a specific agent"""
    if not agent_manager:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        agent = await agent_manager.get_agent(agent_type)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found")
        
        status = await agent.get_status()
        return status
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get agent status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/mcp/tools")
async def list_mcp_tools():
    """List all available MCP tools"""
    try:
        tools = {}
        
        for server_name, server in mcp_servers.items():
            if hasattr(server, 'get_tools'):
                server_tools = server.get_tools()
                tools[server_name] = [tool.__name__ if hasattr(tool, '__name__') else str(tool) for tool in server_tools]
        
        return {
            "status": "success",
            "mcp_servers": tools
        }
    except Exception as e:
        logger.error(f"Failed to list MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "aviation_mas_a2a.app:app",
        host=config.server_host,
        port=config.server_port,
        reload=config.debug
    )