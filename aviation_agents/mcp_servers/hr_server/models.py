# mcp_servers/hr_server/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime, date
from enum import Enum

# Import from adktools
from adktools.models import DomainError

class EmployeeStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    ON_LEAVE = "on_leave"
    TERMINATED = "terminated"

class CertificationType(str, Enum):
    PILOT_LICENSE = "pilot_license"
    MECHANIC_LICENSE = "mechanic_license" 
    ATC_LICENSE = "atc_license"
    DISPATCHER_LICENSE = "dispatcher_license"
    SAFETY_CERTIFICATION = "safety_certification"

class Employee(BaseModel):
    employee_id: str
    first_name: str
    last_name: str
    email: str
    department: str
    position: str
    hire_date: date
    status: EmployeeStatus
    manager_id: Optional[str] = None
    certifications: List[str] = []
    next_training_date: Optional[date] = None

class Certification(BaseModel):
    cert_id: str
    employee_id: str
    cert_type: CertificationType
    cert_number: str
    issue_date: date
    expiry_date: date
    issuing_authority: str
    is_valid: bool = True

class TrainingRecord(BaseModel):
    training_id: str
    employee_id: str
    course_name: str
    training_type: str  # "initial", "recurrent", "upgrade"
    completion_date: Optional[date] = None
    score: Optional[float] = None
    instructor: Optional[str] = None
    next_due_date: Optional[date] = None

# Input Models
class CreateEmployeeInput(BaseModel):
    first_name: str = Field(..., description="Employee's first name")
    last_name: str = Field(..., description="Employee's last name") 
    email: str = Field(..., description="Employee's work email")
    department: str = Field(..., description="Department (e.g., Flight Operations, Maintenance, Ground Services)")
    position: str = Field(..., description="Job position/title")
    manager_id: Optional[str] = Field(None, description="Manager's employee ID")

class UpdateCertificationInput(BaseModel):
    employee_id: str = Field(..., description="Employee ID")
    cert_type: CertificationType = Field(..., description="Type of certification")
    cert_number: str = Field(..., description="Certification number")
    issue_date: date = Field(..., description="Date when certification was issued")
    expiry_date: date = Field(..., description="Certification expiry date")
    issuing_authority: str = Field(..., description="Authority that issued the certification")

class ScheduleTrainingInput(BaseModel):
    employee_id: str = Field(..., description="Employee ID")
    course_name: str = Field(..., description="Name of the training course")
    training_type: str = Field(..., description="Type of training: initial, recurrent, or upgrade")
    scheduled_date: date = Field(..., description="Scheduled training date")

class SearchEmployeesInput(BaseModel):
    department: Optional[str] = Field(None, description="Filter by department")
    position: Optional[str] = Field(None, description="Filter by position")
    certification_type: Optional[CertificationType] = Field(None, description="Filter by certification type")
    status: Optional[EmployeeStatus] = Field(None, description="Filter by employee status")

# Error Models
class EmployeeNotFoundError(DomainError):
    employee_id: str = Field(..., description="The employee ID that was not found")
    error_type: Literal["employee_not_found"] = "employee_not_found"

class CertificationExpiredError(DomainError):
    employee_id: str = Field(..., description="Employee ID with expired certification")
    cert_type: str = Field(..., description="Type of expired certification")
    expiry_date: date = Field(..., description="When the certification expired")
    error_type: Literal["certification_expired"] = "certification_expired"

class InvalidDepartmentError(DomainError):
    department: str = Field(..., description="The invalid department name")
    valid_departments: List[str] = Field(..., description="List of valid departments")
    error_type: Literal["invalid_department"] = "invalid_department"