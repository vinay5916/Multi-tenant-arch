"""
Main entry point for Aviation MAS-A2A System
"""
import asyncio
import uvicorn
from src.aviation_mas_a2a.app import app
from src.aviation_mas_a2a.shared.config import config
from src.aviation_mas_a2a.shared.logging_config import setup_logging


async def main():
    """Main application entry point"""
    # Setup logging
    setup_logging()
    
    print("=" * 50)
    print("Aviation MAS-A2A System")
    print("Multi-Agent System for Aviation Operations")
    print(f"Server: http://{config.server_host}:{config.server_port}")
    print(f"MCP Base Port: {config.mcp_base_port}")
    print("=" * 50)
    
    # Start the FastAPI server
    uvicorn.run(
        app,
        host=config.server_host,
        port=config.server_port,
        reload=config.debug
    )


if __name__ == "__main__":
    asyncio.run(main())
