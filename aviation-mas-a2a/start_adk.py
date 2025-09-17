"""
Startup script for Aviation MAS-A2A system with ADK web interface
"""
import os
import sys
import asyncio
import subprocess
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from aviation_mas_a2a.shared.logging_config import setup_logging
from aviation_mas_a2a.mcp_servers.hr_tools import HRTools
from aviation_mas_a2a.mcp_servers.meeting_tools import MeetingTools
from aviation_mas_a2a.mcp_servers.supply_chain_tools import SupplyChainTools


async def start_mcp_servers():
    """Start all MCP servers in background"""
    print("Starting MCP servers...")
    
    # Start HR tools server
    hr_tools = HRTools()
    asyncio.create_task(hr_tools.start_server(8001))
    
    # Start Meeting tools server
    meeting_tools = MeetingTools()
    asyncio.create_task(meeting_tools.start_server(8002))
    
    # Start Supply Chain tools server
    supply_chain_tools = SupplyChainTools()
    asyncio.create_task(supply_chain_tools.start_server(8003))
    
    print("MCP servers started on ports 8001-8003")
    
    # Give servers time to start
    await asyncio.sleep(2)


def start_adk_web():
    """Start ADK web interface"""
    print("Starting ADK web interface...")
    
    # Activate virtual environment and run ADK web
    venv_python = project_root / ".venv" / "Scripts" / "python.exe"
    
    if not venv_python.exists():
        print("❌ Virtual environment not found. Please run 'uv sync' first.")
        return False
    
    try:
        # Change to project directory
        os.chdir(project_root)
        
        # Run ADK web with the agent
        cmd = [
            str(venv_python), 
            "-m", "google.adk.web",
            "--agent-path", "src/aviation_mas_a2a/agents/base_agent_adk.py",
            "--host", "0.0.0.0",
            "--port", "8000"
        ]
        
        print(f"Running command: {' '.join(cmd)}")
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to start ADK web: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Shutting down ADK web interface...")
        return True


async def main():
    """Main startup function"""
    print("=" * 60)
    print("🚁 Aviation MAS-A2A System - Starting Up")
    print("=" * 60)
    
    # Setup logging
    setup_logging()
    
    try:
        # Start MCP servers first
        await start_mcp_servers()
        
        print("\n✅ MCP servers are running")
        print("🌐 Starting ADK web interface...")
        print("📱 Open http://localhost:8000 in your browser")
        print("🔧 MCP Tools available on ports 8001-8003")
        print("\nPress Ctrl+C to stop\n")
        
        # Start ADK web interface (this will block)
        start_adk_web()
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Aviation MAS-A2A system...")
    except Exception as e:
        print(f"❌ Error starting system: {e}")


if __name__ == "__main__":
    asyncio.run(main())