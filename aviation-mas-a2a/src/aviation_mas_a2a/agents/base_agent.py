"""
Aviation Base Agent using Google ADK with web interface
"""
from typing import Dict, Any, List, Optional
import asyncio
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
    
    def add_mcp_tools(self, tools: List[Any]):
        """Add MCP tools to the agent"""
        self.available_tools.extend(tools)
        logger.info(f"Added {len(tools)} MCP tools to {self.name}")
    
    async def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process a message using LiteLLM"""
        try:
            context = context or {}
            
            # Prepare system message with agent info and available tools
            system_content = f"You are {self.name}. {self.description}\n\nInstructions: {self.instructions}"
            
            if self.available_tools:
                tools_info = f"\n\nAvailable tools: {len(self.available_tools)} MCP tools for {self.agent_type} operations"
                system_content += tools_info
            
            # For demo purposes, if no API key is configured, return a mock response
            if not self.llm_config.get("api_key"):
                mock_response = f"[DEMO MODE] {self.name} received: {message}\n\nThis agent specializes in {self.agent_type} operations with {len(self.available_tools)} available tools."
                
                result = {
                    "status": "success",
                    "agent": self.name,
                    "agent_type": self.agent_type,
                    "response": mock_response,
                    "tools_available": len(self.available_tools),
                    "context": context,
                    "mode": "demo"
                }
                
                logger.info(f"Processed message with {self.name} (demo mode)")
                return result
            
            # Prepare messages for LiteLLM
            messages = [
                {"role": "system", "content": system_content},
                {"role": "user", "content": message}
            ]
            
            # Add context if provided
            if context:
                context_str = f"Context: {context}"
                messages.insert(-1, {"role": "system", "content": context_str})
            
            # Call LiteLLM with proper configuration
            try:
                response = await litellm.acompletion(
                    model=self.llm_model,
                    messages=messages,
                    **{k: v for k, v in self.llm_config.items() if k != "model" and v is not None}
                )
                
                result = {
                    "status": "success",
                    "agent": self.name,
                    "agent_type": self.agent_type,
                    "response": response.choices[0].message.content,
                    "tools_available": len(self.available_tools),
                    "context": context,
                    "mode": "live"
                }
                
                logger.info(f"Processed message with {self.name}")
                return result
                
            except Exception as llm_error:
                logger.warning(f"LiteLLM error, falling back to demo mode: {llm_error}")
                
                # Fallback to demo mode
                mock_response = f"[DEMO MODE - LLM Unavailable] {self.name} received: {message}\n\nThis agent specializes in {self.agent_type} operations with {len(self.available_tools)} available tools."
                
                return {
                    "status": "success",
                    "agent": self.name,
                    "agent_type": self.agent_type,
                    "response": mock_response,
                    "tools_available": len(self.available_tools),
                    "context": context,
                    "mode": "demo",
                    "fallback_reason": str(llm_error)
                }
            
        except Exception as e:
            logger.error(f"Error processing message in {self.name}: {e}")
            return {
                "status": "error",
                "agent": self.name,
                "agent_type": self.agent_type,
                "message": f"Failed to process message: {str(e)}"
            }
    
    async def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            "name": self.name,
            "agent_type": self.agent_type,
            "status": "active",
            "model": self.llm_model,
            "description": self.description,
            "tools_count": len(self.available_tools)
        }
    
    async def shutdown(self):
        """Shutdown the agent"""
        logger.info(f"Shutting down {self.name}")
        # Cleanup resources if needed


# Aviation-specific agent implementations
class AviationBaseAgent(BaseAgent):
    """Main aviation coordination agent"""
    
    def __init__(self):
        super().__init__({
            "name": "Aviation Base Agent",
            "agent_type": "base",
            "description": "Main coordinator for aviation operations",
            "instructions": "You coordinate between HR, meeting, and supply chain operations for aviation."
        })


class HRAgent(BaseAgent):
    """HR operations agent"""
    
    def __init__(self):
        super().__init__({
            "name": "Aviation HR Agent", 
            "agent_type": "hr",
            "description": "Specialized agent for crew management and HR operations",
            "instructions": "You handle crew scheduling, training, certifications, and HR operations."
        })


class MeetingAgent(BaseAgent):
    """Meeting coordination agent"""
    
    def __init__(self):
        super().__init__({
            "name": "Aviation Meeting Agent",
            "agent_type": "meeting", 
            "description": "Specialized agent for meeting and scheduling coordination",
            "instructions": "You handle meeting scheduling, room booking, and calendar coordination."
        })


class SupplyChainAgent(BaseAgent):
    """Supply chain management agent"""
    
    def __init__(self):
        super().__init__({
            "name": "Aviation Supply Chain Agent",
            "agent_type": "supply_chain",
            "description": "Specialized agent for inventory and procurement management", 
            "instructions": "You handle inventory tracking, purchase orders, and vendor management."
        })