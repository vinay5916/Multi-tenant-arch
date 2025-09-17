# mcp_servers/meeting_server/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, date, time
from enum import Enum

# Import from adktools
from adktools.models import DomainError

class MeetingStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class MeetingPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class RoomType(str, Enum):
    CONFERENCE = "conference"
    TRAINING = "training"
    EXECUTIVE = "executive"
    VIDEO_CONFERENCE = "video_conference"
    BRIEFING = "briefing"

class MeetingRoom(BaseModel):
    room_id: str
    name: str
    capacity: int
    room_type: RoomType
    equipment: List[str] = []  # ["projector", "video_conf", "whiteboard"]
    location: str
    is_available: bool = True

class Meeting(BaseModel):
    meeting_id: str
    title: str
    description: Optional[str] = None
    organizer: str  # employee_id
    attendees: List[str] = []  # employee_ids
    room_id: str
    start_time: datetime
    end_time: datetime
    status: MeetingStatus = MeetingStatus.SCHEDULED
    priority: MeetingPriority = MeetingPriority.MEDIUM
    recurring: bool = False
    outlook_meeting_id: Optional[str] = None

# Input Models
class CreateMeetingInput(BaseModel):
    title: str = Field(..., description="Meeting title")
    description: Optional[str] = Field(None, description="Meeting description")
    organizer: str = Field(..., description="Organizer's employee ID")
    attendees: List[str] = Field(default=[], description="List of attendee employee IDs")
    room_name: str = Field(..., description="Preferred meeting room name")
    start_time: str = Field(..., description="Meeting start time in ISO format")
    end_time: str = Field(..., description="Meeting end time in ISO format")
    priority: MeetingPriority = Field(default=MeetingPriority.MEDIUM, description="Meeting priority")

class FindAvailableRoomsInput(BaseModel):
    start_time: str = Field(..., description="Start time in ISO format")
    end_time: str = Field(..., description="End time in ISO format")
    capacity_needed: Optional[int] = Field(None, description="Minimum room capacity required")
    room_type: Optional[RoomType] = Field(None, description="Preferred room type")
    equipment_needed: List[str] = Field(default=[], description="Required equipment")

class UpdateMeetingInput(BaseModel):
    meeting_id: str = Field(..., description="Meeting ID to update")
    title: Optional[str] = Field(None, description="New meeting title")
    start_time: Optional[str] = Field(None, description="New start time in ISO format")
    end_time: Optional[str] = Field(None, description="New end time in ISO format")
    room_name: Optional[str] = Field(None, description="New room name")
    status: Optional[MeetingStatus] = Field(None, description="New meeting status")

# Error Models
class RoomNotAvailableError(DomainError):
    room_name: str = Field(..., description="The room that's not available")
    conflicting_meeting_id: Optional[str] = Field(None, description="ID of conflicting meeting")
    start_time: datetime = Field(..., description="Requested start time")
    end_time: datetime = Field(..., description="Requested end time")
    error_type: Literal["room_not_available"] = "room_not_available"

class MeetingNotFoundError(DomainError):
    meeting_id: str = Field(..., description="The meeting ID that was not found")
    error_type: Literal["meeting_not_found"] = "meeting_not_found"

class RoomNotFoundError(DomainError):
    room_name: str = Field(..., description="The room name that was not found")
    available_rooms: List[str] = Field(..., description="List of available room names")
    error_type: Literal["room_not_found"] = "room_not_found"

class OutlookIntegrationError(DomainError):
    operation: str = Field(..., description="The Outlook operation that failed")
    details: str = Field(..., description="Error details")
    error_type: Literal["outlook_integration_error"] = "outlook_integration_error"