# mcp_servers/meeting_server/tools.py - Simplified tools without adk dependencies
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import asyncio

# Meeting room types
ROOM_TYPES = {
    "CONF_A1": {"name": "Flight Operations Center", "capacity": 20, "equipment": ["projector", "flight_displays", "weather_monitors"]},
    "CONF_B1": {"name": "Pilot Briefing Room", "capacity": 12, "equipment": ["projector", "charts", "weather_display"]},
    "EXEC_01": {"name": "Executive Boardroom", "capacity": 8, "equipment": ["projector", "conference_phone", "whiteboard"]},
    "TRAIN_A": {"name": "Training Room A", "capacity": 25, "equipment": ["projector", "simulator_access", "training_materials"]},
    "MAINT_C": {"name": "Maintenance Conference Room", "capacity": 15, "equipment": ["technical_displays", "parts_catalog"]},
    "ATC_BR": {"name": "ATC Briefing Room", "capacity": 10, "equipment": ["radar_displays", "communication_systems"]}
}

# Mock databases
bookings_db: Dict[str, Dict[str, Any]] = {}
room_availability_db: Dict[str, List[Dict[str, Any]]] = {}

async def book_meeting_room(booking_data: Dict[str, Any]) -> Dict[str, Any]:
    """Book a meeting room"""
    try:
        booking_id = f"BOOK_{str(uuid.uuid4())[:8]}"
        room_id = booking_data.get("room_id", "CONF_A1")
        
        booking = {
            "booking_id": booking_id,
            "room_id": room_id,
            "room_name": ROOM_TYPES.get(room_id, {}).get("name", "Unknown Room"),
            "meeting_title": booking_data.get("meeting_title", "Aviation Meeting"),
            "organizer": booking_data.get("organizer", "Unknown"),
            "start_time": booking_data.get("start_time", datetime.now().strftime("%Y-%m-%dT%H:%M:%S")),
            "end_time": booking_data.get("end_time", (datetime.now() + timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")),
            "attendees": booking_data.get("attendees", []),
            "equipment_needed": booking_data.get("equipment_needed", []),
            "status": "confirmed",
            "created_at": datetime.now().isoformat()
        }
        
        bookings_db[booking_id] = booking
        
        return {
            "status": "success",
            "message": f"Room {room_id} booked successfully",
            "booking_id": booking_id,
            "details": booking
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to book room: {str(e)}"
        }

async def check_room_availability(availability_data: Dict[str, Any]) -> Dict[str, Any]:
    """Check room availability"""
    try:
        room_id = availability_data.get("room_id", "CONF_A1")
        check_date = availability_data.get("date", datetime.now().strftime("%Y-%m-%d"))
        
        # Mock availability check
        available_slots = [
            {"start": "09:00", "end": "10:00", "status": "available"},
            {"start": "10:00", "end": "11:00", "status": "booked"},
            {"start": "11:00", "end": "12:00", "status": "available"},
            {"start": "14:00", "end": "15:00", "status": "available"},
            {"start": "15:00", "end": "16:00", "status": "available"},
            {"start": "16:00", "end": "17:00", "status": "maintenance"}
        ]
        
        return {
            "status": "success",
            "message": f"Availability checked for room {room_id}",
            "room_id": room_id,
            "room_name": ROOM_TYPES.get(room_id, {}).get("name", "Unknown Room"),
            "date": check_date,
            "availability": available_slots,
            "total_available_slots": len([slot for slot in available_slots if slot["status"] == "available"])
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to check availability: {str(e)}"
        }

async def cancel_booking(cancel_data: Dict[str, Any]) -> Dict[str, Any]:
    """Cancel a room booking"""
    try:
        booking_id = cancel_data.get("booking_id")
        reason = cancel_data.get("reason", "User requested cancellation")
        
        if booking_id in bookings_db:
            booking = bookings_db[booking_id]
            booking["status"] = "cancelled"
            booking["cancellation_reason"] = reason
            booking["cancelled_at"] = datetime.now().isoformat()
            
            return {
                "status": "success",
                "message": f"Booking {booking_id} cancelled successfully",
                "booking_id": booking_id,
                "details": booking
            }
        else:
            return {
                "status": "error",
                "message": f"Booking {booking_id} not found"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to cancel booking: {str(e)}"
        }

async def generate_meeting_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate meeting room reports"""
    try:
        report_type = report_data.get("report_type", "utilization")
        report_id = f"RPT_{str(uuid.uuid4())[:8]}"
        
        if report_type == "room_utilization":
            report_content = {
                "total_rooms": len(ROOM_TYPES),
                "total_bookings": len(bookings_db),
                "active_bookings": len([b for b in bookings_db.values() if b.get("status") == "confirmed"]),
                "cancelled_bookings": len([b for b in bookings_db.values() if b.get("status") == "cancelled"]),
                "room_details": ROOM_TYPES,
                "utilization_rate": "85%" # Mock rate
            }
        else:
            report_content = {
                "message": f"Report type '{report_type}' generated",
                "data": {
                    "rooms": len(ROOM_TYPES),
                    "bookings": len(bookings_db)
                }
            }
        
        return {
            "status": "success",
            "message": f"Meeting report generated successfully",
            "report_id": report_id,
            "report_type": report_type,
            "content": report_content,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate report: {str(e)}"
        }