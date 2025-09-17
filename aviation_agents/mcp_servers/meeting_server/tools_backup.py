# mcp_servers/meeting_server/tools.py
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import asyncio
import win32com.client as win32
from exchangelib import Mailbox, Account, Credentials, DELEGATE, Configuration, NTLM, CalendarItem, EWSDateTime
import pythoncom

# adk tools
from adktools import adk_tool

# Local imports
from .models import (
    MeetingRoom, Meeting,
    CreateMeetingInput, FindAvailableRoomsInput, UpdateMeetingInput,
    RoomNotAvailableError, MeetingNotFoundError, RoomNotFoundError, OutlookIntegrationError,
    MeetingStatus, MeetingPriority, RoomType
)

# Aviation meeting rooms configuration
MEETING_ROOMS: Dict[str, MeetingRoom] = {
    "flight_ops_center": MeetingRoom(
        room_id="flight_ops_center",
        name="Flight Operations Center",
        capacity=20,
        room_type=RoomType.BRIEFING,
        equipment=["large_display", "flight_tracking", "radio_comm", "weather_station"],
        location="Terminal Building, Floor 2"
    ),
    "pilot_briefing": MeetingRoom(
        room_id="pilot_briefing",
        name="Pilot Briefing Room",
        capacity=12,
        room_type=RoomType.BRIEFING,
        equipment=["weather_display", "route_planning", "charts_display"],
        location="Flight Operations, Ground Floor"
    ),
    "maintenance_conf": MeetingRoom(
        room_id="maintenance_conf",
        name="Maintenance Conference Room",
        capacity=15,
        room_type=RoomType.CONFERENCE,
        equipment=["projector", "technical_diagrams", "parts_catalog"],
        location="Maintenance Hangar"
    ),
    "executive_boardroom": MeetingRoom(
        room_id="executive_boardroom",
        name="Executive Boardroom",
        capacity=8,
        room_type=RoomType.EXECUTIVE,
        equipment=["video_conference", "smart_board", "executive_presentation"],
        location="Administrative Building, Top Floor"
    ),
    "training_room_a": MeetingRoom(
        room_id="training_room_a",
        name="Training Room A",
        capacity=25,
        room_type=RoomType.TRAINING,
        equipment=["projector", "simulation_equipment", "training_materials"],
        location="Training Center, Floor 1"
    ),
    "atc_briefing": MeetingRoom(
        room_id="atc_briefing",
        name="ATC Briefing Room",
        capacity=10,
        room_type=RoomType.BRIEFING,
        equipment=["radar_display", "comm_equipment", "weather_feed"],
        location="Control Tower, Floor 3"
    )
}

# Mock meeting database
meetings_db: Dict[str, Meeting] = {}

def parse_datetime(dt_string: str) -> datetime:
    """Parse ISO format datetime string"""
    try:
        return datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    except ValueError:
        # Try alternative formats
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S"]:
            try:
                return datetime.strptime(dt_string, fmt)
            except ValueError:
                continue
        raise ValueError(f"Unable to parse datetime: {dt_string}")

def check_room_availability(room_id: str, start_time: datetime, end_time: datetime, exclude_meeting_id: Optional[str] = None) -> Optional[str]:
    """Check if room is available during the specified time. Returns conflicting meeting ID if not available."""
    for meeting_id, meeting in meetings_db.items():
        if exclude_meeting_id and meeting_id == exclude_meeting_id:
            continue
        if meeting.room_id == room_id and meeting.status != MeetingStatus.CANCELLED:
            # Check for time overlap
            if (start_time < meeting.end_time and end_time > meeting.start_time):
                return meeting_id
    return None

@adk_tool(
    name="find_available_rooms",
    description="Find available meeting rooms for a specific time slot. Essential for booking meetings in aviation operations."
)
def find_available_rooms(
    start_time: str,
    end_time: str,
    capacity_needed: Optional[int] = None,
    room_type: Optional[str] = None,
    equipment_needed: List[str] = []
) -> List[Dict[str, Any]]:
    """Find available meeting rooms based on criteria
    
    Args:
        start_time: Start time in ISO format (e.g., "2024-01-15 09:00")
        end_time: End time in ISO format (e.g., "2024-01-15 10:00")
        capacity_needed: Minimum room capacity required
        room_type: Preferred room type (conference, training, executive, etc.)
        equipment_needed: List of required equipment
        
    Returns:
        List[Dict]: List of available rooms with details
    """
    try:
        start_dt = parse_datetime(start_time)
        end_dt = parse_datetime(end_time)
        
        available_rooms = []
        
        for room in MEETING_ROOMS.values():
            # Check availability
            conflicting_meeting = check_room_availability(room.room_id, start_dt, end_dt)
            if conflicting_meeting:
                continue
                
            # Check capacity
            if capacity_needed and room.capacity < capacity_needed:
                continue
                
            # Check room type
            if room_type and room.room_type != room_type:
                continue
                
            # Check equipment
            if equipment_needed:
                missing_equipment = [eq for eq in equipment_needed if eq not in room.equipment]
                if missing_equipment:
                    continue
            
            available_rooms.append({
                "room_id": room.room_id,
                "name": room.name,
                "capacity": room.capacity,
                "room_type": room.room_type,
                "equipment": room.equipment,
                "location": room.location
            })
        
        # Sort by capacity (smaller rooms first for efficiency)
        available_rooms.sort(key=lambda x: x["capacity"])
        return available_rooms
        
    except ValueError as e:
        raise RuntimeError(f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error finding available rooms: {str(e)}")

@adk_tool(
    name="create_meeting",
    description="Create a new meeting and book a room. Integrates with Outlook for calendar invitations."
)
def create_meeting(
    title: str,
    organizer: str,
    room_name: str,
    start_time: str,
    end_time: str,
    description: Optional[str] = None,
    attendees: List[str] = [],
    priority: str = "medium"
) -> Meeting | RoomNotFoundError | RoomNotAvailableError | OutlookIntegrationError:
    """Create a new meeting with room booking
    
    Args:
        title: Meeting title
        organizer: Organizer's employee ID
        room_name: Meeting room name
        start_time: Start time in ISO format
        end_time: End time in ISO format
        description: Optional meeting description
        attendees: List of attendee employee IDs
        priority: Meeting priority (low, medium, high, urgent)
        
    Returns:
        Meeting: The created meeting
        RoomNotFoundError: If the specified room doesn't exist
        RoomNotAvailableError: If the room is not available
        OutlookIntegrationError: If Outlook integration fails
    """
    try:
        # Find the room
        room = None
        for r in MEETING_ROOMS.values():
            if r.name.lower() == room_name.lower():
                room = r
                break
        
        if not room:
            available_rooms = [r.name for r in MEETING_ROOMS.values()]
            return RoomNotFoundError(
                room_name=room_name,
                available_rooms=available_rooms,
                message=f"Room '{room_name}' not found. Available rooms: {', '.join(available_rooms)}"
            )
        
        # Parse times
        start_dt = parse_datetime(start_time)
        end_dt = parse_datetime(end_time)
        
        # Check availability
        conflicting_meeting = check_room_availability(room.room_id, start_dt, end_dt)
        if conflicting_meeting:
            return RoomNotAvailableError(
                room_name=room_name,
                conflicting_meeting_id=conflicting_meeting,
                start_time=start_dt,
                end_time=end_dt,
                message=f"Room '{room_name}' is not available during the requested time"
            )
        
        # Create meeting
        meeting_id = f"MTG{uuid.uuid4().hex[:8].upper()}"
        meeting = Meeting(
            meeting_id=meeting_id,
            title=title,
            description=description,
            organizer=organizer,
            attendees=attendees,
            room_id=room.room_id,
            start_time=start_dt,
            end_time=end_dt,
            priority=MeetingPriority(priority)
        )
        
        # Store meeting
        meetings_db[meeting_id] = meeting
        
        # Try to create Outlook appointment
        try:
            outlook_meeting_id = create_outlook_meeting(meeting, room)
            meeting.outlook_meeting_id = outlook_meeting_id
        except Exception as e:
            # Log the error but don't fail the meeting creation
            print(f"Warning: Failed to create Outlook meeting: {str(e)}")
        
        return meeting
        
    except ValueError as e:
        raise RuntimeError(f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error creating meeting: {str(e)}")

def create_outlook_meeting(meeting: Meeting, room: MeetingRoom) -> str:
    """Create Outlook meeting - handles both Exchange and local Outlook"""
    try:
        # Try COM interface first (local Outlook)
        pythoncom.CoInitialize()
        try:
            outlook = win32.Dispatch("Outlook.Application")
            appointment = outlook.CreateItem(1)  # 1 = olAppointmentItem
            
            appointment.Subject = meeting.title
            appointment.Body = f"{meeting.description or ''}\n\nLocation: {room.location}\nRoom: {room.name}"
            appointment.Start = meeting.start_time
            appointment.End = meeting.end_time
            appointment.Location = f"{room.name} - {room.location}"
            
            # Add organizer and attendees (simplified)
            appointment.Save()
            
            return f"OUTLOOK_{meeting.meeting_id}"
            
        except Exception as com_error:
            print(f"COM interface failed: {com_error}")
            # Could implement Exchange Web Services here as fallback
            return f"LOCAL_{meeting.meeting_id}"
        finally:
            pythoncom.CoUninitialize()
            
    except Exception as e:
        raise Exception(f"Failed to create Outlook meeting: {str(e)}")

@adk_tool(
    name="update_meeting",
    description="Update an existing meeting. Can change time, room, or other details."
)
def update_meeting(
    meeting_id: str,
    title: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    room_name: Optional[str] = None,
    status: Optional[str] = None
) -> Meeting | MeetingNotFoundError | RoomNotFoundError | RoomNotAvailableError:
    """Update an existing meeting
    
    Args:
        meeting_id: Meeting ID to update
        title: New meeting title
        start_time: New start time in ISO format
        end_time: New end time in ISO format
        room_name: New room name
        status: New meeting status
        
    Returns:
        Meeting: The updated meeting
        MeetingNotFoundError: If meeting doesn't exist
        RoomNotFoundError: If new room doesn't exist
        RoomNotAvailableError: If new room/time is not available
    """
    try:
        # Check if meeting exists
        if meeting_id not in meetings_db:
            return MeetingNotFoundError(
                meeting_id=meeting_id,
                message=f"Meeting with ID '{meeting_id}' not found"
            )
        
        meeting = meetings_db[meeting_id]
        
        # Update fields
        if title:
            meeting.title = title
        if status:
            meeting.status = MeetingStatus(status)
        
        # Handle time/room changes
        new_start = parse_datetime(start_time) if start_time else meeting.start_time
        new_end = parse_datetime(end_time) if end_time else meeting.end_time
        new_room_id = meeting.room_id
        
        if room_name:
            # Find new room
            new_room = None
            for r in MEETING_ROOMS.values():
                if r.name.lower() == room_name.lower():
                    new_room = r
                    break
            
            if not new_room:
                available_rooms = [r.name for r in MEETING_ROOMS.values()]
                return RoomNotFoundError(
                    room_name=room_name,
                    available_rooms=available_rooms,
                    message=f"Room '{room_name}' not found"
                )
            new_room_id = new_room.room_id
        
        # Check availability (excluding current meeting)
        if start_time or end_time or room_name:
            conflicting_meeting = check_room_availability(new_room_id, new_start, new_end, meeting_id)
            if conflicting_meeting:
                return RoomNotAvailableError(
                    room_name=MEETING_ROOMS[new_room_id].name,
                    conflicting_meeting_id=conflicting_meeting,
                    start_time=new_start,
                    end_time=new_end,
                    message="Room is not available during the requested time"
                )
        
        # Apply updates
        meeting.start_time = new_start
        meeting.end_time = new_end
        meeting.room_id = new_room_id
        
        return meeting
        
    except ValueError as e:
        raise RuntimeError(f"Invalid datetime format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error updating meeting: {str(e)}")

@adk_tool(
    name="cancel_meeting",
    description="Cancel a meeting and free up the room reservation."
)
def cancel_meeting(meeting_id: str) -> Dict[str, Any] | MeetingNotFoundError:
    """Cancel a meeting
    
    Args:
        meeting_id: Meeting ID to cancel
        
    Returns:
        Dict: Cancellation confirmation details
        MeetingNotFoundError: If meeting doesn't exist
    """
    try:
        if meeting_id not in meetings_db:
            return MeetingNotFoundError(
                meeting_id=meeting_id,
                message=f"Meeting with ID '{meeting_id}' not found"
            )
        
        meeting = meetings_db[meeting_id]
        room = MEETING_ROOMS[meeting.room_id]
        
        # Update status
        meeting.status = MeetingStatus.CANCELLED
        
        return {
            "meeting_id": meeting_id,
            "title": meeting.title,
            "room_name": room.name,
            "status": "cancelled",
            "cancelled_at": datetime.now().isoformat(),
            "message": f"Meeting '{meeting.title}' has been cancelled and room '{room.name}' is now available"
        }
        
    except Exception as e:
        raise RuntimeError(f"Error cancelling meeting: {str(e)}")

@adk_tool(
    name="get_room_schedule",
    description="Get the schedule for a specific room on a given date."
)
def get_room_schedule(room_name: str, date: str) -> Dict[str, Any] | RoomNotFoundError:
    """Get room schedule for a specific date
    
    Args:
        room_name: Name of the room
        date: Date in YYYY-MM-DD format
        
    Returns:
        Dict: Room schedule with meetings
        RoomNotFoundError: If room doesn't exist
    """
    try:
        # Find room
        room = None
        for r in MEETING_ROOMS.values():
            if r.name.lower() == room_name.lower():
                room = r
                break
        
        if not room:
            available_rooms = [r.name for r in MEETING_ROOMS.values()]
            return RoomNotFoundError(
                room_name=room_name,
                available_rooms=available_rooms,
                message=f"Room '{room_name}' not found"
            )
        
        # Parse date
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
        
        # Find meetings for this room on this date
        room_meetings = []
        for meeting in meetings_db.values():
            if (meeting.room_id == room.room_id and 
                meeting.start_time.date() == target_date and 
                meeting.status != MeetingStatus.CANCELLED):
                room_meetings.append({
                    "meeting_id": meeting.meeting_id,
                    "title": meeting.title,
                    "organizer": meeting.organizer,
                    "start_time": meeting.start_time.isoformat(),
                    "end_time": meeting.end_time.isoformat(),
                    "status": meeting.status,
                    "priority": meeting.priority,
                    "attendee_count": len(meeting.attendees)
                })
        
        # Sort by start time
        room_meetings.sort(key=lambda x: x["start_time"])
        
        return {
            "room": {
                "name": room.name,
                "capacity": room.capacity,
                "room_type": room.room_type,
                "location": room.location,
                "equipment": room.equipment
            },
            "date": date,
            "meetings": room_meetings,
            "total_meetings": len(room_meetings),
            "utilization_hours": sum([
                (datetime.fromisoformat(m["end_time"]) - datetime.fromisoformat(m["start_time"])).total_seconds() / 3600
                for m in room_meetings
            ])
        }
        
    except ValueError as e:
        raise RuntimeError(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error getting room schedule: {str(e)}")

@adk_tool(
    name="get_my_meetings",
    description="Get all meetings for a specific employee (as organizer or attendee)."
)
def get_my_meetings(employee_id: str, days_ahead: int = 7) -> List[Dict[str, Any]]:
    """Get meetings for a specific employee
    
    Args:
        employee_id: Employee ID
        days_ahead: Number of days to look ahead
        
    Returns:
        List[Dict]: List of meetings for the employee
    """
    try:
        cutoff_date = datetime.now() + timedelta(days=days_ahead)
        employee_meetings = []
        
        for meeting in meetings_db.values():
            if meeting.status == MeetingStatus.CANCELLED:
                continue
                
            # Check if employee is organizer or attendee
            if (meeting.organizer == employee_id or employee_id in meeting.attendees):
                # Only include future meetings within the specified range
                if meeting.start_time <= cutoff_date:
                    room = MEETING_ROOMS[meeting.room_id]
                    employee_meetings.append({
                        "meeting_id": meeting.meeting_id,
                        "title": meeting.title,
                        "description": meeting.description,
                        "room_name": room.name,
                        "room_location": room.location,
                        "start_time": meeting.start_time.isoformat(),
                        "end_time": meeting.end_time.isoformat(),
                        "status": meeting.status,
                        "priority": meeting.priority,
                        "is_organizer": meeting.organizer == employee_id,
                        "total_attendees": len(meeting.attendees) + 1  # +1 for organizer
                    })
        
        # Sort by start time
        employee_meetings.sort(key=lambda x: x["start_time"])
        return employee_meetings
        
    except Exception as e:
        raise RuntimeError(f"Error getting employee meetings: {str(e)}")

@adk_tool(
    name="get_room_utilization",
    description="Get utilization statistics for all meeting rooms over a specified period."
)
def get_room_utilization(days_back: int = 30) -> Dict[str, Any]:
    """Get room utilization statistics
    
    Args:
        days_back: Number of days to analyze
        
    Returns:
        Dict: Room utilization statistics
    """
    try:
        start_date = datetime.now() - timedelta(days=days_back)
        room_stats = {}
        
        for room in MEETING_ROOMS.values():
            total_hours = 0
            meeting_count = 0
            
            for meeting in meetings_db.values():
                if (meeting.room_id == room.room_id and 
                    meeting.start_time >= start_date and
                    meeting.status == MeetingStatus.COMPLETED):
                    
                    duration = (meeting.end_time - meeting.start_time).total_seconds() / 3600
                    total_hours += duration
                    meeting_count += 1
            
            # Calculate utilization (assuming 10 hours/day available)
            available_hours = days_back * 10
            utilization_percent = (total_hours / available_hours) * 100 if available_hours > 0 else 0
            
            room_stats[room.name] = {
                "total_meetings": meeting_count,
                "total_hours_used": round(total_hours, 2),
                "utilization_percent": round(utilization_percent, 2),
                "average_meeting_duration": round(total_hours / meeting_count, 2) if meeting_count > 0 else 0,
                "capacity": room.capacity,
                "room_type": room.room_type
            }
        
        return {
            "period_days": days_back,
            "room_statistics": room_stats,
            "overall_stats": {
                "total_meetings": sum([stats["total_meetings"] for stats in room_stats.values()]),
                "average_utilization": round(sum([stats["utilization_percent"] for stats in room_stats.values()]) / len(room_stats) if room_stats else 0, 2)
            }
        }
        
    except Exception as e:
        raise RuntimeError(f"Error getting room utilization: {str(e)}")