# executors/hr_executor.py
import asyncio
import logging
from typing import Any, Dict, AsyncIterable, List
import json

from .base_executor import BaseAgentExecutor, RequestContext, TaskUpdater, TaskState, Artifact
from mcp_servers.hr_server.tools import (
    create_employee_record,
    schedule_training,
    track_certification,
    generate_hr_report
)

logger = logging.getLogger(__name__)


class HRAgentExecutor(BaseAgentExecutor):
    """HR Agent executor following mas-a2a pattern with tool integration"""
    
    def __init__(self):
        system_prompt = """You are an expert Aviation HR assistant specializing in human resources management for aviation organizations.

Your expertise includes:
- Employee lifecycle management (hiring, onboarding, performance, offboarding)
- Aviation-specific certifications and training (pilot licenses, mechanic certifications, ATC licenses)
- Regulatory compliance (FAA, EASA, ICAO requirements)
- Training scheduling and tracking
- Crew resource management
- Safety training and recurrency requirements

Key responsibilities:
1. EMPLOYEE MANAGEMENT:
   - Create and maintain employee records
   - Track certifications and licenses
   - Schedule training and recurrency
   - Generate compliance reports

2. AVIATION COMPLIANCE:
   - Monitor certification expiry dates
   - Ensure regulatory compliance
   - Track training requirements
   - Manage documentation

Available tools:
- create_employee_record: Create new employee profiles
- schedule_training: Schedule training sessions
- track_certification: Monitor certification status
- generate_hr_report: Generate HR reports

Always use the appropriate tools to perform HR tasks. Provide clear, professional responses."""

        super().__init__(
            agent_name="Aviation HR Agent",
            agent_type="hr_specialist", 
            system_prompt=system_prompt
        )
    
    async def execute_task(self, context: RequestContext, task_updater: TaskUpdater) -> AsyncIterable[Any]:
        """Execute HR-specific tasks"""
        try:
            # Update status
            task_updater.update_status(TaskState.WORKING, "Analyzing HR request", 25.0)
            
            # Get LLM response to understand the request
            llm_response = await self._call_llm(context.user_message)
            
            # Check if we need to use tools
            tool_results = await self._process_hr_tools(context.user_message, context)
            
            # Update progress
            task_updater.update_status(TaskState.WORKING, "Processing HR data", 75.0)
            
            # Combine LLM response with tool results
            final_response = await self._combine_responses(llm_response, tool_results, context.user_message)
            
            # Add final artifact
            task_updater.add_artifact(
                content=final_response,
                artifact_type="hr_response",
                metadata={
                    "agent_type": "hr",
                    "tools_used": len(tool_results) > 0,
                    "tenant_id": context.tenant_id
                }
            )
            
            # Complete task
            task_updater.complete()
            
            yield task_updater.artifacts[-1]
            
        except Exception as e:
            logger.error(f"HR Agent execution failed: {str(e)}")
            task_updater.fail(f"HR task failed: {str(e)}")
            raise
    
    async def _process_hr_tools(self, user_message: str, context: RequestContext) -> List[Dict[str, Any]]:
        """Process HR-related tool calls based on user message"""
        tool_results = []
        message_lower = user_message.lower()
        
        try:
            # Detect tool usage needs based on keywords
            if any(keyword in message_lower for keyword in ["create employee", "add employee", "new hire", "onboard"]):
                # Example employee creation - in real scenario, extract from message
                result = await create_employee_record({
                    "name": "Sample Employee",
                    "employee_id": f"EMP_{context.task_id[:8]}",
                    "position": "Aviation Specialist",
                    "department": "Operations",
                    "hire_date": "2024-01-01",
                    "certifications": []
                })
                tool_results.append({"tool": "create_employee_record", "result": result})
            
            if any(keyword in message_lower for keyword in ["training", "schedule", "course"]):
                result = await schedule_training({
                    "employee_id": f"EMP_{context.task_id[:8]}",
                    "training_type": "Safety Training",
                    "scheduled_date": "2024-02-01",
                    "instructor": "Safety Officer",
                    "duration_hours": 8
                })
                tool_results.append({"tool": "schedule_training", "result": result})
            
            if any(keyword in message_lower for keyword in ["certification", "license", "track", "expiry"]):
                result = await track_certification({
                    "employee_id": f"EMP_{context.task_id[:8]}",
                    "certification_type": "Pilot License",
                    "certification_number": "PPL123456",
                    "issue_date": "2023-01-01",
                    "expiry_date": "2025-01-01",
                    "status": "active"
                })
                tool_results.append({"tool": "track_certification", "result": result})
            
            if any(keyword in message_lower for keyword in ["report", "generate", "summary"]):
                result = await generate_hr_report({
                    "report_type": "employee_summary",
                    "department": "Operations",
                    "date_range": "2024-01-01_2024-12-31"
                })
                tool_results.append({"tool": "generate_hr_report", "result": result})
                
        except Exception as e:
            logger.error(f"Tool execution failed: {str(e)}")
            tool_results.append({"tool": "error", "result": f"Tool execution failed: {str(e)}"})
        
        return tool_results
    
    async def _combine_responses(self, llm_response: str, tool_results: List[Dict[str, Any]], user_message: str) -> str:
        """Combine LLM response with tool results"""
        if not tool_results:
            return llm_response
        
        # Create a comprehensive response
        combined_response = f"{llm_response}\n\n"
        
        if tool_results:
            combined_response += "## HR System Actions Performed:\n\n"
            for tool_result in tool_results:
                tool_name = tool_result.get("tool", "unknown")
                result = tool_result.get("result", {})
                
                if tool_name != "error":
                    combined_response += f"✅ **{tool_name.replace('_', ' ').title()}:**\n"
                    if isinstance(result, dict):
                        for key, value in result.items():
                            combined_response += f"   - {key.replace('_', ' ').title()}: {value}\n"
                    else:
                        combined_response += f"   - Result: {result}\n"
                    combined_response += "\n"
                else:
                    combined_response += f"❌ **Error:** {result}\n\n"
        
        return combined_response