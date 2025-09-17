"""
Aviation Base Agent using Google ADK with web interface
"""
from typing import Dict, Any, List
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from loguru import logger

from ..shared.config import config
from ..mcp_servers.hr_tools import HRTools
from ..mcp_servers.meeting_tools import MeetingTools
from ..mcp_servers.supply_chain_tools import SupplyChainTools


class AviationBaseAgent:
    """Aviation Base Agent using Google ADK with web interface"""
    
    def __init__(self):
        self.name = "Aviation Base Agent"
        
        # Initialize MCP tool servers
        self.hr_tools = HRTools()
        self.meeting_tools = MeetingTools()
        self.supply_chain_tools = SupplyChainTools()
        
        # Create Google ADK agent with LiteLLM
        self.agent = Agent(
            name="aviation_base_agent",
            model=LiteLlm(model=config.litellm_model or "gpt-3.5-turbo"),
            description="Aviation multi-agent coordinator for HR, meetings, and supply chain operations",
            instruction=self._get_agent_instruction(),
            tools=self._get_agent_tools(),
        )
        
        logger.info(f"Aviation Base Agent initialized with ADK web interface")
    
    def _get_agent_instruction(self) -> str:
        """Get the comprehensive instruction for the aviation agent"""
        return f"""You are the Aviation Base Agent, a comprehensive coordinator for aviation operations.

Your primary responsibilities:
1. HR Operations: Handle employee management, crew scheduling, training, certifications
2. Meeting Coordination: Schedule meetings, manage calendars, coordinate team communications  
3. Supply Chain: Manage inventory, parts procurement, vendor relationships, maintenance supplies
4. General Coordination: Route complex requests to appropriate specialized functions

Aviation Departments: {', '.join(config.aviation_departments)}

When users ask for help with:
- Employee/crew/pilot/staff management, training, certifications → Use HR tools
- Scheduling meetings/appointments/conferences, calendar management → Use meeting tools  
- Inventory/parts/procurement/maintenance supplies, vendor management → Use supply chain tools
- Complex multi-department requests → Coordinate across multiple tool sets

Always use the appropriate tools for each request. Analyze tool responses and provide clear, 
professional feedback to users. If a tool returns an error, explain it clearly and suggest alternatives.

Maintain aviation industry standards and terminology in all communications.
Be concise but thorough in your responses."""
    
    def _get_agent_tools(self) -> List[Any]:
        """Get all available MCP tools for the agent"""
        tools = []
        
        # Add HR tools
        tools.extend(self.hr_tools.get_tools())
        
        # Add meeting tools  
        tools.extend(self.meeting_tools.get_tools())
        
        # Add supply chain tools
        tools.extend(self.supply_chain_tools.get_tools())
        
        logger.info(f"Aviation Base Agent configured with {len(tools)} tools")
        return tools
    
    async def execute(self, message: str) -> Dict[str, Any]:
        """Execute request through the ADK agent"""
        try:
            logger.info(f"Aviation Base Agent processing: {message}")
            
            # Use the ADK agent to process the request
            response = await self.agent.execute(message)
            
            return {
                "response": response,
                "metadata": {
                    "agent": "aviation_base_agent",
                    "model": config.litellm_model or "gpt-3.5-turbo",
                    "status": "success"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in Aviation Base Agent: {e}")
            return {
                "response": f"❌ Aviation System Error: {str(e)}",
                "metadata": {
                    "agent": "aviation_base_agent",
                    "status": "error"
                }
            }

    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.name,
            "agent_type": "base",
            "status": "active",
            "model": config.litellm_model or "gpt-3.5-turbo",
            "description": "Aviation multi-agent coordinator",
            "tools_count": len(self._get_agent_tools())
        }
    
    async def shutdown(self):
        """Shutdown the agent"""
        logger.info(f"Shutting down {self.name}")
        # Cleanup resources if needed


# Create the root_agent instance for ADK discovery
root_agent = AviationBaseAgent()