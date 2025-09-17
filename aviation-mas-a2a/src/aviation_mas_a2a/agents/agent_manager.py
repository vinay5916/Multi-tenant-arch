"""
Agent manager for coordinating multiple aviation agents using Google ADK
"""
import asyncio
from typing import Dict, List, Any, Optional
from loguru import logger

from ..shared.config import config
from .base_agent import BaseAgent, AviationBaseAgent, HRAgent, MeetingAgent, SupplyChainAgent


class AgentManager:
    """Manages multiple aviation agents in the MAS-A2A system"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.active_conversations: Dict[str, Dict[str, Any]] = {}
        
    async def register_agent(self, agent_type: str, agent_config: Dict[str, Any] = None) -> BaseAgent:
        """Register a new agent in the system"""
        try:
            # Create specialized agents based on type
            if agent_type == "base":
                agent = AviationBaseAgent()
            elif agent_type == "hr":
                agent = HRAgent()
            elif agent_type == "meeting":
                agent = MeetingAgent()
            elif agent_type == "supply_chain":
                agent = SupplyChainAgent()
            else:
                # Fallback to generic agent
                agent_config = agent_config or {}
                agent_config.update({
                    "agent_type": agent_type,
                    "name": f"Aviation {agent_type.title()} Agent",
                    "description": f"Specialized agent for {agent_type} operations in aviation"
                })
                agent = BaseAgent(agent_config)
            
            self.agents[agent_type] = agent
            
            logger.info(f"Registered {agent_type} agent: {agent.name}")
            return agent
            
        except Exception as e:
            logger.error(f"Failed to register {agent_type} agent: {e}")
            raise
    
    async def initialize_agents(self) -> Dict[str, BaseAgent]:
        """Initialize all required aviation agents"""
        try:
            agent_types = ["base", "hr", "meeting", "supply_chain"]
            
            for agent_type in agent_types:
                if agent_type not in self.agents:
                    await self.register_agent(agent_type)
            
            logger.info(f"Initialized {len(self.agents)} agents")
            return self.agents
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    async def get_agent(self, agent_type: str) -> Optional[BaseAgent]:
        """Get an agent by type"""
        return self.agents.get(agent_type)
    
    async def route_message(self, message: str, target_agent: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Route a message to the appropriate agent"""
        try:
            context = context or {}
            
            # If no target specified, determine best agent
            if not target_agent:
                target_agent = await self._determine_target_agent(message, context)
            
            # Get the target agent
            agent = await self.get_agent(target_agent)
            if not agent:
                return {
                    "status": "error",
                    "message": f"Agent '{target_agent}' not found",
                    "available_agents": list(self.agents.keys())
                }
            
            # Process the message
            response = await agent.process_message(message, context)
            
            logger.info(f"Routed message to {target_agent} agent")
            return {
                "status": "success",
                "agent": target_agent,
                "response": response,
                "context": context
            }
            
        except Exception as e:
            logger.error(f"Failed to route message: {e}")
            return {
                "status": "error",
                "message": f"Failed to route message: {str(e)}"
            }
    
    async def _determine_target_agent(self, message: str, context: Dict[str, Any]) -> str:
        """Determine which agent should handle the message"""
        message_lower = message.lower()
        
        # HR keywords
        if any(keyword in message_lower for keyword in ["crew", "pilot", "staff", "training", "certification", "schedule"]):
            return "hr"
        
        # Meeting keywords
        if any(keyword in message_lower for keyword in ["meeting", "schedule", "calendar", "appointment", "conference"]):
            return "meeting"
        
        # Supply chain keywords
        if any(keyword in message_lower for keyword in ["inventory", "parts", "supply", "order", "vendor", "procurement"]):
            return "supply_chain"
        
        # Default to base agent
        return "base"
    
    async def start_conversation(self, conversation_id: str, participants: List[str]) -> Dict[str, Any]:
        """Start a multi-agent conversation"""
        try:
            self.active_conversations[conversation_id] = {
                "id": conversation_id,
                "participants": participants,
                "messages": [],
                "started_at": asyncio.get_event_loop().time(),
                "status": "active"
            }
            
            logger.info(f"Started conversation {conversation_id} with agents: {participants}")
            return {
                "status": "success",
                "conversation_id": conversation_id,
                "participants": participants
            }
            
        except Exception as e:
            logger.error(f"Failed to start conversation: {e}")
            return {"status": "error", "message": str(e)}
    
    async def broadcast_message(self, message: str, exclude_agents: List[str] = None) -> Dict[str, Any]:
        """Broadcast a message to all agents"""
        try:
            exclude_agents = exclude_agents or []
            responses = {}
            
            for agent_type, agent in self.agents.items():
                if agent_type not in exclude_agents:
                    try:
                        response = await agent.process_message(message)
                        responses[agent_type] = response
                    except Exception as e:
                        responses[agent_type] = {"status": "error", "message": str(e)}
            
            logger.info(f"Broadcasted message to {len(responses)} agents")
            return {
                "status": "success",
                "message": "Message broadcasted",
                "responses": responses
            }
            
        except Exception as e:
            logger.error(f"Failed to broadcast message: {e}")
            return {"status": "error", "message": str(e)}
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get status of all agents and the system"""
        try:
            agent_status = {}
            
            for agent_type, agent in self.agents.items():
                try:
                    status = await agent.get_status()
                    agent_status[agent_type] = status
                except Exception as e:
                    agent_status[agent_type] = {"status": "error", "message": str(e)}
            
            return {
                "status": "success",
                "system_status": "operational",
                "total_agents": len(self.agents),
                "active_conversations": len(self.active_conversations),
                "agents": agent_status
            }
            
        except Exception as e:
            logger.error(f"Failed to get system status: {e}")
            return {"status": "error", "message": str(e)}
    
    async def shutdown(self):
        """Shutdown all agents and cleanup resources"""
        try:
            for agent_type, agent in self.agents.items():
                try:
                    if hasattr(agent, 'shutdown'):
                        await agent.shutdown()
                    logger.info(f"Shutdown {agent_type} agent")
                except Exception as e:
                    logger.error(f"Error shutting down {agent_type} agent: {e}")
            
            self.agents.clear()
            self.active_conversations.clear()
            logger.info("Agent manager shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise