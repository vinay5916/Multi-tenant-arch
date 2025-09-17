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
    """Create a new employee record
    
    Args:
        first_name: Employee's first name
        last_name: Employee's last name
        email: Employee's work email address
        department: Department (must be valid aviation department)
        position: Job position/title
        manager_id: Optional manager's employee ID
        
    Returns:
        Employee: The created employee record
        InvalidDepartmentError: If department is not valid
    """
    try:
        # Validate department
        if department not in VALID_DEPARTMENTS:
            return InvalidDepartmentError(
                department=department,
                valid_departments=VALID_DEPARTMENTS,
                message=f"Invalid department '{department}'. Must be one of: {', '.join(VALID_DEPARTMENTS)}"
            )
        
        # Generate employee ID
        employee_id = f"EMP{uuid.uuid4().hex[:8].upper()}"
        
        # Create employee
        employee = Employee(
            employee_id=employee_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            department=department,
            position=position,
            hire_date=date.today(),
            status=EmployeeStatus.ACTIVE,
            manager_id=manager_id
        )
        
        # Store in mock database
        employees_db[employee_id] = employee
        certifications_db[employee_id] = []
        trainings_db[employee_id] = []
        
        return employee
        
    except Exception as e:
        raise RuntimeError(f"Error creating employee: {str(e)}")

@adk_tool(
    name="search_employees",
    description="Search for employees based on various criteria. Useful for finding staff with specific qualifications or in specific departments."
)
def search_employees(
    department: Optional[str] = None,
    position: Optional[str] = None,
    certification_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[Employee]:
    """Search employees by various criteria
    
    Args:
        department: Filter by department
        position: Filter by position
        certification_type: Filter by certification type
        status: Filter by employee status
        
    Returns:
        List[Employee]: List of employees matching the criteria
    """
    try:
        results = []
        
        for employee in employees_db.values():
            # Check filters
            if department and employee.department != department:
                continue
            if position and position.lower() not in employee.position.lower():
                continue
            if status and employee.status != status:
                continue
            if certification_type:
                # Check if employee has this certification type
                employee_certs = certifications_db.get(employee.employee_id, [])
                has_cert = any(cert.cert_type == certification_type for cert in employee_certs)
                if not has_cert:
                    continue
                    
            results.append(employee)
            
        return results
        
    except Exception as e:
        raise RuntimeError(f"Error searching employees: {str(e)}")

@adk_tool(
    name="update_certification",
    description="Add or update an employee's certification. Critical for maintaining compliance in aviation operations."
)
def update_certification(
    employee_id: str,
    cert_type: str,
    cert_number: str,
    issue_date: str,  # ISO format date string
    expiry_date: str,  # ISO format date string
    issuing_authority: str
) -> Certification | EmployeeNotFoundError:
    """Update or add employee certification
    
    Args:
        employee_id: Employee ID
        cert_type: Type of certification
        cert_number: Certification number
        issue_date: Issue date in YYYY-MM-DD format
        expiry_date: Expiry date in YYYY-MM-DD format
        issuing_authority: Authority that issued the certification
        
    Returns:
        Certification: The updated certification record
        EmployeeNotFoundError: If employee doesn't exist
    """
    try:
        # Check if employee exists
        if employee_id not in employees_db:
            return EmployeeNotFoundError(
                employee_id=employee_id,
                message=f"Employee with ID '{employee_id}' not found"
            )
        
        # Parse dates
        issue_dt = datetime.strptime(issue_date, "%Y-%m-%d").date()
        expiry_dt = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        
        # Create certification
        cert_id = f"CERT{uuid.uuid4().hex[:8].upper()}"
        certification = Certification(
            cert_id=cert_id,
            employee_id=employee_id,
            cert_type=CertificationType(cert_type),
            cert_number=cert_number,
            issue_date=issue_dt,
            expiry_date=expiry_dt,
            issuing_authority=issuing_authority,
            is_valid=expiry_dt > date.today()
        )
        
        # Store certification
        if employee_id not in certifications_db:
            certifications_db[employee_id] = []
        certifications_db[employee_id].append(certification)
        
        return certification
        
    except ValueError as e:
        raise RuntimeError(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error updating certification: {str(e)}")

@adk_tool(
    name="check_expiring_certifications",
    description="Check for certifications that are expiring soon. Critical for maintaining operational compliance."
)
def check_expiring_certifications(days_ahead: int = 30) -> List[Dict[str, Any]]:
    """Check for certifications expiring within specified days
    
    Args:
        days_ahead: Number of days to look ahead for expiring certifications
        
    Returns:
        List[Dict]: List of expiring certifications with employee details
    """
    try:
        expiring = []
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        for employee_id, certs in certifications_db.items():
            employee = employees_db.get(employee_id)
            if not employee:
                continue
                
            for cert in certs:
                if cert.expiry_date <= cutoff_date and cert.is_valid:
                    expiring.append({
                        "employee_id": employee_id,
                        "employee_name": f"{employee.first_name} {employee.last_name}",
                        "department": employee.department,
                        "position": employee.position,
                        "cert_type": cert.cert_type,
                        "cert_number": cert.cert_number,
                        "expiry_date": cert.expiry_date.isoformat(),
                        "days_until_expiry": (cert.expiry_date - date.today()).days,
                        "issuing_authority": cert.issuing_authority
                    })
        
        # Sort by expiry date
        expiring.sort(key=lambda x: x["expiry_date"])
        return expiring
        
    except Exception as e:
        raise RuntimeError(f"Error checking expiring certifications: {str(e)}")

@adk_tool(
    name="schedule_training",
    description="Schedule training for an employee. Essential for maintaining currency and compliance in aviation operations."
)
def schedule_training(
    employee_id: str,
    course_name: str,
    training_type: str,
    scheduled_date: str  # ISO format date string
) -> TrainingRecord | EmployeeNotFoundError:
    """Schedule training for an employee
    
    Args:
        employee_id: Employee ID
        course_name: Name of the training course
        training_type: Type of training (initial, recurrent, upgrade)
        scheduled_date: Scheduled date in YYYY-MM-DD format
        
    Returns:
        TrainingRecord: The scheduled training record
        EmployeeNotFoundError: If employee doesn't exist
    """
    try:
        # Check if employee exists
        if employee_id not in employees_db:
            return EmployeeNotFoundError(
                employee_id=employee_id,
                message=f"Employee with ID '{employee_id}' not found"
            )
        
        # Parse scheduled date
        scheduled_dt = datetime.strptime(scheduled_date, "%Y-%m-%d").date()
        
        # Create training record
        training_id = f"TRN{uuid.uuid4().hex[:8].upper()}"
        training = TrainingRecord(
            training_id=training_id,
            employee_id=employee_id,
            course_name=course_name,
            training_type=training_type,
            next_due_date=scheduled_dt
        )
        
        # Store training record
        if employee_id not in trainings_db:
            trainings_db[employee_id] = []
        trainings_db[employee_id].append(training)
        
        # Update employee's next training date
        employee = employees_db[employee_id]
        if not employee.next_training_date or scheduled_dt < employee.next_training_date:
            employee.next_training_date = scheduled_dt
        
        return training
        
    except ValueError as e:
        raise RuntimeError(f"Invalid date format: {str(e)}")
    except Exception as e:
        raise RuntimeError(f"Error scheduling training: {str(e)}")

@adk_tool(
    name="get_employee_details",
    description="Get detailed information about a specific employee including certifications and training records."
)
def get_employee_details(employee_id: str) -> Dict[str, Any] | EmployeeNotFoundError:
    """Get complete employee details including certifications and training
    
    Args:
        employee_id: Employee ID to look up
        
    Returns:
        Dict: Complete employee information
        EmployeeNotFoundError: If employee doesn't exist
    """
    try:
        # Check if employee exists
        if employee_id not in employees_db:
            return EmployeeNotFoundError(
                employee_id=employee_id,
                message=f"Employee with ID '{employee_id}' not found"
            )
        
        employee = employees_db[employee_id]
        certs = certifications_db.get(employee_id, [])
        trainings = trainings_db.get(employee_id, [])
        
        return {
            "employee": employee.dict(),
            "certifications": [cert.dict() for cert in certs],
            "training_records": [training.dict() for training in trainings],
            "certification_status": {
                "total_certs": len(certs),
                "valid_certs": len([c for c in certs if c.is_valid]),
                "expired_certs": len([c for c in certs if not c.is_valid])
            }
        }
        
    except Exception as e:
        raise RuntimeError(f"Error getting employee details: {str(e)}")

@adk_tool(
    name="get_department_summary",
    description="Get summary statistics and information for a specific department."
)
def get_department_summary(department: str) -> Dict[str, Any] | InvalidDepartmentError:
    """Get department summary including employee count, certifications, etc.
    
    Args:
        department: Department name
        
    Returns:
        Dict: Department summary information
        InvalidDepartmentError: If department is not valid
    """
    try:
        # Validate department
        if department not in VALID_DEPARTMENTS:
            return InvalidDepartmentError(
                department=department,
                valid_departments=VALID_DEPARTMENTS,
                message=f"Invalid department '{department}'. Must be one of: {', '.join(VALID_DEPARTMENTS)}"
            )
        
        # Get department employees
        dept_employees = [emp for emp in employees_db.values() if emp.department == department]
        
        # Count by status
        status_counts = {}
        for status in EmployeeStatus:
            status_counts[status.value] = len([emp for emp in dept_employees if emp.status == status])
        
        # Count certifications
        total_certs = 0
        expiring_soon = 0
        cutoff_date = date.today() + timedelta(days=30)
        
        for emp in dept_employees:
            emp_certs = certifications_db.get(emp.employee_id, [])
            total_certs += len(emp_certs)
            expiring_soon += len([c for c in emp_certs if c.expiry_date <= cutoff_date and c.is_valid])
        
        return {
            "department": department,
            "total_employees": len(dept_employees),
            "employee_status_breakdown": status_counts,
            "certification_summary": {
                "total_certifications": total_certs,
                "certifications_expiring_soon": expiring_soon
            },
            "common_positions": list(set([emp.position for emp in dept_employees]))
        }
        
    except Exception as e:
        raise RuntimeError(f"Error getting department summary: {str(e)}")