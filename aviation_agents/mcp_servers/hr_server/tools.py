# mcp_servers/hr_server/tools.py - Simplified tools without adk dependencies
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid
import asyncio

# Aviation industry departments
VALID_DEPARTMENTS = [
    "Flight Operations", "Maintenance", "Ground Services", "Air Traffic Control",
    "Safety & Security", "Customer Service", "Cargo Operations", "Engineering",
    "Quality Assurance", "Training", "Human Resources", "Finance"
]

# Mock database (in production, this would be a proper database)
employees_db: Dict[str, Dict[str, Any]] = {}
certifications_db: Dict[str, List[Dict[str, Any]]] = {}
trainings_db: Dict[str, List[Dict[str, Any]]] = {}

async def create_employee_record(employee_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a new employee record"""
    try:
        employee_id = employee_data.get("employee_id", f"EMP_{str(uuid.uuid4())[:8]}")
        
        employee = {
            "employee_id": employee_id,
            "name": employee_data.get("name", "Unknown"),
            "position": employee_data.get("position", "Staff"),
            "department": employee_data.get("department", "General"),
            "hire_date": employee_data.get("hire_date", datetime.now().strftime("%Y-%m-%d")),
            "certifications": employee_data.get("certifications", []),
            "status": "active",
            "created_at": datetime.now().isoformat()
        }
        
        employees_db[employee_id] = employee
        
        return {
            "status": "success",
            "message": f"Employee {employee['name']} created successfully",
            "employee_id": employee_id,
            "details": employee
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to create employee: {str(e)}"
        }

async def schedule_training(training_data: Dict[str, Any]) -> Dict[str, Any]:
    """Schedule training for an employee"""
    try:
        training_id = f"TRN_{str(uuid.uuid4())[:8]}"
        employee_id = training_data.get("employee_id")
        
        training = {
            "training_id": training_id,
            "employee_id": employee_id,
            "training_type": training_data.get("training_type", "General Training"),
            "scheduled_date": training_data.get("scheduled_date", datetime.now().strftime("%Y-%m-%d")),
            "instructor": training_data.get("instructor", "TBD"),
            "duration_hours": training_data.get("duration_hours", 8),
            "status": "scheduled",
            "created_at": datetime.now().isoformat()
        }
        
        if employee_id not in trainings_db:
            trainings_db[employee_id] = []
        trainings_db[employee_id].append(training)
        
        return {
            "status": "success",
            "message": f"Training scheduled successfully",
            "training_id": training_id,
            "details": training
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to schedule training: {str(e)}"
        }

async def track_certification(cert_data: Dict[str, Any]) -> Dict[str, Any]:
    """Track employee certification"""
    try:
        cert_id = f"CERT_{str(uuid.uuid4())[:8]}"
        employee_id = cert_data.get("employee_id")
        
        certification = {
            "certification_id": cert_id,
            "employee_id": employee_id,
            "certification_type": cert_data.get("certification_type", "Unknown"),
            "certification_number": cert_data.get("certification_number", ""),
            "issue_date": cert_data.get("issue_date", datetime.now().strftime("%Y-%m-%d")),
            "expiry_date": cert_data.get("expiry_date", ""),
            "status": cert_data.get("status", "active"),
            "created_at": datetime.now().isoformat()
        }
        
        if employee_id not in certifications_db:
            certifications_db[employee_id] = []
        certifications_db[employee_id].append(certification)
        
        return {
            "status": "success",
            "message": f"Certification tracked successfully",
            "certification_id": cert_id,
            "details": certification
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to track certification: {str(e)}"
        }

async def generate_hr_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate HR reports"""
    try:
        report_type = report_data.get("report_type", "summary")
        report_id = f"RPT_{str(uuid.uuid4())[:8]}"
        
        if report_type == "employee_summary":
            report_content = {
                "total_employees": len(employees_db),
                "active_employees": len([e for e in employees_db.values() if e.get("status") == "active"]),
                "departments": list(set([e.get("department") for e in employees_db.values()])),
                "recent_hires": [e for e in employees_db.values() if 
                               datetime.strptime(e.get("hire_date", "1900-01-01"), "%Y-%m-%d") > 
                               datetime.now() - timedelta(days=30)]
            }
        else:
            report_content = {
                "message": f"Report type '{report_type}' generated",
                "data": {
                    "employees": len(employees_db),
                    "certifications": sum(len(certs) for certs in certifications_db.values()),
                    "trainings": sum(len(trainings) for trainings in trainings_db.values())
                }
            }
        
        return {
            "status": "success",
            "message": f"HR report generated successfully",
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