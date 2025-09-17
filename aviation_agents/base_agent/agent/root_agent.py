# Aviation Base Agent for ADK
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RootAgent:
    """Aviation base agent that ADK can discover"""
    
    def __init__(self):
        self.name = "Aviation Base Agent"
        logger.info("Aviation Base Agent initialized via agent.root_agent")
    
    async def execute(self, message: str) -> Dict[str, Any]:
        """Execute aviation agent request"""
        try:
            logger.info(f"Aviation Base Agent received: {message}")
            
            # Simple routing based on keywords
            message_lower = message.lower()
            
            if any(word in message_lower for word in ['hr', 'employee', 'staff', 'crew', 'pilot', 'training']):
                response = f"🏢 HR Operations: Processing request - {message}"
                agent_type = "hr"
            elif any(word in message_lower for word in ['meeting', 'schedule', 'calendar', 'appointment']):
                response = f"📅 Meeting Coordination: Processing request - {message}"  
                agent_type = "meeting"
            elif any(word in message_lower for word in ['supply', 'inventory', 'parts', 'maintenance', 'procurement']):
                response = f"📦 Supply Chain: Processing request - {message}"
                agent_type = "supply_chain"
            else:
                response = f"✈️ Aviation Operations: General coordination - {message}"
                agent_type = "general"
            
            return {
                "response": response,
                "metadata": {
                    "agent": agent_type,
                    "base_agent": "aviation_system", 
                    "status": "success"
                }
            }
            
        except Exception as e:
            logger.error(f"Error in aviation base agent: {e}")
            return {
                "response": f"❌ Aviation System Error: {str(e)}",
                "metadata": {
                    "agent": "base_agent",
                    "status": "error"
                }
            }

# Create the root_agent instance that ADK will find
root_agent = RootAgent()