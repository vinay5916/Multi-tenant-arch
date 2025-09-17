# executors/meeting_executor.py
import asyncio
import logging
from typing import Any, Dict, AsyncIterable, List
import json

from .base_executor import BaseAgentExecutor, RequestContext, TaskUpdater, TaskState, Artifact
from mcp_servers.meeting_server.tools import (
    book_meeting_room,
    check_room_availability,
    cancel_booking,
    generate_meeting_report
)

logger = logging.getLogger(__name__)


class MeetingAgentExecutor(BaseAgentExecutor):
    """Meeting Agent executor following mas-a2a pattern with tool integration"""
    
    def __init__(self):
        system_prompt = """You are an expert Aviation Meeting Room Management assistant specializing in conference room booking and meeting coordination for aviation organizations.

Your expertise includes:
- Meeting room booking and management
- Room availability checking
- Equipment and resource coordination
- Meeting scheduling for aviation teams
- Conference room optimization

Key responsibilities:
1. ROOM MANAGEMENT:
   - Book and manage meeting rooms
   - Check room availability
   - Handle booking modifications and cancellations
   - Coordinate equipment needs

2. MEETING COORDINATION:
   - Schedule team meetings
   - Coordinate cross-department sessions
   - Manage recurring meetings
   - Handle special aviation briefings

Available tools:
- book_meeting_room: Reserve meeting rooms
- check_room_availability: Check room schedules
- cancel_booking: Cancel room reservations
- generate_meeting_report: Generate meeting reports

Always use the appropriate tools to perform meeting management tasks. Provide clear, helpful responses for meeting coordination."""

        super().__init__(
            agent_name="Aviation Meeting Agent",
            agent_type="meeting_coordinator", 
            system_prompt=system_prompt
        )
    
    async def execute_task(self, context: RequestContext, task_updater: TaskUpdater) -> AsyncIterable[Any]:
        """Execute meeting-specific tasks"""
        try:
            # Update status
            task_updater.update_status(TaskState.WORKING, "Analyzing meeting request", 25.0)
            
            # Get LLM response to understand the request
            llm_response = await self._call_llm(context.user_message)
            
            # Check if we need to use tools
            tool_results = await self._process_meeting_tools(context.user_message, context)
            
            # Update progress
            task_updater.update_status(TaskState.WORKING, "Processing meeting data", 75.0)
            
            # Combine LLM response with tool results
            final_response = await self._combine_responses(llm_response, tool_results, context.user_message)
            
            # Add final artifact
            task_updater.add_artifact(
                content=final_response,
                artifact_type="meeting_response",
                metadata={
                    "agent_type": "meeting",
                    "tools_used": len(tool_results) > 0,
                    "tenant_id": context.tenant_id
                }
            )
            
            # Complete task
            task_updater.complete()
            
            yield task_updater.artifacts[-1]
            
        except Exception as e:
            logger.error(f"Meeting Agent execution failed: {str(e)}")
            task_updater.fail(f"Meeting task failed: {str(e)}")
            raise
    
    async def _process_meeting_tools(self, user_message: str, context: RequestContext) -> List[Dict[str, Any]]:
        """Process meeting-related tool calls based on user message"""
        tool_results = []
        message_lower = user_message.lower()
        
        try:
            # Detect tool usage needs based on keywords
            if any(keyword in message_lower for keyword in ["book", "reserve", "schedule meeting", "room booking"]):
                result = await book_meeting_room({
                    "room_id": "CONF_A1",
                    "meeting_title": "Aviation Team Meeting",
                    "organizer": context.user_id,
                    "start_time": "2024-02-01T10:00:00",
                    "end_time": "2024-02-01T11:00:00",
                    "attendees": ["team@aviation.com"],
                    "equipment_needed": ["projector", "conference_phone"]
                })
                tool_results.append({"tool": "book_meeting_room", "result": result})
            
            if any(keyword in message_lower for keyword in ["availability", "check", "available", "free"]):
                result = await check_room_availability({
                    "room_id": "CONF_A1",
                    "date": "2024-02-01",
                    "start_time": "09:00",
                    "end_time": "17:00"
                })
                tool_results.append({"tool": "check_room_availability", "result": result})
            
            if any(keyword in message_lower for keyword in ["cancel", "delete", "remove booking"]):
                result = await cancel_booking({
                    "booking_id": f"BOOK_{context.task_id[:8]}",
                    "reason": "User requested cancellation",
                    "cancelled_by": context.user_id
                })
                tool_results.append({"tool": "cancel_booking", "result": result})
            
            if any(keyword in message_lower for keyword in ["report", "summary", "meeting stats"]):
                result = await generate_meeting_report({
                    "report_type": "room_utilization",
                    "date_range": "2024-01-01_2024-01-31",
                    "room_filter": "all"
                })
                tool_results.append({"tool": "generate_meeting_report", "result": result})
                
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
            combined_response += "## Meeting System Actions Performed:\n\n"
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