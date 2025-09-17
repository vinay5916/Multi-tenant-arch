"""
Aviation Base Agent for Google ADK Web Interface
Standalone file without relative imports to work with ADK
"""
import os
import sys
from typing import Dict, Any, List, Optional
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from loguru import logger


# Simple configuration instead of relative imports
class SimpleConfig:
    def __init__(self):
        self.default_model = "gpt-3.5-turbo"
        self.litellm_api_key = os.getenv("LITELLM_API_KEY")
        self.temperature = 0.1
        self.max_tokens = 2000


config = SimpleConfig()


class AviationBaseAgent:
    """Aviation Base Agent using Google ADK with web interface"""
    
    def __init__(self):
        self.name = "Aviation Base Agent"
        
        # Create Google ADK agent with LiteLLM
        self.agent = Agent(
            name="aviation_base_agent",
            model=LiteLlm(
                model=config.default_model,
                api_key=config.litellm_api_key,
                temperature=config.temperature,
                max_tokens=config.max_tokens
            ),
            description="Aviation operations coordinator for HR, meetings, and supply chain",
            instruction=self._get_agent_instruction(),
            tools=self._get_agent_tools(),
        )
        
        logger.info(f"Aviation Base Agent initialized with model: {config.default_model}")
    
    def _get_agent_instruction(self) -> str:
        """Get the comprehensive instruction for the aviation agent"""
        return """You are the Aviation Base Agent, a comprehensive coordinator for aviation operations.

Your primary responsibilities:
1. HR Operations: Handle employee management, crew scheduling, training, certifications
2. Meeting Coordination: Schedule meetings, manage calendars, coordinate team communications  
3. Supply Chain: Manage inventory, parts procurement, vendor relationships, maintenance supplies
4. General Coordination: Route complex requests to appropriate specialized functions

Aviation Departments: Flight Operations, Maintenance, Ground Services, Air Traffic Control, Safety & Security, Customer Service, Cargo Operations, Engineering, Quality Assurance, Training, Human Resources, Finance

When users ask for help with:
- Employee/crew/pilot/staff management, training, certifications → Provide HR guidance
- Scheduling meetings/appointments/conferences, calendar management → Provide meeting coordination
- Inventory/parts/procurement/maintenance supplies, vendor management → Provide supply chain guidance
- Complex multi-department requests → Provide comprehensive coordination

Always provide clear, professional responses. If you need to perform specific actions, explain what you would do and what information you would need.

Maintain aviation industry standards and terminology in all communications.
Be concise but thorough in your responses."""
    
    def _get_agent_tools(self) -> List[Any]:
        """Get all available tools for the agent"""
        # For now, return empty list since we don't have MCP tools connected yet
        # This will be expanded once the base agent is working
        tools = []
        
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
                    "model": config.default_model,
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
    
    def process_message(self, message: str) -> str:
        """Synchronous message processing for ADK compatibility"""
        try:
            logger.info(f"Processing message: {message}")
            
            # Simple response without async for ADK web compatibility
            response = f"""Aviation Base Agent Response:

Message received: {message}

I'm ready to help with aviation operations including:
• HR Operations (crew management, training, certifications)
• Meeting Coordination (scheduling, calendar management)
• Supply Chain (inventory, procurement, vendor management)

How can I assist you with your aviation operations today?"""
            
            logger.info("Message processed successfully")
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"❌ Error processing your request: {str(e)}"


# Create the root_agent instance for ADK discovery
# This is the key - ADK looks for this specific variable name
root_agent = AviationBaseAgent()


# Alternative approach - also export the agent directly
agent = root_agent.agent if hasattr(root_agent, 'agent') else root_agent


# For debugging - log when this module is imported
logger.info("Aviation Base Agent module loaded successfully")
logger.info(f"Root agent created: {root_agent.name}")