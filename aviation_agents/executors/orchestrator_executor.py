# executors/orchestrator_executor.py
import asyncio
import logging
from typing import Any, Dict, AsyncIterable, List
import json
from uuid import uuid4

from .base_executor import BaseAgentExecutor, RequestContext, TaskUpdater, TaskState, Artifact
from .hr_executor import HRAgentExecutor
from .meeting_executor import MeetingAgentExecutor  
from .supply_chain_executor import SupplyChainAgentExecutor

logger = logging.getLogger(__name__)


class OrchestratorAgentExecutor(BaseAgentExecutor):
    """Orchestrator Agent executor that coordinates all sub-agents following mas-a2a pattern"""
    
    def __init__(self):
        system_prompt = """You are the Aviation Multi-Agent System Orchestrator responsible for coordinating specialized aviation agents to fulfill user requests.

Your role is to:
1. Analyze incoming user requests
2. Determine which specialized agents are needed
3. Coordinate agent-to-agent communication
4. Aggregate and synthesize responses from sub-agents
5. Provide comprehensive responses to users

Available specialized agents:
- HR Agent: Employee management, certifications, training, compliance
- Meeting Agent: Room booking, meeting coordination, scheduling
- Supply Chain Agent: Inventory, procurement, supplier management

Analysis guidelines:
- For HR-related queries (employees, training, certifications): Use HR Agent
- For meeting/room-related queries (booking, scheduling): Use Meeting Agent  
- For inventory/parts/supplier queries: Use Supply Chain Agent
- For complex queries: Use multiple agents and synthesize responses
- For general aviation questions: Handle directly

Always provide clear, professional responses that leverage the appropriate specialized capabilities."""

        super().__init__(
            agent_name="Aviation Orchestrator Agent",
            agent_type="orchestrator", 
            system_prompt=system_prompt
        )
        
        # Initialize sub-agent executors
        self.hr_executor = HRAgentExecutor()
        self.meeting_executor = MeetingAgentExecutor()
        self.supply_chain_executor = SupplyChainAgentExecutor()
        
        # Agent routing keywords
        self.agent_routing = {
            "hr": ["employee", "staff", "training", "certification", "hire", "onboard", "hr", "personnel"],
            "meeting": ["meeting", "room", "book", "schedule", "conference", "reservation", "calendar"],
            "supply_chain": ["inventory", "parts", "supplier", "order", "stock", "procurement", "purchase"]
        }
    
    async def execute_task(self, context: RequestContext, task_updater: TaskUpdater) -> AsyncIterable[Any]:
        """Execute orchestration - analyze request and delegate to appropriate agents"""
        try:
            # Update status
            task_updater.update_status(TaskState.WORKING, "Analyzing request and routing to agents", 10.0)
            
            # Determine which agents to use
            required_agents = await self._determine_required_agents(context.user_message)
            
            # Update status  
            task_updater.update_status(TaskState.WORKING, f"Delegating to {len(required_agents)} agent(s)", 25.0)
            
            # Execute sub-agents in parallel if multiple
            agent_responses = []
            if len(required_agents) > 1:
                agent_responses = await self._execute_agents_parallel(required_agents, context)
            elif len(required_agents) == 1:
                agent_responses = await self._execute_agents_sequential(required_agents, context)
            else:
                # Handle directly if no specific agents needed
                agent_responses = [await self._handle_general_query(context)]
            
            # Update status
            task_updater.update_status(TaskState.WORKING, "Synthesizing agent responses", 75.0)
            
            # Synthesize responses
            final_response = await self._synthesize_responses(agent_responses, context.user_message)
            
            # Add final artifact
            task_updater.add_artifact(
                content=final_response,
                artifact_type="orchestrated_response",
                metadata={
                    "agent_type": "orchestrator",
                    "sub_agents_used": [agent["agent"] for agent in required_agents],
                    "tenant_id": context.tenant_id
                }
            )
            
            # Complete task
            task_updater.complete()
            
            yield task_updater.artifacts[-1]
            
        except Exception as e:
            logger.error(f"Orchestrator execution failed: {str(e)}")
            task_updater.fail(f"Orchestration failed: {str(e)}")
            raise
    
    async def _determine_required_agents(self, user_message: str) -> List[Dict[str, Any]]:
        """Determine which agents are needed based on the user message"""
        required_agents = []
        message_lower = user_message.lower()
        
        # Check for each agent type
        for agent_type, keywords in self.agent_routing.items():
            if any(keyword in message_lower for keyword in keywords):
                required_agents.append({
                    "agent": agent_type,
                    "executor": getattr(self, f"{agent_type}_executor"),
                    "priority": 1  # All agents have equal priority for now
                })
        
        # If no specific agents identified, we'll handle it as a general query
        return required_agents
    
    async def _execute_agents_parallel(self, required_agents: List[Dict[str, Any]], context: RequestContext) -> List[Dict[str, Any]]:
        """Execute multiple agents in parallel"""
        tasks = []
        
        for agent_info in required_agents:
            # Create a new context for each agent
            agent_context = RequestContext(
                task_id=f"{context.task_id}_{agent_info['agent']}",
                context_id=context.context_id,
                user_message=context.user_message,
                tenant_id=context.tenant_id,
                user_id=context.user_id
            )
            
            task = asyncio.create_task(
                agent_info["executor"].execute(agent_context)
            )
            tasks.append((agent_info["agent"], task))
        
        # Wait for all agents to complete
        results = []
        for agent_name, task in tasks:
            try:
                result = await task
                results.append({
                    "agent": agent_name,
                    "result": result,
                    "status": "success"
                })
            except Exception as e:
                logger.error(f"Agent {agent_name} failed: {str(e)}")
                results.append({
                    "agent": agent_name,
                    "result": f"Agent execution failed: {str(e)}",
                    "status": "error"
                })
        
        return results
    
    async def _execute_agents_sequential(self, required_agents: List[Dict[str, Any]], context: RequestContext) -> List[Dict[str, Any]]:
        """Execute agents sequentially"""
        results = []
        
        for agent_info in required_agents:
            try:
                # Create a new context for the agent
                agent_context = RequestContext(
                    task_id=f"{context.task_id}_{agent_info['agent']}",
                    context_id=context.context_id,
                    user_message=context.user_message,
                    tenant_id=context.tenant_id,
                    user_id=context.user_id
                )
                
                result = await agent_info["executor"].execute(agent_context)
                results.append({
                    "agent": agent_info["agent"],
                    "result": result,
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"Agent {agent_info['agent']} failed: {str(e)}")
                results.append({
                    "agent": agent_info["agent"],
                    "result": f"Agent execution failed: {str(e)}",
                    "status": "error"
                })
        
        return results
    
    async def _handle_general_query(self, context: RequestContext) -> Dict[str, Any]:
        """Handle general queries that don't require specific agents"""
        try:
            response = await self._call_llm(context.user_message)
            return {
                "agent": "orchestrator",
                "result": {
                    "task_id": context.task_id,
                    "agent_name": "Orchestrator",
                    "status": "completed",
                    "artifacts": [{"content": response, "type": "general_response"}]
                },
                "status": "success"
            }
        except Exception as e:
            return {
                "agent": "orchestrator", 
                "result": f"General query failed: {str(e)}",
                "status": "error"
            }
    
    async def _synthesize_responses(self, agent_responses: List[Dict[str, Any]], user_message: str) -> str:
        """Synthesize responses from multiple agents into a coherent response"""
        if len(agent_responses) == 1:
            # Single agent response
            response_data = agent_responses[0]["result"]
            if isinstance(response_data, dict) and "artifacts" in response_data:
                return response_data["artifacts"][0]["content"]
            else:
                return str(response_data)
        
        # Multiple agent responses - synthesize
        synthesis_prompt = f"""Based on the user query: "{user_message}"

The following specialized agents have provided responses:

"""
        
        for agent_response in agent_responses:
            agent_name = agent_response["agent"]
            if agent_response["status"] == "success":
                response_data = agent_response["result"]
                if isinstance(response_data, dict) and "artifacts" in response_data:
                    content = response_data["artifacts"][0]["content"]
                else:
                    content = str(response_data)
                synthesis_prompt += f"**{agent_name.title()} Agent Response:**\n{content}\n\n"
            else:
                synthesis_prompt += f"**{agent_name.title()} Agent:** Failed to process request\n\n"
        
        synthesis_prompt += """Please synthesize these responses into a single, coherent response that addresses the user's query comprehensively. Organize the information logically and highlight key insights from each agent."""
        
        try:
            synthesized_response = await self._call_llm(synthesis_prompt)
            return synthesized_response
        except Exception as e:
            # Fallback to concatenated responses
            logger.error(f"Synthesis failed: {str(e)}")
            fallback_response = "Here are the responses from our specialized agents:\n\n"
            for agent_response in agent_responses:
                agent_name = agent_response["agent"]
                if agent_response["status"] == "success":
                    response_data = agent_response["result"]
                    if isinstance(response_data, dict) and "artifacts" in response_data:
                        content = response_data["artifacts"][0]["content"]
                    else:
                        content = str(response_data)
                    fallback_response += f"## {agent_name.title()} Agent:\n{content}\n\n"
            return fallback_response