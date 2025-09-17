"""
Meeting Tools for Aviation System using FastMCP
"""
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastmcp import FastMCP
from loguru import logger

from ..shared.config import config


class MeetingTools:
    """Meeting coordination tools for aviation system"""
    
    def __init__(self):
        self.mcp = FastMCP("Aviation Meeting Server")
        self.meetings_db: Dict[str, Dict[str, Any]] = {}
        self.calendars_db: Dict[str, List[str]] = {}  # user_id -> meeting_ids
        
        # Register MCP tools
        self._register_tools()
        logger.info("Meeting Tools initialized")
    
    def _register_tools(self):
        """Register all meeting tools with FastMCP"""
        
        @self.mcp.tool()
        async def schedule_meeting(
            title: str,
            date: str,
            time: str,
            duration_minutes: int = 60,
            attendees: Optional[List[str]] = None,
            location: Optional[str] = None,
            meeting_type: str = "general"
        ) -> Dict[str, Any]:
            """Schedule a meeting for aviation operations"""
            try:
                meeting_id = f"MTG_{str(uuid.uuid4())[:8]}"
                
                meeting = {
                    "meeting_id": meeting_id,
                    "title": title,
                    "date": date,
                    "time": time,
                    "duration_minutes": duration_minutes,
                    "attendees": attendees or [],
                    "location": location,
                    "meeting_type": meeting_type,
                    "status": "scheduled",
                    "created_at": datetime.now().isoformat(),
                    "created_by": "aviation_system"
                }
                
                self.meetings_db[meeting_id] = meeting
                
                # Add to attendees' calendars
                for attendee in (attendees or []):
                    if attendee not in self.calendars_db:
                        self.calendars_db[attendee] = []
                    self.calendars_db[attendee].append(meeting_id)
                
                logger.info(f"Scheduled meeting: {meeting_id}")
                return {
                    "status": "success",
                    "message": f"Meeting '{title}' scheduled successfully",
                    "meeting_id": meeting_id,
                    "details": meeting
                }
                
            except Exception as e:
                logger.error(f"Error scheduling meeting: {e}")
                return {"status": "error", "message": f"Failed to schedule meeting: {str(e)}"}
        
        @self.mcp.tool()
        async def get_meeting_details(meeting_id: str) -> Dict[str, Any]:
            """Get detailed information about a scheduled meeting"""
            try:
                if meeting_id not in self.meetings_db:
                    return {"status": "error", "message": "Meeting not found"}
                
                meeting = self.meetings_db[meeting_id]
                return {
                    "status": "success",
                    "meeting": meeting
                }
                
            except Exception as e:
                logger.error(f"Error getting meeting details: {e}")
                return {"status": "error", "message": f"Failed to get meeting details: {str(e)}"}
        
        @self.mcp.tool()
        async def update_meeting_status(
            meeting_id: str,
            status: str,
            notes: Optional[str] = None
        ) -> Dict[str, Any]:
            """Update the status of a meeting (scheduled, in-progress, completed, cancelled)"""
            try:
                if meeting_id not in self.meetings_db:
                    return {"status": "error", "message": "Meeting not found"}
                
                valid_statuses = ["scheduled", "in-progress", "completed", "cancelled"]
                if status not in valid_statuses:
                    return {
                        "status": "error", 
                        "message": f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
                    }
                
                self.meetings_db[meeting_id]["status"] = status
                self.meetings_db[meeting_id]["updated_at"] = datetime.now().isoformat()
                
                if notes:
                    self.meetings_db[meeting_id]["notes"] = notes
                
                logger.info(f"Updated meeting {meeting_id} status to {status}")
                return {
                    "status": "success",
                    "message": f"Meeting status updated to {status}",
                    "meeting": self.meetings_db[meeting_id]
                }
                
            except Exception as e:
                logger.error(f"Error updating meeting status: {e}")
                return {"status": "error", "message": f"Failed to update meeting status: {str(e)}"}
        
        @self.mcp.tool()
        async def get_calendar_events(
            user_id: str,
            date_from: Optional[str] = None,
            date_to: Optional[str] = None
        ) -> Dict[str, Any]:
            """Get calendar events for a user within a date range"""
            try:
                if user_id not in self.calendars_db:
                    return {
                        "status": "success",
                        "user_id": user_id,
                        "events": [],
                        "message": "No events found for user"
                    }
                
                meeting_ids = self.calendars_db[user_id]
                meetings = [self.meetings_db[mid] for mid in meeting_ids if mid in self.meetings_db]
                
                # Filter by date range if provided
                if date_from or date_to:
                    filtered_meetings = []
                    for meeting in meetings:
                        meeting_date = meeting["date"]
                        if date_from and meeting_date < date_from:
                            continue
                        if date_to and meeting_date > date_to:
                            continue
                        filtered_meetings.append(meeting)
                    meetings = filtered_meetings
                
                return {
                    "status": "success",
                    "user_id": user_id,
                    "events": meetings,
                    "event_count": len(meetings)
                }
                
            except Exception as e:
                logger.error(f"Error getting calendar events: {e}")
                return {"status": "error", "message": f"Failed to get calendar events: {str(e)}"}
        
        @self.mcp.tool()
        async def list_meetings_by_type(meeting_type: str) -> Dict[str, Any]:
            """List all meetings of a specific type (safety, maintenance, operations, etc.)"""
            try:
                meetings = [
                    meeting for meeting in self.meetings_db.values()
                    if meeting["meeting_type"].lower() == meeting_type.lower()
                ]
                
                return {
                    "status": "success",
                    "meeting_type": meeting_type,
                    "meeting_count": len(meetings),
                    "meetings": meetings
                }
                
            except Exception as e:
                logger.error(f"Error listing meetings by type: {e}")
                return {"status": "error", "message": f"Failed to list meetings: {str(e)}"}
    
    def get_tools(self) -> List[Any]:
        """Get all registered meeting tools"""
        return list(self.mcp.get_tools().values())
    
    async def start_server(self, port: int = None):
        """Start the Meeting MCP server"""
        server_port = port or config.mcp_base_port + 2
        logger.info(f"Starting Meeting MCP server on port {server_port}")
        await self.mcp.run(host=config.mcp_host, port=server_port)